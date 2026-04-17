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

                # Read one dictionary-style row at a time and normalize it into
                # the shared log model used by the rest of the application.
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
        # Clean up CSV keys and values before normalization. This keeps later
        # filtering and grouping from depending on small formatting differences.
        cleaned = {}

        for key, value in row.items():
            if key is None:
                continue

            normalized_key = str(key).strip()

            if value is None:
                cleaned[normalized_key] = ""
            else:
                cleaned[normalized_key] = str(value).strip()

        # Drop rows that are technically present in the file but contain no data.
        if all(value == "" for value in cleaned.values()):
            return {}

        return cleaned

    def _build_raw_line(self, row: dict) -> str:
        # Reconstruct a readable one-line representation of the row.
        # CSV files do not naturally have a raw log line, so this gives the UI
        # something useful to display in the table and detail view.
        parts = []

        for key, value in row.items():
            parts.append(f"{key}={value}")

        return " | ".join(parts)
