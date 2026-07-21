from django.contrib.auth.models import User
from django.db import models


class PracticeSession(models.Model):
    SESSION_TYPE_CHOICES = [
        ("random", "Random"),
        ("wrongbook", "Wrong Book"),
        ("tag", "Tag"),
        ("review", "Review"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)
    total_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_type} - {self.started_at}"


class PracticeRecord(models.Model):
    PROMPT_TYPE_CHOICES = [
        ("audio_to_word", "Audio to Word"),
    ]

    session = models.ForeignKey(
        PracticeSession,
        on_delete=models.CASCADE,
        related_name="records",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey("vocab.Word", on_delete=models.CASCADE)

    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPE_CHOICES, default="audio_to_word")
    user_input = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
