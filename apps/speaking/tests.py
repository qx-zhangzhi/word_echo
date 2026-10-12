from datetime import datetime, timezone

from django.test import TestCase
from django.urls import reverse

from .guide_data import PART2_TOPIC_TITLES, UNIT_QUESTION_NUMBERS
from .models import SpeakingQuestion, SpeakingTopic
from .views import _guide_sections


class Part2GuideTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        topic = SpeakingTopic.objects.create(title=PART2_TOPIC_TITLES[1], part="part2")
        cls.memorized_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
        cls.question = SpeakingQuestion.objects.create(
            topic=topic,
            question_text="Describe a tall building",
            sample_answer="This is my complete original answer.",
            memorized_at=cls.memorized_at,
        )

    def test_all_19_units_are_present_in_source(self):
        guide = _guide_sections("part2_integrated_guide.md")
        source = " ".join(section["html"] for section in guide)
        for number in range(1, 20):
            self.assertIn(f"M{number:02}", source)
        mapped = [number for numbers in UNIT_QUESTION_NUMBERS.values() for number in numbers]
        self.assertEqual(sorted(mapped), list(range(1, 32)))

    def test_views_include_original_answer_without_changing_memorized_time(self):
        url = reverse("speaking_part2_guide")
        for tab, expected in (
            ("units", "北京住宅楼"),
            ("map", "31 题切换表"),
            ("pdf", "5–8 月 PDF"),
            ("gaps", "目前串不起来"),
        ):
            with self.subTest(tab=tab):
                response = self.client.get(url, {"view": tab})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
                self.assertEqual(response.context["originals"]["1"]["answer"], "This is my complete original answer.")
                self.question.refresh_from_db()
                self.assertEqual(self.question.memorized_at, self.memorized_at)

        self.question.sample_answer = "Updated answer from the review table."
        self.question.save(update_fields=["sample_answer"])
        response = self.client.get(url, {"view": "pdf"})
        self.assertEqual(response.context["originals"]["1"]["answer"], self.question.sample_answer)

    def test_units_are_grouped_by_material_with_switching_advice(self):
        response = self.client.get(reverse("speaking_part2_guide"), {"view": "units"})
        units = response.context["material_units"]
        self.assertEqual(len(units), 19)
        self.assertEqual(units[0]["id"], "M01")
        self.assertEqual(units[0]["questions"][0]["answer"], "This is my complete original answer.")
        self.assertIn("用途、位置、外观", units[0]["questions"][0]["focus"])
        travel = next(unit for unit in units if unit["id"] == "M02")
        self.assertEqual([item["number"] for item in travel["questions"]], [2, 4, 10, 27])

    def test_internal_document_links_point_to_guide_tabs(self):
        sections = _guide_sections("part2_pdf_coverage.md")
        source = " ".join(section["html"] for section in sections)
        self.assertIn(reverse("speaking_part2_guide") + "?view=map", source)
