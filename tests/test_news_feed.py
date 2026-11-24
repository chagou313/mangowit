from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from EducationInformation import news_feed
from EducationInformation.models import NewsFetchRun, NewsItem


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


def bing_item(title, real_url, summary, source="中国青年报", days_ago=2):
    date = (timezone.now() - timedelta(days=days_ago)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    link = "http://www.bing.com/news/apiclick.aspx?ref=FexRss&amp;url=" + real_url.replace(":", "%3a").replace("/", "%2f")
    return (f"<item><title>{title}</title><link>{link}</link><description>{summary}</description>"
            f"<pubDate>{date}</pubDate><News:Source>{source}</News:Source></item>")


class ParseFeedTests(TestCase):
    def test_google_titles_lose_the_source_suffix(self):
        [item] = news_feed.parse_feed(rss(google_item("某中学开展青春期健康教育讲座", "人民网", "https://news.google.com/rss/articles/abc")))
        self.assertEqual(item["title"], "某中学开展青春期健康教育讲座")
        self.assertEqual(item["source"], "人民网")
        self.assertEqual(item["summary"], "")  # Google's description only repeats the headline
        self.assertIsNotNone(item["published"])

    def test_bing_links_point_to_the_original_article(self):
        [item] = news_feed.parse_feed(rss(bing_item(
            "教育部发布中小学生健康教育指南", "https://www.example.cn/a/1.html",
            "指南提出学校要系统开展青春期教育，帮助学生正确认识身体变化。")))
        self.assertEqual(item["url"], "https://www.example.cn/a/1.html")
        self.assertEqual(item["source"], "中国青年报")
        self.assertIn("青春期教育", item["summary"])

    def test_broken_feed_gives_no_items(self):
        self.assertEqual(news_feed.parse_feed(b"<html>not rss"), [])


class FilterTests(TestCase):
    def test_education_news_is_kept(self):
        for title in ["春蕾计划青春期健康教育讲座走进资溪二中", "检察官进校园开展防性侵普法宣传",
                      "全国人大代表建议性教育独立成课"]:
            with self.subTest(title=title):
                self.assertTrue(news_feed.is_suitable(title))

    def test_crime_reports_ads_and_off_topic_news_are_dropped(self):
        for title in ["男子猥亵女童被判处有期徒刑", "某地破获一起卖淫案", "无痛人流哪家好",
                      "震惊！某校学生做出这种事", "Sex education in schools", "今日股市收盘点评"]:
            with self.subTest(title=title):
                self.assertFalse(news_feed.is_suitable(title))


class FetchNewsTests(TestCase):
    def feeds(self, url):
        if "google" in url:
            return rss(
                google_item("某中学开展青春期健康教育讲座", "人民网", "https://news.google.com/rss/articles/a"),
                google_item("男子涉嫌猥亵被刑拘", "某网", "https://news.google.com/rss/articles/b"),
                google_item("十年前的青春期教育讲座", "旧闻网", "https://news.google.com/rss/articles/c", days_ago=900),
            )
        return rss(bing_item("某中学开展青春期健康教育讲座！", "https://www.example.cn/dup.html", "同一条新闻的另一个标题写法，内容相同。"))

    def test_stores_suitable_new_items_once(self):
        result = news_feed.fetch_news(fetch=self.feeds)
        self.assertEqual(result["added"], 1)
        self.assertTrue(NewsItem.objects.get().title.startswith("某中学开展青春期健康教育讲座"))
        again = news_feed.fetch_news(fetch=self.feeds)
        self.assertEqual(again["added"], 0)
        self.assertEqual(NewsItem.objects.count(), 1)

    def test_one_failing_feed_does_not_stop_the_rest(self):
        def flaky(url):
            if "bing" in url:
                raise TimeoutError("timed out")
            return self.feeds(url)
        result = news_feed.fetch_news(fetch=flaky)
        self.assertEqual(result["added"], 1)
        self.assertTrue(result["errors"])

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
    def test_shows_featured_laws_and_fetched_news(self):
        NewsItem.objects.create(title="某中学开展青春期健康教育讲座", url="https://example.cn/news/1",
                                source="人民网", summary="讲座介绍了青春期身体变化。", published_at=timezone.now())
        NewsItem.objects.create(title="被隐藏的新闻", url="https://example.cn/news/2", published_at=timezone.now(), is_hidden=True)
        response = self.client.get(reverse("news"))
        self.assertContains(response, reverse("news2"))
        self.assertContains(response, reverse("law3"))
        self.assertContains(response, "某中学开展青春期健康教育讲座")
        self.assertContains(response, 'href="https://example.cn/news/1" target="_blank" rel="noopener noreferrer nofollow"')
        self.assertNotContains(response, "被隐藏的新闻")

    def test_empty_feed_says_it_is_loading(self):
        response = self.client.get(reverse("news"))
        self.assertContains(response, "正在获取最新资讯")
        self.assertNotContains(response, "alert(")
