# apps/primary_dictation/views.py

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    PrimaryDictationResult,
    PrimaryDictationSession,
    PrimaryDictationWord,
    PrimaryWordSet,
)


def normalize_answer(value: str) -> str:
    return (value or "").strip().lower()


@login_required
def word_set_list(request):
    grade = request.GET.get("grade", "").strip()

    word_sets = PrimaryWordSet.objects.filter(is_active=True)

    if grade:
        word_sets = word_sets.filter(grade=grade)

    word_sets = word_sets.prefetch_related("words").order_by(
        "grade",
        "term",
        "sort_order",
        "id",
    )

    return render(
        request,
        "primary_dictation/word_set_list.html",
        {
            "word_sets": word_sets,
            "grade": grade,
            "grade_choices": PrimaryWordSet.GRADE_CHOICES,
        },
    )


@login_required
def word_set_detail(request, set_id):
    word_set = get_object_or_404(
        PrimaryWordSet,
        id=set_id,
        is_active=True,
    )

    words = (
        PrimaryDictationWord.objects
        .filter(word_set=word_set, is_active=True)
        .order_by("sort_order", "id")
    )

    recent_sessions = (
        PrimaryDictationSession.objects
        .filter(user=request.user, word_set=word_set)
        .order_by("-started_at")[:5]
    )

    return render(
        request,
        "primary_dictation/word_set_detail.html",
        {
            "word_set": word_set,
            "words": words,
            "recent_sessions": recent_sessions,
        },
    )


@login_required
def dictation_start(request, set_id):
    word_set = get_object_or_404(
        PrimaryWordSet,
        id=set_id,
        is_active=True,
    )

    words = list(
        PrimaryDictationWord.objects
        .filter(word_set=word_set, is_active=True)
        .order_by("sort_order", "id")
    )

    if not words:
        return redirect("primary_word_set_detail", set_id=word_set.id)

    session = PrimaryDictationSession.objects.create(
        user=request.user,
        word_set=word_set,
        total_count=len(words),
    )

    return redirect("primary_dictation_session", session_id=session.id)


@login_required
def dictation_session(request, session_id):
    session = get_object_or_404(
        PrimaryDictationSession.objects.select_related("word_set"),
        id=session_id,
        user=request.user,
    )

    if session.submitted_at:
        return redirect("primary_dictation_result", session_id=session.id)

    words = (
        PrimaryDictationWord.objects
        .filter(word_set=session.word_set, is_active=True)
        .order_by("sort_order", "id")
    )

    return render(
        request,
        "primary_dictation/dictation_session.html",
        {
            "session": session,
            "word_set": session.word_set,
            "words": words,
        },
    )


@login_required
@transaction.atomic
def dictation_submit(request, session_id):
    session = get_object_or_404(
        PrimaryDictationSession.objects.select_related("word_set"),
        id=session_id,
        user=request.user,
    )

    if session.submitted_at:
        return redirect("primary_dictation_result", session_id=session.id)

    words = list(
        PrimaryDictationWord.objects
        .filter(word_set=session.word_set, is_active=True)
        .order_by("sort_order", "id")
    )

    correct_count = 0
    wrong_count = 0

    for word in words:
        answer_key = f"answer_{word.id}"
        answer_text = normalize_answer(request.POST.get(answer_key, ""))
        target_word = normalize_answer(word.word)

        is_correct = answer_text == target_word

        if is_correct:
            correct_count += 1
        else:
            wrong_count += 1

        PrimaryDictationResult.objects.create(
            session=session,
            word=word,
            answer_text=answer_text,
            is_correct=is_correct,
        )

    session.total_count = len(words)
    session.correct_count = correct_count
    session.wrong_count = wrong_count
    session.submitted_at = timezone.now()
    session.save(update_fields=[
        "total_count",
        "correct_count",
        "wrong_count",
        "submitted_at",
    ])

    return redirect("primary_dictation_result", session_id=session.id)


@login_required
def dictation_result(request, session_id):
    session = get_object_or_404(
        PrimaryDictationSession.objects.select_related("word_set"),
        id=session_id,
        user=request.user,
    )

    results = (
        PrimaryDictationResult.objects
        .filter(session=session)
        .select_related("word")
        .order_by("id")
    )

    wrong_results = results.filter(is_correct=False)

    return render(
        request,
        "primary_dictation/dictation_result.html",
        {
            "session": session,
            "word_set": session.word_set,
            "results": results,
            "wrong_results": wrong_results,
        },
    )
