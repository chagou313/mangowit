from django.core.management.base import BaseCommand

from AI_communication.seed_data import seed_ai_data


class Command(BaseCommand):
    help = "Insert or update the built-in AI question and answer data."

    def handle(self, *args, **options):
        count = seed_ai_data()
        self.stdout.write(
            self.style.SUCCESS(f"已初始化 {count} 条 AI 问答。")
        )
