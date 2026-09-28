from django.shortcuts import get_object_or_404, redirect, render

from .models import Topic


def community_index(request):
    topics = Topic.objects.all().order_by("-created_at")
    return render(request, "community_index.html", {"topics": topics})


def publish_topic(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if not title or not content:
            return render(
                request,
                "publish_topic.html",
                {"initial_title": title, "error_message": "话题标题和详细内容不能为空"},
            )
        topic = Topic.objects.create(title=title, content=content)
        return redirect("topic_detail", topic_id=topic.id)

    initial_title = request.GET.get("title", "")
    return render(request, "publish_topic.html", {"initial_title": initial_title})


def sexual_impulse(request):
    return render(request, "sexual_impulse.html")


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    return render(
        request,
        "topic_detail.html",
        {"title": topic.title, "content": topic.content},
    )
