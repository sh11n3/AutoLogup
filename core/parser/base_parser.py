from abc import ABC, abstractmethod

from core.models.log_entry import LogEntry


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[LogEntry]:
        pass