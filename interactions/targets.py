"""Pages that readers can like and comment on.

A target is a short string key: a news/law article key ("news1"), the fixed
community post ("sexual_impulse"), a user-published topic ("topic-12"), or an
automatically collected news item ("news-34"), or a curated law
("law-school_protection").
"""
import re

from django.urls import reverse

from EducationInformation.articles import ARTICLES

FIXED_POSTS = {
    "sexual_impulse": {"category": "社区", "title": "青少年如何正确看待性冲动？", "url_name": "sexual_impulse"},
}
_TOPIC = re.compile(r"^topic-(\d+)$")
_NEWS = re.compile(r"^news-(\d+)$")
_LAW = re.compile(r"^law-([a-z0-9_]+)$")


def resolve(target):
    """Return {"category", "title", "url"} for a target key, or None if unknown."""
    if target in ARTICLES:
        info = ARTICLES[target]
        return {"category": info["category"], "title": info["title"], "url": reverse(target)}
    if target in FIXED_POSTS:
        info = FIXED_POSTS[target]
        return {"category": info["category"], "title": info["title"], "url": reverse(info["url_name"])}
    match = _TOPIC.match(target or "")
    if match:
        from CommunityForums.models import Topic

        topic = Topic.objects.filter(pk=int(match.group(1))).first()
        if topic:
            return {
                "category": "社区",
                "title": topic.title,
                "url": reverse("topic_detail", args=[topic.pk]),
            }
    match = _LAW.match(target or "")
    if match:
        from EducationInformation.laws import LAWS_BY_SLUG

        law = LAWS_BY_SLUG.get(match.group(1))
        if law:
            return {"category": "法规", "title": law["title"], "url": reverse("law_detail", args=[law["slug"]])}
    match = _NEWS.match(target or "")
    if match:
        from EducationInformation.models import NewsItem

        item = NewsItem.objects.filter(pk=int(match.group(1)), is_hidden=False).first()
        if item:
            return {"category": "新闻", "title": item.title, "url": reverse("news_item", args=[item.pk])}
    return None


def news_target(news_id):
    return f"news-{news_id}"


def topic_target(topic_id):
    return f"topic-{topic_id}"
