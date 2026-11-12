from django.test import TestCase, override_settings
from django.urls import reverse

from AI_communication.models import AIQuestion
from AI_communication.seed_data import seed_ai_data
from CommunityForums.models import Topic


PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


class AIAnswerMatchingTests(TestCase):
    def setUp(self):
        seed_ai_data()

    def ask(self, question):
        return self.client.post(reverse("get_answer"), {"question": question}).json()

    def test_chinese_punctuation_and_word_order_still_match(self):
        for question in ["什么是性教育？", "什么是性教育", "性教育是什么"]:
            with self.subTest(question=question):
                response = self.ask(question)
                self.assertTrue(response["matched"])
                self.assertTrue(response["answer"].startswith("性教育是指"))

    def test_unrelated_question_gets_fallback_without_saving_it(self):
        before = AIQuestion.objects.count()
        response = self.ask("今天天气怎么样")
        self.assertFalse(response["matched"])
        self.assertEqual(AIQuestion.objects.count(), before)

    def test_get_request_is_rejected(self):
        self.assertEqual(self.client.get(reverse("get_answer")).status_code, 405)


@PLAIN_STATIC
class CommunityTopicListTests(TestCase):
    def test_published_topic_appears_on_community_page(self):
        topic = Topic.objects.create(title="我的新话题", content="内容")
        response = self.client.get(reverse("community"))
        self.assertContains(response, "我的新话题")
        self.assertContains(response, reverse("topic_detail", args=[topic.id]))


@PLAIN_STATIC
class VideoPageNavigationTests(TestCase):
    def test_back_to_directory_links_to_knowledge_page(self):
        for name in ["video1", "video2"]:
            with self.subTest(page=name):
                self.assertContains(
                    self.client.get(reverse(name)),
                    f'href="{reverse("knowledge")}" class="nav-link">回到目录',
                )
