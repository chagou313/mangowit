from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SexEducationEntryRouteTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_legacy_quiz_redirects_to_category_selection(self):
        response = self.client.get(reverse("quiz"))

        self.assertRedirects(response, reverse("category_select"))

    def test_anonymous_profile_redirects_to_login_register(self):
        response = self.client.get(reverse("profile"))

        self.assertRedirects(
            response,
            f'{reverse("login_register")}?next={reverse("profile")}',
        )

    def test_authenticated_profile_renders(self):
        user = get_user_model().objects.create_user(
            username="profile-user",
            password="safe-test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile-user")


class ChallengeEntryRouteTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_legacy_question_redirects_to_category_selection(self):
        response = self.client.get(reverse("question"))

        self.assertRedirects(response, reverse("category_select"))

    def test_level_selection_without_category_redirects(self):
        response = self.client.get("/level_select/")

        self.assertRedirects(response, reverse("category_select"))

    def test_level_selection_with_category_renders(self):
        response = self.client.get("/level_select/physiology/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "physiology")
