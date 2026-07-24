from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.http import urlencode
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SynonymEntryForm
from .models import SynonymEntry, SynonymItem
from .services import parse_synonym_item_lines
from .synonym_ai import SynonymAIError, generate_synonym_data, generate_synonym_exam


def _replace_synonym_items(entry: SynonymEntry, raw_text: str) -> None:
    items = parse_synonym_item_lines(raw_text)

    entry.items.all().delete()

    objs = [
        SynonymItem(
            entry=entry,
            word=item.word,
            usage_context=item.usage_context,
            fixed_sentence=item.fixed_sentence,
            comparison_note=item.comparison_note,
        )
        for item in items
    ]
    if objs:
        SynonymItem.objects.bulk_create(objs)


def _normalize_answer(value: str) -> str:
    return " ".join((value or "").casefold().strip().split())


def _review_context(entry: SynonymEntry, result: dict | None = None) -> dict:
    items = list(entry.items.all())
    learned_count = SynonymEntry.objects.filter(user=entry.user, is_learned=True).count()
    pending_count = SynonymEntry.objects.filter(user=entry.user, is_learned=False).count()
    return {
        "entry": entry,
        "items": items,
        "result": result,
        "learned_count": learned_count,
        "pending_count": pending_count,
    }


@login_required
@require_POST
def synonym_ai_generate(request):
    try:
        data = generate_synonym_data(
            request.POST.get("headword", ""),
            request.POST.get("known_words", ""),
        )
    except SynonymAIError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse(data)


@login_required
def synonym_list(request):
    sort = request.GET.get("sort", "created_desc")
    sort_options = {
        "created_desc": ("-created_at", "时间倒序"),
        "created_asc": ("created_at", "时间正序"),
    }
    order_by, sort_label = sort_options.get(sort, sort_options["created_desc"])
    entries = (
        SynonymEntry.objects
        .filter(user=request.user)
        .prefetch_related("items")
        .order_by(order_by, "headword")
    )
    return render(request, "synonyms/synonym_list.html", {
        "entries": entries,
        "sort": sort if sort in sort_options else "created_desc",
        "sort_label": sort_label,
    })


@login_required
def synonym_detail(request, pk):
    entry = get_object_or_404(SynonymEntry, pk=pk, user=request.user)
    items = list(entry.items.all())
    return render(request, "synonyms/synonym_detail.html", {
        "entry": entry,
        "items": items,
        "practice_items": [
            {
                "word": item.word,
                "context": item.usage_context,
                "sentence": item.fixed_sentence,
                "note": item.comparison_note,
            }
            for item in items
        ],
    })


@login_required
def synonym_create(request):
    if request.method == "POST":
        form = SynonymEntryForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                entry = form.save(commit=False)
                entry.user = request.user
                entry.save()
                raw_words = form.cleaned_data.get("synonym_words", "")
                _replace_synonym_items(entry, raw_words)

            return redirect("synonym_detail", pk=entry.pk)
    else:
        form = SynonymEntryForm()

    return render(request, "synonyms/synonym_form.html", {
        "form": form,
        "mode": "create",
    })


@login_required
def synonym_update(request, pk):
    entry = get_object_or_404(SynonymEntry, pk=pk, user=request.user)

    initial_words = "\n".join(
        " | ".join(part for part in [
            item.word,
            item.usage_context,
            item.fixed_sentence,
            item.comparison_note,
        ] if part)
        for item in entry.items.all()
    )

    if request.method == "POST":
        form = SynonymEntryForm(request.POST, instance=entry)
        if form.is_valid():
            with transaction.atomic():
                entry = form.save()
                raw_words = form.cleaned_data.get("synonym_words", "")
                _replace_synonym_items(entry, raw_words)
            return redirect("synonym_detail", pk=entry.pk)
    else:
        form = SynonymEntryForm(instance=entry, initial={
            "synonym_words": initial_words,
        })

    return render(request, "synonyms/synonym_form.html", {
        "form": form,
        "mode": "update",
        "entry": entry,
    })


@login_required
def synonym_delete(request, pk):
    entry = get_object_or_404(SynonymEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("synonym_list")

    return render(request, "synonyms/synonym_confirm_delete.html", {
        "entry": entry,
    })


def _build_default_exam(entry: SynonymEntry, items: list[SynonymItem]) -> dict:
    return {
        "question": entry.example_sentence or f"请写出一个适合表达“{entry.meaning_cn or entry.headword}”的替换词组。",
        "instruction": "写出一个最合适的英文词或词组。点击 AI 出题可以生成更具体的语境题。",
        "acceptable_answers": [item.word for item in items],
        "explanation": "判定会按本组同义词表中的可接受答案进行；答题后会显示区别说明，帮助你确认语境。",
    }


def _exam_context(entry: SynonymEntry, items: list[SynonymItem], exam: dict | None = None, result: dict | None = None, error: str = "") -> dict:
    exam = exam or _build_default_exam(entry, items)
    return {
        "entry": entry,
        "items": items,
        "exam": exam,
        "result": result,
        "error": error,
        "answers_text": "\n".join(exam.get("acceptable_answers", [])),
        "generate_query": urlencode({"generate": "1"}),
    }


@login_required
def synonym_exam(request, pk):
    entry = get_object_or_404(
        SynonymEntry.objects.prefetch_related("items"),
        pk=pk,
        user=request.user,
    )
    items = list(entry.items.all())

    if request.method == "POST":
        answer = request.POST.get("answer", "")
        accepted = [line.strip() for line in request.POST.get("acceptable_answers", "").splitlines() if line.strip()]
        table_answers = [item.word for item in items]
        allowed = accepted or table_answers
        normalized_answer = _normalize_answer(answer)
        normalized_allowed = {_normalize_answer(value) for value in allowed}
        is_correct = bool(normalized_answer and normalized_answer in normalized_allowed)

        entry.review_attempts += 1
        entry.reviewed_at = timezone.now()
        if is_correct:
            entry.review_correct += 1
            entry.is_learned = True
        else:
            entry.is_learned = False
        entry.save(update_fields=["review_attempts", "review_correct", "reviewed_at", "is_learned", "updated_at"])

        exam = {
            "question": request.POST.get("question", ""),
            "instruction": request.POST.get("instruction", ""),
            "acceptable_answers": allowed,
            "explanation": request.POST.get("explanation", ""),
        }
        result = {
            "is_correct": is_correct,
            "answer": answer.strip(),
            "correct_words": allowed,
        }
        return render(request, "synonyms/synonym_exam.html", _exam_context(entry, items, exam, result))

    error = ""
    exam = None
    if request.GET.get("generate") == "1":
        try:
            exam = generate_synonym_exam(entry, items)
        except SynonymAIError as exc:
            error = str(exc)
    return render(request, "synonyms/synonym_exam.html", _exam_context(entry, items, exam, error=error))


@login_required
def synonym_review_list(request):
    entries = (
        SynonymEntry.objects
        .filter(user=request.user)
        .prefetch_related("items")
        .order_by("is_learned", "reviewed_at", "headword")
    )
    learned_count = entries.filter(is_learned=True).count()
    pending_count = entries.filter(is_learned=False).count()
    return render(request, "synonyms/synonym_review_list.html", {
        "entries": entries,
        "learned_count": learned_count,
        "pending_count": pending_count,
    })


@login_required
def synonym_review(request, pk):
    entry = get_object_or_404(
        SynonymEntry.objects.prefetch_related("items"),
        pk=pk,
        user=request.user,
    )
    items = list(entry.items.all())

    if request.method == "POST":
        answer = request.POST.get("answer", "")
        normalized_answer = _normalize_answer(answer)
        accepted = {_normalize_answer(item.word) for item in items}
        is_correct = bool(normalized_answer and normalized_answer in accepted)

        entry.review_attempts += 1
        entry.reviewed_at = timezone.now()
        if is_correct:
            entry.review_correct += 1
            entry.is_learned = True
        else:
            entry.is_learned = False
        entry.save(update_fields=["review_attempts", "review_correct", "reviewed_at", "is_learned", "updated_at"])

        result = {
            "is_correct": is_correct,
            "answer": answer.strip(),
            "correct_words": [item.word for item in items],
        }
        return render(request, "synonyms/synonym_review.html", _review_context(entry, result))

    return render(request, "synonyms/synonym_review.html", _review_context(entry))
