# apps/vocab/forms.py

from django import forms

from .models import Word


class WordCreateForm(forms.Form):
    word = forms.CharField(
        max_length=100,
        label="单词",
        widget=forms.TextInput(attrs={
            "class": "input",
            "placeholder": "例如 accommodate",
            "autofocus": "autofocus",
        }),
    )


class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = [
            "word",
            "tts_text",
            "phonetic",
            "meaning_cn",
            "part_of_speech",
            "example_sentence",
            "note",
            "difficulty",
            "is_active",
        ]

        widgets = {
            "word": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "单词",
            }),
            "tts_text": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "TTS 发音文本，默认等于单词",
            }),
            "phonetic": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "音标，例如 /əˈkɒmədeɪt/",
            }),
            "meaning_cn": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "中文释义",
            }),
            "part_of_speech": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "词性，例如 verb / noun",
            }),
            "example_sentence": forms.Textarea(attrs={
                "class": "textarea",
                "rows": 4,
                "placeholder": "例句",
            }),
            "note": forms.Textarea(attrs={
                "class": "textarea",
                "rows": 4,
                "placeholder": "备注，支持换行",
            }),
            "difficulty": forms.NumberInput(attrs={
                "class": "input",
                "min": 1,
                "max": 5,
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "checkbox",
            }),
        }

    def clean_word(self):
        word = self.cleaned_data["word"].strip().lower()
        return word

    def clean_tts_text(self):
        tts_text = self.cleaned_data.get("tts_text", "").strip()
        return tts_text

    def clean_difficulty(self):
        difficulty = self.cleaned_data.get("difficulty") or 3
        return max(1, min(5, int(difficulty)))
