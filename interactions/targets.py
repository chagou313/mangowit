"""Pages that readers can like and comment on.

A target is a short string key: a news/law article key ("news1"), the fixed
community post ("sexual_impulse"), or a user-published topic ("topic-12").
"""
import re

from django.urls import reverse

from EducationInformation.articles import ARTICLES

FIXED_POSTS = {
    "sexual_impulse": {"category": "社区", "title": "青少年如何正确看待性冲动？", "url_name": "sexual_impulse"},
}
_TOPIC = re.compile(r"^topic-(\d+)$")


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
    return None


def topic_target(topic_id):
    return f"topic-{topic_id}"
