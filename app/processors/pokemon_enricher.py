import requests

from app.models import Item


POKEAPI_BASE = "https://pokeapi.co/api/v2"


# Für Namen, die Serebii nicht auf Englisch liefert.
# Das können wir später dynamischer machen.
NAME_ALIASES = {
    "バクフーン": "typhlosion",
    "ガブリアス": "garchomp",
}


def enrich_pokemon(item: Item) -> Item:
    if item.category != "pokemon_event":
        return item

    pokemon = item.metadata.get("pokemon")

    if not pokemon:
        return item

    lookup_name = NAME_ALIASES.get(
        pokemon,
        pokemon
    )

    lookup_name = lookup_name.lower().strip()

    try:
        response = requests.get(
            f"{POKEAPI_BASE}/pokemon/{lookup_name}",
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as exc:
        print(
            f"[PokéAPI] Could not enrich {pokemon}: {exc}"
        )
        return item

    item.metadata["pokemon_id"] = data["id"]

    item.metadata["pokemon"] = (
        data["name"]
        .replace("-", " ")
        .title()
    )

    sprite = (
        data.get("sprites", {})
        .get("other", {})
        .get("official-artwork", {})
        .get("front_default")
    )

    if not sprite:
        sprite = (
            data.get("sprites", {})
            .get("front_default")
        )

    if sprite:
        item.metadata["image_url"] = sprite

    return item