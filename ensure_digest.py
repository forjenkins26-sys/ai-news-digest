"""ensure_digest.py — guarantee the daily AI digest actually goes out.

Why this exists (03-Sep-2026)
-----------------------------
The digest is sent by a GitHub Actions cron. GitHub silently DISABLES a
scheduled workflow after 60 days without a repository commit, which is exactly
what happened: last commit 23-Jun, workflow switched off 22-Aug, last email
23-Aug. Ten days passed before anyone noticed, because nothing anywhere reports
"the newsletter did not arrive".

So continuity cannot depend on GitHub alone. This runs locally on a daily
schedule and acts as the backstop:

  1. check the inbox for today's digest (read-only IMAP)
  2. if it already arrived -> do nothing, exit 0
  3. if it did not -> build and send it from here

Two independent paths, and the local one only fires when the cloud one failed,
so a working GitHub run never produces a duplicate.

    python ensure_digest.py            # check, send only if missing
    python ensure_digest.py --check    # report only, never send
    python ensure_digest.py --force    # send regardless (testing)
"""

from __future__ import annotations

import argparse
import email
import imaplib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
os.chdir(BASE)
sys.path.insert(0, str(BASE))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ensure_digest")

# The digest subject always carries this; both the cloud and local senders use
# the same builder, so one probe covers both.
SUBJECT_MARK = "Daily AI & QA Digest"


def _load_env() -> None:
    env = BASE / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def digest_arrived_today() -> bool | None:
    """True/False, or None when the mailbox could not be checked.

    READ-ONLY: selects the mailbox with readonly=True and uses BODY.PEEK, so
    nothing is ever marked as read.
    """
    user = os.environ.get("GMAIL_ADDRESS", "")
    pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not user or not pw:
        log.warning("no GMAIL_ADDRESS / GMAIL_APP_PASSWORD - cannot check inbox")
        return None

    today = datetime.now().strftime("%d-%b-%Y")
    try:
        M = imaplib.IMAP4_SSL("imap.gmail.com", timeout=30)
        M.login(user, pw)
        M.select("INBOX", readonly=True)
        typ, data = M.uid("SEARCH", None, f'(SINCE {today})')
        uids = (data[0] or b"").split()
        for u in uids:
            typ, d = M.uid("FETCH", u, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")
            if not d or not d[0]:
                continue
            subj = email.message_from_bytes(d[0][1]).get("Subject", "")
            # header may be RFC2047-encoded; the marker survives base64 only
            # after decoding, so decode before matching
            from email.header import decode_header
            plain = ""
            for part, enc in decode_header(subj):
                plain += part.decode(enc or "utf-8", errors="ignore") if isinstance(part, bytes) else part
            if SUBJECT_MARK in plain:
                log.info("today's digest already arrived: %s", plain[:70])
                M.logout()
                return True
        M.logout()
        return False
    except Exception as e:
        log.warning("inbox check failed (%s) - cannot confirm", e)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, never send")
    ap.add_argument("--force", action="store_true", help="send regardless")
    args = ap.parse_args()

    _load_env()
    arrived = None if args.force else digest_arrived_today()

    if args.check:
        log.info("digest today: %s", {True: "YES", False: "NO", None: "UNKNOWN"}[arrived])
        return 0

    if arrived is True:
        log.info("nothing to do - GitHub Actions delivered it")
        return 0

    if arrived is None and not args.force:
        # Could not read the mailbox. Sending anyway risks a duplicate; not
        # sending risks a silent gap. A duplicate is the cheaper mistake.
        log.warning("inbox unreadable - sending anyway (a duplicate beats a gap)")

    log.info("sending digest locally (cloud run did not deliver)")
    import ai_news_digest
    return ai_news_digest.main([])


if __name__ == "__main__":
    sys.exit(main())
