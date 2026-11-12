from django.conf import settings
from django.db import models


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    target = models.CharField("评论对象", max_length=40, db_index=True)
    body = models.TextField("内容", max_length=300)
    is_hidden = models.BooleanField("已隐藏", default=False)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}：{self.body[:30]}"
