from app.collectors.serebii import SerebiiCollector
from app.notifiers.ntfy import NtfyNotifier
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


def main():
    init_db()
    rules = load_rules()
    notifier = NtfyNotifier(
        topic="watchtower-pokemon-8f3d91a72c"
    )

    collectors = [
        SerebiiCollector(),
    ]

    first_run = get_setting("bootstrap_complete") != "true"

    if first_run:
        print("First run: importing existing items without notifications")

    for collector in collectors:
        items = collector.fetch()

        for item in items:
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
    main()
