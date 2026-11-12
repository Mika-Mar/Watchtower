import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from app.collectors.serebii import SerebiiCollector
from app.models import Item
from app.notifiers.bark import BarkNotifier
from app.notifiers.group import NotificationGroup
from app.notifiers.ntfy import NtfyNotifier
from app.processors.pokemon_enricher import enrich_pokemon
from app.processors.relevance import load_rules, is_relevant
from app.storage import (
    init_db,
    get_item_hash,
    content_hash,
    save_item,
    update_item,
    get_setting,
    set_setting,
)


def main(test_notification: bool = False):
    load_dotenv(Path(__file__).resolve().parent / ".env")
    bark = BarkNotifier(
        device_key=os.environ.get("BARK_DEVICE_KEY", ""),
        server=os.environ.get("BARK_SERVER", "https://api.day.app"),
    )
    notifiers = [bark]
    if os.environ.get("NTFY_TOPIC", "").strip():
        notifiers.append(NtfyNotifier(
            topic=os.environ["NTFY_TOPIC"],
            server=os.environ.get("NTFY_SERVER", "https://ntfy.sh"),
            token=os.environ.get("NTFY_TOKEN", ""),
        ))
    notifier = NotificationGroup(notifiers)

    if test_notification:
        notifier.notify_new(Item(
            id="watchtower-notification-test",
            source="test",
            category="pokemon_event",
            title="Watchtower test notification",
            metadata={"pokemon": "Pikachu", "location": "Test", "games": "Test"},
        ))
        destinations = "Bark, ntfy" if len(notifiers) > 1 else "Bark (ntfy is disabled)"
        print(f"Test notification accepted by: {destinations}")
        return

    init_db()
    rules = load_rules()

    collectors = [
        SerebiiCollector(),
    ]

    first_run = get_setting("bootstrap_complete") != "true"

    if first_run:
        print("First run: importing existing items without notifications")

    for collector in collectors:
        items = collector.fetch()

        for item in items:
            item = enrich_pokemon(item)
            old_hash = get_item_hash(item.id)
            new_hash = content_hash(item)

            if old_hash is None:
                save_item(item)

                if first_run:
                    print("BOOTSTRAP:", item.title)
                elif is_relevant(item, rules):
                    print("NEW:", item.title)
                    notifier.notify_new(item)
                else:
                    print("IGNORED:", item.title)

            elif old_hash != new_hash:
                update_item(item)

                if first_run:
                    print("BOOTSTRAP UPDATE:", item.title)
                elif is_relevant(item, rules):
                    print("NEW:", item.title)
                    notifier.notify_new(item)
                else:
                    print("IGNORED:", item.title)

            else:
                print("KNOWN:", item.title)

    if first_run:
        set_setting("bootstrap_complete", "true")
        print("Bootstrap complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watchtower Pokémon event notifications")
    parser.add_argument(
        "--test-notification",
        action="store_true",
        help="Send a test notification to configured Bark/ntfy recipients and exit.",
    )
    args = parser.parse_args()
    main(test_notification=args.test_notification)
