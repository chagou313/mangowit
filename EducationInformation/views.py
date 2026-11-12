from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from interactions.targets import resolve
from interactions.views import interaction_context, reaction_state

from .models import Article, ArticleReaction


def education_index(request):
    articles = Article.objects.all()[:5]
    return render(request, 'education_index.html', {'articles': articles})


def render_article(request, article, extra=None):
    context = interaction_context(request, article)
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
    if resolve(article) is None or kind not in dict(ArticleReaction.KIND_CHOICES):
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
