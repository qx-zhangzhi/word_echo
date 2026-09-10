import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CambridgeVocabEntryForm, CambridgeVocabImportForm
from .models import CambridgeVocabEntry


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("cambridge_vocab_list")


def _filtered_entries(request):
    entries = CambridgeVocabEntry.objects.filter(user=request.user)

    skill = request.GET.get("skill", "")
    entry_type = request.GET.get("entry_type", "")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()

    if skill in {"listening", "reading"}:
        entries = entries.filter(skill=skill)
    else:
        skill = ""

    if entry_type in {"unknown", "answer", "synonym"}:
        entries = entries.filter(entry_type=entry_type)
    else:
        entry_type = ""

    if status == "learned":
        entries = entries.filter(is_learned=True)
    elif status == "pending":
        entries = entries.filter(is_learned=False)
    else:
        status = ""

    if query:
        entries = entries.filter(
            Q(word__icontains=query)
            | Q(meaning_cn__icontains=query)
            | Q(synonym_replacements__icontains=query)
            | Q(book__icontains=query)
            | Q(test__icontains=query)
            | Q(section_or_passage__icontains=query)
            | Q(question_numbers__icontains=query)
            | Q(source_title__icontains=query)
            | Q(source_detail__icontains=query)
        )

    return entries, {
        "skill": skill,
        "entry_type": entry_type,
        "status": status,
        "q": query,
    }


@login_required
def entry_list(request):
    entries, filters = _filtered_entries(request)
    sort = request.GET.get("sort", "created_desc")
    sort_options = {
        "created_desc": ("-created_at", "word"),
        "source": ("skill", "book", "test", "section_or_passage", "question_numbers", "word"),
        "unlearned": ("is_learned", "-created_at", "word"),
        "learned_recent": ("-learned_at", "-created_at", "word"),
    }
    order_by = sort_options.get(sort, sort_options["created_desc"])
    if sort not in sort_options:
        sort = "created_desc"

    stats = CambridgeVocabEntry.objects.filter(user=request.user).aggregate(
        total=Count("id"),
        listening=Count("id", filter=Q(skill="listening")),
        reading=Count("id", filter=Q(skill="reading")),
        pending=Count("id", filter=Q(is_learned=False)),
    )

    return render(request, "cambridge_vocab/entry_list.html", {
        "entries": entries.order_by(*order_by),
        "filters": filters,
        "sort": sort,
        "stats": stats,
        "skill_choices": CambridgeVocabEntry.SKILL_CHOICES,
        "entry_type_choices": CambridgeVocabEntry.ENTRY_TYPE_CHOICES,
    })


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(CambridgeVocabEntry, pk=pk, user=request.user)
    return render(request, "cambridge_vocab/entry_detail.html", {"entry": entry})


@login_required
def entry_create(request):
    if request.method == "POST":
        form = CambridgeVocabEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect("cambridge_vocab_detail", pk=entry.pk)
    else:
        form = CambridgeVocabEntryForm()

    return render(request, "cambridge_vocab/entry_form.html", {"form": form, "mode": "create"})


def _clean_entry_payload(item):
    allowed = {
        "skill",
        "entry_type",
        "word",
        "meaning_cn",
        "synonym_replacements",
        "original_expression",
        "example_sentence",
        "book",
        "test",
        "section_or_passage",
        "question_numbers",
        "source_title",
        "source_detail",
        "note",
    }
    payload = {key: str(value).strip() for key, value in item.items() if key in allowed and value is not None}
    if payload.get("skill") not in {"listening", "reading"}:
        raise ValidationError("skill 只能是 listening 或 reading")
    if payload.get("entry_type") not in {"unknown", "answer", "synonym"}:
        payload["entry_type"] = "unknown"
    if not payload.get("word"):
        raise ValidationError("word 不能为空")
    return payload


def _parse_import_payload(raw_text):
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON 格式不对：第 {exc.lineno} 行附近有问题") from exc

    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValidationError("请粘贴 JSON 数组，或者包含 entries 数组的 JSON 对象")

    entries = []
    errors = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"第 {index} 条不是对象")
            continue
        try:
            entries.append(_clean_entry_payload(item))
        except ValidationError as exc:
            errors.append(f"第 {index} 条：{exc.messages[0]}")

    if errors:
        raise ValidationError(errors)
    if not entries:
        raise ValidationError("没有找到可导入的词条")
    return entries


def _import_entries(user, entries):
    result = {"created": 0, "updated": 0}
    for payload in entries:
        lookup = {
            "user": user,
            "skill": payload["skill"],
            "book": payload.get("book", ""),
            "test": payload.get("test", ""),
            "section_or_passage": payload.get("section_or_passage", ""),
            "question_numbers": payload.get("question_numbers", ""),
            "word": payload["word"],
        }
        defaults = {key: value for key, value in payload.items() if key not in lookup}
        _, created = CambridgeVocabEntry.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        if created:
            result["created"] += 1
        else:
            result["updated"] += 1
    return result


@login_required
def entry_import(request):
    result = None
    if request.method == "POST":
        form = CambridgeVocabImportForm(request.POST)
        if form.is_valid():
            try:
                entries = _parse_import_payload(form.cleaned_data["raw_text"])
                result = _import_entries(request.user, entries)
            except ValidationError as exc:
                form.add_error("raw_text", exc)
    else:
        form = CambridgeVocabImportForm()

    return render(request, "cambridge_vocab/entry_import.html", {
        "form": form,
        "result": result,
    })


@login_required
def entry_update(request, pk):
    entry = get_object_or_404(CambridgeVocabEntry, pk=pk, user=request.user)
    if request.method == "POST":
        form = CambridgeVocabEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("cambridge_vocab_detail", pk=entry.pk)
    else:
        form = CambridgeVocabEntryForm(instance=entry)

    return render(request, "cambridge_vocab/entry_form.html", {"form": form, "mode": "update", "entry": entry})


@login_required
def entry_delete(request, pk):
    entry = get_object_or_404(CambridgeVocabEntry, pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        return redirect("cambridge_vocab_list")
    return render(request, "cambridge_vocab/entry_confirm_delete.html", {"entry": entry})


@login_required
@require_POST
def entry_toggle_learned(request, pk):
    entry = get_object_or_404(CambridgeVocabEntry, pk=pk, user=request.user)
    if entry.is_learned:
        entry.is_learned = False
        entry.learned_at = None
    else:
        entry.is_learned = True
        entry.learned_at = timezone.now()
    entry.save(update_fields=["is_learned", "learned_at", "updated_at"])
    return redirect(_safe_next_url(request))
