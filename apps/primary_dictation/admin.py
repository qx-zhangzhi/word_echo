# apps/primary_dictation/admin.py

from django.contrib import admin

from .models import (
    PrimaryDictationResult,
    PrimaryDictationSession,
    PrimaryDictationWord,
    PrimaryWordSet,
)


class PrimaryDictationWordInline(admin.TabularInline):
    model = PrimaryDictationWord
    extra = 5
    fields = (
        "word",
        "meaning_cn",
        "phonetic",
        "audio_url",
        "sort_order",
        "is_active",
    )


@admin.register(PrimaryWordSet)
class PrimaryWordSetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "grade",
        "term",
        "unit",
        "sort_order",
        "is_active",
        "updated_at",
    )
    list_filter = ("grade", "term", "is_active")
    search_fields = ("title", "unit", "description")
    ordering = ("grade", "term", "sort_order", "id")
    inlines = [PrimaryDictationWordInline]


@admin.register(PrimaryDictationWord)
class PrimaryDictationWordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "word_set",
        "word",
        "meaning_cn",
        "sort_order",
        "is_active",
    )
    list_filter = ("word_set__grade", "word_set", "is_active")
    search_fields = ("word", "meaning_cn", "example_sentence")
    ordering = ("word_set", "sort_order", "id")


class PrimaryDictationResultInline(admin.TabularInline):
    model = PrimaryDictationResult
    extra = 0
    readonly_fields = (
        "word",
        "answer_text",
        "is_correct",
        "created_at",
    )
    can_delete = False


@admin.register(PrimaryDictationSession)
class PrimaryDictationSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "word_set",
        "total_count",
        "correct_count",
        "wrong_count",
        "started_at",
        "submitted_at",
    )
    list_filter = ("word_set", "started_at")
    search_fields = ("user__username", "word_set__title")
    readonly_fields = (
        "user",
        "word_set",
        "total_count",
        "correct_count",
        "wrong_count",
        "started_at",
        "submitted_at",
    )
    inlines = [PrimaryDictationResultInline]


@admin.register(PrimaryDictationResult)
class PrimaryDictationResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session",
        "word",
        "answer_text",
        "is_correct",
        "created_at",
    )
    list_filter = ("is_correct", "created_at")
    search_fields = ("word__word", "answer_text")
