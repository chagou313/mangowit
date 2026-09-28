from django.test import TestCase
from django.urls import reverse

from CommunityForums.models import Topic


class TopicDetailTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_missing_topic_returns_404(self):
        response = self.client.get(reverse("topic_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_existing_topic_renders(self):
        topic = Topic.objects.create(title="测试话题", content="测试话题内容")

        response = self.client.get(reverse("topic_detail", args=[topic.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试话题")
        self.assertContains(response, "测试话题内容")
