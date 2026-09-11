import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from app.collectors.base import Collector
from app.models import Item


class SerebiiCollector(Collector):
    BASE_URL = "https://www.serebii.net"

    def __init__(self, year: int | None = None):
        self.year = year or datetime.now().year
        self.url = f"{self.BASE_URL}/events/{self.year}.shtml"

    def fetch(self) -> list[Item]:
        response = requests.get(
            self.url,
            timeout=20,
            headers={
                "User-Agent": "Watchtower/0.1"
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        items = []

        for table in soup.find_all("table"):
            if not self._is_event_table(table):
                continue

            try:
                item = self._parse_event_table(table)
            except Exception as exc:
                print(f"[Serebii] Could not parse table: {exc}")
                continue

            if item:
                items.append(item)

        print(f"[Serebii] Found {len(items)} events for {self.year}")

        return items

    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.split())

    def _is_event_table(self, table: Tag) -> bool:
        """
        Identify event tables by semantic labels instead of CSS classes.
        """
        text = self._clean(table.get_text(" ", strip=True))

        required = (
            "Description",
            "Type",
            "Location",
            "Start Date",
            "End Date",
            "Games Available",
        )

        return all(label in text for label in required)

    def _parse_event_table(self, table: Tag) -> Item | None:
        rows = []

        for tr in table.find_all("tr"):
            cells = [
                self._clean(cell.get_text(" ", strip=True))
                for cell in tr.find_all(["td", "th"], recursive=False)
            ]

            if cells:
                rows.append(cells)

        if not rows:
            return None

        # Useful while developing:
        # print("=" * 80)
        # for row in rows:
        #     print(row)

        name = self._extract_name(table)

        description = None
        event_type = None
        location = None

        start_date = None
        end_date = None
        games = None

        for index, row in enumerate(rows):
            normalized = [cell.lower() for cell in row]

            # --------------------------------
            # Description / Type / Location
            # --------------------------------

            if (
                "description" in normalized
                and "type" in normalized
                and "location" in normalized
            ):
                if index + 1 < len(rows):
                    values = rows[index + 1]

                    if len(values) >= 1:
                        description = values[0]

                    if len(values) >= 2:
                        event_type = values[1]

                    if len(values) >= 3:
                        location = values[2]

            # --------------------------------
            # Start Date / End Date
            # --------------------------------

            if (
                "start date" in normalized
                and "end date" in normalized
            ):
                if index + 1 < len(rows):
                    values = rows[index + 1]

                    if len(values) >= 1:
                        start_date = values[0]

                    if len(values) >= 2:
                        end_date = values[1]

            # --------------------------------
            # Games Available
            # --------------------------------

            for cell_index, cell in enumerate(normalized):
                if cell == "games available":
                    # Could be:
                    #
                    # ["Games Available", "HOME"]
                    #
                    # or:
                    #
                    # ["Games Available"]
                    # ["HOME"]

                    if cell_index + 1 < len(row):
                        games = row[cell_index + 1]

                    elif index + 1 < len(rows):
                        next_row = rows[index + 1]

                        if next_row:
                            games = next_row[0]

        if not name:
            print("[Serebii] Event table without Pokémon name")
            return None

        event_id = self._make_id(
            name=name,
            description=description,
            start_date=start_date,
        )

        event_url = self._extract_event_url(table)

        return Item(
            id=event_id,
            source="serebii",
            category="pokemon_event",
            title=description or f"{name} Distribution",
            body=self._clean(table.get_text(" ", strip=True)),
            url=event_url or self.url,
            metadata={
                "pokemon": name,
                "type": event_type,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "games": games,
                "year": self.year,
            },
        )

    def _extract_name(self, table: Tag) -> str | None:
        """
        Serebii puts the Pokémon name near the beginning of the event table.

        Instead of relying on a CSS class, look for text preceding
        "Level <number>".
        """
        text = self._clean(table.get_text(" ", strip=True))

        match = re.search(
            r"(?:^|\s)([^\s][^|]{0,80}?)\s+[♂♀]?\s*Level\s+\d+",
            text,
            flags=re.IGNORECASE,
        )

        if match:
            candidate = self._clean(match.group(1))

            # In case some unrelated table content got captured,
            # only take the last reasonable section.
            if len(candidate) > 50:
                words = candidate.split()
                candidate = " ".join(words[-5:])

            return candidate.strip()

        return None

    def _extract_event_url(self, table: Tag) -> str | None:
        """
        Try to find a stable Serebii link associated with the Pokémon/event.
        """
        for link in table.find_all("a", href=True):
            href = link["href"]

            if "/events/dex/" in href:
                return urljoin(self.BASE_URL, href)

        return None

    @staticmethod
    def _make_id(
        name: str,
        description: str | None,
        start_date: str | None,
    ) -> str:
        """
        Produce a deterministic ID.

        If we fetch the same event tomorrow, it gets the same ID.
        """
        raw = "|".join(
            [
                name.lower().strip(),
                (description or "").lower().strip(),
                (start_date or "").lower().strip(),
            ]
        )

        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]

        return f"serebii:{digest}"