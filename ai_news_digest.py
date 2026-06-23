#!/usr/bin/env python3
"""
Daily AI News Digest  (STANDALONE — independent of the Naukri/LinkedIn bot)
--------------------------------------------------------------------------
Fetches AI news from free RSS feeds (last 24h), dedupes, ranks, and emails a
newsletter using Gmail SMTP.

Runs free on GitHub Actions (cloud IP is fine — RSS has no bot wall).

Env vars (set as GitHub Secrets, or local .env):
  GMAIL_ADDRESS       - sender Gmail  (aitestengineer26@gmail.com)
  GMAIL_APP_PASSWORD  - 16-char app password for that account
  REPORT_EMAIL        - recipient (defaults to GMAIL_ADDRESS)
  GEMINI_API_KEY      - OPTIONAL. If set, Gemini writes punchy summaries.
                        Without it, the RSS description is used (still free).
"""

import os
import re
import sys
import html
import smtplib
import logging
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
import feedparser

# Load .env if present (local runs). On GitHub Actions, env comes from secrets.
try:
    from pathlib import Path
    _envf = Path(__file__).with_name(".env")
    if _envf.exists():
        for _line in _envf.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("ai-news")

IST = timezone(timedelta(hours=5, minutes=30))

# ── Free RSS feeds (AI focused) ──────────────────────────────────────────
FEEDS = [
    ("TechCrunch AI",   "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI",    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI",  "https://venturebeat.com/category/ai/feed/"),
    ("Ars Technica AI", "https://arstechnica.com/ai/feed/"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Google AI",       "https://blog.google/technology/ai/rss/"),
    ("OpenAI",          "https://openai.com/news/rss.xml"),
    ("DeepMind",        "https://deepmind.google/blog/rss.xml"),
    ("Hugging Face",    "https://huggingface.co/blog/feed.xml"),
]

# Keywords that bump a story's priority (impactful / actionable).
HOT_KEYWORDS = {
    "openai": 5, "anthropic": 5, "claude": 5, "chatgpt": 5, "gpt-5": 6, "gpt5": 6,
    "gemini": 4, "google": 3, "meta": 3, "microsoft": 3, "deepmind": 4, "grok": 3,
    "launch": 4, "release": 4, "released": 4, "announce": 3, "unveil": 3,
    "raises": 4, "funding": 4, "billion": 4, "million": 2, "valuation": 3,
    "agent": 4, "agentic": 4, "model": 2, "open source": 4, "open-source": 4,
    "free": 2, "api": 2, "regulation": 3, "ban": 3, "lawsuit": 3, "policy": 2,
    "job": 3, "jobs": 3, "layoff": 3, "automation": 3, "deepfake": 3, "scam": 3,
}

WINDOW_HOURS = 24
FALLBACK_HOURS = 48
MAX_STORIES = 12
MIN_STORIES = 8


def _entry_dt(entry):
    """Best-effort published datetime (UTC). None if unknown."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)          # strip HTML tags
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _score(title, summary):
    blob = f"{title} {summary}".lower()
    return sum(w for kw, w in HOT_KEYWORDS.items() if kw in blob)


def _norm_title(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())[:60]


def fetch_stories():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=WINDOW_HOURS)
    fallback_cutoff = now - timedelta(hours=FALLBACK_HOURS)

    raw = []
    for source, url in FEEDS:
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(resp.content)
            if not feed.entries:
                log.info("No entries: %s", source)
                continue
            for e in feed.entries:
                title = _clean(e.get("title"))
                if not title:
                    continue
                summary = _clean(e.get("summary") or e.get("description"))
                link = e.get("link", "")
                dt = _entry_dt(e)
                raw.append({
                    "source": source, "title": title, "summary": summary[:400],
                    "link": link, "dt": dt,
                    "score": _score(title, summary),
                })
            log.info("Fetched %d from %s", len(feed.entries), source)
        except Exception as ex:
            log.warning("Feed failed %s: %s", source, ex)

    # dedupe by normalized title (keep highest score)
    seen = {}
    for s in raw:
        k = _norm_title(s["title"])
        if k and (k not in seen or s["score"] > seen[k]["score"]):
            seen[k] = s
    items = list(seen.values())

    def within(cut):
        return [s for s in items if s["dt"] and s["dt"] >= cut]

    recent = within(cutoff)
    if len(recent) < MIN_STORIES:
        log.info("Only %d in 24h, widening to 48h", len(recent))
        recent = within(fallback_cutoff)
    if len(recent) < MIN_STORIES:
        # last resort: take undated/older items too, by score
        recent = items

    recent.sort(key=lambda s: (s["score"], s["dt"] or datetime.min.replace(tzinfo=timezone.utc)),
                reverse=True)
    return recent[:MAX_STORIES]


# ── Optional: Gemini writes punchy summaries (free tier) ─────────────────
def gemini_rewrite(stories, api_key):
    """Return dict idx->fields via one Gemini call. None on fail."""
    bullet = "\n".join(
        f"{i+1}. [{s['source']}] {s['title']} — {s['summary']}"
        for i, s in enumerate(stories)
    )
    prompt = (
        "You are a daily AI newsletter writer. For each numbered story below, "
        "write 3 short lines in plain English (a 15-year-old understands), high energy, "
        "no corporate fluff:\n"
        "what: <the news, 1 sentence>\n"
        "why: <real-world impact on jobs/money/tools, 1 sentence>\n"
        "do: <1 specific action or thing to watch>\n\n"
        "Return ONLY valid JSON: a list of objects with keys idx, emoji, headline, what, why, do. "
        "headline = 6-8 word punchy rewrite. emoji = one relevant emoji.\n\n"
        f"STORIES:\n{bullet}"
    )
    try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.0-flash:generateContent?key=" + api_key)
        r = requests.post(url, timeout=60, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
        })
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        import json
        data = json.loads(text)
        return {int(d["idx"]): d for d in data if "idx" in d}
    except Exception as ex:
        log.warning("Gemini rewrite failed (using RSS text): %s", ex)
        return None


def build_html(stories, ai):
    date_str = datetime.now(IST).strftime("%b %d")
    top = stories[0]["title"] if stories else "AI news"

    parts = [f"""\
<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:640px;margin:0 auto;color:#1a1a1a;">
<p>Hey 👋</p>
<p>Every day I think AI has peaked. Every day I'm wrong.</p>
<p>Here's what dropped in the last 24 hours — and what actually matters.</p>
<hr style="border:none;border-top:2px solid #eee;">
<h2 style="margin:18px 0 4px;">🔥 Today's Top Stories</h2>
<p style="color:#666;margin-top:0;">{len(stories)} updates that matter.</p>
"""]

    for i, s in enumerate(stories):
        a = ai.get(i + 1) if ai else None
        emoji = (a or {}).get("emoji", "🚀")
        headline = (a or {}).get("headline") or s["title"]
        if a:
            block = (
                f'<p style="margin:4px 0;"><b>What happened:</b> {html.escape(a.get("what",""))}</p>'
                f'<p style="margin:4px 0;"><b>Why it matters:</b> {html.escape(a.get("why",""))}</p>'
                f'<p style="margin:4px 0;"><b>What to do:</b> {html.escape(a.get("do",""))}</p>'
            )
        else:
            block = f'<p style="margin:4px 0;color:#333;">{html.escape(s["summary"]) or s["title"]}</p>'
        parts.append(f"""
<div style="margin:22px 0;padding-bottom:16px;border-bottom:1px solid #f0f0f0;">
  <h3 style="margin:0 0 8px;">{emoji} {html.escape(headline)}</h3>
  {block}
  <p style="margin:8px 0 0;"><a href="{html.escape(s['link'])}" style="color:#0b66c3;">Read on {html.escape(s['source'])} →</a></p>
</div>""")

    parts.append("""
<hr style="border:none;border-top:2px solid #eee;">
<p>That's your AI edge for today.</p>
<p style="color:#666;">If you're not paying attention to AI right now — AI is still paying attention to you.</p>
<p>See you tomorrow,<br>Your Daily AI Agent 🤖</p>
</div>""")

    subject = f"🤖 {date_str} — {top[:60]}"
    return subject, "".join(parts)


def send_email(subject, body_html):
    sender = os.environ["GMAIL_ADDRESS"]
    pwd = os.environ["GMAIL_APP_PASSWORD"]
    to = os.environ.get("REPORT_EMAIL", sender)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(re.sub(r"<[^>]+>", "", body_html), "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(sender, pwd)
        server.sendmail(sender, [to], msg.as_string())
    log.info("Email sent to %s", to)


def main():
    stories = fetch_stories()
    log.info("Selected %d stories", len(stories))
    if not stories:
        log.error("No stories found — not sending.")
        return 1

    api_key = os.environ.get("GEMINI_API_KEY")
    ai = gemini_rewrite(stories, api_key) if api_key else None

    subject, body = build_html(stories, ai)
    send_email(subject, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
