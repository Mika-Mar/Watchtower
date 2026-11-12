import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import requests

from app.models import Item
from app.notifiers.bark import BarkNotifier, POKEMON_ICON
from main import main


class BarkNotifierTests(unittest.TestCase):
    def setUp(self):
        self.item = Item(
            id="test-event",
            source="test",
            category="pokemon_event",
            title="Pokémon distribution",
            url="https://example.com/event",
            metadata={
                "pokemon": "Pikachu",
                "image_url": "https://example.com/artwork.png",
            },
        )

    @patch("app.notifiers.bark.requests.post")
    def test_new_event_uses_bark_api_with_icon_artwork_and_link(self, post):
        BarkNotifier("test-key").notify_new(self.item)

        post.assert_called_once_with(
            "https://api.day.app/push",
            json={
                "device_key": "test-key",
                "title": "🎉 New Pokémon Event",
                "body": "Pikachu\nPokémon distribution\n\n🌍 Unknown\n🎮 Unknown\n📅 ? → ?",
                "level": "active",
                "group": "Watchtower Pokémon",
                "icon": POKEMON_ICON,
                "image": "https://example.com/artwork.png",
                "url": "https://example.com/event",
            },
            timeout=10,
        )
        post.return_value.raise_for_status.assert_called_once_with()

    @patch("app.notifiers.bark.requests.post")
    def test_updated_event_without_artwork_or_link_keeps_icon(self, post):
        self.item.url = None
        self.item.metadata = {}
        BarkNotifier("test-key", "https://bark.example.com/base/").notify_updated(self.item)

        self.assertEqual(post.call_args.args, ("https://bark.example.com/base/push",))
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["title"], "⚠️ Pokémon Event Updated")
        self.assertEqual(payload["icon"], POKEMON_ICON)
        self.assertNotIn("image", payload)
        self.assertNotIn("url", payload)

    @patch("app.notifiers.bark.requests.post")
    def test_delivery_errors_propagate(self, post):
        post.return_value.raise_for_status.side_effect = requests.HTTPError("Rejected")
        with self.assertRaises(requests.HTTPError):
            BarkNotifier("test-key").notify_new(self.item)

        post.side_effect = requests.Timeout("Timed out")
        with self.assertRaises(requests.Timeout):
            BarkNotifier("test-key").notify_new(self.item)

    @patch.dict(os.environ, {}, clear=True)
    @patch("main.load_dotenv")
    @patch("main.init_db")
    def test_missing_key_stops_before_database_changes(self, init_db, load_dotenv):
        with self.assertRaisesRegex(ValueError, "BARK_DEVICE_KEY"):
            main()
        init_db.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("main.init_db", side_effect=RuntimeError("stop before database access"))
    @patch("main.BarkNotifier")
    def test_main_loads_project_env_and_preserves_environment_overrides(self, notifier, init_db):
        with TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".env").write_text(
                "BARK_DEVICE_KEY=file-key\nBARK_SERVER=https://bark.example.com\n"
            )
            with patch("main.__file__", str(project / "main.py")):
                with self.assertRaisesRegex(RuntimeError, "stop before database access"):
                    main()
                notifier.assert_called_with(
                    device_key="file-key", server="https://bark.example.com"
                )
                os.environ["BARK_DEVICE_KEY"] = "environment-key"
                with self.assertRaisesRegex(RuntimeError, "stop before database access"):
                    main()
                notifier.assert_called_with(
                    device_key="environment-key", server="https://bark.example.com"
                )

    def test_blank_device_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "BARK_DEVICE_KEY"):
            BarkNotifier("  ")


if __name__ == "__main__":
    unittest.main()
