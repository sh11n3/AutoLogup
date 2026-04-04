import re

from core.models.log_entry import LogEntry
from core.parser.base_parser import BaseParser
from core.parser.normalizer import Normalizer
from core.parser.text_parser import TextParser
from utils.file_utils import read_file_lines


class SQLParser(BaseParser):
    INSERT_REGEX = re.compile(
        r"INSERT\s+INTO\s+[`\"]?(?P<table>[A-Za-z0-9_]+)[`\"]?\s*"
        r"\((?P<columns>.*?)\)\s*VALUES\s*(?P<values>.*?);",
        re.IGNORECASE | re.DOTALL,
    )

    VALUE_GROUP_REGEX = re.compile(r"\((.*?)\)", re.DOTALL)

    def __init__(self):
        self.normalizer = Normalizer()
        self.text_parser = TextParser()

    def parse(self, file_path: str) -> list[LogEntry]:
        lines = read_file_lines(file_path)
        if not lines:
            return []

        content = "".join(lines).strip()
        if not content:
            return []

        insert_entries = self._parse_insert_statements(content, file_path)
        if insert_entries:
            return insert_entries

        # Fallback: als Textlog behandeln
        return self.text_parser.parse(file_path)

    def _parse_insert_statements(self, content: str, file_path: str) -> list[LogEntry]:
        entries: list[LogEntry] = []

        for match in self.INSERT_REGEX.finditer(content):
            table_name = match.group("table").strip()
            raw_columns = match.group("columns").strip()
            raw_values = match.group("values").strip()

            columns = self._parse_columns(raw_columns)
            if not columns:
                continue

            value_groups = self._parse_value_groups(raw_values)
            for group in value_groups:
                values = self._split_sql_values(group)

                if len(values) != len(columns):
                    continue

                row_data = {}
                for column, value in zip(columns, values):
                    row_data[column] = self._clean_sql_value(value)

                row_data["table"] = table_name

                raw = f"INSERT_ROW table={table_name} | " + " | ".join(
                    f"{key}={value}" for key, value in row_data.items()
                )

                entry = self.normalizer.normalize(
                    data=row_data,
                    raw=raw,
                    source_file=file_path,
                )
                entries.append(entry)

        return entries

    def _parse_columns(self, raw_columns: str) -> list[str]:
        columns = []
        for column in raw_columns.split(","):
            cleaned = column.strip().strip("`").strip('"').strip("'")
            if cleaned:
                columns.append(cleaned)
        return columns

    def _parse_value_groups(self, raw_values: str) -> list[str]:
        groups = []
        for match in self.VALUE_GROUP_REGEX.finditer(raw_values):
            group = match.group(1).strip()
            if group:
                groups.append(group)
        return groups

    def _split_sql_values(self, value_group: str) -> list[str]:
        values = []
        current = []
        in_quotes = False
        quote_char = ""

        i = 0
        while i < len(value_group):
            char = value_group[i]

            if char in {"'", '"'}:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif quote_char == char:
                    # Escaped quote like ''
                    if i + 1 < len(value_group) and value_group[i + 1] == char:
                        current.append(char)
                        i += 1
                    else:
                        in_quotes = False
                        quote_char = ""
                else:
                    current.append(char)

            elif char == "," and not in_quotes:
                values.append("".join(current).strip())
                current = []
            else:
                current.append(char)

            i += 1

        if current:
            values.append("".join(current).strip())

        return values

    def _clean_sql_value(self, value: str):
        cleaned = value.strip()

        if cleaned.upper() == "NULL":
            return None

        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
            cleaned = cleaned[1:-1]

        # numerische Konvertierung
        if cleaned.isdigit():
            try:
                return int(cleaned)
            except ValueError:
                return cleaned

        try:
            return float(cleaned)
        except ValueError:
            return cleaned