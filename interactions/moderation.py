"""Lightweight checks applied to comments before they are shown.

This is a first line of defence, not a substitute for moderators: staff can
hide any comment in the admin. Health vocabulary (性, 避孕, 月经 ...) is
deliberately not blocked, because discussing it is the point of the site.
"""
import re

MAX_LENGTH = 300

# Abuse, harassment and spam terms. Keep this list focused on words that are
# never needed for a sincere question about sexual health.
BLOCKED_WORDS = [
    # insults (chosen so they don't appear inside everyday words like 妈妈的 or 生日你)
    "傻逼", "煞笔", "沙比", "傻b", "操你", "草泥马", "贱人", "婊子", "去死吧",
    "脑残", "智障", "人渣", "畜生", "滚蛋",
    # solicitation and spam (talking *about* pornography or one-night stands is allowed)
    "约炮", "援交", "裸聊", "包夜", "加微信", "加v", "加qq", "代写", "刷单",
    "兼职日结", "博彩", "网赌", "贷款",
]

_NOISE = re.compile(r"[\s\-_.,，。·•*~～!！?？、|/\\]+")
_CONTACT = re.compile(
    r"(https?://|www\.|\.com\b|\.cn\b|1[3-9]\d{9}|(?:微信|vx|wx|qq|扣扣)[:：]?\s*[\w\-]{5,})",
    re.IGNORECASE,
)


def check_comment(text):
    """Return an error message for text that should not be posted, or None."""
    body = (text or "").strip()
    if not body:
        return "评论内容不能为空。"
    if len(body) > MAX_LENGTH:
        return f"评论最多 {MAX_LENGTH} 个字，现在是 {len(body)} 个字。"
    compact = _NOISE.sub("", body.lower())
    if any(word in compact for word in BLOCKED_WORDS):
        return "评论里有不文明或广告用语，请修改后再发。"
    if _CONTACT.search(body):
        return "为了保护大家的安全，评论里不能留网址、电话或社交账号。"
    return None
