import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mangowit.settings")
django.setup()

from AI_communication.seed_data import seed_ai_data  # noqa: E402


if __name__ == "__main__":
    count = seed_ai_data()
    print(f"已初始化 {count} 条 AI 问答。")
