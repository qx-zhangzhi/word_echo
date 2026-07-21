from django.contrib.auth.models import User
from django.db import models


class PhraseEntry(models.Model):
    CATEGORY_CHOICES = [
        ("writing", "Writing"),
        ("speaking", "Speaking"),
        ("general", "General"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    english_text = models.TextField()
    chinese_text = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    usage_note = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True)
    is_favorite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        text = (self.english_text or "").strip()
        return text[:80] if text else f"Phrase #{self.pk}"
