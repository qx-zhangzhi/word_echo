# jianpu/models.py

from django.db import models


def default_cell():
    return {
        "note": "",
        "lyric": "",
        "octave": 0,
        "duration": "quarter",
    }


def default_score_data():
    rows = []
    for _ in range(4):
        row = []
        for _ in range(16):
            row.append(default_cell())
        rows.append(row)
    return rows


class JianpuScore(models.Model):
    title = models.CharField("歌曲名称", max_length=200, default="未命名歌曲")
    key = models.CharField("调号", max_length=20, default="1=C")
    time_signature = models.CharField("拍号", max_length=20, default="4/4")
    tempo = models.IntegerField("速度", default=90)

    score_data = models.JSONField("简谱数据", default=default_score_data)

    is_public = models.BooleanField("是否公开", default=False)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "简谱"
        verbose_name_plural = "简谱"

    def __str__(self):
        return self.title
