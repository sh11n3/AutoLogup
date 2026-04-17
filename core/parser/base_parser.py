from abc import ABC, abstractmethod

from core.models.log_entry import LogEntry


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[LogEntry]:
        # Parse one file and return a list of normalized log entries.
        # Concrete parsers are free to interpret the source format however
        # they need to, as long as they return `LogEntry` objects.
        pass
