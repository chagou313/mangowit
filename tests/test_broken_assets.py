import re

from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.urls import reverse

from AI_communication.models import AIQuestion
from sex_education_app.models import CustomUser


PAGES = [
    "/", "/community/", "/physiology/", "/psychology/", "/safety/", "/ai/",
    "/category_select/", "/level_select/physiology/", "/quiz/physiology/1/",
    "/quiz/psychology/2/", "/quiz/prevention/3/",
]


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class LocalAssetReferenceTests(TestCase):
    def test_pages_only_reference_existing_local_assets(self):
        for page in PAGES:
            html = re.sub(r"<!--.*?-->", "", self.client.get(page).content.decode(), flags=re.S)
            for src in re.findall(r'<(?:script|link)[^>]+(?:src|href)="([^"]+)"', html):
                if src.startswith(("http", "//")):
                    continue
                with self.subTest(page=page, src=src):
                    self.assertTrue(src.startswith("/static/"), "relative asset path")
                    self.assertIsNotNone(finders.find(src[len("/static/"):]))


class AddQuestionPermissionTests(TestCase):
    data = {"question_text": "q", "answer_text": "a"}

    def test_anonymous_user_cannot_add_answers(self):
        self.client.post(reverse("add_question"), self.data)
        self.assertFalse(AIQuestion.objects.exists())

    def test_regular_user_cannot_add_answers(self):
        self.client.force_login(CustomUser.objects.create_user("u", password="x"))
        self.client.post(reverse("add_question"), self.data)
        self.assertFalse(AIQuestion.objects.exists())

    def test_staff_can_add_answers(self):
        self.client.force_login(
            CustomUser.objects.create_user("s", password="x", is_staff=True)
        )
        response = self.client.post(reverse("add_question"), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AIQuestion.objects.get().aianswer.answer_text, "a")
