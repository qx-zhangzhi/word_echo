from django.contrib import admin
from .models import PhraseEntry


@admin.register(PhraseEntry)
class PhraseEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_english",
        "category",
        "is_favorite",
        "user",
        "updated_at",
    )
    search_fields = ("english_text", "chinese_text", "usage_note", "source")
    list_filter = ("category", "is_favorite", "updated_at")

    def short_english(self, obj):
        text = (obj.english_text or "").strip()
        return text[:60]
    short_english.short_description = "English"
