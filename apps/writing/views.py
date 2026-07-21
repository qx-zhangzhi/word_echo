from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe

from .forms import WritingEntryForm
from .models import WritingEntry, WritingHighlightWord
from .services import highlight_text, parse_highlight_words


def _replace_highlight_words(entry: WritingEntry, raw_text: str) -> None:
    words = parse_highlight_words(raw_text)

    entry.highlight_words.all().delete()

    objs = [WritingHighlightWord(entry=entry, word=w) for w in words]
    if objs:
        WritingHighlightWord.objects.bulk_create(objs)


@login_required
def writing_list(request):
    entries = WritingEntry.objects.filter(user=request.user)
    return render(request, "writing/writing_list.html", {"entries": entries})


@login_required
def writing_detail(request, pk):
    entry = get_object_or_404(WritingEntry, pk=pk, user=request.user)
    words = list(entry.highlight_words.values_list("word", flat=True))
    highlighted_html = highlight_text(entry.content, words)

    return render(request, "writing/writing_detail.html", {
        "entry": entry,
        "highlight_words": words,
        "highlighted_html": mark_safe(highlighted_html),
    })

@login_required
def writing_create(request):
    if request.method == "POST":
        form = WritingEntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()

            raw_words = form.cleaned_data.get("highlight_words", "")
            _replace_highlight_words(entry, raw_words)

            return redirect("writing_detail", pk=entry.pk)
    else:
        form = WritingEntryForm()

    return render(request, "writing/writing_form.html", {
        "form": form,
        "mode": "create",
    })

@login_required
def writing_update(request, pk):
    entry = get_object_or_404(WritingEntry, pk=pk, user=request.user)

    initial_words = ", ".join(
        entry.highlight_words.values_list("word", flat=True)
    )

    if request.method == "POST":
        form = WritingEntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            entry = form.save()
            raw_words = form.cleaned_data.get("highlight_words", "")
            _replace_highlight_words(entry, raw_words)
            return redirect("writing_detail", pk=entry.pk)
    else:
        form = WritingEntryForm(instance=entry, initial={
            "highlight_words": initial_words,
        })

    return render(request, "writing/writing_form.html", {
        "form": form,
        "mode": "update",
        "entry": entry,
    })


@login_required
def writing_delete(request, pk):
    entry = get_object_or_404(WritingEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("writing_list")

    return render(request, "writing/writing_confirm_delete.html", {
        "entry": entry,
    })
