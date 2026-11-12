from django.test import TestCase, override_settings
from django.urls import reverse

from CommunityForums.models import Topic
from EducationInformation.models import ArticleReaction
from interactions.models import Comment
from interactions.moderation import check_comment
from sex_education_app.models import CustomUser


PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


def comment_url(target):
    return reverse("post_comment", args=[target])


class ModerationTests(TestCase):
    def test_health_questions_and_everyday_words_pass(self):
        for text in ["避孕套怎么用？", "月经推迟正常吗", "看色情片会有什么影响？",
                     "我妈妈的话很有道理", "生日你好"]:
            with self.subTest(text=text):
                self.assertIsNone(check_comment(text))

    def test_abuse_spam_and_contact_details_are_blocked(self):
        for text in ["你个傻 逼", "加微信 abc12345", "详情见 www.example.com", "联系13812345678"]:
            with self.subTest(text=text):
                self.assertIsNotNone(check_comment(text))

    def test_length_limits(self):
        self.assertIsNotNone(check_comment("   "))
        self.assertIsNotNone(check_comment("好" * 301))
        self.assertIsNone(check_comment("好" * 300))


class PostCommentTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("reader", password="pw-123456")

    def test_anonymous_reader_must_log_in(self):
        response = self.client.post(comment_url("news1"), {"body": "写得好"})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Comment.objects.exists())

    def test_logged_in_reader_can_comment(self):
        self.client.force_login(self.user)
        response = self.client.post(comment_url("law1"), {"body": "  学到了  "})
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["comment"]["body"], "学到了")
        self.assertEqual(payload["comment"]["user"], "reader")
        self.assertEqual(payload["comment_count"], 1)
        self.assertEqual(Comment.objects.get().target, "law1")

    def test_rejected_comment_is_not_saved(self):
        self.client.force_login(self.user)
        response = self.client.post(comment_url("news1"), {"body": "加微信 abc12345"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertFalse(Comment.objects.exists())

    def test_unknown_or_deleted_targets_are_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(comment_url("news9"), {"body": "hi"}).status_code, 404)
        topic = Topic.objects.create(title="t", content="c")
        url = comment_url(f"topic-{topic.id}")
        self.assertEqual(self.client.post(url, {"body": "hi"}).status_code, 201)
        topic.delete()
        self.assertEqual(self.client.post(url, {"body": "hi"}).status_code, 404)

    def test_rate_limit(self):
        self.client.force_login(self.user)
        for i in range(5):
            self.assertEqual(self.client.post(comment_url("news1"), {"body": f"第{i}条"}).status_code, 201)
        self.assertEqual(self.client.post(comment_url("news1"), {"body": "太快了"}).status_code, 429)


@PLAIN_STATIC
class CommentDisplayTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("reader", password="pw-123456")

    def test_comments_show_on_every_commentable_page(self):
        topic = Topic.objects.create(title="我的话题", content="内容")
        pages = {
            "news2": reverse("news2"),
            "law3": reverse("law3"),
            "sexual_impulse": reverse("sexual_impulse"),
            f"topic-{topic.id}": reverse("topic_detail", args=[topic.id]),
        }
        for target, path in pages.items():
            with self.subTest(page=path):
                Comment.objects.create(user=self.user, target=target, body=f"关于{target}的评论")
                response = self.client.get(path)
                self.assertContains(response, f"关于{target}的评论")
                self.assertContains(response, '<span id="comment-count">1</span>', html=True)
                self.assertNotContains(response, "submit-comment")

    def test_hidden_comments_are_not_shown_or_counted(self):
        Comment.objects.create(user=self.user, target="news1", body="正常评论")
        Comment.objects.create(user=self.user, target="news1", body="被隐藏的评论", is_hidden=True)
        response = self.client.get(reverse("news1"))
        self.assertContains(response, "正常评论")
        self.assertNotContains(response, "被隐藏的评论")
        self.assertContains(response, '<span id="comment-count">1</span>', html=True)

    def test_comment_text_is_escaped(self):
        Comment.objects.create(user=self.user, target="news1", body="<script>alert(1)</script>")
        response = self.client.get(reverse("news1"))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_form_shown_only_when_logged_in(self):
        self.assertContains(self.client.get(reverse("news1")), "后参与讨论")
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("news1")), 'id="comment-form"')


@PLAIN_STATIC
class TopicReactionTests(TestCase):
    def test_topics_can_be_liked_and_favorited(self):
        user = CustomUser.objects.create_user("reader", password="pw-123456")
        topic = Topic.objects.create(title="社区里的问题", content="内容")
        self.client.force_login(user)
        target = f"topic-{topic.id}"
        state = self.client.post(reverse("toggle_reaction", args=[target, "like"])).json()
        self.assertEqual(state["like_count"], 1)
        self.client.post(reverse("toggle_reaction", args=[target, "favorite"]))
        self.assertEqual(ArticleReaction.objects.filter(article=target).count(), 2)
        response = self.client.get(reverse("favorite_news"))
        self.assertContains(response, "社区里的问题")
        self.assertContains(response, reverse("topic_detail", args=[topic.id]))
