# apps/speaking/forms.py

from django import forms

from .models import SpeakingTopic, SpeakingQuestion


class SpeakingTopicForm(forms.ModelForm):
    class Meta:
        model = SpeakingTopic
        fields = [
            "title",
            "part",
            "description",
            "sort_order",
            "is_active",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "例如：Work / Study / Hometown",
            }),
            "part": forms.Select(attrs={
                "class": "input",
            }),
            "description": forms.Textarea(attrs={
                "class": "textarea",
                "placeholder": "这个话题的说明，可不填",
                "rows": 4,
            }),
            "sort_order": forms.NumberInput(attrs={
                "class": "input",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "checkbox",
            }),
        }


class SpeakingQuestionForm(forms.ModelForm):
    class Meta:
        model = SpeakingQuestion
        fields = [
            "question_text",
            "sample_answer",
            "key_points",
            "useful_expressions",
            "sort_order",
            "is_active",
        ]
        widgets = {
            "question_text": forms.Textarea(attrs={
                "class": "textarea",
                "placeholder": "请输入雅思口语问题",
                "rows": 3,
            }),
            "sample_answer": forms.Textarea(attrs={
                "class": "textarea",
                "placeholder": "参考回答，可不填",
                "rows": 5,
            }),
            "key_points": forms.Textarea(attrs={
                "class": "textarea",
                "placeholder": "答题要点，可不填",
                "rows": 4,
            }),
            "useful_expressions": forms.Textarea(attrs={
                "class": "textarea",
                "placeholder": "有用表达，可不填",
                "rows": 4,
            }),
            "sort_order": forms.NumberInput(attrs={
                "class": "input",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "checkbox",
            }),
        }
