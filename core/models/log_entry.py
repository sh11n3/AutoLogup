from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    timestamp: str = ""
    username: str = ""
    ip: str = ""
    status: str = ""
    method: str = ""
    path: str = ""
    level: str = ""
    message: str = ""
    raw: str = ""
    source_file: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_display_string(self) -> str:
        parts = [
            f"TIME={self.timestamp}",
            f"USER={self.username}",
            f"IP={self.ip}",
            f"STATUS={self.status}",
            f"METHOD={self.method}",
            f"PATH={self.path}",
            f"LEVEL={self.level}",
            f"MESSAGE={self.message}",
        ]
        return " | ".join(parts)