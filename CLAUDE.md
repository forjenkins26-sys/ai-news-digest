# CLAUDE.md — Daily AI News Digest

Guidance for Claude Code when working in `D:\My AI Automation Building\AINewsBot`.

## What this is

Standalone Python bot that emails a daily AI + QA news digest. **Completely
independent** of the Naukri bot (`D:\My AI Automation Building\NaukriBot`) — own folder, own git repo, own Gmail
account (`aitestengineer26@gmail.com`, sends to itself).

Runs **free on GitHub Actions** (cloud) — RSS has no bot wall, so the laptop can be off.

Repo: https://github.com/forjenkins26-sys/ai-news-digest  •  Status: LIVE.

## Run

```bash
# Local
pip install -r requirements.txt
cp .env.example .env          # fill GMAIL_APP_PASSWORD etc.
python ai_news_digest.py

# Production: GitHub Actions cron in .github/workflows/ai_news.yml
#   cron: "30 2 * * *"  ==  08:00 IST daily
#   steps: setup-python 3.11 -> pip install -r requirements.txt -> python ai_news_digest.py
```

## Environment (GitHub Secrets, or local `.env` gitignored)

| Var | Purpose |
|---|---|
| `GMAIL_ADDRESS` | sender Gmail (`aitestengineer26@gmail.com`) |
| `GMAIL_APP_PASSWORD` | 16-char Gmail app password (needs 2FA on the account) |
| `REPORT_EMAIL` | recipient (defaults to `GMAIL_ADDRESS`) |
| `GEMINI_API_KEY` | OPTIONAL — if set, Gemini rewrites each story; without it falls back to RSS description (still works) |

## Architecture (`ai_news_digest.py`, single file)

`main()` (`:382`):
1. `fetch_stories(FEEDS_AI, HOT_KEYWORDS, "AI", MIN_AI, MAX_AI)` (`:161`) — 14 AI feeds
2. `fetch_stories(FEEDS_QA, QA_KEYWORDS, "QA", MIN_QA, MAX_QA)` — 6 QA feeds
3. Per section: keep last 24h (`_entry_dt`), widen to 48h if too few (QA blogs post slower), dedupe by `_norm_title`, rank by `_score` keywords
4. If `GEMINI_API_KEY`: `gemini_rewrite()` (`:228`) reads each article (`fetch_article_text`, `:213`) → What happened / Why it matters / What to do (instructed NOT to fabricate stats). No key → single RSS bullet.
5. `build_html()` (`:301`) — premium digest (centered header, Top picks, per-story card, summary box)
6. `send_email()` (`:364`) — Gmail SMTP

## Feeds

- `FEEDS_AI` (`:54`) — TechCrunch, The Verge, VentureBeat, Ars Technica, MIT Tech Review, The Decoder, AI News, Synced, OpenAI, Google AI, Google Cloud AI, DeepMind, Hugging Face, GitHub Changelog. (Anthropic has no public RSS — covered via outlets.)
- `FEEDS_QA` (`:74`) — TestGuild, Software Testing Help, Applitools, BrowserStack, Cypress, Automation Panda (+ AI-testing keywords weighted high: MCP, RAG, LLM eval, DeepEval, LangChain/LangGraph, CrewAI, n8n, prompt injection).

## Key files

- `ai_news_digest.py` — the bot (everything here)
- `requirements.txt` — `requests`, `feedparser`
- `.github/workflows/ai_news.yml` — daily cron
- `.env` — local secrets (gitignored, never pushed)
- `README.md` — user-facing overview

## Gotchas

- Cloud-safe (RSS has no bot wall) — opposite of the Naukri bot.
- Gemini step is optional; everything degrades gracefully without the key.
- Local run needs `PYTHONUTF8=1` on Windows for emoji-heavy HTML.

## Related

Naukri job bot is a **separate** local project at `D:\My AI Automation Building\NaukriBot`. Shares nothing except
both send via Gmail.
