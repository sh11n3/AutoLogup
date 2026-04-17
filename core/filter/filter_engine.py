import re
from datetime import datetime

from core.filter.query_parser import QueryParser
from core.models.log_entry import LogEntry


class FilterEngine:
    DATETIME_FORMATS = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    )

    def __init__(self):
        self.query_parser = QueryParser()

    def filter_logs(self, logs: list[LogEntry], query: str) -> list[LogEntry]:
        query = query.strip()

        if not query:
            return logs

        expression = self.query_parser.parse(query)

        if not expression:
            return logs

        result = []

        for log in logs:
            if self._matches(log, expression):
                result.append(log)

        return result

    def _matches(self, log: LogEntry, node: dict) -> bool:
        node_type = node.get("type")

        if node_type == "binary":
            operator = node["operator"]

            if operator == "AND":
                return self._matches(log, node["left"]) and self._matches(log, node["right"])

            if operator == "OR":
                return self._matches(log, node["left"]) or self._matches(log, node["right"])

            return False

        if node_type == "condition":
            return self._match_condition(log, node)

        return False

    def _match_condition(self, log: LogEntry, condition: dict) -> bool:
        field = condition["field"]
        operator = condition["operator"]
        expected_value = condition["value"]

        actual_value = self._get_field_value(log, field)

        if actual_value is None:
            return False

        if operator == "=":
            return self._compare_values(field, actual_value, expected_value) == 0

        if operator == "!=":
            return self._compare_values(field, actual_value, expected_value) != 0

        if operator == "contains":
            actual_str = str(actual_value).strip().lower()
            expected_str = str(expected_value).strip().lower()
            return expected_str in actual_str

        if operator == "startswith":
            actual_str = str(actual_value).strip().lower()
            expected_str = str(expected_value).strip().lower()
            return actual_str.startswith(expected_str)

        if operator == "regex":
            try:
                return re.search(expected_value, str(actual_value), re.IGNORECASE) is not None
            except re.error:
                return False

        if operator == ">":
            return self._compare_values(field, actual_value, expected_value) > 0

        if operator == ">=":
            return self._compare_values(field, actual_value, expected_value) >= 0

        if operator == "<":
            return self._compare_values(field, actual_value, expected_value) < 0

        if operator == "<=":
            return self._compare_values(field, actual_value, expected_value) <= 0

        return False

    def _get_field_value(self, log: LogEntry, field: str):
        field = field.strip().lower()

        if hasattr(log, field):
            return getattr(log, field)

        if field in log.extra:
            return log.extra[field]

        for extra_key, value in log.extra.items():
            normalized_key = str(extra_key).strip().lower()
            if normalized_key.endswith(f".{field}") or normalized_key.endswith(f"@{field}"):
                return value

        return None

    def _compare_values(self, field: str, actual_value, expected_value) -> int:
        actual_datetime = self._to_datetime(actual_value) if field == "timestamp" else None
        expected_datetime = self._to_datetime(expected_value) if field == "timestamp" else None

        if actual_datetime is not None and expected_datetime is not None:
            return self._compare_order(actual_datetime, expected_datetime)

        actual_number = self._to_number(actual_value)
        expected_number = self._to_number(expected_value)
        if actual_number is not None and expected_number is not None:
            return self._compare_order(actual_number, expected_number)

        actual_str = str(actual_value).strip().lower()
        expected_str = str(expected_value).strip().lower()
        return self._compare_order(actual_str, expected_str)

    def _compare_order(self, actual, expected) -> int:
        if actual < expected:
            return -1
        if actual > expected:
            return 1
        return 0

    def _to_number(self, value):
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None

    def _to_datetime(self, value):
        if isinstance(value, datetime):
            return value

        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass

        for datetime_format in self.DATETIME_FORMATS:
            try:
                return datetime.strptime(text, datetime_format)
            except ValueError:
                continue

        return None
