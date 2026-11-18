"""Notification dispatcher with pluggable channel architecture."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

MAX_CHANNELS = 16
DEFAULT_BATCH_SIZE = 32
DIGEST_SUBJECT_PREFIX = "[digest]"


class ChannelKind(Enum):
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"


class NotificationChannel(ABC):
    @abstractmethod
    def kind(self) -> ChannelKind: ...

    @abstractmethod
    def send(self, user: dict, subject: str, body: str) -> bool: ...


class Sendable(Protocol):
    def send(self, user: dict, subject: str, body: str) -> bool: ...


@dataclass
class ChannelConfig:
    kind: ChannelKind
    enabled: bool = True
    retries: int = 0
    options: dict = field(default_factory=dict)


class EmailChannel(NotificationChannel):
    def kind(self) -> ChannelKind:
        return ChannelKind.EMAIL

    def send(self, user: dict, subject: str, body: str) -> bool:
        address = user.get("email")
        if not address:
            return False
        try:
            _deliver_email(address, subject, body)
            return True
        except Exception:
            logging.warning("email delivery failed for %s", address)
            return False


class SlackChannel(NotificationChannel):
    def kind(self) -> ChannelKind:
        return ChannelKind.SLACK

    def send(self, user: dict, subject: str, body: str) -> bool:
        webhook = user.get("slack_webhook")
        if not webhook:
            return False
        try:
            _post_slack(webhook, subject, body)
            return True
        except Exception:
            logging.warning("slack delivery failed")
            return False


class ChannelFactory:
    _registry: dict[ChannelKind, type] = {}

    @classmethod
    def register(cls, kind: ChannelKind, channel_type: type) -> None:
        cls._registry[kind] = channel_type

    @classmethod
    def create(cls, config: ChannelConfig) -> NotificationChannel:
        channel_type = cls._registry.get(config.kind)
        if channel_type is None:
            raise ValueError(f"no channel registered for {config.kind}")
        return channel_type()


class NotificationPipeline:
    def __init__(self, channels: list[NotificationChannel], batch_size: int = DEFAULT_BATCH_SIZE):
        self.channels = channels
        self.batch_size = batch_size
        self._sent_ids: set[str] = set()

    def dispatch(self, user: dict, events: list[dict]) -> bool:
        delivered = False
        for offset in range(0, len(events), self.batch_size):
            batch = events[offset: offset + self.batch_size]
            for event in batch:
                if event["id"] in self._sent_ids:
                    continue
                for channel in self.channels:
                    subject = f"{DIGEST_SUBJECT_PREFIX} {event.get('title', '')}"
                    if channel.send(user, subject, event.get("body", "")):
                        self._sent_ids.add(event["id"])
                        delivered = True
                        break
        return delivered


def send_user_digest(user: dict, events: list[dict]) -> bool:
    configs = [
        ChannelConfig(ChannelKind.EMAIL),
        ChannelConfig(ChannelKind.SLACK),
    ]
    channels = [ChannelFactory.create(config) for config in configs if config.enabled]
    pipeline = NotificationPipeline(channels[:MAX_CHANNELS])
    return pipeline.dispatch(user, events)


def _deliver_email(address: str, subject: str, body: str) -> None:
    raise RuntimeError("smtp transport not configured")


def _post_slack(webhook: str, subject: str, body: str) -> None:
    raise RuntimeError("slack transport not configured")
