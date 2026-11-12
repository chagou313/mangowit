import logging

from cloudinary.exceptions import Error as CloudinaryError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from challenge.progress import best_scores, category_progress, user_stats
from challenge.question_bank import CATEGORIES, LEVEL_NAMES, QUESTIONS
from CommunityForums.models import Topic
from EducationInformation.articles import ARTICLES
from EducationInformation.models import ArticleReaction
from interactions.models import Comment
from interactions.targets import resolve

from .forms import RegistrationForm, UserProfileForm


logger = logging.getLogger(__name__)


def _daily_question():
    """The same question for everyone on a given day, cycling through the bank."""
    pool = [
        (category, level, question)
        for category, levels in QUESTIONS.items()
        for level, questions in levels.items()
        for question in questions
    ]
    category, level, question = pool[timezone.localdate().toordinal() % len(pool)]
    return {
        "text": question["text"],
        "category": CATEGORIES[category]["name"],
        "url": reverse("quiz_play", args=[category, level]),
    }


def _next_level(user):
    """The first level this reader hasn't passed, in category order."""
    best = best_scores(user)
    for category, levels in QUESTIONS.items():
        for level in sorted(levels):
            if not best.get((category, level), {}).get("passed"):
                return {
                    "name": f"{CATEGORIES[category]['name']} · {LEVEL_NAMES[level]}",
                    "url": reverse("quiz_play", args=[category, level]),
                }
    return None


def index(request):
    articles = []
    for key, info in ARTICLES.items():
        articles.append({
            **info,
            "url": reverse(key),
            "likes": ArticleReaction.objects.filter(article=key, kind=ArticleReaction.LIKE).count(),
            "comments": Comment.objects.filter(target=key, is_hidden=False).count(),
        })
    context = {
        "articles": articles,
        "topics": Topic.objects.order_by("-created_at")[:5],
        "daily": _daily_question(),
    }
    if request.user.is_authenticated:
        context["stats"] = user_stats(request.user)
        context["next_level"] = _next_level(request.user)
    return render(request, "index.html", context)


def knowledge(request):
    return render(request, "knowledge.html")


def news(request):
    return render(request, "news.html")


def quiz(request):
    return redirect("category_select")


def community(request):
    topics = Topic.objects.order_by("-created_at")[:8]
    return render(request, "community.html", {"topics": topics})


def physiological_knowledge(request):
    return render(request, "knowledge/physiological_knowledge.html")


def psychological_knowledge(request):
    return render(request, "knowledge/psychological_knowledge.html")


def safety_knowledge(request):
    return render(request, "knowledge/safety_knowledge.html")


@login_required(login_url="login_register")
def quiz_history(request):
    return render(request, "quiz_history.html", {
        "attempts": request.user.quiz_attempts.all()[:100],
        "stats": user_stats(request.user),
        "level_names": LEVEL_NAMES,
    })


def category_select(request):
    passed = category_progress(request.user)
    progress = {
        key: {"passed": count, "percent": round(100 * count / 3)} for key, count in passed.items()
    }
    return render(request, "category_select.html", {"progress": progress})


def _reacted_articles(user, kind):
    items = []
    for reaction in user.article_reactions.filter(kind=kind):
        info = resolve(reaction.article)
        if info:  # skip posts that have since been deleted
            items.append({**info, "saved_at": reaction.created_at})
    return items


@login_required(login_url="login_register")
def favorite_news(request):
    return render(request, "favorite_news.html", {
        "favorites": _reacted_articles(request.user, ArticleReaction.FAVORITE),
        "likes": _reacted_articles(request.user, ArticleReaction.LIKE),
    })


def _safe_next(request):
    target = request.GET.get("next", "")
    if url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return ""


def login_register(request):
    form_type = request.GET.get("form_type", "login")
    form = None

    if request.method == "POST":
        if form_type == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info("User %s logged in successfully.", username)
                messages.success(request, "登录成功！")
                return redirect(_safe_next(request) or "index")
            messages.error(request, "用户名或密码错误，请重试。")
            logger.warning("Failed login attempt for user %s.", username)
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "注册成功，请登录。")
                return redirect("login_register")
            messages.error(request, "注册失败，请检查输入信息。")
    elif form_type == "register":
        form = RegistrationForm()

    return render(
        request,
        "login_register.html",
        {"form_type": form_type, "form": form},
    )


def user_logout(request):
    logout(request)
    messages.success(request, "退出登录成功！")
    return redirect("index")


def _profile_context(request, form):
    user = request.user
    reactions = user.article_reactions
    passed = category_progress(user)
    recent_comments = []
    for comment in user.comments.filter(is_hidden=False)[:3]:
        target = resolve(comment.target)
        if target:
            recent_comments.append({"body": comment.body, "created_at": comment.created_at, **target})
    return {
        "form": form,
        "stats": user_stats(user),
        "favorite_count": reactions.filter(kind=ArticleReaction.FAVORITE).count(),
        "like_count": reactions.filter(kind=ArticleReaction.LIKE).count(),
        "comment_count": user.comments.filter(is_hidden=False).count(),
        "category_progress": [
            {"key": key, "name": info["name"], "icon": info["icon"], "passed": passed[key],
             "total": len(QUESTIONS[key]), "percent": round(100 * passed[key] / len(QUESTIONS[key]))}
            for key, info in CATEGORIES.items()
        ],
        "recent_attempts": user.quiz_attempts.all()[:3],
        "recent_comments": recent_comments,
    }


@login_required(login_url="login_register")
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except CloudinaryError:
                request.user.refresh_from_db()
                form = UserProfileForm(request.POST, instance=request.user)
                form.add_error(
                    "profile_picture",
                    "头像上传失败，请稍后重试。",
                )
                return render(request, "profile.html", _profile_context(request, form))
            messages.success(request, "个人信息更新成功！")
            return redirect("profile")
        messages.error(request, "保存失败，请根据下面的提示修改。")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "profile.html", _profile_context(request, form))
