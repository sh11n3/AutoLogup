class QueryParser:
    def parse(self, query: str) -> tuple[list[dict], list[str]]:
        query = query.strip()

        if not query:
            return [], []

        tokens = query.split()
        conditions = []
        operators = []

        current_parts = []

        for token in tokens:
            upper = token.upper()

            if upper in {"AND", "OR"}:
                if current_parts:
                    condition = self._parse_condition(" ".join(current_parts))
                    if condition:
                        conditions.append(condition)
                    current_parts = []

                operators.append(upper)
            else:
                current_parts.append(token)

        if current_parts:
            condition = self._parse_condition(" ".join(current_parts))
            if condition:
                conditions.append(condition)

        return conditions, operators

    def _parse_condition(self, text: str) -> dict | None:
        text = text.strip()

        if "~" in text:
            field, value = text.split("~", 1)
            operator = "~"
        elif "=" in text:
            field, value = text.split("=", 1)
            operator = "="
        else:
            return None

        field = field.strip().lower()
        value = value.strip()

        if not field:
            return None

        return {
            "field": field,
            "operator": operator,
            "value": value,
        }