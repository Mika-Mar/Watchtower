import re

import requests

from app.models import Item
from app.notifiers.bark import BarkNotifier, POKEMON_ICON


class NtfyNotifier:
    def __init__(self, topic: str, server: str = "https://ntfy.sh", token: str = ""):
        topic = topic.strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", topic):
            raise ValueError("NTFY_TOPIC must contain 1–64 letters, numbers, underscores or hyphens.")
        self.topic = topic
        self.server = server.rstrip("/")
        self.token = token.strip()

    def notify_new(self, item: Item):
        self._send(item, "🎉 New Pokémon Event")

    def notify_updated(self, item: Item):
        self._send(item, "⚠️ Pokémon Event Updated")

    def _send(self, item: Item, title: str):
        payload = {
            "topic": self.topic,
            "title": title,
            "message": BarkNotifier._format_message(item),
            "icon": POKEMON_ICON,
        }
        if item.url:
            payload["click"] = item.url
        if item.metadata.get("image_url"):
            payload["attach"] = item.metadata["image_url"]
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = requests.post(
            self.server, json=payload, headers=headers, timeout=10,
        )
        response.raise_for_status()
