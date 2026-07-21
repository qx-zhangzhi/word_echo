from django.contrib import admin
from .models import SynonymEntry, SynonymItem


class SynonymItemInline(admin.TabularInline):
    model = SynonymItem
    extra = 1


@admin.register(SynonymEntry)
class SynonymEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "headword", "meaning_cn", "user", "updated_at")
    search_fields = ("headword", "meaning_cn", "usage_note", "example_sentence")
    inlines = [SynonymItemInline]


@admin.register(SynonymItem)
class SynonymItemAdmin(admin.ModelAdmin):
    list_display = ("id", "word", "entry", "note", "created_at")
    search_fields = ("word", "note")
