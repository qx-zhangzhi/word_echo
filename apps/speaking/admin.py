# apps/speaking/admin.py

from django.contrib import admin
from .models import SpeakingTopic, SpeakingQuestion, SpeakingAnswer


class SpeakingQuestionInline(admin.TabularInline):
    model = SpeakingQuestion
    extra = 1
    fields = ("question_text", "sort_order", "is_active")


@admin.register(SpeakingTopic)
class SpeakingTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "part", "sort_order", "is_active", "created_at")
    list_filter = ("part", "is_active")
    search_fields = ("title", "description")
    ordering = ("part", "sort_order", "id")
    inlines = [SpeakingQuestionInline]


@admin.register(SpeakingQuestion)
class SpeakingQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "short_question", "sort_order", "is_active", "created_at")
    list_filter = ("topic__part", "topic", "is_active")
    search_fields = ("question_text", "sample_answer", "key_points", "useful_expressions")
    ordering = ("topic", "sort_order", "id")

    def short_question(self, obj):
        return obj.question_text[:80]

    short_question.short_description = "问题"


@admin.register(SpeakingAnswer)
class SpeakingAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "score_overall",
        "score_fluency",
        "score_pronunciation",
        "created_at",
    )
    list_filter = ("question__topic", "created_at")
    search_fields = ("answer_text", "feedback", "corrected_answer")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
