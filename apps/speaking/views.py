# apps/speaking/views.py

from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .forms import SpeakingTopicForm, SpeakingQuestionForm
from .models import SpeakingTopic, SpeakingQuestion, SpeakingAnswer


def topic_list(request):
    topics = (
        SpeakingTopic.objects
        .filter(is_active=True)
        .prefetch_related("questions")
        .order_by("part", "sort_order", "id")
    )

    return render(
        request,
        "speaking/topic_list.html",
        {
            "topics": topics,
        },
    )


def review_table(request):
    sort = request.GET.get("sort", "default")
    question_order = ["sort_order", "id"]
    if sort == "unmemorized":
        question_order = [F("memorized_at").asc(nulls_first=True), "sort_order", "id"]
    elif sort == "recent":
        question_order = [F("memorized_at").desc(nulls_last=True), "sort_order", "id"]

    active_questions = (
        SpeakingQuestion.objects
        .filter(is_active=True)
        .order_by(*question_order)
    )

    topics = (
        SpeakingTopic.objects
        .filter(is_active=True, questions__is_active=True)
        .prefetch_related(Prefetch("questions", queryset=active_questions))
        .distinct()
        .order_by("part", "sort_order", "id")
    )

    questions = SpeakingQuestion.objects.filter(
        topic__in=topics,
        is_active=True,
    )
    total_questions = questions.count()
    memorized_questions = questions.filter(memorized_at__isnull=False).count()

    return render(
        request,
        "speaking/review_table.html",
        {
            "topics": topics,
            "total_questions": total_questions,
            "memorized_questions": memorized_questions,
            "sort": sort,
        },
    )


@require_http_methods(["POST"])
def mark_question_memorized(request, question_id):
    question = get_object_or_404(
        SpeakingQuestion,
        id=question_id,
        is_active=True,
        topic__is_active=True,
    )
    question.memorized_at = timezone.now()
    question.save(update_fields=["memorized_at", "updated_at"])

    next_url = request.POST.get("next") or ""
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = "speaking_review_table"
    return redirect(next_url)


def topic_create(request):
    if request.method == "POST":
        form = SpeakingTopicForm(request.POST)
        if form.is_valid():
            topic = form.save()
            return redirect("speaking_topic_detail", topic_id=topic.id)
    else:
        form = SpeakingTopicForm(initial={
            "part": "part1",
            "sort_order": 0,
            "is_active": True,
        })

    return render(
        request,
        "speaking/topic_form.html",
        {
            "form": form,
            "page_title": "新增话题",
        },
    )


def topic_detail(request, topic_id):
    topic = get_object_or_404(
        SpeakingTopic,
        id=topic_id,
        is_active=True,
    )

    questions = (
        SpeakingQuestion.objects
        .filter(topic=topic, is_active=True)
        .prefetch_related("answers")
        .order_by("sort_order", "id")
    )

    return render(
        request,
        "speaking/topic_detail.html",
        {
            "topic": topic,
            "questions": questions,
        },
    )


def question_create(request, topic_id):
    topic = get_object_or_404(
        SpeakingTopic,
        id=topic_id,
        is_active=True,
    )

    if request.method == "POST":
        form = SpeakingQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.topic = topic
            question.save()
            return redirect("speaking_topic_detail", topic_id=topic.id)
    else:
        form = SpeakingQuestionForm(initial={
            "sort_order": 0,
            "is_active": True,
        })

    return render(
        request,
        "speaking/question_form.html",
        {
            "form": form,
            "topic": topic,
            "page_title": "新增问题",
        },
    )


def question_detail(request, question_id):
    question = get_object_or_404(
        SpeakingQuestion.objects.select_related("topic"),
        id=question_id,
        is_active=True,
    )

    answers = (
        SpeakingAnswer.objects
        .filter(question=question)
        .order_by("-created_at")
    )

    return render(
        request,
        "speaking/question_detail.html",
        {
            "question": question,
            "answers": answers,
        },
    )


@require_http_methods(["POST"])
def create_answer(request, question_id):
    question = get_object_or_404(
        SpeakingQuestion,
        id=question_id,
        is_active=True,
    )

    answer_text = request.POST.get("answer_text", "").strip()
    audio_file = request.FILES.get("audio_file")

    SpeakingAnswer.objects.create(
        question=question,
        answer_text=answer_text,
        audio_file=audio_file,
    )

    return redirect("speaking_question_detail", question_id=question.id)
