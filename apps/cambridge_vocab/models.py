from django.contrib.auth.models import User
from django.db import models


class CambridgeVocabEntry(models.Model):
    SKILL_CHOICES = [
        ("listening", "听力"),
        ("reading", "阅读"),
    ]
    ENTRY_TYPE_CHOICES = [
        ("unknown", "不认识的词"),
        ("answer", "答案词"),
        ("synonym", "同义替换"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.CharField(max_length=20, choices=SKILL_CHOICES)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, default="unknown")

    word = models.CharField(max_length=120)
    meaning_cn = models.CharField(max_length=255, blank=True)
    synonym_replacements = models.TextField(blank=True)
    original_expression = models.CharField(max_length=255, blank=True)
    example_sentence = models.TextField(blank=True)
    note = models.TextField(blank=True)

    book = models.CharField(max_length=40, blank=True)
    test = models.CharField(max_length=40, blank=True)
    section_or_passage = models.CharField(max_length=80, blank=True)
    question_numbers = models.CharField(max_length=80, blank=True)
    source_title = models.CharField(max_length=255, blank=True)
    source_detail = models.TextField(blank=True)

    is_learned = models.BooleanField(default=False)
    learned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_learned", "-created_at", "word"]
        indexes = [
            models.Index(fields=["user", "skill", "entry_type"]),
            models.Index(fields=["user", "is_learned", "learned_at"]),
            models.Index(fields=["book", "test", "question_numbers"]),
        ]

    def __str__(self):
        return self.word

    @property
    def source_label(self):
        parts = [self.book, self.test, self.section_or_passage]
        label = " · ".join(part for part in parts if part)
        if self.question_numbers:
            label = f"{label} · Q{self.question_numbers}" if label else f"Q{self.question_numbers}"
        return label or "未填写来源"
