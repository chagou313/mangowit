# AI_communication/views.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import AIQuestion, AIAnswer
import difflib
import logging
import re
from django.db import transaction

logger = logging.getLogger(__name__)

def ai_home(request):
    return render(request, 'ai_index.html')

NO_ANSWER = "抱歉，小青芒暂时还不会回答这个问题。可以换个说法试试，或者去交流社区问问大家。"
_IGNORED_CHARS = re.compile(r"[\s?？!！。.,，、~～]+")
MATCH_THRESHOLD = 0.6


# Question words that change how a question is phrased but not what it asks.
_QUESTION_WORDS = re.compile("请问|什么是|是什么|怎么样|怎么|怎样|如何|什么|吗|呢|啊|的")


def _normalize(text):
    text = _IGNORED_CHARS.sub("", text).lower()
    return _QUESTION_WORDS.sub("", text) or text


def find_answer(question_text):
    """Return the stored answer whose question best matches the user's text."""
    target = _normalize(question_text)
    if not target:
        return None
    best_answer, best_score = None, 0.0
    for answer in AIAnswer.objects.select_related("question"):
        candidate = _normalize(answer.question.question_text)
        if candidate == target:
            return answer.answer_text
        score = difflib.SequenceMatcher(None, target, candidate).ratio()
        if score > best_score:
            best_answer, best_score = answer, score
    if best_answer is not None and best_score >= MATCH_THRESHOLD:
        return best_answer.answer_text
    return None


@require_POST
def get_answer(request):
    question_text = (request.POST.get("question") or "").strip()
    if not question_text:
        return JsonResponse({"error": "问题不能为空"}, status=400)
    answer = find_answer(question_text)
    if answer is None:
        logger.info("No stored answer for question: %s", question_text[:100])
        return JsonResponse({"answer": NO_ANSWER, "matched": False})
    return JsonResponse({"answer": answer, "matched": True})


def _staff_only(user):
    return user.is_active and user.is_staff


@user_passes_test(_staff_only, login_url='login_register')
@require_POST
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
