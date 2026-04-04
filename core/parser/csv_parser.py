import csv

from core.models.log_entry import LogEntry
from core.parser.base_parser import BaseParser
from core.parser.normalizer import Normalizer


class CSVParser(BaseParser):
    def __init__(self):
        self.normalizer = Normalizer()

    def parse(self, file_path: str) -> list[LogEntry]:
        entries: list[LogEntry] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore", newline="") as file:
                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    return []

                for row in reader:
                    if row is None:
                        continue

                    cleaned_row = self._clean_row(row)
                    if not cleaned_row:
                        continue

                    raw = self._build_raw_line(cleaned_row)

                    entry = self.normalizer.normalize(
                        data=cleaned_row,
                        raw=raw,
                        source_file=file_path,
                    )
                    entries.append(entry)

        except Exception as error:
            print(f"Error parsing CSV file '{file_path}': {error}")

        return entries

    def _clean_row(self, row: dict) -> dict:
        cleaned = {}

        for key, value in row.items():
            if key is None:
                continue

            normalized_key = str(key).strip()

            if value is None:
                cleaned[normalized_key] = ""
            else:
                cleaned[normalized_key] = str(value).strip()

        # Prüfen, ob die Zeile komplett leer ist
        if all(value == "" for value in cleaned.values()):
            return {}

        return cleaned

    def _build_raw_line(self, row: dict) -> str:
        parts = []

        for key, value in row.items():
            parts.append(f"{key}={value}")

        return " | ".join(parts)