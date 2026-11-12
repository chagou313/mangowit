from django.contrib import admin

from .models import QuizAttempt


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "level", "correct", "total", "points", "passed", "created_at")
    list_filter = ("category", "level", "passed")
    search_fields = ("user__username",)
