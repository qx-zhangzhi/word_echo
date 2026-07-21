from django import forms
from .models import SynonymEntry


class SynonymEntryForm(forms.ModelForm):
    synonym_words = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 8,
            "placeholder": "每行一个：\nincome | 个人收入 / Task 2 | Many families rely on a stable income. | 个人总收入，最安全\nrevenue | 公司经营 / Task 1 | The company's revenue increased by 10%. | 总营业收入，未扣成本",
        }),
        help_text="格式：词组 | 分类/语境 | 固定句子 | 区别说明。AI 会保留你填的词，再补成 IELTS 高频辨析表。",
    )

    class Meta:
        model = SynonymEntry
        fields = [
            "headword",
            "meaning_cn",
            "usage_note",
            "example_sentence",
        ]
        widgets = {
            "usage_note": forms.Textarea(attrs={"rows": 4}),
            "example_sentence": forms.Textarea(attrs={"rows": 4}),
        }
