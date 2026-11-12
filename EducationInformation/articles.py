"""The news and law articles that readers can like and favorite.

The articles are hand-written templates, so they are identified by a fixed key
(also their URL name) rather than by a database row.
"""

ARTICLES = {
    "news1": {"category": "新闻", "title": "山东枣庄一小学女教师因一节性教育课，得到人民日报表扬并转载"},
    "news2": {"category": "新闻", "title": "守护花蕾 护航青春——2025“春蕾计划”青春期健康教育讲座走进资溪二中"},
    "news3": {"category": "新闻", "title": "益阳市蚂蚁社会服务中心走进逸夫学校开展防性侵教育活动"},
    "law1": {"category": "法规", "title": "普法 |《中华人民共和国未成年人保护法》"},
    "law2": {"category": "法规", "title": "【利剑护蕾】保护未成年人免受性侵害的相关法律法规"},
    "law3": {"category": "法规", "title": "最高人民法院、最高人民检察院、公安部、司法部关于依法惩治性侵害未成年人犯罪的意见"},
}
