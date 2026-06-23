# Daily AI News Digest

Standalone bot — **completely independent** of the Naukri / LinkedIn job bot.
Own folder, own GitHub repo, own Gmail account (`aitestengieer26@gmail.com`).

Every morning at **08:00 IST** it:
1. Fetches AI news from 9 free RSS feeds (TechCrunch, The Verge, VentureBeat,
   Ars Technica, MIT Tech Review, Google AI, OpenAI, DeepMind, Hugging Face)
2. Keeps stories from the **last 24h** (widens to 48h if too few)
3. Dedupes + ranks by impact keywords (OpenAI / launch / funding / jobs …)
4. Emails the top ~12 as a newsletter

Runs **free on GitHub Actions** — cloud, laptop can be off. RSS has no bot wall.

## Setup

1. Create a new GitHub repo (e.g. `ai-news-digest`), push this folder to it.
2. Generate a Gmail **app password** for `aitestengieer26@gmail.com`:
   https://myaccount.google.com/apppasswords (needs 2FA on the account).
3. In the repo → Settings → Secrets and variables → Actions, add:
   | Secret | Value |
   |---|---|
   | `GMAIL_ADDRESS` | `aitestengieer26@gmail.com` |
   | `GMAIL_APP_PASSWORD` | the 16-char app password |
   | `REPORT_EMAIL` | `aitestengieer26@gmail.com` |
   | `GEMINI_API_KEY` | *(optional)* free key from aistudio.google.com/apikey |
4. Actions tab → "Daily AI News Digest" → Run workflow (test now).

## Local test

```
pip install -r requirements.txt
cp .env.example .env   # fill in the app password
python ai_news_digest.py
```

## Optional: punchy AI summaries

Without `GEMINI_API_KEY` → each story shows its RSS description.
With it → Gemini rewrites every story as *What happened / Why it matters /
What to do*. Free tier. No key = still works.
