# Daily AI News Digest

Standalone bot — **completely independent** of the Naukri / LinkedIn job bot.
Own folder, own GitHub repo, own Gmail account (`aitestengineer26@gmail.com`).

Every morning at **08:00 IST** it emails two sections:
- **🔥 AI News** — 14 feeds (TechCrunch, The Verge, VentureBeat, Ars Technica,
  MIT Tech Review, The Decoder, AI News, Synced, OpenAI, Google AI,
  Google Cloud AI, DeepMind, Hugging Face, GitHub Changelog) — same coverage
  the old Feedly/Zapier digest pulled. (Anthropic has no public RSS; its news is
  covered via TechCrunch / The Decoder / Ars Technica.)
- **🧪 QA & Test Automation** — 6 feeds (TestGuild, Software Testing Help,
  Applitools, BrowserStack, Cypress, Automation Panda)

For each section it:
1. Keeps stories from the **last 24h** (widens to 48h if too few — QA blogs post slower)
2. Dedupes + ranks by impact keywords (AI: OpenAI/launch/funding; QA: Playwright/Selenium/test automation/SDET)
3. Emails the top picks (AI ~10, QA ~6)

Runs **free on GitHub Actions** — cloud, laptop can be off. RSS has no bot wall.

## Setup

1. Create a new GitHub repo (e.g. `ai-news-digest`), push this folder to it.
2. Generate a Gmail **app password** for `aitestengineer26@gmail.com`:
   https://myaccount.google.com/apppasswords (needs 2FA on the account).
3. In the repo → Settings → Secrets and variables → Actions, add:
   | Secret | Value |
   |---|---|
   | `GMAIL_ADDRESS` | `aitestengineer26@gmail.com` |
   | `GMAIL_APP_PASSWORD` | the 16-char app password |
   | `REPORT_EMAIL` | `aitestengineer26@gmail.com` |
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
