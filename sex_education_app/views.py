import logging

from cloudinary.exceptions import Error as CloudinaryError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from challenge.progress import best_scores, category_progress, user_stats
from challenge.question_bank import CATEGORIES, LEVEL_NAMES, QUESTIONS
from CommunityForums.models import Topic
from EducationInformation.articles import ARTICLES
from EducationInformation.laws import LAWS
from EducationInformation.models import ArticleReaction, NewsFetchRun, NewsItem
from EducationInformation.news_feed import refresh_if_stale
from interactions.models import Comment
from interactions.targets import news_target, resolve

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


def _counts(targets):
    """{target: (likes, comments)} for a batch of interaction targets."""
    likes = dict(
        ArticleReaction.objects.filter(article__in=targets, kind=ArticleReaction.LIKE)
        .values_list("article").annotate(n=Count("id"))
    )
    comments = dict(
        Comment.objects.filter(target__in=targets, is_hidden=False)
        .values_list("target").annotate(n=Count("id"))
    )
    return {t: (likes.get(t, 0), comments.get(t, 0)) for t in targets}


def news(request):
    refresh_if_stale()

    def feed_row(item, tab, pin=""):
        day = timezone.localtime(item.published_at)
        return {"key": news_target(item.pk), "tab": tab, "pin": pin, "title": item.title,
                "url": reverse("news_item", args=[item.pk]),
                "meta": f"{item.source or '网络'} · {day.year}年{day.month}月{day.day}日"}

    feed = list(NewsItem.objects.filter(is_hidden=False)[:80])
    rows = [
        {"key": key, "tab": "news", "pin": "精选", "title": ARTICLES[key]["title"], "url": reverse(key), "meta": "精选报道"}
        for key in ["news1", "news2", "news3"]
    ]
    rows += [feed_row(item, "news") for item in feed if item.kind == "news"]
    rows += [
        {"key": f"law-{law['slug']}", "tab": "law", "pin": law["kind"], "title": law["title"],
         "url": reverse("law_detail", args=[law["slug"]]), "meta": f"{law['issuer']} · {law['effective']}"}
        for law in LAWS
    ]
    rows += [
        {"key": key, "tab": "law", "pin": "普法", "title": ARTICLES[key]["title"], "url": reverse(key), "meta": "普法文章"}
        for key in ["law1", "law2", "law3"]
    ]
    rows += [feed_row(item, "law", "动态") for item in feed if item.kind == "law"]
    counts = _counts([row["key"] for row in rows])
    for row in rows:
        row["likes"], row["comments"] = counts[row["key"]]
    last_run = NewsFetchRun.objects.filter(finished_at__isnull=False).first()
    return render(request, "news.html", {
        "rows": rows,
        "news_count": sum(1 for row in rows if row["tab"] == "news"),
        "law_count": sum(1 for row in rows if row["tab"] == "law"),
        "last_update": last_run.finished_at if last_run else None,
    })


def community(request):
    topics = Topic.objects.order_by("-created_at")[:8]
    return render(request, "community.html", {"topics": topics})


@login_required(login_url="login_register")
def quiz_history(request):
    return render(request, "quiz_history.html", {
        "attempts": request.user.quiz_attempts.all()[:100],
        "stats": user_stats(request.user),
        "level_names": LEVEL_NAMES,
    })


QUIZ_TOPICS = [
    ("physiology", "生理知识大冒险", "身体发育、月经与遗精、生殖健康和日常护理，弄懂青春期身体的变化。"),
    ("psychology", "心理知识探秘之旅", "情绪起伏、自我认同、喜欢一个人和人际关系，学会照顾自己的心情。"),
    ("prevention", "防范性知识守护战", "身体边界、识别危险信号、求助渠道和相关法律，学会保护自己。"),
]


def category_select(request):
    passed = category_progress(request.user)
    topics = [
        {"key": key, "title": title, "desc": desc, "passed": passed.get(key, 0), **CATEGORIES[key]}
        for key, title, desc in QUIZ_TOPICS
    ]
    return render(request, "category_select.html", {
        "topics": topics,
        "total_passed": sum(t["passed"] for t in topics),
    })


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
    username = ""

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
        {"form_type": form_type, "form": form, "username": username},
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
