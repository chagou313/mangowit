# AI_communication/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import AIQuestion, AIAnswer
import random
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

def ai_home(request):
    return render(request, 'ai_index.html')

def get_answer(request):
    if request.method == 'POST':
        question_text = request.POST.get('question')
        if not question_text:
            logger.warning("用户提交的问题为空")
            return JsonResponse({'error': '问题不能为空'}, status=400)

        try:
            question_text = question_text.strip().lower()
            question, created = AIQuestion.objects.get_or_create(question_text=question_text)
            if created:
                logger.info(f"新插入问题: {question.question_text}")
                answer = "这个问题是新插入的，尚未有详细答案。"
            else:
                answer = AIAnswer.objects.get(question=question).answer_text
        except AIAnswer.DoesNotExist:
            logger.warning(f"未找到问题 '{question_text}' 的答案")
            answer = "抱歉，没有找到相关答案。"
        except Exception as e:
            logger.error(f"获取答案时发生错误: {e}")
            return JsonResponse({'error': '服务器错误'}, status=500)

        return JsonResponse({'answer': answer})
    logger.warning("用户使用了无效的请求方法")
    return JsonResponse({'error': '无效的请求方法'}, status=400)

def add_question(request):
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        answer_text = request.POST.get('answer_text')

        if not question_text or not answer_text:
            return JsonResponse({'status': 'error', 'message': '问题和答案不能为空'}, status=400)

        try:
            with transaction.atomic():
                # 创建 AIQuestion 实例
                ai_question = AIQuestion.objects.create(question_text=question_text)

                # 创建对应的 AIAnswer 实例
                AIAnswer.objects.create(question=ai_question, answer_text=answer_text)
        except Exception as e:
            logger.error(f"添加问题和答案时发生错误: {e}")
            return JsonResponse({'status': 'error', 'message': '服务器错误'}, status=500)

        return JsonResponse({'status': 'success', 'message': '问题和答案已成功添加。'})

    return JsonResponse({'status': 'error', 'message': '请求方法错误'}, status=400)
