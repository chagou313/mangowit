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
