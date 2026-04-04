from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    timestamp: str | None = None
    username: str | None = None
    ip: str | None = None
    status: int | None = None
    method: str | None = None
    path: str | None = None
    level: str | None = None
    message: str | None = None
    raw: str = ""
    source_file: str = ""
    extra: dict[str, Any] = field(default_factory=dict)