# apps/speaking/views.py

from pathlib import Path

from django.db.models import Count, F, Max, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from markdown_it import MarkdownIt

from .forms import SpeakingTopicForm, SpeakingQuestionForm
from .guide_data import (
    PART2_TOPIC_LABELS,
    PART2_TOPIC_TITLES,
    PREFERRED_PDF_ORIGINALS,
    UNIT_GROUPS,
    UNIT_META,
    UNIT_QUESTION_NUMBERS,
)
from .models import SpeakingTopic, SpeakingQuestion, SpeakingAnswer


GUIDE_CONTENT_DIR = Path(__file__).resolve().parent / "content"


def _guide_sections(filename):
    source = (GUIDE_CONTENT_DIR / filename).read_text(encoding="utf-8")
    lines = source.splitlines()
    markdown = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = markdown.parse(source)
    headings = [
        (token.map[0], tokens[index + 1].content)
        for index, token in enumerate(tokens)
        if token.type == "heading_open" and token.tag == "h2"
    ]

    sections = []
    for index, (start, title) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        body_tokens = markdown.parse("\n".join(lines[start + 1:end]))
        for token in body_tokens:
            if token.type != "inline":
                continue
            for child in token.children or []:
                if child.type != "link_open":
                    continue
                href = child.attrGet("href") or ""
                if href.startswith("part2_integrated_guide.md"):
                    child.attrSet("href", reverse("speaking_part2_guide") + "?view=map")
                elif href.startswith("part2_pdf_coverage.md"):
                    child.attrSet("href", reverse("speaking_part2_guide") + "?view=pdf")
        sections.append({
            "title": title,
            "html": markdown.renderer.render(body_tokens, markdown.options, {}),
            "id": f"section-{index + 1}",
        })
    return sections


def _part2_switch_notes():
    """Read the maintained switching table instead of duplicating its advice."""
    source = (GUIDE_CONTENT_DIR / "part2_integrated_guide.md").read_text(encoding="utf-8")
    rows = {}
    in_table = False
    new_numbers = {"新 01": 27, "新 03": 28, "新 04": 29, "新 05": 30, "新 06": 31}
    for line in source.splitlines():
        if line.startswith("## 31 题切换表"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5 or cells[0] in {"原编号", "---"}:
            continue
        number = new_numbers.get(cells[0])
        if number is None and cells[0].isdigit():
            number = int(cells[0])
        if number:
            rows[number] = {
                "shared_facts": cells[3].replace("**", "").replace("`", ""),
                "focus": cells[4].replace("**", "").replace("`", ""),
            }
    return rows


def _part2_material_units(questions_by_title):
    switch_notes = _part2_switch_notes()
    units = []
    for unit_id, numbers in UNIT_QUESTION_NUMBERS.items():
        title, group = UNIT_META[unit_id]
        unit_questions = []
        for number in numbers:
            english_title = PART2_TOPIC_TITLES[number]
            question = questions_by_title.get(english_title)
            note = switch_notes.get(number, {})
            unit_questions.append({
                "number": number,
                "label": PART2_TOPIC_LABELS[number],
                "title": english_title,
                "question_text": question.question_text if question else "",
                "answer": question.sample_answer if question else "",
                "key_points": question.key_points if question else "",
                "useful_expressions": question.useful_expressions if question else "",
                "shared_facts": note.get("shared_facts", ""),
                "focus": note.get("focus", ""),
                "memorized_at": question.memorized_at if question else None,
                "url": (
                    reverse("speaking_review_table_part", kwargs={"part": "part2"})
                    + f"#question-{question.id}"
                ) if question else "",
            })
        units.append({
            "id": unit_id,
            "title": title,
            "group": group,
            "questions": unit_questions,
            "question_count": len(unit_questions),
            "memorized_count": sum(bool(item["memorized_at"]) for item in unit_questions),
        })
    return units


def part2_guide(request):
    view = request.GET.get("view", "units")
    if view not in {"units", "map", "pdf", "gaps"}:
        view = "units"

    guide = _guide_sections("part2_integrated_guide.md")
    coverage = _guide_sections("part2_pdf_coverage.md")
    if view == "units":
        sections = [
            section for section in guide
            if section["title"].startswith(("先背什么", "高复用单元", "其余 14", "复习顺序"))
        ]
    elif view == "map":
        sections = [section for section in guide if "题切换表" in section["title"]]
    elif view == "pdf":
        sections = [section for section in coverage if section["title"].startswith(("5–8 月", "9–12 月"))]
    else:
        sections = [section for section in coverage if section["title"].startswith("目前串不起来")]

    questions = (
        SpeakingQuestion.objects
        .filter(topic__part="part2", topic__is_active=True, topic__title__in=PART2_TOPIC_TITLES.values(), is_active=True)
        .select_related("topic")
        .order_by("topic__sort_order", "sort_order", "id")
    )
    questions_by_title = {}
    for question in questions:
        questions_by_title.setdefault(question.topic.title, question)

    material_units = _part2_material_units(questions_by_title)

    originals = {}
    for number, title in PART2_TOPIC_TITLES.items():
        question = questions_by_title.get(title)
        if question and question.sample_answer:
            originals[str(number)] = {
                "title": title,
                "answer": question.sample_answer,
                "url": reverse("speaking_review_table_part", kwargs={"part": "part2"}) + f"#question-{question.id}",
            }

    return render(request, "speaking/part2_guide.html", {
        "view": view,
        "sections": sections,
        "originals": originals,
        "unit_question_numbers": UNIT_QUESTION_NUMBERS,
        "preferred_pdf_originals": PREFERRED_PDF_ORIGINALS,
        "material_units": material_units,
        "unit_groups": UNIT_GROUPS,
    })


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


def review_fragment_redirect(request, part="part1", anchor=""):
    if part not in {"part1", "part2", "part3"}:
        part = "part1"
    target = reverse("speaking_review_table_part", kwargs={"part": part})
    if anchor:
        target = f"{target}#{anchor}"
    return redirect(target)


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
