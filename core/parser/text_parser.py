import re

from core.models.log_entry import LogEntry
from core.parser.base_parser import BaseParser
from core.parser.normalizer import Normalizer
from utils.file_utils import read_file_lines


class TextParser(BaseParser):
    IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    STATUS_REGEX = re.compile(r"\b(?:status=)?([1-5]\d{2})\b", re.IGNORECASE)
    LEVEL_REGEX = re.compile(r"\b(INFO|WARN|WARNING|ERROR|DEBUG|CRITICAL)\b", re.IGNORECASE)
    METHOD_REGEX = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b", re.IGNORECASE)

    # einfache Zeitformate für V1
    TIMESTAMP_REGEXES = [
        re.compile(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\b"),      # 2025-04-01 12:30:45
        re.compile(r"\b\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2}\b"),      # 01/04/2025 12:30:45
        re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}[ T]\d{2}:\d{2}:\d{2}\b"),  # 3/16/2022 15:58:00
    ]

    PATH_REGEX = re.compile(r"(\/[A-Za-z0-9_\-\/\.\?\=\&%:]*)")

    def __init__(self):
        self.normalizer = Normalizer()

    def parse(self, file_path: str) -> list[LogEntry]:
        lines = read_file_lines(file_path)
        entries: list[LogEntry] = []

        for line in lines:
            raw = line.strip()

            if not raw:
                continue

            extracted = self._extract_fields(raw)
            entry = self.normalizer.normalize(
                data=extracted,
                raw=raw,
                source_file=file_path,
            )
            entries.append(entry)

        return entries

    def _extract_fields(self, raw: str) -> dict:
        data: dict = {}

        timestamp = self._extract_timestamp(raw)
        if timestamp:
            data["timestamp"] = timestamp

        ip = self._extract_ip(raw)
        if ip:
            data["ip"] = ip

        status = self._extract_status(raw)
        if status is not None:
            data["status"] = status

        level = self._extract_level(raw)
        if level:
            data["level"] = level

        method = self._extract_method(raw)
        if method:
            data["method"] = method

        path = self._extract_path(raw)
        if path:
            data["path"] = path

        data["message"] = raw

        return data

    def _extract_timestamp(self, raw: str) -> str | None:
        for regex in self.TIMESTAMP_REGEXES:
            match = regex.search(raw)
            if match:
                return match.group(0)
        return None

    def _extract_ip(self, raw: str) -> str | None:
        match = self.IP_REGEX.search(raw)
        if match:
            return match.group(0)
        return None

    def _extract_status(self, raw: str) -> int | None:
        match = self.STATUS_REGEX.search(raw)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    def _extract_level(self, raw: str) -> str | None:
        match = self.LEVEL_REGEX.search(raw)
        if match:
            value = match.group(1).upper()
            if value == "WARNING":
                return "WARN"
            return value
        return None

    def _extract_method(self, raw: str) -> str | None:
        match = self.METHOD_REGEX.search(raw)
        if match:
            return match.group(1).upper()
        return None

    def _extract_path(self, raw: str) -> str | None:
        match = self.PATH_REGEX.search(raw)
        if match:
            return match.group(1)
        return None