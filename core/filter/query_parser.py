class QueryParser:
    # Word-based operators are normalized so the filter engine only has to deal
    # with one internal operator name for each logical operation.
    WORD_OPERATORS = {
        "contains": "contains",
        "startswith": "startswith",
        "regex": "regex",
        "matches": "regex",
    }
    SYMBOL_OPERATORS = ("!=", ">=", "<=", "=", ">", "<", "~")

    def parse(self, query: str) -> dict | None:
        self.query = query.strip()
        self.length = len(self.query)
        self.position = 0

        if not self.query:
            return None

        expression = self._parse_or_expression()
        self._skip_whitespace()

        if expression is None or self.position != self.length:
            return None

        # Return a small expression tree that the filter engine can evaluate.
        # A failed parse returns None so invalid queries can safely fall back.
        return expression

    def _parse_or_expression(self) -> dict | None:
        # Parse OR at the top level so AND binds more strongly than OR.
        # That gives the usual boolean precedence without extra work in evaluation.
        left = self._parse_and_expression()
        if left is None:
            return None

        while self._match_keyword("OR"):
            right = self._parse_and_expression()
            if right is None:
                return None

            left = {
                "type": "binary",
                "operator": "OR",
                "left": left,
                "right": right,
            }

        return left

    def _parse_and_expression(self) -> dict | None:
        left = self._parse_primary()
        if left is None:
            return None

        while self._match_keyword("AND"):
            right = self._parse_primary()
            if right is None:
                return None

            left = {
                "type": "binary",
                "operator": "AND",
                "left": left,
                "right": right,
            }

        return left

    def _parse_primary(self) -> dict | None:
        self._skip_whitespace()

        if self._peek() == "(":
            # Parentheses start a nested expression and override the normal
            # boolean precedence for that part of the query.
            self.position += 1
            expression = self._parse_or_expression()
            self._skip_whitespace()

            if expression is None or self._peek() != ")":
                return None

            self.position += 1
            return expression

        return self._parse_condition()

    def _parse_condition(self) -> dict | None:
        field = self._parse_field()
        if not field:
            return None

        operator = self._parse_operator()
        if not operator:
            return None

        value = self._parse_value()
        if value is None:
            return None

        return {
            "type": "condition",
            "field": field.lower(),
            "operator": operator,
            "value": value,
        }

    def _parse_field(self) -> str | None:
        self._skip_whitespace()
        start = self.position

        while self.position < self.length:
            char = self.query[self.position]
            if char.isspace() or char in "()!<>=~":
                break
            self.position += 1

        field = self.query[start:self.position].strip()
        return field or None

    def _parse_operator(self) -> str | None:
        self._skip_whitespace()

        # Check symbol operators first so longer operators such as ">=" or "!="
        # are matched before their shorter prefixes.
        for operator in self.SYMBOL_OPERATORS:
            if self.query.startswith(operator, self.position):
                self.position += len(operator)
                return "contains" if operator == "~" else operator

        word = self._parse_word()
        if not word:
            return None

        normalized = self.WORD_OPERATORS.get(word.lower())
        if normalized is None:
            return None

        return normalized

    def _parse_value(self) -> str | None:
        self._skip_whitespace()
        if self.position >= self.length:
            return None

        if self._peek() in {'"', "'"}:
            # Quoted values can contain spaces, regex characters, and words that
            # would otherwise look like boolean operators.
            return self._parse_quoted_value()

        start = self.position

        while self.position < self.length:
            char = self.query[self.position]

            if char == ")":
                break

            if char.isspace():
                checkpoint = self.position
                self._skip_whitespace()

                # Stop only when the following token clearly begins a boolean
                # operator or a closing parenthesis.
                if self._is_boolean_operator_boundary() or self._peek() == ")":
                    self.position = checkpoint
                    break

                continue

            self.position += 1

        value = self.query[start:self.position].strip()
        return value or None

    def _parse_quoted_value(self) -> str | None:
        quote = self._peek()
        self.position += 1
        chars = []

        while self.position < self.length:
            char = self.query[self.position]

            if char == "\\" and self.position + 1 < self.length:
                # Keep escape handling intentionally simple so quoted regexes
                # and embedded quotes can still be written inline.
                self.position += 1
                chars.append(self.query[self.position])
                self.position += 1
                continue

            if char == quote:
                self.position += 1
                return "".join(chars)

            chars.append(char)
            self.position += 1

        return None

    def _parse_word(self) -> str:
        start = self.position

        while self.position < self.length and self.query[self.position].isalpha():
            self.position += 1

        return self.query[start:self.position]

    def _match_keyword(self, keyword: str) -> bool:
        self._skip_whitespace()
        end = self.position + len(keyword)
        segment = self.query[self.position:end]

        if segment.upper() != keyword:
            return False

        if self.position > 0 and not self.query[self.position - 1].isspace() and self.query[self.position - 1] != "(":
            return False

        if end < self.length and not self.query[end].isspace() and self.query[end] != "(":
            return False

        self.position = end
        return True

    def _is_boolean_operator_boundary(self) -> bool:
        for keyword in ("AND", "OR"):
            end = self.position + len(keyword)
            segment = self.query[self.position:end]

            if segment.upper() != keyword:
                continue

            if end == self.length or self.query[end].isspace() or self.query[end] == "(":
                return True

        return False

    def _skip_whitespace(self):
        while self.position < self.length and self.query[self.position].isspace():
            self.position += 1

    def _peek(self) -> str | None:
        if self.position >= self.length:
            return None

        return self.query[self.position]
