from datetime import timedelta

from django.utils import timezone

from apps.vocab.models import Word
from .models import PracticeRecord, PracticeSession


def pick_words_for_session(user, session_type="random", limit=10):
    qs = Word.objects.filter(user=user, is_active=True)

    if session_type == "wrongbook":
        qs = qs.order_by("-wrong_count", "word")
    elif session_type == "review":
        now = timezone.now()
        qs = qs.filter(next_review_at__isnull=False, next_review_at__lte=now).order_by("next_review_at")
    else:
        qs = qs.order_by("?")

    return list(qs[:limit])


def create_session(user, session_type="random", limit=10):
    words = pick_words_for_session(user=user, session_type=session_type, limit=limit)
    session = PracticeSession.objects.create(
        user=user,
        session_type=session_type,
        total_count=len(words),
    )
    return session, words


def normalize_answer(text):
    return (text or "").strip().lower()


def check_answer(word_obj, user_input):
    return normalize_answer(word_obj.word) == normalize_answer(user_input)


def update_word_stats(word_obj, is_correct):
    now = timezone.now()
    word_obj.last_practiced_at = now

    if is_correct:
        word_obj.correct_count += 1
        word_obj.memory_level = min(word_obj.memory_level + 1, 10)
        word_obj.is_forgotten = False

        if word_obj.memory_level >= 5:
            word_obj.next_review_at = now + timedelta(days=7)
        elif word_obj.memory_level >= 2:
            word_obj.next_review_at = now + timedelta(days=2)
        else:
            word_obj.next_review_at = now + timedelta(days=1)
    else:
        word_obj.wrong_count += 1
        word_obj.memory_level = 0
        word_obj.is_forgotten = True
        word_obj.next_review_at = now

    word_obj.save()


def submit_answer(session, word_obj, user, user_input):
    is_correct = check_answer(word_obj, user_input)

    PracticeRecord.objects.create(
        session=session,
        user=user,
        word=word_obj,
        user_input=user_input,
        is_correct=is_correct,
    )

    if is_correct:
        session.correct_count += 1
        session.save(update_fields=["correct_count"])

    update_word_stats(word_obj, is_correct)
    return is_correct
