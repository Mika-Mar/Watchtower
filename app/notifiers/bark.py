import requests

from app.models import Item

POKEMON_ICON = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse4.mm.bing.net%2Fth%2Fid%2FOIP.Caauk3ptnvXNENEytZ1vXQHaHa%3Fr%3D0%26pid%3DApi&f=1&ipt=8417f7b0ec164173adb93d960775e99ce6f250c98b396ee4f8f148554e0cd443&ipo=images"


class BarkNotifier:
    def __init__(self, device_key: str, server: str = "https://api.day.app"):
        if not device_key.strip():
            raise ValueError(
                "Set BARK_DEVICE_KEY in .env or your environment to the device key "
                "from the Bark app (without brackets or the full URL)."
            )
        self.device_key = device_key.strip()
        self.server = server.rstrip("/")

    def notify_new(self, item: Item):
        self._send(
            item=item,
            title="🎉 New Pokémon Event",
        )

    def notify_updated(self, item: Item):
        self._send(
            item=item,
            title="⚠️ Pokémon Event Updated",
        )

    def _send(
        self,
        item: Item,
        title: str,
    ):
        meta = item.metadata

        image_url = meta.get("image_url")

        payload = {
            "device_key": self.device_key,
            "title": title,
            "body": self._format_message(item),
            "level": "active",
            "group": "Watchtower Pokémon",
            "icon": POKEMON_ICON,
        }

        # Notification antippen -> Event-Seite öffnen
        if item.url:
            payload["url"] = item.url

        # Pokémon-Artwork als Attachment
        if image_url:
            payload["image"] = image_url

        response = requests.post(
            f"{self.server}/push",
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

    @staticmethod
    def _format_message(item: Item) -> str:
        meta = item.metadata

        return "\n".join([
            meta.get("pokemon", "Unknown"),
            item.title,
            "",
            f"🌍 {meta.get('location', 'Unknown')}",
            f"🎮 {meta.get('games', 'Unknown')}",
            f"📅 {meta.get('start_date', '?')} → {meta.get('end_date', '?')}",
        ])
