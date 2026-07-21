from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SynonymEntryForm
from .models import SynonymEntry, SynonymItem
from .services import parse_synonym_item_lines
from .synonym_ai import SynonymAIError, generate_synonym_data


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
    entries = SynonymEntry.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "synonyms/synonym_list.html", {
        "entries": entries,
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
