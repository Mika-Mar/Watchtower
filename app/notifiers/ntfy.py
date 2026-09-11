import requests

from app.models import Item


class NtfyNotifier:
    def __init__(self, topic: str, server: str = "https://ntfy.sh"):
        self.topic = topic
        self.server = server.rstrip("/")

    def notify_new(self, item: Item):
        requests.post(
            f"{self.server}/{self.topic}",
            data=self._format_message(item).encode("utf-8"),
            headers={
                "Title": f"New: {item.title}",
                "Priority": "default",
                "Tags": "pokemon",
            },
            timeout=10,
        ).raise_for_status()

    def notify_updated(self, item: Item):
        requests.post(
            f"{self.server}/{self.topic}",
            data=self._format_message(item).encode("utf-8"),
            headers={
                "Title": f"Updated: {item.title}",
                "Priority": "default",
                "Tags": "warning,pokemon",
            },
            timeout=10,
        ).raise_for_status()

    @staticmethod
    def _format_message(item: Item) -> str:
        meta = item.metadata

        return "\n".join([
            f"Pokémon: {meta.get('pokemon', 'Unknown')}",
            f"Type: {meta.get('type', 'Unknown')}",
            f"Region: {meta.get('location', 'Unknown')}",
            f"Start: {meta.get('start_date', 'Unknown')}",
            f"End: {meta.get('end_date', 'Unknown')}",
            f"Games: {meta.get('games', 'Unknown')}",
            "",
            item.url or "",
        ])