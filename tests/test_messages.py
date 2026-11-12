from django.test import TestCase, override_settings
from django.urls import reverse

from sex_education_app.models import CustomUser


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class MessageDisplayTests(TestCase):
    def setUp(self):
        CustomUser.objects.create_user("reader", password="pw-123456")

    def test_failed_login_is_shown_on_the_login_page_and_keeps_the_username(self):
        response = self.client.post(reverse("login_register"), {"username": "reader", "password": "wrong"})
        self.assertContains(response, "用户名或密码错误，请重试。", count=1)
        self.assertContains(response, 'value="reader"')

    def test_failed_logins_do_not_pile_up_for_later_pages(self):
        for _ in range(3):
            self.client.post(reverse("login_register"), {"username": "reader", "password": "wrong"})
        self.client.post(reverse("login_register"), {"username": "reader", "password": "pw-123456"})
        home = self.client.get(reverse("index"))
        self.assertContains(home, "登录成功！", count=1)
        self.assertNotContains(home, "用户名或密码错误")
        profile = self.client.get(reverse("profile"))
        self.assertNotContains(profile, "登录成功！")
        self.assertNotContains(profile, "用户名或密码错误")

    def test_registration_errors_are_in_chinese(self):
        response = self.client.post(
            reverse("login_register") + "?form_type=register",
            {"username": "newbie", "password1": "123", "password2": "123"},
        )
        self.assertContains(response, "注册失败，请检查输入信息。", count=1)
        self.assertContains(response, "密码")
        self.assertNotContains(response, "This password")

    def test_logout_message_shows_once_on_the_next_page(self):
        self.client.login(username="reader", password="pw-123456")
        response = self.client.get(reverse("logout"), follow=True)
        self.assertContains(response, "退出登录成功！", count=1)
        self.assertNotContains(self.client.get(reverse("index")), "退出登录成功！")
