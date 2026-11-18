"""Send per-user digest notifications via email and slack."""
import logging


def send_user_digest(user: dict, events: list[dict]) -> bool:
    """Send each event once per call; return True if any delivery succeeded.

    Dedup key is ``event["id"]``. An event is only recorded as sent when a
    channel actually accepts it, so failed events are retried on repeat ids.
    """
    sent_ids = set()
    delivered = False
    for event in events:
        event_id = event["id"]
        if event_id in sent_ids:
            continue
        subject = f"[digest] {event.get('title', '')}"
        body = event.get("body", "")
        for send in (_send_email, _send_slack):
            if send(user, subject, body):
                sent_ids.add(event_id)
                delivered = True
                break
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
