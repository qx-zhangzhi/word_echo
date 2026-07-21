from django.contrib.auth.models import User
from django.db import models


class WritingEntry(models.Model):
    TASK_TYPE_CHOICES = [
        ("task1", "Task 1"),
        ("task2", "Task 2"),
    ]

    CHART_TYPE_CHOICES = [
        ("", "不选择"),
        ("line", "折线图"),
        ("bar", "柱状图"),
        ("pie", "饼图"),
        ("table", "表格"),
        ("map", "地图"),
        ("process", "流程图"),
        ("mixed", "混合图"),
        ("other", "其他"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=255, blank=True)
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        default="task2",
    )

    # Task 1 图表类型
    chart_type = models.CharField(
        max_length=20,
        choices=CHART_TYPE_CHOICES,
        blank=True,
        default="",
    )

    # Task 1 图表图片
    chart_image = models.ImageField(
        upload_to="writing/charts/",
        null=True,
        blank=True,
    )

    prompt = models.TextField(blank=True)
    content = models.TextField()
    note = models.TextField(blank=True)
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Writing #{self.pk}"


class WritingHighlightWord(models.Model):
    entry = models.ForeignKey(
        WritingEntry,
        on_delete=models.CASCADE,
        related_name="highlight_words",
    )
    word = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("entry", "word")
        ordering = ["word"]

    def __str__(self):
        return self.word
