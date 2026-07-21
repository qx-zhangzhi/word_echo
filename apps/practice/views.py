from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.vocab.models import Word
from .models import PracticeSession
from .services import create_session, submit_answer


@login_required
def practice_setup(request):
    return render(request, "practice/practice_setup.html")


@login_required
def practice_run(request):
    session_type = request.GET.get("type", "random")
    limit = int(request.GET.get("limit", 10))
    device = request.GET.get("device", "mobile")
    if device not in {"mobile", "desktop"}:
        device = "mobile"

    session, words = create_session(
        user=request.user,
        session_type=session_type,
        limit=limit,
    )

    context = {
        "session": session,
        "words": words,
        "device": device,
    }
    return render(request, "practice/practice_run.html", context)


@login_required
def practice_submit(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=400)

    session_id = request.POST.get("session_id")
    word_id = request.POST.get("word_id")
    user_input = request.POST.get("user_input", "")

    session = get_object_or_404(PracticeSession, pk=session_id, user=request.user)
    word = get_object_or_404(Word, pk=word_id, user=request.user)

    is_correct = submit_answer(
        session=session,
        word_obj=word,
        user=request.user,
        user_input=user_input,
    )

    return JsonResponse({
        "ok": True,
        "is_correct": is_correct,
        "correct_word": word.word,
        "meaning_cn": word.meaning_cn,
        "example_sentence": word.example_sentence,
    })


@login_required
def practice_result(request, session_id):
    session = get_object_or_404(PracticeSession, pk=session_id, user=request.user)

    if session.finished_at is None:
        session.finished_at = timezone.now()
        session.save(update_fields=["finished_at"])

    records = session.records.select_related("word").all()

    return render(request, "practice/practice_result.html", {
        "session": session,
        "records": records,
    })


@login_required
def wrong_word_list(request):
    words = Word.objects.filter(
        user=request.user,
        wrong_count__gt=0,
    ).order_by("-wrong_count", "word")

    return render(request, "practice/wrong_word_list.html", {"words": words})
