from django.contrib.auth.models import User
from django.db import models


class WordTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Word(models.Model):
    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("wrongbook", "Wrong Book"),
        ("import", "Import"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.CharField(max_length=100)
    phonetic = models.CharField(max_length=100, blank=True)
    meaning_cn = models.CharField(max_length=255, blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    example_sentence = models.TextField(blank=True)
    note = models.TextField(blank=True)

    tags = models.ManyToManyField(WordTag, blank=True)

    difficulty = models.PositiveSmallIntegerField(default=3)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    is_active = models.BooleanField(default=True)

    tts_text = models.CharField(max_length=255, blank=True)

    wrong_count = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    last_practiced_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateTimeField(null=True, blank=True)
    memory_level = models.PositiveSmallIntegerField(default=0)
    is_forgotten = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "word")
        ordering = ["word"]

    def __str__(self):
        return self.word
