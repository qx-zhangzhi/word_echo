from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from openai import APITimeoutError, BadRequestError, NotFoundError

from .models import SynonymEntry
from .services import parse_synonym_item_lines, parse_synonym_words
from .synonym_ai import SynonymAIError, generate_synonym_data


class ParseSynonymWordsTests(TestCase):
    def test_accepts_chinese_separators_bullets_and_deduplicates(self):
        raw = "important， significant；crucial\n- Essential\n1. IMPORTANT"
        self.assertEqual(parse_synonym_words(raw), ["important", "significant", "crucial", "Essential"])

    def test_parses_item_lines_with_sentence_and_note(self):
        raw = "income | 个人收入 / Task 2 | Many families rely on a stable income. | 最安全\nrevenue | 公司经营 / Task 1 | Revenue increased by 10%. | 未扣成本"
        items = parse_synonym_item_lines(raw)
        self.assertEqual(items[0].word, "income")
        self.assertEqual(items[0].usage_context, "个人收入 / Task 2")
        self.assertEqual(items[0].fixed_sentence, "Many families rely on a stable income.")
        self.assertEqual(items[0].comparison_note, "最安全")
        self.assertEqual(items[1].word, "revenue")

    def test_item_lines_keep_legacy_separators(self):
        items = parse_synonym_item_lines("fine，great；excellent")
        self.assertEqual([item.word for item in items], ["fine", "great", "excellent"])


@override_settings(
    SYNONYM_AI_API_KEY="test-key",
    SYNONYM_AI_BASE_URL="https://example.test/v1",
    SYNONYM_AI_MODEL="test-model",
    SYNONYM_AI_TIMEOUT=5,
    SYNONYM_AI_TEMPERATURE="",
)
class SynonymAITests(TestCase):
    @patch("apps.synonyms.synonym_ai.OpenAI")
    def test_generate_returns_clean_form_data(self, openai):
        content = '{"meaning_cn":"重要的","items":[{"word":"important","usage_context":"Task 2","fixed_sentence":"It is important.","comparison_note":"普通"},{"word":"Significant","usage_context":"正式写作","fixed_sentence":"It is significant.","comparison_note":"正式"},{"word":"significant"},{"word":"crucial","usage_context":"关键性","fixed_sentence":"It is crucial.","comparison_note":"关键"}],"usage_note":"区别","practice_sentence":"It is ____ to check."}'
        openai.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )
        self.assertEqual(generate_synonym_data("important", "important"), {
            "meaning_cn": "重要的",
            "synonym_words": "important | Task 2 | It is important. | 普通\nSignificant | 正式写作 | It is significant. | 正式\ncrucial | 关键性 | It is crucial. | 关键",
            "usage_note": "区别",
            "example_sentence": "It is ____ to check.",
        })
        openai.return_value.chat.completions.create.assert_called_once()
        self.assertNotIn("temperature", openai.return_value.chat.completions.create.call_args.kwargs)

    @override_settings(SYNONYM_AI_TEMPERATURE="0.2")
    @patch("apps.synonyms.synonym_ai.OpenAI")
    def test_generate_passes_configured_temperature(self, openai):
        content = '{"meaning_cn":"好的","synonyms":["fine","excellent"],"usage_note":"区别","example_sentence":"It is good."}'
        openai.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )
        generate_synonym_data("good")
        self.assertEqual(openai.return_value.chat.completions.create.call_args.kwargs["temperature"], 0.2)

    @patch("apps.synonyms.synonym_ai.OpenAI")
    def test_generate_reports_timeout_clearly(self, openai):
        request = SimpleNamespace()
        openai.return_value.chat.completions.create.side_effect = APITimeoutError(request=request)
        with self.assertRaisesMessage(SynonymAIError, "连接超时"):
            generate_synonym_data("limit")

    @patch("apps.synonyms.synonym_ai.OpenAI")
    def test_generate_reports_unsupported_parameters_clearly(self, openai):
        openai.return_value.chat.completions.create.side_effect = BadRequestError(
            "unsupported",
            response=SimpleNamespace(status_code=400, headers={}, request=SimpleNamespace()),
            body={"error": {"code": "unsupported_value"}},
        )
        with self.assertRaisesMessage(SynonymAIError, "请求参数不被模型支持"):
            generate_synonym_data("limit")

    @patch("apps.synonyms.synonym_ai.OpenAI")
    def test_generate_reports_missing_model_clearly(self, openai):
        openai.return_value.chat.completions.create.side_effect = NotFoundError(
            "missing",
            response=SimpleNamespace(status_code=404, headers={}, request=SimpleNamespace()),
            body={"error": {"code": "model_not_found"}},
        )
        with self.assertRaisesMessage(SynonymAIError, "模型不可用"):
            generate_synonym_data("limit")

    def test_endpoint_requires_login(self):
        response = self.client.post(reverse("synonym_ai_generate"), {"headword": "good"})
        self.assertEqual(response.status_code, 302)

    @patch("apps.synonyms.views.generate_synonym_data")
    def test_endpoint_returns_generated_data(self, generate):
        user = get_user_model().objects.create_user("learner", password="pw")
        self.client.force_login(user)
        generate.return_value = {"synonym_words": "fine, excellent"}
        response = self.client.post(reverse("synonym_ai_generate"), {"headword": "good"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["synonym_words"], "fine, excellent")


class SynonymSaveTests(TestCase):
    def test_create_parses_common_separators(self):
        user = get_user_model().objects.create_user("learner", password="pw")
        self.client.force_login(user)
        response = self.client.post(reverse("synonym_create"), {
            "headword": "good",
            "meaning_cn": "好的",
            "usage_note": "",
            "example_sentence": "",
            "synonym_words": "fine，great；excellent",
        })
        self.assertEqual(response.status_code, 302)
        entry = SynonymEntry.objects.get(user=user, headword="good")
        self.assertEqual(set(entry.items.values_list("word", flat=True)), {"fine", "great", "excellent"})

    def test_create_saves_sentence_and_comparison_per_item(self):
        user = get_user_model().objects.create_user("learner2", password="pw")
        self.client.force_login(user)
        response = self.client.post(reverse("synonym_create"), {
            "headword": "important",
            "meaning_cn": "重要的",
            "usage_note": "",
            "example_sentence": "It is ____ to check.",
            "synonym_words": "important | Task 2 | It is important to check. | 普通",
        })
        self.assertEqual(response.status_code, 302)
        item = SynonymEntry.objects.get(user=user, headword="important").items.get()
        self.assertEqual(item.usage_context, "Task 2")
        self.assertEqual(item.fixed_sentence, "It is important to check.")
        self.assertEqual(item.comparison_note, "普通")


class SynonymReviewTests(TestCase):
    def _create_entry(self):
        user = get_user_model().objects.create_user("reviewer", password="pw")
        entry = SynonymEntry.objects.create(
            user=user,
            headword="important",
            meaning_cn="重要的",
            example_sentence="It is ____ to check.",
        )
        entry.items.create(word="significant")
        entry.items.create(word="crucial")
        return user, entry

    def test_review_correct_answer_marks_entry_learned(self):
        user, entry = self._create_entry()
        self.client.force_login(user)
        response = self.client.post(reverse("synonym_review", args=[entry.pk]), {"answer": " Significant "})
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertTrue(entry.is_learned)
        self.assertEqual(entry.review_attempts, 1)
        self.assertEqual(entry.review_correct, 1)
        self.assertIsNotNone(entry.reviewed_at)

    def test_review_wrong_answer_keeps_entry_pending(self):
        user, entry = self._create_entry()
        entry.is_learned = True
        entry.save(update_fields=["is_learned"])
        self.client.force_login(user)
        response = self.client.post(reverse("synonym_review", args=[entry.pk]), {"answer": "useful"})
        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertFalse(entry.is_learned)
        self.assertEqual(entry.review_attempts, 1)
        self.assertEqual(entry.review_correct, 0)

    def test_review_list_shows_entries(self):
        user, entry = self._create_entry()
        self.client.force_login(user)
        response = self.client.get(reverse("synonym_review_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, entry.headword)
        self.assertContains(response, "待复习")
