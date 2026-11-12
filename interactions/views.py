from datetime import timedelta

from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.http import require_POST

from EducationInformation.models import ArticleReaction

from .models import Comment
from .moderation import check_comment
from .targets import resolve

RATE_LIMIT = 5  # comments per user per minute


def reaction_state(request, target):
    """Like count and the current reader's like/favorite state for one target."""
    reactions = ArticleReaction.objects.filter(article=target)
    mine = set()
    if request.user.is_authenticated:
        mine = set(reactions.filter(user=request.user).values_list("kind", flat=True))
    return {
        "like_count": reactions.filter(kind=ArticleReaction.LIKE).count(),
        "liked": ArticleReaction.LIKE in mine,
        "favorited": ArticleReaction.FAVORITE in mine,
    }


def visible_comments(target):
    return Comment.objects.filter(target=target, is_hidden=False).select_related("user")


def interaction_context(request, target, can_favorite=True):
    """Everything the shared like/favorite/comment components need."""
    comments = visible_comments(target)
    return {
        "article_key": target,
        "can_favorite": can_favorite,
        "reactions": reaction_state(request, target),
        "comments": comments[:50],
        "comment_count": comments.count(),
        "login_url": reverse("login_register") + "?" + urlencode({"next": request.path}),
    }


def comment_json(comment):
    return {
        "id": comment.pk,
        "user": comment.user.username,
        "body": comment.body,
        "created": timezone.localtime(comment.created_at).strftime("%Y-%m-%d %H:%M"),
    }


@require_POST
def post_comment(request, target):
    if resolve(target) is None:
        raise Http404
    if not request.user.is_authenticated:
        return JsonResponse({"error": "请先登录再发表评论。"}, status=401)

    body = (request.POST.get("body") or "").strip()
    problem = check_comment(body)
    if problem:
        return JsonResponse({"error": problem}, status=400)

    recent = Comment.objects.filter(
        user=request.user, created_at__gte=timezone.now() - timedelta(minutes=1)
    ).count()
    if recent >= RATE_LIMIT:
        return JsonResponse({"error": "评论太频繁了，请过一分钟再试。"}, status=429)

    comment = Comment.objects.create(user=request.user, target=target, body=body)
    return JsonResponse({
        "comment": comment_json(comment),
        "comment_count": visible_comments(target).count(),
    }, status=201)
