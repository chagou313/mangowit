import random
import secrets

from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import QuizAttempt
from .progress import best_scores
from .question_bank import (
    CATEGORIES,
    LEVEL_NAMES,
    PASS_BONUS,
    PASS_SCORE,
    POINTS_PER_CORRECT,
    QUESTIONS,
    SOURCES,
    get_level,
)

SESSION_KEY = "quiz_attempt"
RESULT_KEY = "quiz_result"
LEVEL_CARDS = {
    1: {"title": "新手试炼场", "image": "game1.png"},
    2: {"title": "高手进阶营", "image": "ganme2.png"},
    3: {"title": "大师挑战阁", "image": "game3.png"},
}


def level_select(request, category=None):
    if category is None:
        return redirect("category_select")
    if category not in CATEGORIES:
        raise Http404
    best = best_scores(request.user)
    levels = []
    for level in sorted(QUESTIONS[category]):
        info = best.get((category, level), {})
        total = len(QUESTIONS[category][level])
        levels.append({
            "number": level,
            "name": LEVEL_NAMES[level],
            "url": reverse("quiz_play", args=[category, level]),
            "best": info.get("best"),
            "passed": info.get("passed", False),
            "total": total,
            "percent": round(100 * info.get("best", 0) / total),
            **LEVEL_CARDS[level],
        })
    return render(request, "level_select.html", {
        "category": category,
        "category_name": CATEGORIES[category]["name"],
        "levels": levels,
        "pass_score": PASS_SCORE,
    })


def play(request, category, level):
    questions = get_level(category, level)
    if not questions:
        raise Http404
    attempt = {
        "id": secrets.token_hex(8),
        "category": category,
        "level": level,
        "perms": [random.sample(range(len(q["options"])), len(q["options"])) for q in questions],
        "answers": [],
    }
    request.session[SESSION_KEY] = attempt
    shown = [
        {"index": i, "text": q["text"], "options": [q["options"][j] for j in attempt["perms"][i]]}
        for i, q in enumerate(questions)
    ]
    return render(request, "quiz_play.html", {
        "category": category,
        "category_name": CATEGORIES[category]["name"],
        "level": level,
        "level_name": LEVEL_NAMES[level],
        "questions": shown,
        "attempt_id": attempt["id"],
        "answer_url": reverse("quiz_answer", args=[category, level]),
        "pass_score": PASS_SCORE,
    })


def _sources(keys):
    return [{"name": SOURCES[k][0], "url": SOURCES[k][1]} for k in keys if k != "consensus"]


@require_POST
def answer(request, category, level):
    questions = get_level(category, level)
    attempt = request.session.get(SESSION_KEY)
    if (
        not questions
        or not attempt
        or attempt["category"] != category
        or attempt["level"] != level
        or attempt["id"] != request.POST.get("attempt")
    ):
        return JsonResponse({"error": "这次答题已经失效，请重新开始本关。"}, status=409)

    index = len(attempt["answers"])
    try:
        asked = int(request.POST.get("question", ""))
        choice = int(request.POST.get("choice", ""))
    except ValueError:
        return JsonResponse({"error": "提交的答案格式不对。"}, status=400)
    if asked != index or index >= len(questions) or not 0 <= choice < len(questions[index]["options"]):
        return JsonResponse({"error": "请按顺序作答。"}, status=400)

    question = questions[index]
    correct_shown = attempt["perms"][index].index(question["answer"])
    is_correct = choice == correct_shown
    attempt["answers"].append(is_correct)
    request.session.modified = True

    payload = {
        "correct": is_correct,
        "answer": correct_shown,
        "explanation": question["explanation"],
        "sources": _sources(question["sources"]),
        "finished": len(attempt["answers"]) == len(questions),
    }
    if payload["finished"]:
        _finish(request, attempt, len(questions))
        payload["result_url"] = reverse("quiz_result")
    return JsonResponse(payload)


def _finish(request, attempt, total):
    correct = sum(attempt["answers"])
    passed = correct >= PASS_SCORE
    points = correct * POINTS_PER_CORRECT + (PASS_BONUS if passed else 0)
    if request.user.is_authenticated:
        QuizAttempt.objects.create(
            user=request.user,
            category=attempt["category"],
            level=attempt["level"],
            correct=correct,
            total=total,
            points=points,
            passed=passed,
        )
    request.session[RESULT_KEY] = {
        "category": attempt["category"],
        "level": attempt["level"],
        "correct": correct,
        "total": total,
        "points": points,
        "passed": passed,
        "saved": request.user.is_authenticated,
    }
    del request.session[SESSION_KEY]


def result(request):
    data = request.session.get(RESULT_KEY)
    if not data:
        return redirect("category_select")
    category, level = data["category"], data["level"]
    next_level = level + 1 if level + 1 in QUESTIONS[category] else None
    return render(request, "quiz_result.html", {
        **data,
        "category_name": CATEGORIES[category]["name"],
        "level_name": LEVEL_NAMES[level],
        "retry_url": reverse("quiz_play", args=[category, level]),
        "next_url": reverse("quiz_play", args=[category, next_level]) if next_level else None,
        "levels_url": reverse("level_select", args=[category]),
        "pass_score": PASS_SCORE,
        "login_url": reverse("login_register") + "?next=" + reverse("level_select", args=[category]),
    })
