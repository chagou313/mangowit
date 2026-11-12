import json
import re

from django.test import TestCase, override_settings
from django.urls import reverse

from challenge.models import QuizAttempt
from challenge.question_bank import QUESTIONS
from sex_education_app.models import CustomUser


PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


def embedded_questions(response):
    raw = re.search(r'<script id="quiz-data" type="application/json">(.*?)</script>',
                    response.content.decode(), re.S).group(1)
    return json.loads(raw)


@PLAIN_STATIC
class QuizFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("player", password="pw-123456")

    def start(self, category="physiology", level=1):
        response = self.client.get(reverse("quiz_play", args=[category, level]))
        self.assertEqual(response.status_code, 200)
        return self.client.session["quiz_attempt"]

    def answer(self, attempt, index, choice, category="physiology", level=1):
        return self.client.post(
            reverse("quiz_answer", args=[category, level]),
            {"attempt": attempt["id"], "question": index, "choice": choice},
        )

    def play_through(self, correct_count, category="physiology", level=1):
        attempt = self.start(category, level)
        questions = QUESTIONS[category][level]
        last = None
        for i, q in enumerate(questions):
            right = attempt["perms"][i].index(q["answer"])
            choice = right if i < correct_count else (right + 1) % 4
            last = self.answer(attempt, i, choice, category, level)
            self.assertEqual(last.json()["correct"], i < correct_count)
            self.assertEqual(last.json()["answer"], right)
        return last.json()

    def test_page_does_not_reveal_answers(self):
        response = self.client.get(reverse("quiz_play", args=["physiology", 1]))
        shown = embedded_questions(response)
        bank = QUESTIONS["physiology"][1]
        self.assertEqual([q["text"] for q in shown], [q["text"] for q in bank])
        for item, q in zip(shown, bank):
            self.assertEqual(set(item), {"index", "text", "options"})
            self.assertEqual(sorted(item["options"]), sorted(q["options"]))
        page = response.content.decode()
        for q in bank:
            self.assertNotIn(json.dumps(q["explanation"])[1:-1], page)

    def test_each_level_has_its_own_questions(self):
        first = embedded_questions(self.client.get(reverse("quiz_play", args=["physiology", 1])))
        second = embedded_questions(self.client.get(reverse("quiz_play", args=["physiology", 2])))
        self.assertEqual(second[0]["text"], QUESTIONS["physiology"][2][0]["text"])
        self.assertFalse({q["text"] for q in first} & {q["text"] for q in second})

    def test_passing_run_is_saved_with_points(self):
        self.client.force_login(self.user)
        final = self.play_through(5)
        self.assertTrue(final["finished"])
        attempt = QuizAttempt.objects.get()
        self.assertEqual((attempt.correct, attempt.total, attempt.passed, attempt.points), (5, 5, True, 20))
        result = self.client.get(final["result_url"])
        self.assertContains(result, "闯关成功")
        self.assertContains(result, reverse("quiz_play", args=["physiology", 2]))

    def test_failing_run_scores_without_bonus(self):
        self.client.force_login(self.user)
        self.play_through(2, "prevention", 3)
        attempt = QuizAttempt.objects.get()
        self.assertEqual((attempt.correct, attempt.passed, attempt.points), (2, False, 4))

    def test_anonymous_runs_are_not_saved(self):
        final = self.play_through(4)
        self.assertFalse(QuizAttempt.objects.exists())
        self.assertContains(self.client.get(final["result_url"]), "这次成绩没有保存")

    def test_answers_must_come_in_order_and_match_the_attempt(self):
        attempt = self.start()
        self.assertEqual(self.answer(attempt, 1, 0).status_code, 400)
        self.assertEqual(self.answer({"id": "stale"}, 0, 0).status_code, 409)
        self.assertEqual(self.answer(attempt, 0, 0, level=2).status_code, 409)
        self.assertEqual(self.answer(attempt, 0, 7).status_code, 400)

    def test_unknown_category_or_level_is_404(self):
        self.assertEqual(self.client.get(reverse("quiz_play", args=["cooking", 1])).status_code, 404)
        self.assertEqual(self.client.get(reverse("quiz_play", args=["physiology", 4])).status_code, 404)
        self.assertEqual(self.client.get(reverse("level_select", args=["cooking"])).status_code, 404)

    def test_old_question_pages_redirect_to_the_quiz(self):
        for path in ["/question1/", "/question33/", "/result/"]:
            with self.subTest(path=path):
                self.assertRedirects(self.client.get(path), reverse("category_select"))


@PLAIN_STATIC
class QuizProgressTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user("player", password="pw-123456")
        self.client.force_login(self.user)

    def record(self, category, level, correct):
        passed = correct >= 3
        QuizAttempt.objects.create(user=self.user, category=category, level=level, correct=correct,
                                   total=5, points=correct * 2 + (10 if passed else 0), passed=passed)

    def test_level_select_shows_best_score(self):
        self.record("psychology", 1, 2)
        self.record("psychology", 1, 4)
        response = self.client.get(reverse("level_select", args=["psychology"]))
        self.assertContains(response, "心理健康 - 选择关卡")
        self.assertContains(response, "已通过 · 最好成绩 4/5")
        self.assertContains(response, "--p: 80%")
        self.assertContains(response, reverse("quiz_play", args=["psychology", 3]))

    def test_category_select_counts_passed_levels(self):
        self.record("physiology", 1, 5)
        self.record("physiology", 2, 3)
        self.record("physiology", 3, 1)
        response = self.client.get(reverse("category_select"))
        self.assertContains(response, "已通过 2 / 3 关")

    def test_history_lists_attempts_and_totals(self):
        self.record("prevention", 1, 5)
        self.record("prevention", 2, 1)
        response = self.client.get(reverse("quiz_history"))
        self.assertContains(response, "<b>2</b><span>闯关次数</span>", html=True)
        self.assertContains(response, "<b>22</b><span>累计积分</span>", html=True)
        self.assertContains(response, "未通过")

    def test_history_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("quiz_history")).status_code, 302)


@PLAIN_STATIC
class ProfileStatsTests(TestCase):
    def test_profile_shows_real_quiz_and_comment_stats(self):
        from interactions.models import Comment

        user = CustomUser.objects.create_user("player", password="pw-123456")
        QuizAttempt.objects.create(user=user, category="physiology", level=1, correct=5,
                                   total=5, points=20, passed=True)
        QuizAttempt.objects.create(user=user, category="physiology", level=2, correct=1,
                                   total=5, points=2, passed=False)
        Comment.objects.create(user=user, target="law1", body="很有用的法律知识")
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))

        self.assertContains(response, "<b>22</b><span>积分</span>", html=True)
        self.assertContains(response, "<b>2</b><span>闯关次数</span>", html=True)
        self.assertContains(response, "<b>1/9</b><span>已通过关卡</span>", html=True)
        self.assertContains(response, "<b>1</b><span>评论</span>", html=True)
        self.assertContains(response, "很有用的法律知识")
        self.assertContains(response, "1/3 关")
        self.assertNotContains(response, "via.placeholder.com")
