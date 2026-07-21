from django.contrib import admin
from .models import WritingEntry, WritingHighlightWord


class WritingHighlightWordInline(admin.TabularInline):
    model = WritingHighlightWord
    extra = 1


@admin.register(WritingEntry)
class WritingEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "task_type",
        "score",
        "updated_at",
    )
    search_fields = ("title", "prompt", "content", "note")
    list_filter = ("task_type", "updated_at")
    inlines = [WritingHighlightWordInline]


@admin.register(WritingHighlightWord)
class WritingHighlightWordAdmin(admin.ModelAdmin):
    list_display = ("id", "word", "entry", "created_at")
    search_fields = ("word",)
