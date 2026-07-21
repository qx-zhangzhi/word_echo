from django.contrib.auth.models import User
from django.db import models


class SynonymEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    headword = models.CharField(max_length=100)
    meaning_cn = models.CharField(max_length=255, blank=True)
    usage_note = models.TextField(blank=True)
    example_sentence = models.TextField(blank=True)
    is_learned = models.BooleanField(default=False)
    review_attempts = models.PositiveIntegerField(default=0)
    review_correct = models.PositiveIntegerField(default=0)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["headword"]
        unique_together = ("user", "headword")

    def __str__(self):
        return self.headword


class SynonymItem(models.Model):
    entry = models.ForeignKey(
        SynonymEntry,
        on_delete=models.CASCADE,
        related_name="items",
    )
    word = models.CharField(max_length=100)
    note = models.CharField(max_length=255, blank=True)
    usage_context = models.CharField(max_length=100, blank=True)
    fixed_sentence = models.TextField(blank=True)
    comparison_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["word"]
        unique_together = ("entry", "word")

    def __str__(self):
        return self.word
