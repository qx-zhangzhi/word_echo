import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.speaking.models import SpeakingQuestion, SpeakingTopic


DEFAULT_SOURCE = "/Users/zhangzhi6/ielts/oral/review_bank/answer_bank.md"

ENTRY_RE = re.compile(r"^## (?P<date>\d{4}-\d{2}-\d{2}) \| (?P<part>Part [123]) \| (?P<title>.+?)\s*$")
QUESTION_RE = re.compile(r"^### Question(?: \d+)?\s*$")
FIELD_RE = re.compile(r"^\*\*(?P<name>Question|Original|Polished|Band 7 Version|Key Chunks|Notes|Review Prompt)\*\*\s*$")

PART_MAP = {
    "Part 1": "part1",
    "Part 2": "part2",
    "Part 3": "part3",
}


def clean_block(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def split_entries(text):
    entries = []
    current = None

    for line in text.splitlines():
        match = ENTRY_RE.match(line)
        if match:
            if current:
                entries.append(current)
            current = {
                "date": match.group("date"),
                "part": PART_MAP[match.group("part")],
                "title": match.group("title").strip(),
                "lines": [],
            }
            continue

        if current:
            current["lines"].append(line)

    if current:
        entries.append(current)

    return entries


def parse_questions(lines):
    questions = []
    current = None
    active_field = None

    def flush_question():
        nonlocal current
        if not current:
            return
        for key, value in list(current.items()):
            if isinstance(value, list):
                current[key] = clean_block(value)
        if current.get("Question"):
            questions.append(current)
        current = None

    for line in lines:
        if QUESTION_RE.match(line):
            flush_question()
            current = {}
            active_field = None
            continue

        if current is None:
            continue

        field_match = FIELD_RE.match(line)
        if field_match:
            active_field = field_match.group("name")
            current.setdefault(active_field, [])
            continue

        if active_field:
            current[active_field].append(line)

    flush_question()
    return questions


def build_key_points(question):
    sections = []
    if question.get("Polished"):
        sections.append("Polished\n" + question["Polished"])
    if question.get("Review Prompt"):
        sections.append("Review Prompt\n" + question["Review Prompt"])
    if question.get("Notes"):
        sections.append("Notes\n" + question["Notes"])
    if question.get("Original"):
        sections.append("Original\n" + question["Original"])
    return "\n\n".join(sections)


class Command(BaseCommand):
    help = "Import IELTS speaking answers from the Markdown review bank."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help=f"Markdown answer bank path. Default: {DEFAULT_SOURCE}",
        )

    def handle(self, *args, **options):
        source = Path(options["source"]).expanduser()
        if not source.exists():
            raise CommandError(f"Source file does not exist: {source}")

        entries = split_entries(source.read_text(encoding="utf-8"))
        if not entries:
            raise CommandError("No entries found. Expected headings like: ## 2026-09-02 | Part 1 | Headphones")

        topic_count = 0
        question_count = 0

        for entry in entries:
            questions = parse_questions(entry["lines"])
            if not questions:
                continue

            topic, _ = SpeakingTopic.objects.update_or_create(
                title=entry["title"],
                part=entry["part"],
                defaults={
                    "description": f"Imported from {source.name}. Last review entry: {entry['date']}.",
                    "is_active": True,
                },
            )
            topic_count += 1

            for index, question in enumerate(questions, start=1):
                sample_answer = question.get("Band 7 Version") or question.get("Polished") or ""
                useful_expressions = question.get("Key Chunks", "")

                SpeakingQuestion.objects.update_or_create(
                    topic=topic,
                    question_text=question["Question"],
                    defaults={
                        "sample_answer": sample_answer,
                        "key_points": build_key_points(question),
                        "useful_expressions": useful_expressions,
                        "sort_order": index,
                        "is_active": True,
                    },
                )
                question_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {question_count} questions across {topic_count} topic entries from {source}"
            )
        )
