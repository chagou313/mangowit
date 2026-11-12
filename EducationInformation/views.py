from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from .articles import ARTICLES
from .models import Article, ArticleReaction


def education_index(request):
    articles = Article.objects.all()[:5]
    return render(request, 'education_index.html', {'articles': articles})


def reaction_state(request, article):
    """Like count and the current reader's like/favorite state for one article."""
    reactions = ArticleReaction.objects.filter(article=article)
    mine = set()
    if request.user.is_authenticated:
        mine = set(reactions.filter(user=request.user).values_list("kind", flat=True))
    return {
        "like_count": reactions.filter(kind=ArticleReaction.LIKE).count(),
        "liked": ArticleReaction.LIKE in mine,
        "favorited": ArticleReaction.FAVORITE in mine,
    }


def render_article(request, article, extra=None):
    context = {
        "article_key": article,
        "reactions": reaction_state(request, article),
        "login_url": reverse("login_register") + "?" + urlencode({"next": request.path}),
    }
    context.update(extra or {})
    return render(request, f"{article}.html", context)


def news1(request):
    return render_article(request, "news1", {
        'official_url': 'https://www.toutiao.com/article/7492683601142759945/'
    })


def news2(request):
    return render_article(request, "news2")


def news3(request):
    return render_article(request, "news3")


def law1(request):
    return render_article(request, "law1")


def law2(request):
    return render_article(request, "law2")


def law3(request):
    return render_article(request, "law3")


@require_POST
def toggle_reaction(request, article, kind):
    if article not in ARTICLES or kind not in dict(ArticleReaction.KIND_CHOICES):
        raise Http404
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录"}, status=401)

    existing = ArticleReaction.objects.filter(user=request.user, article=article, kind=kind)
    if existing.exists():
        existing.delete()
    else:
        try:
            with transaction.atomic():
                ArticleReaction.objects.create(user=request.user, article=article, kind=kind)
        except IntegrityError:
            pass  # a double click already created it
    return JsonResponse(reaction_state(request, article))
