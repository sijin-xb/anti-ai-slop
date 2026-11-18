"""Send per-user event digests over email and Slack."""
from __future__ import annotations

import logging

DIGEST_SUBJECT_PREFIX = "[digest]"


def send_user_digest(user: dict, events: list[dict]) -> bool:
    delivered = False
    sent_ids: set[str] = set()
    for event in events:
        if event["id"] in sent_ids:
            continue
        subject = f"{DIGEST_SUBJECT_PREFIX} {event.get('title', '')}"
        body = event.get("body", "")
        if _send_email(user, subject, body) or _send_slack(user, subject, body):
            sent_ids.add(event["id"])
            delivered = True
    return delivered


def _send_email(user: dict, subject: str, body: str) -> bool:
    address = user.get("email")
    if not address:
        return False
    try:
        _deliver_email(address, subject, body)
        return True
    except Exception:
        logging.warning("email delivery failed for %s", address)
        return False


def _send_slack(user: dict, subject: str, body: str) -> bool:
    webhook = user.get("slack_webhook")
    if not webhook:
        return False
    try:
        _post_slack(webhook, subject, body)
        return True
    except Exception:
        logging.warning("slack delivery failed")
        return False


def _deliver_email(address: str, subject: str, body: str) -> None:
    raise RuntimeError("smtp transport not configured")


def _post_slack(webhook: str, subject: str, body: str) -> None:
    raise RuntimeError("slack transport not configured")
