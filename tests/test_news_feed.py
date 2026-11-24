import urllib.parse
from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from EducationInformation import news_feed
from EducationInformation.laws import LAWS
from EducationInformation.models import NewsFetchRun, NewsItem
from interactions.models import Comment
from sex_education_app.models import CustomUser


PLAIN_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


def rss(*items):
    return ("<?xml version='1.0' encoding='utf-8'?><rss version='2.0' "
            "xmlns:News='https://www.bing.com/news/search?q=&amp;format=rss'><channel>"
            + "".join(items) + "</channel></rss>").encode("utf-8")


def google_item(title, source, link, days_ago=1):
    date = (timezone.now() - timedelta(days=days_ago)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return (f"<item><title>{title} - {source}</title><link>{link}</link><pubDate>{date}</pubDate>"
            f"<description>&lt;a href=\"{link}\"&gt;{title}&lt;/a&gt;</description>"
            f"<source url=\"https://example.cn\">{source}</source></item>")


def plain_item(title, link, summary, days_ago=2):
    date = (timezone.now() - timedelta(days=days_ago)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    return (f"<item><title>{title}</title><link>{link}</link><description>{summary}</description>"
            f"<pubDate>{date}</pubDate></item>")


class ParseFeedTests(TestCase):
    def test_google_titles_lose_the_source_suffix(self):
        [item] = news_feed.parse_feed(rss(google_item("某中学开展青春期健康教育讲座", "人民网", "https://news.google.com/rss/articles/abc")))
        self.assertEqual(item["title"], "某中学开展青春期健康教育讲座")
        self.assertEqual(item["source"], "人民网")
        self.assertEqual(item["summary"], "")  # Google's description only repeats the headline
        self.assertIsNotNone(item["published"])

    def test_feed_without_source_uses_the_site_name(self):
        [item] = news_feed.parse_feed(rss(plain_item(
            "教育部发布中小学生健康教育指南", "https://www.example.cn/a/1.html",
            "指南提出学校要系统开展青春期教育，帮助学生正确认识身体变化。")))
        self.assertEqual(item["source"], "example.cn")
        self.assertIn("青春期教育", item["summary"])

    def test_titles_are_cleaned(self):
        for raw, clean in [
            ("祁阳市人民中心小学开展女生防性侵专题安全教育讲座2026-11-12 10:24:42", "祁阳市人民中心小学开展女生防性侵专题安全教育讲座"),
            ("给成年人上一堂青少年性教育课|沈奕斐|复旦大学|家庭教育_新浪新闻", "给成年人上一堂青少年性教育课"),
            ("高校举办青少年心理健康论坛- Xi'an Jiaotong-Liverpool University", "高校举办青少年心理健康论坛"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(news_feed.clean_title(raw), clean)

    def test_broken_feed_gives_no_items(self):
        self.assertEqual(news_feed.parse_feed(b"<html>not rss"), [])


class FilterTests(TestCase):
    def test_education_news_is_kept(self):
        for title in ["春蕾计划青春期健康教育讲座走进资溪二中", "检察官进校园开展防性侵普法宣传",
                      "全国人大代表建议性教育独立成课", "官渡法院开展校园防性侵专题法治宣讲活动",
                      "人民日报：全员育心，守护青少年心理健康", "刘宏艳代表：把青少年心理健康教育落在实处",
                      "兴化市海南镇开展“未成年人性侵害预防”法律专题讲座", "盘点全球防范性侵教育 鼓励孩子勇敢说“不”",
                      "法治宣讲进校园 护航少年平安成长"]:
            with self.subTest(title=title):
                self.assertTrue(news_feed.is_suitable(title))

    def test_crime_reports_ads_and_off_topic_news_are_dropped(self):
        for title in ["男子猥亵女童被判处有期徒刑", "某地破获一起卖淫案", "无痛人流哪家好",
                      "震惊！某校学生做出这种事", "Sex education in schools", "今日股市收盘点评",
                      "留守女童遭宿管老师长期性侵", "农村已成性侵女童案高发地",
                      "中国高等教育学会年会在扬州举行", "象牙塔内惨案频发 大学生心理健康引关注", "某区义务教育阶段学校招生工作实施意见"]:
            with self.subTest(title=title):
                self.assertFalse(news_feed.is_suitable(title))


class FetchNewsTests(TestCase):
    def feeds(self, url):
        if "青春期" in urllib.parse.unquote(url):
            return rss(
                google_item("某中学开展青春期健康教育讲座", "人民网", "https://news.google.com/rss/articles/a"),
                google_item("男子涉嫌猥亵被刑拘", "某网", "https://news.google.com/rss/articles/b"),
                google_item("十年前的青春期教育讲座", "旧闻网", "https://news.google.com/rss/articles/c", days_ago=900),
            )
        return rss(plain_item("某中学开展青春期健康教育讲座！", "https://www.example.cn/dup.html", "同一条新闻的另一个标题写法，内容相同。"))

    def test_stores_suitable_new_items_once(self):
        result = news_feed.fetch_news(fetch=self.feeds)
        self.assertEqual(result["added"], 1)
        self.assertTrue(NewsItem.objects.get().title.startswith("某中学开展青春期健康教育讲座"))
        again = news_feed.fetch_news(fetch=self.feeds)
        self.assertEqual(again["added"], 0)
        self.assertEqual(NewsItem.objects.count(), 1)

    def test_one_failing_feed_does_not_stop_the_rest(self):
        def flaky(url):
            if "青春期" not in urllib.parse.unquote(url):
                raise TimeoutError("timed out")
            return self.feeds(url)
        result = news_feed.fetch_news(fetch=flaky)
        self.assertEqual(result["added"], 1)
        self.assertTrue(result["errors"])

    def test_pruning_keeps_items_readers_engaged_with(self):
        now = timezone.now()
        old = NewsItem.objects.create(title="很早以前的健康教育新闻", url="https://example.cn/old",
                                      published_at=now - timedelta(days=200))
        for i in range(news_feed.KEEP_ITEMS):
            NewsItem.objects.create(title=f"健康教育新闻{i}", url=f"https://example.cn/{i}", published_at=now - timedelta(hours=i))
        Comment.objects.create(user=CustomUser.objects.create_user("r", password="pw-123456"),
                               target=f"news-{old.pk}", body="收藏了")
        news_feed.fetch_news(fetch=lambda url: rss())
        self.assertTrue(NewsItem.objects.filter(pk=old.pk).exists())

    def test_keeps_only_the_newest_items(self):
        now = timezone.now()
        for i in range(news_feed.KEEP_ITEMS + 5):
            NewsItem.objects.create(title=f"健康教育新闻{i}", url=f"https://example.cn/{i}",
                                    published_at=now - timedelta(hours=i))
        news_feed.fetch_news(fetch=lambda url: rss())
        self.assertEqual(NewsItem.objects.count(), news_feed.KEEP_ITEMS)
        self.assertFalse(NewsItem.objects.filter(title=f"健康教育新闻{news_feed.KEEP_ITEMS + 4}").exists())


@override_settings(NEWS_AUTO_REFRESH=True)
class RefreshTests(TestCase):
    def test_refreshes_only_when_stale(self):
        with mock.patch.object(news_feed, "fetch_news", return_value={"added": 2, "skipped": 0, "errors": []}) as fetch:
            self.assertTrue(news_feed.refresh_if_stale(background=False))
            self.assertFalse(news_feed.refresh_if_stale(background=False))
            self.assertEqual(fetch.call_count, 1)
            NewsFetchRun.objects.update(started_at=timezone.now() - timedelta(hours=7))
            self.assertTrue(news_feed.refresh_if_stale(background=False))
        self.assertEqual(NewsFetchRun.objects.first().added, 2)

    @override_settings(NEWS_AUTO_REFRESH=False)
    def test_can_be_switched_off(self):
        self.assertFalse(news_feed.refresh_if_stale(background=False))
        self.assertFalse(NewsFetchRun.objects.exists())


@PLAIN_STATIC
class NewsPageTests(TestCase):
    def setUp(self):
        self.item = NewsItem.objects.create(
            title="某中学开展青春期健康教育讲座", url="https://example.cn/news/1", source="人民网",
            summary="讲座介绍了青春期身体变化。", published_at=timezone.now())

    def test_one_list_with_every_item_opening_on_this_site(self):
        NewsItem.objects.create(title="被隐藏的新闻", url="https://example.cn/news/2", published_at=timezone.now(), is_hidden=True)
        Comment.objects.create(user=CustomUser.objects.create_user("r", password="pw-123456"),
                               target=f"news-{self.item.pk}", body="很有用")
        response = self.client.get(reverse("news"))
        detail = reverse("news_item", args=[self.item.pk])
        for url in [reverse("news2"), reverse("law3"), detail]:
            self.assertContains(response, f'class="nw-row" href="{url}"')
        self.assertNotContains(response, 'href="https://example.cn/news/1"')  # the original is linked from the detail page
        self.assertNotContains(response, "被隐藏的新闻")
        row = next(r for r in response.context["rows"] if r["key"] == f"news-{self.item.pk}")
        self.assertEqual((row["likes"], row["comments"]), (0, 1))
        self.assertEqual(response.context["law_count"], len(LAWS) + 3)

    def test_detail_page_links_to_the_original_and_takes_comments(self):
        response = self.client.get(reverse("news_item", args=[self.item.pk]))
        self.assertContains(response, "讲座介绍了青春期身体变化。")
        self.assertContains(response, 'href="https://example.cn/news/1" target="_blank" rel="noopener noreferrer nofollow"')
        self.assertContains(response, reverse("toggle_reaction", args=[f"news-{self.item.pk}", "like"]))
        self.assertContains(response, 'id="comment-count">0<')

    def test_hidden_items_have_no_page_and_cannot_be_liked(self):
        self.item.is_hidden = True
        self.item.save()
        self.assertEqual(self.client.get(reverse("news_item", args=[self.item.pk])).status_code, 404)
        self.client.force_login(CustomUser.objects.create_user("r", password="pw-123456"))
        url = reverse("toggle_reaction", args=[f"news-{self.item.pk}", "like"])
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_saved_news_shows_in_favorites(self):
        user = CustomUser.objects.create_user("r", password="pw-123456")
        self.client.force_login(user)
        self.client.post(reverse("toggle_reaction", args=[f"news-{self.item.pk}", "favorite"]))
        response = self.client.get(reverse("favorite_news"))
        self.assertContains(response, "某中学开展青春期健康教育讲座")
        self.assertContains(response, reverse("news_item", args=[self.item.pk]))

    def test_empty_feed_says_it_is_loading(self):
        NewsItem.objects.all().delete()
        response = self.client.get(reverse("news"))
        self.assertContains(response, "正在获取最新新闻")
        self.assertNotContains(response, "alert(")


class ClassifyTests(TestCase):
    def test_policy_headlines_are_law_updates(self):
        for title in ["《未成年人网络保护条例》明年1月1日起施行", "教育部印发中小学健康教育指南",
                      "两高发布司法解释 加强未成年人保护"]:
            with self.subTest(title=title):
                self.assertEqual(news_feed.classify(title), "law")
        self.assertEqual(news_feed.classify("某中学开展青春期健康教育讲座"), "news")

    def test_law_updates_have_their_own_rules(self):
        self.assertEqual(news_feed.evaluate("严禁向未成年人提供虚拟伴侣等服务新规今年7月施行"), "law")
        self.assertEqual(news_feed.evaluate("教育部印发指导意见全面推进健康学校建设"), "law")
        # a local event that mentions a law is news, not a law update
        self.assertEqual(news_feed.evaluate("大洋街道毓龙公园社区开展《未成年人保护法》普法宣讲活动"), "news")
        for title in ["马来西亚新规实施：16岁以下青少年禁注册社交媒体账号",
                      "人工智能拟人化互动服务新规7月15日起施行",
                      "最高检发布指导性案例 依法严惩性侵害未成年人犯罪"]:
            with self.subTest(title=title):
                self.assertIsNone(news_feed.evaluate(title))

    def test_fetched_items_get_their_kind(self):
        def feed(url):
            return rss(plain_item("教育部印发中小学生健康教育指南", "https://www.example.cn/law.html", ""),
                       plain_item("某中学开展青春期健康教育讲座", "https://www.example.cn/news.html", ""))
        news_feed.fetch_news(fetch=feed)
        self.assertEqual(NewsItem.objects.get(url__endswith="law.html").kind, "law")
        self.assertEqual(NewsItem.objects.get(url__endswith="news.html").kind, "news")


class CuratedLawDataTests(TestCase):
    def test_every_law_is_complete_and_links_to_https(self):
        slugs = [law["slug"] for law in LAWS]
        self.assertEqual(len(slugs), len(set(slugs)))
        for law in LAWS:
            with self.subTest(law=law["slug"]):
                for field in ["title", "kind", "issuer", "effective", "summary", "source"]:
                    self.assertTrue(law[field].strip())
                self.assertGreaterEqual(len(law["points"]), 2)
                self.assertRegex(law["url"], r"^https?://")
                self.assertLessEqual(len(f"law-{law['slug']}"), 40)  # fits ArticleReaction.article


@PLAIN_STATIC
class LawPageTests(TestCase):
    def test_law_tab_lists_core_laws_articles_and_updates(self):
        update = NewsItem.objects.create(title="教育部印发中小学生健康教育指南", url="https://example.cn/l",
                                         published_at=timezone.now(), kind="law")
        response = self.client.get(reverse("news"))
        law_rows = [r for r in response.context["rows"] if r["tab"] == "law"]
        urls = [r["url"] for r in law_rows]
        self.assertIn(reverse("law_detail", args=["school_protection"]), urls)
        self.assertIn(reverse("law1"), urls)
        self.assertIn(reverse("news_item", args=[update.pk]), urls)
        news_urls = [r["url"] for r in response.context["rows"] if r["tab"] == "news"]
        self.assertNotIn(reverse("news_item", args=[update.pk]), news_urls)

    def test_detail_page_shows_points_official_link_and_comments(self):
        law = LAWS[0]
        response = self.client.get(reverse("law_detail", args=[law["slug"]]))
        self.assertContains(response, law["title"])
        self.assertContains(response, law["points"][0])
        self.assertContains(response, f'href="{law["url"]}"')
        self.assertContains(response, "以官方原文为准")
        self.assertContains(response, reverse("toggle_reaction", args=[f"law-{law['slug']}", "favorite"]))

    def test_unknown_law_is_404(self):
        self.assertEqual(self.client.get(reverse("law_detail", args=["no_such_law"])).status_code, 404)

    def test_laws_can_be_saved_and_discussed(self):
        user = CustomUser.objects.create_user("r", password="pw-123456")
        self.client.force_login(user)
        target = "law-online_protection"
        self.assertEqual(self.client.post(reverse("toggle_reaction", args=[target, "favorite"])).status_code, 200)
        self.assertEqual(self.client.post(reverse("post_comment", args=[target]), {"body": "很实用"}).status_code, 201)
        self.assertContains(self.client.get(reverse("favorite_news")), "未成年人网络保护条例")
