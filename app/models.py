from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Item:
    id: str
    source: str
    category: str
    title: str

    body: str = ""
    url: str | None = None
    published_at: datetime | None = None
    content_hash: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)