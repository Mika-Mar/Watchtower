from pathlib import Path
import yaml

from app.models import Item


RULES_PATH = Path("config/rules.yaml")


def load_rules() -> dict:
    with RULES_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def is_relevant(item: Item, rules: dict) -> bool:
    if item.category != "pokemon_event":
        return True

    pokemon_rules = rules.get("pokemon", {})

    location = _normalize(item.metadata.get("location"))
    games = _normalize(item.metadata.get("games"))
    event_type = _normalize(item.metadata.get("type"))

    # Region
    location_rules = pokemon_rules.get("locations", {})
    allowed_locations = {
        _normalize(value)
        for value in location_rules.get("allow", [])
    }

    if allowed_locations and location not in allowed_locations:
        return False

    # Games
    game_rules = pokemon_rules.get("games", {})
    denied_games = [
        _normalize(value)
        for value in game_rules.get("deny", [])
    ]

    for denied in denied_games:
        if denied in games:
            return False

    # Event type
    type_rules = pokemon_rules.get("types", {})
    allowed_types = {
        _normalize(value)
        for value in type_rules.get("allow", [])
    }

    if allowed_types and event_type not in allowed_types:
        return False

    return True