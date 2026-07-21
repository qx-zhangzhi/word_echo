from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .phrase_ai import translate_phrase_with_ai
from .forms import PhraseEntryForm
from .models import PhraseEntry


@login_required
def phrase_list(request):
    entries = PhraseEntry.objects.filter(user=request.user)

    q = (request.GET.get("q") or "").strip()
    category = (request.GET.get("category") or "").strip()

    if q:
        entries = entries.filter(english_text__icontains=q)

    if category:
        entries = entries.filter(category=category)

    return render(request, "phrases/phrase_list.html", {
        "entries": entries,
        "q": q,
        "category": category,
    })


@login_required
def phrase_detail(request, pk):
    entry = get_object_or_404(PhraseEntry, pk=pk, user=request.user)
    return render(request, "phrases/phrase_detail.html", {
        "entry": entry,
    })


@login_required
def phrase_create(request):
    if request.method == "POST":
        form = PhraseEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user

            if not entry.chinese_text.strip():
                entry.chinese_text = translate_phrase_with_ai(entry.english_text)

            entry.save()
            return redirect("phrase_detail", pk=entry.pk)
    else:
        form = PhraseEntryForm()

    return render(request, "phrases/phrase_form.html", {
        "form": form,
        "mode": "create",
    })


@login_required
def phrase_update(request, pk):
    entry = get_object_or_404(PhraseEntry, pk=pk, user=request.user)

    if request.method == "POST":
        form = PhraseEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save()
            return redirect("phrase_detail", pk=entry.pk)
    else:
        form = PhraseEntryForm(instance=entry)

    return render(request, "phrases/phrase_form.html", {
        "form": form,
        "mode": "update",
        "entry": entry,
    })


@login_required
def phrase_delete(request, pk):
    entry = get_object_or_404(PhraseEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("phrase_list")

    return render(request, "phrases/phrase_confirm_delete.html", {
        "entry": entry,
    })


@login_required
def phrase_translate_api(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)

    english_text = (request.POST.get("english_text") or "").strip()
    if not english_text:
        return JsonResponse({"ok": False, "error": "english_text is required"}, status=400)

    chinese_text = translate_phrase_with_ai(english_text)
    return JsonResponse({
        "ok": True,
        "chinese_text": chinese_text,
    })
