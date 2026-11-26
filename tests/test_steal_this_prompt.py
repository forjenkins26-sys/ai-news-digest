"""Tests for steal_this_prompt.py — written before the implementation.

Run:  python -m pytest -q tests/test_steal_this_prompt.py
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import steal_this_prompt as stp  # noqa: E402

BENCHMARK = (
    "Find every newsletter and promo sender in my Gmail that I haven't opened in the "
    "last 60 days. Make a Google Sheet with the sender, how many mails they sent and the "
    "unsubscribe link. Don't unsubscribe, reply or delete anything."
)


def cand(cid, text, source="dev.to", title="t", url="https://dev.to/x"):
    return stp.Candidate(id=cid, source=source, title=title, url=url, text=text)


# ---------- scoring: the 5 traits of the user's benchmark prompt ----------

def test_benchmark_prompt_hits_all_five_traits():
    assert set(stp.trait_hits(BENCHMARK)) == set(stp.TRAITS)


def test_persona_prompt_scores_below_benchmark():
    persona = ("I want you to act as a Linux terminal. I will type commands and you will "
               "reply with what the terminal should show.")
    assert stp.score(persona) < stp.score(BENCHMARK)


def test_image_prompt_is_not_a_prompt_for_this_digest():
    img = ("A 15-second epic cinematic action sequence, ultra-wide shot of a stone colossus, "
           "photorealistic, 8k, dramatic camera movement through a storm at dusk.")
    assert not stp.looks_like_prompt(img)


def test_source_code_is_not_a_prompt():
    code = "def f(x):\n    return {k: v for k, v in x.items() if v != None}\nprint(f({'a': 1}))\n" * 3
    assert not stp.looks_like_prompt(code)


def test_benchmark_looks_like_prompt():
    assert stp.looks_like_prompt(BENCHMARK)


def test_shell_env_block_is_not_a_prompt():
    # real dev.to block seen 26-Nov-2026: routes Claude traffic through a third-party proxy
    sh = ('export ANTHROPIC_BASE_URL="https://proxy.example"\n'
          'export ANTHROPIC_AUTH_TOKEN="your-api-key"\n'
          'export ANTHROPIC_MODEL="claude-sonnet-5-5" # was claude-sonnet-4-5\n'
          'claude -p "Reply with exactly: OK" --output-format json')
    assert not stp.looks_like_prompt(sh)


def test_markdown_pr_template_is_not_a_prompt():
    md = ("## Changes\n- Added authentication middleware (AI-generated)\n## Prompt used\n"
          '"Write a Flask middleware for JWT authentication. Include token validation."\n'
          "## Verification steps\n1. Reviewed the code for security issues\n2. Ran the test suite")
    assert not stp.looks_like_prompt(md)


def test_numbered_prompt_chain_is_a_prompt():
    chain = ('Prompt 1: "Write a Python function to parse a CSV file and return a list of '
             'dictionaries."\nPrompt 2: "Review this function for edge cases: empty CSV, missing '
             'columns, malformed data. List issues."')
    assert stp.looks_like_prompt(chain)


def test_heuristic_pick_takes_one_block_per_post():
    cands = [cand("a1", BENCHMARK, url="https://dev.to/same"),
             cand("a2", BENCHMARK + " Weekly.", url="https://dev.to/same"),
             cand("b1", BENCHMARK + " Monthly.", source="prompts.chat", url="https://p/1")]
    urls = [p.candidate.url for p in stp.heuristic_picks(cands, n=3)]
    assert urls.count("https://dev.to/same") == 1


def test_too_short_is_not_a_prompt():
    assert not stp.looks_like_prompt("Working website , show services , allow bookings")


# ---------- extraction ----------

def test_extract_pre_blocks_unescapes_and_strips_tags():
    html = "<p>intro</p><pre><code>Review my &lt;test&gt; file and list bugs</code></pre>"
    assert stp.extract_blocks(html, "pre") == ["Review my <test> file and list bugs"]


def test_extract_blockquotes():
    html = "<blockquote><p>Build a focus room as one web page.</p></blockquote><p>x</p>"
    assert stp.extract_blocks(html, "blockquote") == ["Build a focus room as one web page."]


# ---------- picking: the model may comment, never author ----------

def test_llm_pick_with_unknown_id_is_dropped():
    cands = [cand("a1", BENCHMARK)]
    raw = [{"id": "zz", "why": "w", "adapted": "x", "drill": "d"},
           {"id": "a1", "why": "w", "adapted": "x", "drill": "d"}]
    picks = stp.validate_llm_picks(raw, cands)
    assert [p.candidate.id for p in picks] == ["a1"]


def test_llm_pick_keeps_verbatim_source_text_not_model_text():
    cands = [cand("a1", BENCHMARK)]
    raw = [{"id": "a1", "prompt": "MODEL REWROTE THIS", "why": "w", "adapted": "x", "drill": "d"}]
    picks = stp.validate_llm_picks(raw, cands)
    assert picks[0].candidate.text == BENCHMARK


def test_llm_commentary_urls_are_stripped():
    cands = [cand("a1", BENCHMARK)]
    raw = [{"id": "a1", "why": "see https://evil.example/login now", "adapted": "x", "drill": "d"}]
    picks = stp.validate_llm_picks(raw, cands)
    assert "http" not in picks[0].why


def test_llm_duplicate_ids_count_once():
    cands = [cand("a1", BENCHMARK), cand("b2", BENCHMARK + " Also add a date column.")]
    raw = [{"id": "a1", "why": "w", "adapted": "x", "drill": "d"},
           {"id": "a1", "why": "w", "adapted": "x", "drill": "d"}]
    assert len(stp.validate_llm_picks(raw, cands)) == 1


def test_heuristic_pick_caps_two_per_source():
    cands = [cand(f"d{i}", BENCHMARK + f" Row {i}.", source="dev.to", url=f"https://dev.to/{i}")
             for i in range(5)]
    cands.append(cand("e1", BENCHMARK + " Weekly.", source="Excellent AI Prompts",
                      url="https://excellentprompts.substack.com/p/1"))
    picks = stp.heuristic_picks(cands, n=3)
    sources = [p.candidate.source for p in picks]
    assert sources.count("dev.to") <= 2 and len(picks) == 3


def test_heuristic_why_names_traits():
    picks = stp.heuristic_picks([cand("a1", BENCHMARK)], n=1)
    assert "numeric filter" in picks[0].why


# ---------- dedupe + state ----------

def test_already_sent_candidates_are_skipped():
    c = cand("a1", BENCHMARK)
    state = {"sent": [c.id]}
    assert stp.unsent([c], state) == []


def test_candidate_id_is_stable_and_short():
    a = stp.make_id("dev.to", BENCHMARK)
    assert a == stp.make_id("dev.to", BENCHMARK) and len(a) == 12


def test_state_sent_list_is_capped(tmp_path):
    state = {"sent": [f"{i:012d}" for i in range(stp.SENT_CAP + 50)]}
    p = tmp_path / "s.json"
    stp.save_state(state, p)
    assert len(json.loads(p.read_text())["sent"]) == stp.SENT_CAP


def test_missing_state_file_gives_empty_state(tmp_path):
    s = stp.load_state(tmp_path / "nope.json")
    assert s["sent"] == [] and "pc_seen" not in s


# ---------- email ----------

def test_subject_never_collides_with_news_backstop_marker():
    subject, _ = stp.build_email([], {"dev.to": "OK 0"}, None)
    assert "Daily AI & QA Digest" not in subject


def test_zero_picks_fails_loud_with_source_status():
    status = {"dev.to": "FAIL HTTPError 503", "prompts.chat": "FAIL timeout"}
    subject, body = stp.build_email([], status, None)
    assert "0 prompts" in subject
    assert "FAIL HTTPError 503" in body and "prompts.chat" in body


def test_email_body_escapes_prompt_html():
    p = stp.Pick(candidate=cand("a1", "<script>alert(1)</script> " + BENCHMARK),
                 why="w", adapted="x", drill="d")
    _, body = stp.build_email([p], {"dev.to": "OK 1"}, None)
    assert "<script>" not in body and "&lt;script&gt;" in body


# ---------- gemini model discovery ----------

def test_model_choice_prefers_newest_plain_flash():
    names = ["models/gemini-2.0-flash", "models/gemini-2.5-flash", "models/gemini-2.5-flash-lite",
             "models/gemini-2.5-flash-image", "models/gemini-2.5-pro", "models/embedding-001"]
    order = stp.rank_flash_models(names)
    assert order[0] == "gemini-2.5-flash"
    assert "gemini-2.5-flash-image" not in order and "embedding-001" not in order
    assert "gemini-2.5-pro" not in order


# ---------- prompts.chat seeding ----------

def test_prompts_chat_code_fences_are_stripped():
    c = stp._row_to_candidate({"act": "A", "prompt": "```\nYou are a senior SDET.\n```"})
    assert c.text == "You are a senior SDET."


def test_archive_picks_are_labelled_in_email():
    p = stp.Pick(candidate=cand("a1", BENCHMARK, source="prompts.chat"), why="w", adapted="x",
                 drill="d")
    _, body = stp.build_email([p], {"prompts.chat": "OK"}, None, archive_count=1)
    assert "1 of these" in body and "archive" in body


def test_prompts_chat_first_run_seeds_without_sending():
    rows = [{"act": "A", "prompt": BENCHMARK, "type": "TEXT", "for_devs": "TRUE"}]
    state = {"sent": []}
    new = stp.new_prompts_chat_rows(rows, state)
    assert new == [] and len(state["pc_seen"]) == 1


def test_prompts_chat_second_run_returns_only_new_rows():
    rows = [{"act": "A", "prompt": BENCHMARK, "type": "TEXT", "for_devs": "TRUE"}]
    state = {"sent": []}
    stp.new_prompts_chat_rows(rows, state)
    rows2 = rows + [{"act": "B", "prompt": BENCHMARK + " Add a date column.", "type": "TEXT",
                     "for_devs": "TRUE"}]
    new = stp.new_prompts_chat_rows(rows2, state)
    assert [r["act"] for r in new] == ["B"]
