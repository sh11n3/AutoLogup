from core.models.log_entry import LogEntry
from core.filter.query_parser import QueryParser


class FilterEngine:
    def __init__(self):
        self.query_parser = QueryParser()

    def filter_logs(self, logs: list[LogEntry], query: str) -> list[LogEntry]:
        query = query.strip()

        if not query:
            return logs

        conditions, operators = self.query_parser.parse(query)

        if not conditions:
            return logs

        result = []

        for log in logs:
            if self._matches(log, conditions, operators):
                result.append(log)

        return result

    def _matches(self, log: LogEntry, conditions: list[dict], operators: list[str]) -> bool:
        evaluations = [self._match_condition(log, condition) for condition in conditions]

        if not evaluations:
            return True

        result = evaluations[0]

        for index, operator in enumerate(operators):
            if index + 1 >= len(evaluations):
                break

            if operator == "AND":
                result = result and evaluations[index + 1]
            elif operator == "OR":
                result = result or evaluations[index + 1]

        return result

    def _match_condition(self, log: LogEntry, condition: dict) -> bool:
        field = condition["field"]
        expected_value = condition["value"]

        actual_value = self._get_field_value(log, field)

        if actual_value is None:
            return False

        # numerische Felder exakt vergleichen
        if isinstance(actual_value, int):
            try:
                return actual_value == int(expected_value)
            except ValueError:
                return False

        # Strings: exakter Vergleich, aber case-insensitive
        actual_str = str(actual_value).strip().lower()
        expected_str = str(expected_value).strip().lower()

        return actual_str == expected_str

    def _get_field_value(self, log: LogEntry, field: str):
        field = field.strip().lower()

        if hasattr(log, field):
            return getattr(log, field)

        if field in log.extra:
            return log.extra[field]

        return None