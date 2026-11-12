"""Totals and per-level progress computed from a reader's saved attempts."""
from django.db.models import Max, Sum

from .question_bank import CATEGORIES, QUESTIONS


def user_stats(user):
    attempts = user.quiz_attempts.all()
    return {
        "attempt_count": attempts.count(),
        "points": attempts.aggregate(total=Sum("points"))["total"] or 0,
        "levels_passed": attempts.filter(passed=True).values("category", "level").distinct().count(),
        "levels_total": sum(len(levels) for levels in QUESTIONS.values()),
    }


def best_scores(user):
    """{(category, level): {"best": n, "passed": bool}} for a logged-in reader."""
    if not user.is_authenticated:
        return {}
    rows = user.quiz_attempts.values("category", "level").annotate(
        best=Max("correct"), passed_any=Max("passed")
    )
    return {(r["category"], r["level"]): {"best": r["best"], "passed": bool(r["passed_any"])} for r in rows}


def category_progress(user):
    """{category: number of passed levels} for the category picker."""
    best = best_scores(user)
    return {
        key: sum(1 for (cat, _), info in best.items() if cat == key and info["passed"])
        for key in CATEGORIES
    }
