# apps/primary_dictation/models.py

from django.conf import settings
from django.db import models
from django.utils import timezone


class PrimaryWordSet(models.Model):
    """小学英语听写词表，例如：三年级上册 Unit 1."""

    GRADE_CHOICES = [
        ("g1", "一年级"),
        ("g2", "二年级"),
        ("g3", "三年级"),
        ("g4", "四年级"),
        ("g5", "五年级"),
        ("g6", "六年级"),
    ]

    TERM_CHOICES = [
        ("upper", "上册"),
        ("lower", "下册"),
        ("other", "其他"),
    ]

    title = models.CharField(max_length=200, verbose_name="词表名称")
    grade = models.CharField(
        max_length=20,
        choices=GRADE_CHOICES,
        default="g3",
        verbose_name="年级",
    )
    term = models.CharField(
        max_length=20,
        choices=TERM_CHOICES,
        default="upper",
        verbose_name="学期",
    )
    unit = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="单元",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="说明",
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "primary_word_set"
        ordering = ["grade", "term", "sort_order", "id"]
        verbose_name = "小学听写词表"
        verbose_name_plural = "小学听写词表"

    def __str__(self):
        return self.title


class PrimaryDictationWord(models.Model):
    """词表中的单词."""

    word_set = models.ForeignKey(
        PrimaryWordSet,
        on_delete=models.CASCADE,
        related_name="words",
        verbose_name="所属词表",
    )
    word = models.CharField(max_length=100, verbose_name="英文单词")
    meaning_cn = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="中文意思",
    )
    phonetic = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="音标",
    )
    example_sentence = models.TextField(
        blank=True,
        default="",
        verbose_name="例句",
    )

    # 可选：以后接你的 CosyVoice，保存音频 URL
    audio_url = models.URLField(
        blank=True,
        default="",
        verbose_name="音频 URL",
    )

    sort_order = models.IntegerField(default=0, verbose_name="排序")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "primary_dictation_word"
        ordering = ["word_set", "sort_order", "id"]
        unique_together = ("word_set", "word")
        verbose_name = "小学听写单词"
        verbose_name_plural = "小学听写单词"

    def __str__(self):
        return self.word


class PrimaryDictationSession(models.Model):
    """一次听写练习."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="用户",
    )
    word_set = models.ForeignKey(
        PrimaryWordSet,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="词表",
    )

    total_count = models.PositiveIntegerField(default=0, verbose_name="总数")
    correct_count = models.PositiveIntegerField(default=0, verbose_name="正确数")
    wrong_count = models.PositiveIntegerField(default=0, verbose_name="错误数")

    started_at = models.DateTimeField(default=timezone.now, verbose_name="开始时间")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="提交时间")

    class Meta:
        db_table = "primary_dictation_session"
        ordering = ["-started_at"]
        verbose_name = "小学听写记录"
        verbose_name_plural = "小学听写记录"

    def __str__(self):
        return f"{self.user} - {self.word_set} - {self.started_at}"


class PrimaryDictationResult(models.Model):
    """一次听写中的单词结果."""

    session = models.ForeignKey(
        PrimaryDictationSession,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="听写记录",
    )
    word = models.ForeignKey(
        PrimaryDictationWord,
        on_delete=models.CASCADE,
        verbose_name="单词",
    )

    answer_text = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="学生答案",
    )
    is_correct = models.BooleanField(default=False, verbose_name="是否正确")

    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")

    class Meta:
        db_table = "primary_dictation_result"
        ordering = ["id"]
        verbose_name = "小学听写结果"
        verbose_name_plural = "小学听写结果"

    def __str__(self):
        return f"{self.word.word} - {self.answer_text}"
