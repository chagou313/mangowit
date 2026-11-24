"""Automatic news feed: fetch, filter and store recent news about sex and health education.

Headlines come from Google News search RSS feeds. Only the title, source, date, a short
summary and the link are stored; readers open the original article on its own site.

The site runs on a free host that sleeps when idle, so there is no scheduler.
Instead the news page calls ``refresh_if_stale()``: when the last fetch is older than
``REFRESH_INTERVAL`` it fetches in a background thread and the page renders at once
with what is already stored.
"""

import html
import logging
import re
import threading
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta
from email.utils import parsedate_to_datetime

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = timedelta(hours=6)
MAX_AGE = timedelta(days=365)
KEEP_ITEMS = 80
TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; MangowitNewsBot/1.0; +https://mangowit.onrender.com)"

QUERIES = [
    "青春期 健康教育",
    "学校 性教育",
    "防性侵 教育 未成年人",
    "未成年人保护 普法 宣传",
    "青少年 心理健康 教育",
    # Policy and law updates, shown under 法律法规 as 法规动态
    "未成年人保护 新规 施行",
    "未成年人 司法解释 发布",
    "教育部 印发 中小学 健康教育",
    "最高检 未成年人 保护 意见",
]

# Headlines about a new or revised law, regulation, judicial document or policy.
LAW_PATTERN = re.compile(
    r"《[^》]*(法|条例|规定|办法|意见|解释|指南|纲要|方案)》|司法解释|新规|施行|印发|修订|修正|立法|条例|规章"
)


def classify(title):
    return "law" if LAW_PATTERN.search(title) else "news"


def feed_urls():
    for query in QUERIES:
        q = urllib.parse.quote(query)
        yield f"https://news.google.com/rss/search?q={q}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"


# A headline must be about our topic...
TOPIC_WORDS = [
    "青春期", "性教育", "性健康", "防性侵", "生理", "心理健康", "心理育人", "育心", "未成年人", "青少年",
    "儿童", "女童", "女生", "男生", "护蕾", "春蕾", "身心", "自我保护", "生命教育", "健康教育",
    "安全教育", "欺凌", "花蕾", "少年", "青春", "学生",
]
# ...describe education, protection or a school activity...
KEEP_WORDS = [
    "教育", "讲座", "课", "科普", "健康", "保护", "普法", "法治", "宣讲", "宣传", "指南", "成长",
    "关爱", "守护", "呵护", "护航", "政策", "法规", "条例", "进校园", "家长", "开展", "活动", "班会",
    "培训", "预防", "防范", "建议", "代表", "委员",
]
# ...and must not look like crime reporting, explicit content, adverts or clickbait.
BLOCK_WORDS = [
    "强奸", "轮奸", "猥亵", "嫖", "卖淫", "色情", "淫秽", "裸", "偷拍", "约炮", "情色", "黄色",
    "性感", "艳照", "激情", "出轨", "小三", "不雅", "床", "成人用品", "致死", "惨案", "杀", "尸", "自杀",
    "跳楼", "坠楼", "农药", "判处", "判刑", "判了", "获刑", "被告", "嫌疑人", "涉嫌", "案发", "被害",
    "受害", "遭", "禽兽", "丧心病狂", "人流", "包皮", "早泄", "阳痿", "壮阳", "哪家好", "哪个好",
    "医院排名", "震惊", "曝光",
]
# "性侵" is allowed only as part of prevention wording such as 防性侵 / 预防性侵害 / 性侵害预防.
SAFE_ABUSE_PHRASES = re.compile(r"(预防|防止|防范|防|反)性侵害?|性侵害?(预防|防范|防治)")
CHINESE = re.compile(r"[\u4e00-\u9fff]")
TAGS = re.compile(r"<[^>]+>")
SPACES = re.compile(r"\s+")
TRAILING_JUNK = re.compile(r"(\s*\d{4}-\d{1,2}-\d{1,2}(\s+\d{1,2}:\d{2}(:\d{2})?)?|_[^_]{1,12}新闻|\s*-\s+[A-Za-z][A-Za-z'.\s-]*)$")


def clean_title(title):
    """Drop timestamps, site suffixes and keyword clutter that some sites add to headlines."""
    parts = [p.strip() for p in title.split("|")]
    if len(parts) > 2:  # "headline|keyword|keyword|..."
        title = parts[0]
    previous = None
    while previous != title:
        previous, title = title, TRAILING_JUNK.sub("", title).strip()
    return title


def is_suitable(title, summary=""):
    text = f"{title} {summary}"
    if not CHINESE.search(title):
        return False
    if any(word in text for word in BLOCK_WORDS) or "性侵" in SAFE_ABUSE_PHRASES.sub("", text):
        return False
    on_topic = any(word in title for word in TOPIC_WORDS) or SAFE_ABUSE_PHRASES.search(title)
    return bool(on_topic) and any(word in title for word in KEEP_WORDS)


def _text(value):
    value = html.unescape(TAGS.sub(" ", value or ""))
    return SPACES.sub(" ", value).strip()


def _child(item, name):
    """Find a child element by local name, ignoring XML namespaces."""
    for child in item:
        if child.tag.rsplit("}", 1)[-1].lower() == name.lower():
            return child
    return None


def parse_feed(data):
    """Parse RSS bytes into a list of dicts with title, url, source, published and summary."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []
    items = []
    for item in root.iter("item"):
        title = _text(getattr(_child(item, "title"), "text", ""))
        link = (getattr(_child(item, "link"), "text", "") or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        source_el = _child(item, "source")
        source = _text(source_el.text if source_el is not None else "")
        if source and title.endswith(f" - {source}"):
            title = title[: -len(source) - 3].strip()  # Google appends " - Source" to titles
        title = clean_title(title)
        if not source:
            source = urllib.parse.urlparse(link).netloc.removeprefix("www.")
        published = None
        date_el = _child(item, "pubDate")
        if date_el is not None and date_el.text:
            try:
                published = parsedate_to_datetime(date_el.text.strip())
                if timezone.is_naive(published):
                    published = timezone.make_aware(published, timezone.utc)
            except (TypeError, ValueError):
                published = None
        summary = _text(getattr(_child(item, "description"), "text", ""))
        if summary.startswith(title) or len(summary) < 20:
            summary = ""  # Google's description just repeats the headline
        items.append({
            "title": title[:200],
            "url": link[:500],
            "source": source[:80],
            "published": published,
            "summary": summary[:300],
        })
    return items


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(2_000_000)


def _key(title):
    return re.sub(r"[\W_]+", "", title).lower()


def fetch_news(fetch=download):
    """Fetch every feed, store suitable new items and prune old ones. Returns a summary dict."""
    from .models import NewsItem

    now = timezone.now()
    seen = {_key(t) for t in NewsItem.objects.values_list("title", flat=True)}
    known_urls = set(NewsItem.objects.values_list("url", flat=True))
    added, skipped, errors = 0, 0, []
    for url in feed_urls():
        try:
            entries = parse_feed(fetch(url))
        except Exception as exc:  # one broken feed must not stop the others
            errors.append(f"{urllib.parse.urlparse(url).netloc}: {exc}")
            continue
        for entry in entries:
            key = _key(entry["title"])
            published = entry["published"] or now
            if (
                key in seen or entry["url"] in known_urls
                or published < now - MAX_AGE or published > now + timedelta(days=1)
                or not is_suitable(entry["title"], entry["summary"])
            ):
                skipped += 1
                continue
            NewsItem.objects.create(
                title=entry["title"], url=entry["url"], source=entry["source"],
                summary=entry["summary"], published_at=published, kind=classify(entry["title"]),
            )
            seen.add(key)
            known_urls.add(entry["url"])
            added += 1
    stale = set(NewsItem.objects.order_by("-published_at").values_list("pk", flat=True)[KEEP_ITEMS:])
    if stale:  # never delete a headline that readers have liked, saved or discussed
        from EducationInformation.models import ArticleReaction
        from interactions.models import Comment

        targets = [f"news-{pk}" for pk in stale]
        engaged = set(ArticleReaction.objects.filter(article__in=targets).values_list("article", flat=True))
        engaged |= set(Comment.objects.filter(target__in=targets).values_list("target", flat=True))
        stale -= {int(t.split("-")[1]) for t in engaged}
        NewsItem.objects.filter(pk__in=stale).delete()
    return {"added": added, "skipped": skipped, "errors": errors}


def _run(run_id):
    from .models import NewsFetchRun

    close_old_connections()
    try:
        result = fetch_news()
        NewsFetchRun.objects.filter(pk=run_id).update(
            finished_at=timezone.now(), added=result["added"], error="; ".join(result["errors"])[:500],
        )
    except Exception as exc:
        logger.exception("News refresh failed")
        NewsFetchRun.objects.filter(pk=run_id).update(finished_at=timezone.now(), error=str(exc)[:500])
    finally:
        close_old_connections()


def refresh_if_stale(background=True):
    """Start a fetch when the last one is older than REFRESH_INTERVAL. Returns True if started."""
    from .models import NewsFetchRun

    if not getattr(settings, "NEWS_AUTO_REFRESH", True):
        return False
    with transaction.atomic():
        last = NewsFetchRun.objects.select_for_update().order_by("-started_at").first()
        if last and last.started_at > timezone.now() - REFRESH_INTERVAL:
            return False
        run = NewsFetchRun.objects.create()
    if background:
        threading.Thread(target=_run, args=(run.pk,), daemon=True).start()
    else:
        _run(run.pk)
    return True
