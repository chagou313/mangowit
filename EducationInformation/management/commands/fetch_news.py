from django.core.management.base import BaseCommand

from EducationInformation.news_feed import fetch_news


class Command(BaseCommand):
    help = "抓取最新的性教育、青春期健康相关新闻标题（过滤后保存）"

    def handle(self, *args, **options):
        result = fetch_news()
        self.stdout.write(f"新增 {result['added']} 条，跳过 {result['skipped']} 条")
        for error in result["errors"]:
            self.stderr.write(f"抓取失败：{error}")
