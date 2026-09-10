from django import forms

from .models import CambridgeVocabEntry


BOOK_CHOICES = [("", "选择剑雅册数")] + [
    (f"Cambridge {number}", f"Cambridge {number}")
    for number in range(4, 21)
]
TEST_CHOICES = [("", "选择 Test")] + [
    (f"Test {number}", f"Test {number}")
    for number in range(1, 5)
]
SECTION_CHOICES = [("", "选择 Part / Passage")] + [
    (f"Listening Part {number}", f"Listening Part {number}")
    for number in range(1, 5)
] + [
    (f"Reading Passage {number}", f"Reading Passage {number}")
    for number in range(1, 4)
]


def skill_from_section(section_or_passage):
    if section_or_passage.startswith("Listening"):
        return "listening"
    if section_or_passage.startswith("Reading"):
        return "reading"
    return ""


class CambridgeVocabImportForm(forms.Form):
    book = forms.ChoiceField(
        label="剑雅册数",
        choices=BOOK_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
    )
    test = forms.ChoiceField(
        label="Test",
        choices=TEST_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
    )
    section_or_passage = forms.ChoiceField(
        label="Part / Passage",
        choices=SECTION_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
    )
    raw_text = forms.CharField(
        label="ChatGPT 总结结果",
        widget=forms.Textarea(attrs={
            "class": "textarea",
            "rows": 16,
            "placeholder": """请粘贴 JSON 数组，例如：
[
  {
    "entry_type": "synonym",
    "word": "reserve",
    "meaning_cn": "预订；保留",
    "synonym_replacements": "book = reserve\nkeep = reserve",
    "question_numbers": "14",
    "source_title": "Hotel booking",
    "source_detail": "题干用 book，录音中说 reserve。",
    "note": "答案词，注意和 preserve 区分"
  }
]""",
        }),
    )


class CambridgeVocabEntryForm(forms.ModelForm):
    book = forms.ChoiceField(
        label="剑雅册数",
        choices=BOOK_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
        required=False,
    )
    test = forms.ChoiceField(
        label="Test",
        choices=TEST_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
        required=False,
    )
    section_or_passage = forms.ChoiceField(
        label="Part / Passage",
        choices=SECTION_CHOICES,
        widget=forms.Select(attrs={"class": "input"}),
        required=False,
    )

    class Meta:
        model = CambridgeVocabEntry
        fields = [
            "skill",
            "entry_type",
            "word",
            "meaning_cn",
            "synonym_replacements",
            "original_expression",
            "example_sentence",
            "book",
            "test",
            "section_or_passage",
            "question_numbers",
            "source_title",
            "source_detail",
            "note",
        ]
        widgets = {
            "skill": forms.Select(attrs={"class": "input"}),
            "entry_type": forms.Select(attrs={"class": "input"}),
            "word": forms.TextInput(attrs={"class": "input", "placeholder": "比如 allocate / sustainable / run out of"}),
            "meaning_cn": forms.TextInput(attrs={"class": "input", "placeholder": "中文意思"}),
            "synonym_replacements": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "一行一个替换：word = replacement / 原文词 -> 答案词"}),
            "original_expression": forms.TextInput(attrs={"class": "input", "placeholder": "题干或原文里的表达"}),
            "example_sentence": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "原句、答案句或自己造句"}),
            "question_numbers": forms.TextInput(attrs={"class": "input", "placeholder": "12 / 14-18"}),
            "source_title": forms.TextInput(attrs={"class": "input", "placeholder": "文章/听力主题，可选"}),
            "source_detail": forms.Textarea(attrs={"class": "textarea", "rows": 4, "placeholder": "记录这题为什么错、题干定位句、原文同义替换等"}),
            "note": forms.Textarea(attrs={"class": "textarea", "rows": 3, "placeholder": "复习备注"}),
        }
        labels = {
            "skill": "类型",
            "entry_type": "记录类别",
            "word": "词 / 短语",
            "meaning_cn": "中文意思",
            "synonym_replacements": "同义替换",
            "original_expression": "原文/题干表达",
            "example_sentence": "例句/原句",
            "book": "剑雅册数",
            "test": "Test",
            "section_or_passage": "Section / Passage",
            "question_numbers": "题号",
            "source_title": "来源标题",
            "source_detail": "来源细节",
            "note": "备注",
        }
