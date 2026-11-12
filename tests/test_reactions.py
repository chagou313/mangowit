from django.test import TestCase, override_settings
from django.urls import reverse

from EducationInformation.models import ArticleReaction
from sex_education_app.models import CustomUser


PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


def toggle_url(article, kind):
    return reverse("toggle_reaction", args=[article, kind])


class ToggleReactionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("reader", password="pw-123456")

    def test_anonymous_reader_must_log_in(self):
        response = self.client.post(toggle_url("news1", "like"))
        self.assertEqual(response.status_code, 401)
        self.assertFalse(ArticleReaction.objects.exists())

    def test_like_toggles_on_and_off(self):
        self.client.force_login(self.user)
        first = self.client.post(toggle_url("news1", "like")).json()
        self.assertEqual(first, {"like_count": 1, "liked": True, "favorited": False})
        second = self.client.post(toggle_url("news1", "like")).json()
        self.assertEqual(second, {"like_count": 0, "liked": False, "favorited": False})

    def test_likes_from_different_readers_add_up(self):
        other = CustomUser.objects.create_user("other", password="pw-123456")
        ArticleReaction.objects.create(user=other, article="law2", kind="like")
        self.client.force_login(self.user)
        state = self.client.post(toggle_url("law2", "like")).json()
        self.assertEqual(state["like_count"], 2)

    def test_favorite_is_independent_of_like(self):
        self.client.force_login(self.user)
        state = self.client.post(toggle_url("news2", "favorite")).json()
        self.assertEqual(state, {"like_count": 0, "liked": False, "favorited": True})

    def test_unknown_article_or_kind_is_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(toggle_url("news9", "like")).status_code, 404)
        self.assertEqual(self.client.post(toggle_url("news1", "share")).status_code, 404)

    def test_get_is_not_allowed(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(toggle_url("news1", "like")).status_code, 405)


@PLAIN_STATIC
class ArticlePageTests(TestCase):
    def test_page_shows_saved_count_and_reader_state(self):
        user = CustomUser.objects.create_user("reader", password="pw-123456")
        other = CustomUser.objects.create_user("other", password="pw-123456")
        ArticleReaction.objects.create(user=other, article="news3", kind="like")
        ArticleReaction.objects.create(user=user, article="news3", kind="favorite")
        self.client.force_login(user)

        response = self.client.get(reverse("news3"))

        self.assertContains(response, '<span id="like-count">1</span>', html=True)
        self.assertContains(response, "已收藏")
        self.assertNotContains(response, "已赞")
        self.assertContains(response, toggle_url("news3", "like"))

    def test_every_article_page_has_working_buttons(self):
        for article in ["news1", "news2", "news3", "law1", "law2", "law3"]:
            with self.subTest(article=article):
                response = self.client.get(reverse(article))
                self.assertContains(response, toggle_url(article, "favorite"))
                self.assertContains(response, "/static/js/reactions.js")
                self.assertNotContains(response, "likeCount.textContent = count + 1")


@PLAIN_STATIC
class FavoritesPageTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("reader", password="pw-123456")

    def test_requires_login(self):
        response = self.client.get(reverse("favorite_news"))
        self.assertRedirects(
            response, reverse("login_register") + "?next=/favorite_news/",
            fetch_redirect_response=False,
        )

    def test_lists_only_this_readers_favorites(self):
        other = CustomUser.objects.create_user("other", password="pw-123456")
        ArticleReaction.objects.create(user=self.user, article="law1", kind="favorite")
        ArticleReaction.objects.create(user=self.user, article="news1", kind="like")
        ArticleReaction.objects.create(user=other, article="news2", kind="favorite")
        self.client.force_login(self.user)

        response = self.client.get(reverse("favorite_news"))

        self.assertContains(response, "中华人民共和国未成年人保护法")
        self.assertContains(response, reverse("law1"))
        self.assertNotContains(response, reverse("news1"))
        self.assertNotContains(response, reverse("news2"))

    def test_empty_state(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("favorite_news")), "还没有收藏任何文章")

    def test_profile_shows_favorite_count(self):
        ArticleReaction.objects.create(user=self.user, article="law1", kind="favorite")
        ArticleReaction.objects.create(user=self.user, article="law2", kind="favorite")
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile"))
        self.assertContains(response, '收藏数量: <span class="font-bold">2</span>')


class LoginRedirectTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user("reader", password="pw-123456")

    def login(self, next_url):
        return self.client.post(
            reverse("login_register") + "?next=" + next_url,
            {"username": "reader", "password": "pw-123456"},
        )

    def test_returns_to_the_article_after_login(self):
        response = self.login("/education/news1/")
        self.assertRedirects(response, "/education/news1/", fetch_redirect_response=False)

    def test_ignores_redirects_to_other_sites(self):
        response = self.login("https://evil.example.com/")
        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
