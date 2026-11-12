from django.conf import settings
from django.db import models

from .articles import ARTICLE_CHOICES

class Article(models.Model):
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    source_url = models.URLField("来源链接")
    publish_date = models.DateTimeField("发布时间", auto_now_add=True)

    class Meta:
        verbose_name = "教育资讯"
        verbose_name_plural = verbose_name
        ordering = ['-publish_date']

    def __str__(self):
        return self.title


class ArticleReaction(models.Model):
    """A reader's like or favorite on one of the news or law articles."""

    LIKE = "like"
    FAVORITE = "favorite"
    KIND_CHOICES = [(LIKE, "点赞"), (FAVORITE, "收藏")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="article_reactions"
    )
    article = models.CharField("文章", max_length=20, choices=ARTICLE_CHOICES)
    kind = models.CharField("类型", max_length=10, choices=KIND_CHOICES)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "点赞与收藏"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "article", "kind"], name="unique_article_reaction"
            )
        ]
        indexes = [models.Index(fields=["article", "kind"])]

    def __str__(self):
        return f"{self.user} {self.get_kind_display()} {self.article}"
