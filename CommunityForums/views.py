from django.shortcuts import get_object_or_404, redirect, render

from interactions.targets import topic_target
from interactions.views import interaction_context

from .models import Topic


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
    return render(request, "sexual_impulse.html", interaction_context(request, "sexual_impulse"))


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    context = interaction_context(request, topic_target(topic.id))
    context.update({"title": topic.title, "content": topic.content})
    return render(request, "topic_detail.html", context)
