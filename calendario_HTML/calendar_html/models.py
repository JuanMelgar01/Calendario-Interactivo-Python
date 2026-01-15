from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Event:
    id: str
    title: str
    description: str
    category: str
    start: datetime
    end: Optional[datetime] = None

    @property
    def is_range(self) -> bool:
        return self.end is not None and self.end != self.start
