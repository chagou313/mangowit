from django.test import TestCase
from django.urls import reverse

from EducationInformation.models import Article


class EducationIndexTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_empty_education_index_renders(self):
        response = self.client.get(reverse("education_index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "暂无教育资讯")

    def test_education_index_lists_articles(self):
        Article.objects.create(
            title="测试教育资讯",
            content="用于页面回归测试的文章内容",
            source_url="https://example.com/article",
        )

        response = self.client.get(reverse("education_index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试教育资讯")
        self.assertContains(response, "https://example.com/article")
