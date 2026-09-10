from django import forms

from .models import CambridgeVocabEntry


class CambridgeVocabEntryForm(forms.ModelForm):
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
            "book": forms.TextInput(attrs={"class": "input", "placeholder": "Cambridge 19"}),
            "test": forms.TextInput(attrs={"class": "input", "placeholder": "Test 1"}),
            "section_or_passage": forms.TextInput(attrs={"class": "input", "placeholder": "Listening Section 2 / Reading Passage 3"}),
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
