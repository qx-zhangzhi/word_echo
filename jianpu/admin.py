# jianpu/admin.py

from django.contrib import admin

from .models import JianpuScore


@admin.register(JianpuScore)
class JianpuScoreAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "key",
        "time_signature",
        "tempo",
        "is_public",
        "updated_at",
    ]
    list_filter = ["is_public", "key", "time_signature"]
    search_fields = ["title"]
    readonly_fields = ["created_at", "updated_at"]
