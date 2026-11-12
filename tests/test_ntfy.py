import os
import unittest
from unittest.mock import Mock, patch

import requests

from app.models import Item
from app.notifiers.group import NotificationGroup
from app.notifiers.ntfy import NtfyNotifier
from main import main


class AndroidNotificationTests(unittest.TestCase):
    def setUp(self):
        self.item = Item(
            id="event", source="test", category="pokemon_event", title="Distribution",
            url="https://example.com/event",
            metadata={"pokemon": "Pikachu", "image_url": "https://example.com/art.png"},
        )

    @patch("app.notifiers.ntfy.requests.post")
    def test_json_delivery_with_artwork_link_and_auth(self, post):
        NtfyNotifier("topic", "https://ntfy.example.com/", " token ").notify_new(self.item)
        self.assertEqual(post.call_args.args, ("https://ntfy.example.com",))
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["topic"], "topic")
        self.assertEqual(payload["title"], "🎉 New Pokémon Event")
        self.assertIn("Pikachu\nDistribution", payload["message"])
        self.assertEqual(payload["click"], self.item.url)
        self.assertEqual(payload["attach"], self.item.metadata["image_url"])
        self.assertEqual(post.call_args.kwargs["headers"], {"Authorization": "Bearer token"})
        self.assertEqual(post.call_args.kwargs["timeout"], 10)
        post.return_value.raise_for_status.assert_called_once_with()

    @patch("app.notifiers.ntfy.requests.post")
    def test_update_without_optional_fields(self, post):
        self.item.url = None
        self.item.metadata = {}
        NtfyNotifier("topic").notify_updated(self.item)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["title"], "⚠️ Pokémon Event Updated")
        self.assertNotIn("click", payload)
        self.assertNotIn("attach", payload)
        self.assertEqual(post.call_args.kwargs["headers"], {})

    def test_invalid_topics(self):
        for topic in ["", " ", "https://ntfy.sh/topic", "topic/name", "a" * 65]:
            with self.subTest(topic=topic), self.assertRaises(ValueError):
                NtfyNotifier(topic)

    def test_each_recipient_is_attempted_after_failure(self):
        for method in ["notify_new", "notify_updated"]:
            for failing_index in [0, 1]:
                recipients = [Mock(), Mock()]
                getattr(recipients[failing_index], method).side_effect = requests.Timeout("Failed")
                with self.assertRaises(requests.Timeout):
                    getattr(NotificationGroup(recipients), method)(self.item)
                for recipient in recipients:
                    getattr(recipient, method).assert_called_once_with(self.item)

    @patch.dict(os.environ, {"BARK_DEVICE_KEY": "key", "NTFY_TOPIC": "android-topic"}, clear=True)
    @patch("main.load_dotenv")
    @patch("main.init_db", side_effect=RuntimeError("stop"))
    @patch("main.NotificationGroup")
    @patch("main.NtfyNotifier")
    @patch("main.BarkNotifier")
    def test_main_configures_both_recipients(self, bark, ntfy, group, init_db, dotenv):
        with self.assertRaisesRegex(RuntimeError, "stop"):
            main()
        ntfy.assert_called_once_with(topic="android-topic", server="https://ntfy.sh", token="")
        group.assert_called_once_with([bark.return_value, ntfy.return_value])
