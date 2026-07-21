from django.contrib import admin
from .models import Word, WordTag


@admin.register(WordTag)
class WordTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "word",
        "meaning_cn",
        "difficulty",
        "wrong_count",
        "correct_count",
        "is_forgotten",
        "is_active",
        "updated_at",
    )
    search_fields = ("word", "meaning_cn", "example_sentence")
    list_filter = ("difficulty", "is_active", "is_forgotten", "tags")
