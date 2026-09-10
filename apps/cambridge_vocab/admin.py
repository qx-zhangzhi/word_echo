from django.contrib import admin

from .models import CambridgeVocabEntry


@admin.register(CambridgeVocabEntry)
class CambridgeVocabEntryAdmin(admin.ModelAdmin):
    list_display = ("word", "skill", "entry_type", "source_label", "is_learned", "learned_at", "created_at")
    list_filter = ("skill", "entry_type", "is_learned", "book", "test")
    search_fields = ("word", "meaning_cn", "synonym_replacements", "source_title", "source_detail", "question_numbers")
