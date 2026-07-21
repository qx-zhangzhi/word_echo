# apps/vocab/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WordForm
from .models import Word
from .services.word_builder import build_word_defaults


def normalize_word(raw_word: str) -> str:
    return (raw_word or "").strip().lower()


@login_required
def word_list(request):
    query = request.GET.get("q", "").strip()

    words = Word.objects.filter(user=request.user)

    if query:
        words = words.filter(
            Q(word__icontains=query)
            | Q(meaning_cn__icontains=query)
            | Q(example_sentence__icontains=query)
        )

    context = {
        "words": words[:100],
        "query": query,
    }
    return render(request, "vocab/word_list.html", context)


@login_required
def word_detail(request, pk):
    word = get_object_or_404(Word, pk=pk, user=request.user)
    return render(request, "vocab/word_detail.html", {"word": word})


@login_required
def word_create(request):
    if request.method == "POST":
        raw_word = request.POST.get("word", "")
        normalized_word = normalize_word(raw_word)

        if not normalized_word:
            return render(request, "vocab/word_form.html", {
                "error": "请输入单词",
                "mode": "create",
            })

        existing_word = Word.objects.filter(
            user=request.user,
            word__iexact=normalized_word,
        ).first()

        if existing_word:
            messages.info(request, f"单词 {existing_word.word} 已存在，已跳转到旧记录。")
            return redirect("word_detail", pk=existing_word.pk)

        data = build_word_defaults(normalized_word)

        try:
            with transaction.atomic():
                word = Word.objects.create(
                    user=request.user,
                    **data,
                )
        except IntegrityError:
            # 防止并发或大小写边界情况导致重复创建
            existing_word = get_object_or_404(
                Word,
                user=request.user,
                word__iexact=normalized_word,
            )
            messages.info(request, f"单词 {existing_word.word} 已存在，已跳转到旧记录。")
            return redirect("word_detail", pk=existing_word.pk)

        if "continue" in request.POST:
            messages.success(request, f"已保存 {word.word}，可以继续添加。")
            return redirect("word_create")

        return redirect("word_detail", pk=word.pk)

    return render(request, "vocab/word_form.html", {
        "mode": "create",
    })


@login_required
def word_update(request, pk):
    word = get_object_or_404(Word, pk=pk, user=request.user)

    if request.method == "POST":
        form = WordForm(request.POST, instance=word)

        if form.is_valid():
            new_word = normalize_word(form.cleaned_data["word"])

            duplicate = (
                Word.objects
                .filter(user=request.user, word__iexact=new_word)
                .exclude(pk=word.pk)
                .first()
            )

            if duplicate:
                messages.warning(request, f"单词 {duplicate.word} 已存在，不能改成重复单词。")
                return redirect("word_detail", pk=duplicate.pk)

            updated_word = form.save(commit=False)
            updated_word.word = new_word

            if not updated_word.tts_text:
                updated_word.tts_text = new_word

            updated_word.save()
            form.save_m2m()

            messages.success(request, "单词已更新。")
            return redirect("word_detail", pk=updated_word.pk)
    else:
        form = WordForm(instance=word)

    return render(request, "vocab/word_form.html", {
        "form": form,
        "mode": "update",
        "word": word,
    })


@login_required
def word_delete(request, pk):
    word = get_object_or_404(Word, pk=pk, user=request.user)

    if request.method == "POST":
        word.delete()
        messages.success(request, "单词已删除。")
        return redirect("word_list")

    return render(request, "vocab/word_confirm_delete.html", {"word": word})
