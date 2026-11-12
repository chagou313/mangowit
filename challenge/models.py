from django.conf import settings
from django.db import models

from .question_bank import CATEGORIES

CATEGORY_CHOICES = [(key, info["name"]) for key, info in CATEGORIES.items()]


class QuizAttempt(models.Model):
    """One finished level of 答题闯关 by a logged-in reader."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    category = models.CharField("分类", max_length=20, choices=CATEGORY_CHOICES)
    level = models.PositiveSmallIntegerField("关卡")
    correct = models.PositiveSmallIntegerField("答对题数")
    total = models.PositiveSmallIntegerField("总题数")
    points = models.PositiveSmallIntegerField("获得积分")
    passed = models.BooleanField("是否通过")
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "闯关记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.get_category_display()} 第{self.level}关 {self.correct}/{self.total}"
