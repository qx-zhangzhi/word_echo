# apps/primary_dictation/management/commands/import_primary_words.py

from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.primary_dictation.models import PrimaryDictationWord, PrimaryWordSet


class Command(BaseCommand):
    help = "Import primary school dictation words into a word set."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Import file path. Supports CSV or plain text.",
        )
        parser.add_argument(
            "--title",
            required=True,
            help="Word set title, for example: 三年级上册 Unit 1",
        )
        parser.add_argument(
            "--grade",
            default="g3",
            help="Grade code: g1/g2/g3/g4/g5/g6. Default: g3",
        )
        parser.add_argument(
            "--term",
            default="upper",
            help="Term code: upper/lower/other. Default: upper",
        )
        parser.add_argument(
            "--unit",
            default="",
            help="Unit name, for example: Unit 1",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing words in this word set before import.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        title = options["title"].strip()
        grade = options["grade"].strip()
        term = options["term"].strip()
        unit = options["unit"].strip()
        replace = options["replace"]

        if not title:
            raise CommandError("--title cannot be empty")

        rows = self._parse_file(file_path)

        if not rows:
            raise CommandError("No valid words found in file.")

        with transaction.atomic():
            word_set, created = PrimaryWordSet.objects.get_or_create(
                title=title,
                defaults={
                    "grade": grade,
                    "term": term,
                    "unit": unit,
                    "description": "",
                    "sort_order": 0,
                    "is_active": True,
                },
            )

            if not created:
                word_set.grade = grade
                word_set.term = term
                word_set.unit = unit
                word_set.is_active = True
                word_set.save(update_fields=["grade", "term", "unit", "is_active", "updated_at"])

            if replace:
                deleted_count, _ = PrimaryDictationWord.objects.filter(word_set=word_set).delete()
                self.stdout.write(f"[REPLACE] deleted existing words: {deleted_count}")

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for index, row in enumerate(rows, start=1):
                word = row["word"].strip().lower()
                meaning_cn = row.get("meaning_cn", "").strip()
                phonetic = row.get("phonetic", "").strip()
                example_sentence = row.get("example_sentence", "").strip()

                if not word:
                    skipped_count += 1
                    continue

                obj, obj_created = PrimaryDictationWord.objects.update_or_create(
                    word_set=word_set,
                    word=word,
                    defaults={
                        "meaning_cn": meaning_cn,
                        "phonetic": phonetic,
                        "example_sentence": example_sentence,
                        "sort_order": index,
                        "is_active": True,
                    },
                )

                if obj_created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"DONE word_set_id={word_set.id}, "
            f"title={word_set.title}, "
            f"created={created_count}, "
            f"updated={updated_count}, "
            f"skipped={skipped_count}"
        ))

    def _parse_file(self, file_path: Path):
        text = file_path.read_text(encoding="utf-8-sig").strip()

        if not text:
            return []

        if file_path.suffix.lower() == ".csv":
            return self._parse_csv(text)

        return self._parse_plain_text(text)

    def _parse_csv(self, text: str):
        rows = []

        lines = text.splitlines()
        sample = lines[0].lower()

        has_header = "word" in sample or "meaning" in sample or "中文" in sample

        reader = csv.reader(lines)

        if has_header:
            dict_reader = csv.DictReader(lines)
            for item in dict_reader:
                rows.append({
                    "word": item.get("word") or item.get("单词") or item.get("english") or "",
                    "meaning_cn": item.get("meaning_cn") or item.get("中文") or item.get("meaning") or "",
                    "phonetic": item.get("phonetic") or item.get("音标") or "",
                    "example_sentence": item.get("example_sentence") or item.get("例句") or "",
                })
            return rows

        for item in reader:
            if not item:
                continue

            rows.append({
                "word": item[0] if len(item) >= 1 else "",
                "meaning_cn": item[1] if len(item) >= 2 else "",
                "phonetic": item[2] if len(item) >= 3 else "",
                "example_sentence": item[3] if len(item) >= 4 else "",
            })

        return rows

    def _parse_plain_text(self, text: str):
        rows = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "," in line:
                parts = [x.strip() for x in line.split(",", 3)]
            elif "\t" in line:
                parts = [x.strip() for x in line.split("\t", 3)]
            else:
                parts = line.split(maxsplit=1)

            word = parts[0] if len(parts) >= 1 else ""
            meaning_cn = parts[1] if len(parts) >= 2 else ""

            rows.append({
                "word": word,
                "meaning_cn": meaning_cn,
                "phonetic": "",
                "example_sentence": "",
            })

        return rows
