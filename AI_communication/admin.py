from django.contrib import admin
from .models import AIQuestion, AIAnswer

@admin.register(AIQuestion)
class AIQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'asked_at')
    search_fields = ('question_text',)
    date_hierarchy = 'asked_at'

@admin.register(AIAnswer)
class AIAnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_text', 'answered_at', 'question')
    search_fields = ('answer_text',)
    date_hierarchy = 'answered_at'
    raw_id_fields = ('question',)  # 使用 raw ID 字段来选择关联的 AIQuestion
