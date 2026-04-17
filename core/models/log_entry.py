from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogEntry:
    # Store one normalized log record in a format the rest of the application
    # can rely on. The fixed fields cover the most common attributes, while
    # `extra` keeps everything source-specific that does not fit the shared model.
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
        # Build a compact one-line summary of the normalized fields.
        # This is useful anywhere the application needs a simple text form
        # without opening the full detail panel.
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
