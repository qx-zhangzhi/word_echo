from django import forms
from .models import PhraseEntry


class PhraseEntryForm(forms.ModelForm):
    class Meta:
        model = PhraseEntry
        fields = [
            "english_text",
            "chinese_text",
            "category",
            "usage_note",
            "source",
            "is_favorite",
        ]
        widgets = {
            "english_text": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "输入英文好句",
            }),
            "chinese_text": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "中文翻译，可自动生成后再修改",
            }),
            "usage_note": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "记录适用场景、句型亮点、可替换部分等",
            }),
        }
