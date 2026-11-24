from django.conf import settings
from django.db import models


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
    """A reader's like or favorite on an article or community post (see interactions.targets)."""

    LIKE = "like"
    FAVORITE = "favorite"
    KIND_CHOICES = [(LIKE, "点赞"), (FAVORITE, "收藏")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="article_reactions"
    )
    article = models.CharField("对象", max_length=40)
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


class NewsItem(models.Model):
    """A headline fetched automatically by news_feed.fetch_news; links to the original article."""

    title = models.CharField("标题", max_length=200)
    url = models.URLField("原文链接", max_length=500, unique=True)
    source = models.CharField("来源", max_length=80, blank=True)
    summary = models.CharField("摘要", max_length=300, blank=True)
    published_at = models.DateTimeField("发布时间", db_index=True)
    fetched_at = models.DateTimeField("抓取时间", auto_now_add=True)
    is_hidden = models.BooleanField("隐藏", default=False)

    class Meta:
        verbose_name = "自动资讯"
        verbose_name_plural = verbose_name
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class NewsFetchRun(models.Model):
    """One run of the news fetcher; the latest one decides when to fetch again."""

    started_at = models.DateTimeField("开始时间", auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField("结束时间", null=True, blank=True)
    added = models.PositiveIntegerField("新增条数", default=0)
    error = models.CharField("错误", max_length=500, blank=True)

    class Meta:
        verbose_name = "资讯抓取记录"
        verbose_name_plural = verbose_name
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.started_at:%Y-%m-%d %H:%M} +{self.added}"
