# apps/speaking/views.py

from django.db.models import Count, F, Max, Prefetch, Q
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


def review_table(request, part=None):
    if part is None:
        return redirect("speaking_review_table_part", part="part1")
    if part not in {"part1", "part2", "part3"}:
        part = "part1"

    sort = request.GET.get("sort", "default")
    if sort not in {"default", "unmemorized", "recent"}:
        sort = "default"

    active_questions = (
        SpeakingQuestion.objects
        .filter(is_active=True)
        .order_by("sort_order", "id")
    )

    topics = (
        SpeakingTopic.objects
        .filter(part=part, is_active=True, questions__is_active=True)
        .annotate(
            active_question_count=Count("questions", filter=Q(questions__is_active=True), distinct=True),
            memorized_question_count=Count(
                "questions",
                filter=Q(questions__is_active=True, questions__memorized_at__isnull=False),
                distinct=True,
            ),
            unmemorized_question_count=Count(
                "questions",
                filter=Q(questions__is_active=True, questions__memorized_at__isnull=True),
                distinct=True,
            ),
            latest_memorized_at=Max("questions__memorized_at", filter=Q(questions__is_active=True)),
        )
        .prefetch_related(Prefetch("questions", queryset=active_questions))
        .distinct()
    )

    if sort == "unmemorized":
        topics = topics.order_by("-unmemorized_question_count", "part", "sort_order", "id")
    elif sort == "recent":
        topics = topics.order_by(F("latest_memorized_at").desc(nulls_last=True), "part", "sort_order", "id")
    else:
        topics = topics.order_by("part", "sort_order", "id")

    topic_count = topics.count()
    all_questions = SpeakingQuestion.objects.filter(topic__part=part, topic__in=topics, is_active=True)
    total_questions = all_questions.count()
    memorized_questions = all_questions.filter(memorized_at__isnull=False).count()

    return render(
        request,
        "speaking/review_table.html",
        {
            "topics": topics,
            "topic_count": topic_count,
            "total_questions": total_questions,
            "memorized_questions": memorized_questions,
            "sort": sort,
            "part": part,
            "part_label": dict(SpeakingTopic.PART_CHOICES).get(part, "Part 1"),
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
