# apps/speaking/views.py

from django.shortcuts import get_object_or_404, redirect, render
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
