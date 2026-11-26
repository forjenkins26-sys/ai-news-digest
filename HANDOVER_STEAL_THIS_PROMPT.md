# HANDOVER — "Steal This Prompt" daily email job

**For:** any AI agent taking over or sharing this job (written for the owner's Muse agent).
**Written:** 26-Nov-2026 by Claude Code. **Owner decides** who runs it; Claude still co-owns it until told otherwise.
**Self-contained:** you need nothing from the chat that produced it. Every fact below was checked with a tool on 26-Nov-2026.

## Status in one table

| Item | State (26-Nov-2026) |
|---|---|
| Job | LIVE. GitHub Actions workflow "Steal This Prompt", state `active` |
| Schedule | cron `45 2 * * *` = 08:15 IST daily, plus manual `workflow_dispatch` |
| Proven runs | 1 manual run green (run id 45763736941, 3m25s): 3 picks, Gemini commentary, email accepted by Gmail SMTP, state committed (15cd9df) |
| First scheduled run | 27-Nov-2026 08:15 IST (not yet observed) |
| Delivery proof | Only the log line `Email sent`. Nobody has looked in the recipient inbox yet |
| Tests | 30 pytest tests green (`tests/test_steal_this_prompt.py`) |
| Sister job | "Daily AI News Digest" in the same repo is `disabled_inactivity` since 11-Nov-2026 and NOT fixed (see Backlog #1) |
| Cost | 0. GitHub Actions free minutes, Gemini free tier, Gmail SMTP |

## 0. Boundaries — read before acting

You MAY do alone: read logs, run the health check, run tests, `--dry-run`, trigger `workflow_dispatch`, report findings.
Ask the owner FIRST: any push to the repo (it is **PUBLIC** — a push is permanent and cached), changing secrets,
changing the recipient, adding a new source that needs a login or costs money, re-enabling or editing the news workflow.
NEVER: commit `.env` or any email address or person's name; write a prompt yourself and present it as sourced;
use the string `Daily AI & QA Digest` in this job's subject (the news backstop `ensure_digest.py` matches it).

## 1. What it does

Every morning it emails 3 prompts worth stealing. Each pick = the prompt **copied verbatim** + link to the original,
why it works, a version adapted to the reader's work (QA, Playwright, Jira, trading-bot research), and a 15-minute drill.
Every pick is also appended to `prompt_library.md` (the growing, searchable library).
The spec it implements is `STEAL_THIS_PROMPT_SPEC.md` (the owner's request, optimized, RICEPOT format).

## 2. Where everything is

| What | Where |
|---|---|
| Local folder | `D:\My AI Automation Building\AINewsBot` |
| Repo | `github.com/forjenkins26-sys/ai-news-digest` (public), branch `main` |
| Job code | `steal_this_prompt.py` (600 lines, single file) |
| Workflow | `.github/workflows/steal_prompt.yml` |
| Tests | `tests/test_steal_this_prompt.py` |
| State (committed by the bot) | `prompt_state.json` — `sent` ids (cap 3000), `pc_seen` (prompts.chat rows seen), `sys_seen`, `last_run`, `runs` |
| Library (committed by the bot) | `prompt_library.md` |
| Secrets (GitHub repo secrets, names only) | `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `REPORT_EMAIL`, `GEMINI_API_KEY` — shared with the news job |
| Local `.env` | gitignored; has the Gmail values but **no** Gemini key, so local runs use heuristic picks |
| Design notes | `blindspot.md` (pre-build risk pass), `README.md` + `CLAUDE.md` (sections "Steal This Prompt") |

## 3. How it works (`steal_this_prompt.py`)

1. **Collect** (`main` :530) from free sources, each wrapped so one failure never stops the run:
   - `FEEDS` :61 — Excellent AI Prompts Substack (`<blockquote>`), dev.to `#promptengineering` and `#claude` (`<pre>`). Items newer than `FRESH_HOURS`=72.
   - prompts.chat CSV :67 (3,187 rows, 11.9 MB). First run seeded every row as seen; later runs only surface new rows (`new_prompts_chat_rows` :234). Dev-tagged rows (119 pass the filters) are the **archive** fallback.
   - system-prompts repo commits :68 → optional "Study a pro prompt" line (`fetch_pro_study` :262).
2. **Filter** `looks_like_prompt` :149 — 120–6000 chars; rejects image/video prompts, source code, shell/env lines (`export X_API_KEY=` can route tokens to a third-party proxy — seen on dev.to 26-Nov), docs that do not open like an instruction.
3. **Score** `score` :136 on the 5 benchmark traits `TRAITS` :72 — data source, numeric filter, output format, destination, negative constraint (from the owner's Gmail-cleanup example prompt) + relevance words; persona "act as" prompts penalised.
4. **Pool**: fresh prompts with score ≥ 6, topped up from the archive if fewer than 3. Max 2 per source, 1 per post (`_diverse_top` :294).
5. **Pick**: Gemini (`gemini_picks` :393) gets up to 12 candidates as untrusted data, returns `[{id, why, adapted, drill}]`. `validate_llm_picks` :327 drops unknown/duplicate ids, strips URLs, and always uses the **source's** text. Model chosen at runtime (`gemini_models` :358 → `rank_flash_models` :344, newest plain flash first, tries 4). All fail → `heuristic_picks` :308.
6. **Email** `build_email` :454 / `send_email` :500. Archive picks are labelled. Zero picks → "⚠️ … 0 prompts today" email with per-source status (never silent).
7. **Save** state + library only after the email is sent; the workflow then commits them. **That commit is the keepalive** — GitHub disables all crons in a repo after 60 days without a commit.

## 4. Daily health check (2 minutes)

```bash
gh workflow list -R forjenkins26-sys/ai-news-digest --all          # want: Steal This Prompt  active
gh run list -R forjenkins26-sys/ai-news-digest -w steal_prompt.yml -L 3   # want: completed success, today
gh run view <run-id> -R forjenkins26-sys/ai-news-digest --log | grep -E "\[(INFO|WARNING|ERROR)\]"
```

Healthy log = one `source …` line per source, `candidates: N fresh, M shortlisted`, `subject: 🧠 Steal This Prompt — <date> (3 picks)`, `Email sent`, then a commit `Steal This Prompt: daily state <date>`.
Known-normal today: `Excellent AI Prompts FAIL HTTPError 403` (Substack blocks GitHub IPs) and 1–2 `Gemini <model> failed: Read timed out` before a later model answers.

## 5. Runbook

| Symptom | Likely cause | Fix |
|---|---|---|
| No run today, workflow `disabled_inactivity` | 60 days without a commit (bot commits stopped) | Owner OK → `gh workflow enable steal_prompt.yml -R …`, dispatch once, find why commits stopped |
| Run failed at "Send today's prompts" | Gmail app password revoked / SMTP error | Owner must make a new app password and update the secret (never handle the password yourself) |
| Run failed at "Save state" | push rejected / permissions | Check `permissions: contents: write` in the workflow and repo Actions settings |
| Footer says `heuristic (no Gemini)` | key invalid, quota, or all models failed | Read `Gemini … failed` lines; key problems need the owner |
| Subject `0 prompts today` | every source failed or empty | Read the status table in the email; probe each URL from a laptop AND from Actions |
| Picks marked "from the archive" every day | fresh supply too thin | Backlog #3 |
| Same prompt twice | different source → different id | Acceptable; dedupe is per source |

## 6. How to change it safely

1. Write the failing test first in `tests/test_steal_this_prompt.py`.
2. `python -m pytest -q tests/test_steal_this_prompt.py` → all green (Windows: set `PYTHONUTF8=1`).
3. `python steal_this_prompt.py --dry-run` → open `prompt_preview.html`, read every pick: is each one a real prompt?
4. Get owner OK → commit + push → `gh workflow run steal_prompt.yml -R forjenkins26-sys/ai-news-digest --ref main` → read the log.
5. Update this file's Change log and `CLAUDE.md`.

## 7. Backlog — open findings, most important first

1. **News digest is off** (sister job): `disabled_inactivity` since 11-Nov, and it hardcodes `gemini-2.0-flash`, which returns 404, so it silently sends raw RSS text. Fix: re-enable the workflow + copy `gemini_models`/`rank_flash_models` into `ai_news_digest.py`. Needs owner OK.
2. **Gemini timeouts**: newest models hit the 90 s read timeout (~3 min wasted per run). Fix: lower timeout to ~40 s and log which model answered.
3. **Thin fresh supply**: first run had 1 fresh pick; 2 of 3 came from the 119-row archive → archive lasts roughly 2 months. Fix: add free sources (prove each from GitHub Actions, not only a laptop).
4. **Substack 403 from Actions**: Excellent AI Prompts never works in the cloud; drop it or find a cloud-safe route.
5. **Placeholder paths** in "Your version" (e.g. `./logs/test-results.json`): tell the model to mark paths as `<your path>`.
6. **No arrival check**: unlike the news job, nothing confirms the email landed. Option: extend `ensure_digest.py` (IMAP, read-only) with a second subject mark.

## 8. Coordinating with Claude

- One writer at a time: before editing, `git pull`; if `git log` shows a commit by the other agent in the last hour, ask first.
- Log every change below (date, agent, what, commit). Report findings to the owner; do not fix a finding and report it as done without a run log as evidence.
- What you need to take over: `gh` logged in to the repo owner's GitHub account with push rights, Python 3.11+, `pip install requests feedparser pytest`. You do NOT need the Gmail password or the Gemini key — they live in GitHub secrets.

## Change log

| Date | Agent | Change | Commit |
|---|---|---|---|
| 26-Nov-2026 | Claude Code | Job built, tests, workflow, first manual run green | 4f5d718, 15cd9df (bot) |
| 26-Nov-2026 | Claude Code | This handover added | (this commit) |
