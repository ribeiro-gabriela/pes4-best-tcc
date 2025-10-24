from dataclasses import dataclass, field
from enum import Enum
from typing import Any

@dataclass
class Event:
    class EventType(Enum):
        NAVIGATE = "navigate"
        ERROR = "error"

    type: EventType
    error: Exception | None
    properties: dict[str, Any] = field(default_factory=dict)