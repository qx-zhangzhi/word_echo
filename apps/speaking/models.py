# apps/speaking/models.py

from django.db import models
from django.utils import timezone


class SpeakingTopic(models.Model):
    """雅思口语话题，例如 Work, Study, Hometown, Technology."""

    PART_CHOICES = (
        ("part1", "Part 1"),
        ("part2", "Part 2"),
        ("part3", "Part 3"),
    )

    title = models.CharField(max_length=200, verbose_name="话题标题")
    part = models.CharField(
        max_length=20,
        choices=PART_CHOICES,
        default="part1",
        verbose_name="雅思部分",
    )
    description = models.TextField(blank=True, default="", verbose_name="话题说明")
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "speaking_topic"
        ordering = ["part", "sort_order", "id"]
        verbose_name = "口语话题"
        verbose_name_plural = "口语话题"

    def __str__(self):
        return f"{self.get_part_display()} - {self.title}"


class SpeakingQuestion(models.Model):
    """某个话题下的具体问题。"""

    topic = models.ForeignKey(
        SpeakingTopic,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="所属话题",
    )
    question_text = models.TextField(verbose_name="问题内容")

    # 可选：给学生看的参考回答
    sample_answer = models.TextField(blank=True, default="", verbose_name="参考回答")

    # 可选：关键词、表达、句型
    key_points = models.TextField(blank=True, default="", verbose_name="答题要点")
    useful_expressions = models.TextField(blank=True, default="", verbose_name="有用表达")

    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "speaking_question"
        ordering = ["topic", "sort_order", "id"]
        verbose_name = "口语问题"
        verbose_name_plural = "口语问题"

    def __str__(self):
        return self.question_text[:80]


class SpeakingAnswer(models.Model):
    """某个问题的一次回答记录。一个问题可以有多次回答。"""

    question = models.ForeignKey(
        SpeakingQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="所属问题",
    )

    answer_text = models.TextField(blank=True, default="", verbose_name="回答文本")

    # 用户录音文件
    audio_file = models.FileField(
        upload_to="speaking/answers/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="回答录音",
    )

    # 跟读/评分结果
    score_overall = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="总分",
    )
    score_fluency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="流利度",
    )
    score_pronunciation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="发音",
    )
    score_grammar = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="语法",
    )
    score_vocab = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="词汇",
    )

    feedback = models.TextField(blank=True, default="", verbose_name="反馈")
    corrected_answer = models.TextField(blank=True, default="", verbose_name="优化后回答")

    duration_seconds = models.IntegerField(blank=True, null=True, verbose_name="录音时长秒数")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "speaking_answer"
        ordering = ["-created_at"]
        verbose_name = "口语回答记录"
        verbose_name_plural = "口语回答记录"

    def __str__(self):
        return f"Answer #{self.id} - {self.question_id}"
