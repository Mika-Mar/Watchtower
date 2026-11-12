import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import requests

from main import main


@patch.dict(os.environ, {"BARK_DEVICE_KEY": "test-key", "NTFY_TOPIC": "test-topic"}, clear=True)
class TestNotificationCommandTests(unittest.TestCase):
    def test_test_mode_sends_to_both_services_without_collecting_or_accessing_database(self):
        with (
            patch("main.load_dotenv"),
            patch("requests.post") as post,
            patch("main.init_db") as init_db,
            patch("main.load_rules") as load_rules,
            patch("main.SerebiiCollector") as collector,
            redirect_stdout(io.StringIO()) as output,
        ):
            main(test_notification=True)

        self.assertEqual(post.call_count, 2)
        bark, ntfy = post.call_args_list
        self.assertEqual(bark.args, ("https://api.day.app/push",))
        self.assertEqual(bark.kwargs["json"]["device_key"], "test-key")
        self.assertIn("Watchtower test notification", bark.kwargs["json"]["body"])
        self.assertEqual(ntfy.args, ("https://ntfy.sh",))
        self.assertEqual(ntfy.kwargs["json"]["topic"], "test-topic")
        self.assertEqual(ntfy.kwargs["json"]["message"], bark.kwargs["json"]["body"])
        self.assertIn("accepted by: Bark, ntfy", output.getvalue())
        init_db.assert_not_called()
        load_rules.assert_not_called()
        collector.assert_not_called()

    def test_test_mode_reports_when_only_bark_is_enabled(self):
        with (
            patch.dict(os.environ, {"NTFY_TOPIC": ""}),
            patch("main.load_dotenv"),
            patch("requests.post") as post,
            redirect_stdout(io.StringIO()) as output,
        ):
            main(test_notification=True)

        post.assert_called_once()
        self.assertIn("Bark (ntfy is disabled)", output.getvalue())

    def test_test_mode_propagates_failure_after_attempting_other_service(self):
        with (
            patch("main.load_dotenv"),
            patch("requests.post", side_effect=[requests.Timeout("Timed out"), Mock()]) as post,
            redirect_stdout(io.StringIO()) as output,
        ):
            with self.assertRaises(requests.Timeout):
                main(test_notification=True)

        self.assertEqual(post.call_count, 2)
        self.assertNotIn("accepted by", output.getvalue())
