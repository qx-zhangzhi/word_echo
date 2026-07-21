from django import forms
from .models import WritingEntry


class WritingEntryForm(forms.ModelForm):
    highlight_words = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "例如：significant, beneficial, it is widely believed that, play a crucial role",
        }),
        help_text="可填写词、短语或句式，用英文逗号分隔；也支持每行一个。",
    )

    class Meta:
        model = WritingEntry
        fields = [
            "title",
            "task_type",
            "chart_type",
            "chart_image",
            "prompt",
            "content",
            "score",
            "note",
        ]
        widgets = {
            "prompt": forms.Textarea(attrs={"rows": 4}),
            "content": forms.Textarea(attrs={"rows": 14}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }
