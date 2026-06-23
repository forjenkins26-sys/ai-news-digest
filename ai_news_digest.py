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

# ── Free RSS feeds — AI focused (same coverage Feedly/Zapier pulled) ──────
FEEDS_AI = [
    # News outlets
    ("TechCrunch AI",   "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge AI",    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("VentureBeat AI",  "https://venturebeat.com/category/ai/feed/"),
    ("Ars Technica AI", "https://arstechnica.com/ai/feed/"),
    ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("The Decoder",     "https://the-decoder.com/feed/"),
    ("AI News",         "https://www.artificialintelligence-news.com/feed/"),
    ("Synced",          "https://syncedreview.com/feed/"),
    # Primary / company sources (Anthropic has no public RSS — covered via the outlets above)
    ("OpenAI",          "https://openai.com/news/rss.xml"),
    ("Google AI",       "https://blog.google/technology/ai/rss/"),
    ("Google Cloud AI", "https://cloudblog.withgoogle.com/products/ai-machine-learning/rss/"),
    ("DeepMind",        "https://deepmind.google/blog/rss.xml"),
    ("Hugging Face",    "https://huggingface.co/blog/feed.xml"),
    ("GitHub Changelog","https://github.blog/changelog/feed/"),
]

# ── Free RSS feeds — QA / Test Automation + AI Testing (LLM/agents/eval) ──
FEEDS_QA = [
    # Classic QA / test automation
    ("TestGuild",            "https://testguild.com/feed/"),
    ("Software Testing Help","https://www.softwaretestinghelp.com/feed/"),
    ("Applitools",           "https://applitools.com/blog/feed/"),
    ("BrowserStack",         "https://www.browserstack.com/blog/feed/"),
    ("Cypress",              "https://www.cypress.io/blog/rss.xml"),
    ("Automation Panda",     "https://automationpanda.com/feed/"),
    # AI testing / LLM / agents / eval (MCP, RAG, LangChain, CrewAI, n8n, evals)
    ("CrewAI",               "https://blog.crewai.com/rss/"),
    ("n8n",                  "https://n8n.io/blog/feed/"),
    ("InfoQ AI/ML",          "https://feed.infoq.com/ai-ml-data-eng/"),
    ("Simon Willison",       "https://simonwillison.net/atom/everything/"),
    ("MarkTechPost",         "https://www.marktechpost.com/feed/"),
]

# Keywords that bump an AI story's priority (impactful / actionable).
HOT_KEYWORDS = {
    "openai": 5, "anthropic": 5, "claude": 5, "chatgpt": 5, "gpt-5": 6, "gpt5": 6,
    "gemini": 4, "google": 3, "meta": 3, "microsoft": 3, "deepmind": 4, "grok": 3,
    "launch": 4, "release": 4, "released": 4, "announce": 3, "unveil": 3,
    "raises": 4, "funding": 4, "billion": 4, "million": 2, "valuation": 3,
    "agent": 4, "agentic": 4, "model": 2, "open source": 4, "open-source": 4,
    "free": 2, "api": 2, "regulation": 3, "ban": 3, "lawsuit": 3, "policy": 2,
    "job": 3, "jobs": 3, "layoff": 3, "automation": 3, "deepfake": 3, "scam": 3,
}

# Keywords that bump a QA / test-automation / AI-testing story's priority.
QA_KEYWORDS = {
    # classic QA / test automation
    "selenium": 5, "playwright": 6, "cypress": 5, "appium": 5, "webdriver": 4,
    "test automation": 6, "automated testing": 5, "sdet": 5, "qa": 3, "testing": 3,
    "framework": 3, "ci/cd": 4, "pipeline": 3, "flaky": 4, "e2e": 4, "end-to-end": 4,
    "api testing": 5, "performance testing": 4, "load testing": 4, "regression": 3,
    "self-healing": 5, "codeless": 3, "low-code": 3,
    "bdd": 3, "cucumber": 3, "junit": 3, "pytest": 4, "testng": 3, "allure": 3,
    # AI testing / LLM / agents / eval (user-requested topics)
    "ai testing": 6, "ai agent": 6, "ai agents": 6, "agentic": 6, "agent": 4,
    "mcp": 6, "model context protocol": 7, "rag": 6, "retrieval augmented": 6,
    "llm": 5, "large language model": 5, "llm eval": 7, "llm evaluation": 7,
    "evaluation": 4, "eval": 4, "benchmark": 4, "deepeval": 7, "ai harness": 6,
    "langchain": 6, "langgraph": 6, "langflow": 6, "crewai": 6, "crew ai": 6,
    "autogen": 5, "n8n": 6, "workflow automation": 4, "guardrails": 5,
    "prompt injection": 6, "hallucination": 5, "vector": 3, "embedding": 3,
    # generic
    "release": 2, "launch": 3, "open source": 3, "free": 2, "tutorial": 2,
}

WINDOW_HOURS = 24
FALLBACK_HOURS = 48
# Per-section caps — "Top 5 Stories" style
MAX_AI = 5
MIN_AI = 3
MAX_QA = 5
MIN_QA = 3


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


def _score(title, summary, keywords):
    blob = f"{title} {summary}".lower()
    return sum(w for kw, w in keywords.items() if kw in blob)


def _norm_title(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())[:60]


def fetch_stories(feeds, keywords, category, min_n, max_n):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=WINDOW_HOURS)
    fallback_cutoff = now - timedelta(hours=FALLBACK_HOURS)

    raw = []
    for source, url in feeds:
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
                    "link": link, "dt": dt, "category": category,
                    "score": _score(title, summary, keywords),
                })
            log.info("[%s] Fetched %d from %s", category, len(feed.entries), source)
        except Exception as ex:
            log.warning("[%s] Feed failed %s: %s", category, source, ex)

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
    if len(recent) < min_n:
        log.info("[%s] Only %d in 24h, widening to 48h", category, len(recent))
        recent = within(fallback_cutoff)
    if len(recent) < min_n:
        recent = items  # last resort: include undated/older, by score

    recent.sort(key=lambda s: (s["score"], s["dt"] or datetime.min.replace(tzinfo=timezone.utc)),
                reverse=True)
    return recent[:max_n]


def fetch_article_text(url, limit=2600):
    """Best-effort: pull readable paragraph text from an article page."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        h = r.text
        # drop non-content blocks
        h = re.sub(r"(?is)<(script|style|nav|footer|header|aside|form)[^>]*>.*?</\1>", " ", h)
        paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", h)
        text = " ".join(_clean(p) for p in paras if len(_clean(p)) > 40)
        return text[:limit]
    except Exception:
        return ""


# ── Optional: Gemini writes rich bullet summaries (free tier) ────────────
def gemini_rewrite(stories, api_key):
    """Return dict idx->{emoji, headline, bullets[]} via one Gemini call. None on fail."""
    blocks = []
    for i, s in enumerate(stories):
        body = fetch_article_text(s["link"]) or s["summary"]
        blocks.append(f"### STORY {i+1}\nSource: {s['source']}\nTitle: {s['title']}\nArticle: {body}")
    joined = "\n\n".join(blocks)

    prompt = (
        "You are a sharp daily tech-news editor. For each numbered story, write a "
        "punchy short-form brief like a premium newsletter.\n"
        "Rules:\n"
        "- headline: rewrite to 8-12 words, specific and curiosity-driving (keep key names/numbers).\n"
        "- bullets: 4 to 5 bullets. Each is ONE tight sentence with a concrete fact, number, "
        "name, or implication from the article. No fluff, no 'in conclusion'. Plain English.\n"
        "- Only use facts present in the provided article text. Do NOT invent statistics, "
        "dollar amounts, dates, or names that are not in the text.\n"
        "- emoji: one relevant emoji.\n\n"
        "Return ONLY valid JSON: a list of objects with keys idx (int), emoji, headline, "
        "bullets (list of strings).\n\n"
        f"{joined}"
    )
    try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               "gemini-2.0-flash:generateContent?key=" + api_key)
        r = requests.post(url, timeout=120, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.6, "responseMimeType": "application/json"},
        })
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        import json
        data = json.loads(text)
        return {int(d["idx"]): d for d in data if "idx" in d}
    except Exception as ex:
        log.warning("Gemini rewrite failed (using RSS text): %s", ex)
        return None


def _src_date(s):
    return s["dt"].strftime("%b %d, %Y") if s.get("dt") else "recent"


def _render_story(s, a, num, total, default_emoji):
    emoji = (a or {}).get("emoji", default_emoji)
    headline = (a or {}).get("headline") or s["title"]
    bullets = (a or {}).get("bullets") if a else None
    if not bullets:
        bullets = [s["summary"] or s["title"]]   # fallback: RSS summary as one bullet

    li = "".join(
        f'<li style="margin:7px 0;line-height:1.5;">{html.escape(str(b))}</li>'
        for b in bullets
    )
    return f"""
<div style="margin:26px 0;">
  <p style="margin:0 0 2px;font-size:12px;letter-spacing:1px;color:#999;text-transform:uppercase;">
    Story {num:02d} of {total:02d}</p>
  <h3 style="margin:0 0 4px;font-size:19px;line-height:1.3;">{emoji} {html.escape(headline)}</h3>
  <p style="margin:0 0 8px;font-size:13px;color:#888;">
    📰 Source: <a href="{html.escape(s['link'])}" style="color:#0b66c3;text-decoration:none;">{html.escape(s['source'])}</a> — {_src_date(s)}</p>
  <ul style="margin:0;padding-left:20px;color:#222;">{li}</ul>
</div>
<hr style="border:none;border-top:1px solid #eee;margin:0;">"""


def build_html(ai_stories, qa_stories, gmap):
    """gmap: dict keyed by 1-based index over the combined (ai + qa) list, or None."""
    now = datetime.now(IST)
    long_date = now.strftime("%A, %B %d, %Y")
    greet = "Good morning" if now.hour < 12 else "Hello"

    def section(title, sub, stories, start_idx, default_emoji):
        out = [f"""
<h2 style="margin:26px 0 2px;font-size:22px;">{title}</h2>
<p style="color:#666;margin:0 0 6px;font-size:13px;">{sub}</p>
<hr style="border:none;border-top:2px solid #1a1a1a;margin:6px 0 0;">"""]
        n = len(stories)
        for k, s in enumerate(stories):
            a = gmap.get(start_idx + k + 1) if gmap else None
            out.append(_render_story(s, a, k + 1, n, default_emoji))
        return "".join(out)

    parts = [f"""\
<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:660px;margin:0 auto;color:#1a1a1a;">
<div style="text-align:center;padding:8px 0 4px;">
  <h1 style="margin:0;font-size:26px;">🤖 Your Daily AI & QA Digest</h1>
  <p style="margin:6px 0 0;color:#666;font-size:14px;">📅 {long_date}</p>
</div>
<p style="margin:18px 0;">{greet}! Here are today's top stories from the last 24 hours — curated, filtered, and summarized into punchy short-form bullets. Everything you need for your morning session. ☕</p>
"""]

    parts.append(section("🔥 AI News",
                         f"Top {len(ai_stories)} AI stories of the day",
                         ai_stories, 0, "🚀"))
    if qa_stories:
        parts.append(section("🧪 QA &amp; AI Testing",
                             f"Top {len(qa_stories)} — test automation + LLM/agents/eval (MCP, RAG, LangChain, n8n)",
                             qa_stories, len(ai_stories), "🧪"))

    parts.append("""
<p style="margin:22px 0 4px;">That's your AI + QA edge for today.</p>
<p style="color:#666;margin:0;">If you're not paying attention to AI right now — AI is still paying attention to you.</p>
<p style="margin:14px 0 0;">See you tomorrow,<br>Your Daily AI Agent 🤖</p>
</div>""")

    subject = f"🤖 {now.strftime('%b %d')} — Your Daily AI & QA Digest (Top {len(ai_stories)+len(qa_stories)})"
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
    ai_stories = fetch_stories(FEEDS_AI, HOT_KEYWORDS, "AI", MIN_AI, MAX_AI)
    qa_stories = fetch_stories(FEEDS_QA, QA_KEYWORDS, "QA", MIN_QA, MAX_QA)
    log.info("Selected %d AI + %d QA stories", len(ai_stories), len(qa_stories))
    if not ai_stories and not qa_stories:
        log.error("No stories found — not sending.")
        return 1

    api_key = os.environ.get("GEMINI_API_KEY")
    gmap = gemini_rewrite(ai_stories + qa_stories, api_key) if api_key else None

    subject, body = build_html(ai_stories, qa_stories, gmap)
    send_email(subject, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
