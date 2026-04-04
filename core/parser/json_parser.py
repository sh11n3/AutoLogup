import json

from core.models.log_entry import LogEntry
from core.parser.base_parser import BaseParser
from core.parser.normalizer import Normalizer
from utils.file_utils import read_file_lines


class JSONParser(BaseParser):
    def __init__(self):
        self.normalizer = Normalizer()

    def parse(self, file_path: str) -> list[LogEntry]:
        lines = read_file_lines(file_path)

        if not lines:
            return []

        content = "".join(lines).strip()
        if not content:
            return []

        # 1. Erst versuchen: komplette Datei als JSON parsen
        parsed_entries = self._parse_full_json(content, file_path)
        if parsed_entries is not None:
            return parsed_entries

        # 2. Fallback: JSON Lines
        return self._parse_json_lines(lines, file_path)

    def _parse_full_json(self, content: str, file_path: str) -> list[LogEntry] | None:
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            return None

        if isinstance(obj, list):
            entries: list[LogEntry] = []

            for item in obj:
                if not isinstance(item, dict):
                    continue

                raw = json.dumps(item, ensure_ascii=False)
                flat_item = self._flatten_dict(item)
                entry = self.normalizer.normalize(
                    data=flat_item,
                    raw=raw,
                    source_file=file_path,
                )
                entries.append(entry)

            return entries

        if isinstance(obj, dict):
            raw = json.dumps(obj, ensure_ascii=False)
            flat_obj = self._flatten_dict(obj)
            entry = self.normalizer.normalize(
                data=flat_obj,
                raw=raw,
                source_file=file_path,
            )
            return [entry]

        return []

    def _parse_json_lines(self, lines: list[str], file_path: str) -> list[LogEntry]:
        entries: list[LogEntry] = []

        for line in lines:
            raw = line.strip()
            if not raw:
                continue

            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if not isinstance(item, dict):
                continue

            flat_item = self._flatten_dict(item)
            entry = self.normalizer.normalize(
                data=flat_item,
                raw=raw,
                source_file=file_path,
            )
            entries.append(entry)

        return entries

    def _flatten_dict(self, data: dict, parent_key: str = "", sep: str = ".") -> dict:
        items = {}

        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else str(key)

            if isinstance(value, dict):
                items.update(self._flatten_dict(value, new_key, sep))
            else:
                items[new_key] = value

        return items