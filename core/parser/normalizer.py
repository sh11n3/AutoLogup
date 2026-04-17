from core.models.log_entry import LogEntry


class Normalizer:
    # These key sets define how source-specific field names are mapped onto the
    # shared LogEntry structure used everywhere else in the app.
    USERNAME_KEYS = {"username", "user", "login", "account", "userid", "user_id"}
    IP_KEYS = {"ip", "ip_address", "client_ip", "source_ip", "src_ip", "remote_addr"}
    STATUS_KEYS = {"status", "status_code", "code", "response_code"}
    METHOD_KEYS = {"method", "http_method", "verb"}
    PATH_KEYS = {"path", "url", "uri", "endpoint", "route", "request_path"}
    LEVEL_KEYS = {"level", "severity", "log_level"}
    MESSAGE_KEYS = {"message", "msg", "event", "description", "details"}
    TIMESTAMP_KEYS = {"timestamp", "time", "datetime", "date", "created_at"}

    def normalize(self, data: dict, raw: str, source_file: str) -> LogEntry:
        # Normalize incoming keys once up front so all later lookups become
        # case-insensitive and consistent across different source formats.
        lowered = {str(k).strip().lower(): v for k, v in data.items()}

        timestamp = self._to_str(self._find_best_value(lowered, self.TIMESTAMP_KEYS))
        username = self._to_str(self._find_best_value(lowered, self.USERNAME_KEYS))
        ip = self._to_str(self._find_best_value(lowered, self.IP_KEYS))
        status = self._to_status_str(self._find_best_value(lowered, self.STATUS_KEYS))
        method = self._to_str(self._find_best_value(lowered, self.METHOD_KEYS)).upper()
        path = self._to_str(self._find_best_value(lowered, self.PATH_KEYS))
        level = self._to_level_str(self._find_best_value(lowered, self.LEVEL_KEYS))
        message = self._to_message(lowered, raw)

        entry = LogEntry(
            timestamp=timestamp,
            username=username,
            ip=ip,
            status=status,
            method=method,
            path=path,
            level=level,
            message=message,
            raw=raw or "",
            source_file=source_file or "",
            extra=self._build_extra(lowered),
        )

        return entry

    def _find_best_value(self, data: dict, keys: set[str]):
        # Try exact matches first, then fall back to flattened nested suffixes.
        # That allows keys such as "user", "username", or "event.user" to feed
        # the same normalized target field.
        # First prefer an exact key match.
        for key in keys:
            if key in data:
                return data[key]

        # Then allow suffix matches for flattened keys such as event.ip or log.user.
        for data_key, value in data.items():
            for key in keys:
                if data_key.endswith(f".{key}") or data_key.endswith(f"@{key}") or data_key == key:
                    return value

        return None

    def _to_str(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _to_status_str(self, value) -> str:
        if value is None:
            return ""

        try:
            return str(int(value))
        except (ValueError, TypeError):
            return str(value).strip()

    def _to_level_str(self, value) -> str:
        if value is None:
            return ""

        level = str(value).strip().upper()
        # Normalize common synonyms so grouping and filtering do not split
        # values such as WARN and WARNING into separate buckets.
        if level == "WARNING":
            return "WARN"
        return level

    def _to_message(self, data: dict, raw: str) -> str:
        message_value = self._find_best_value(data, self.MESSAGE_KEYS)
        if message_value is not None:
            return str(message_value).strip()

        return raw or ""

    def _build_extra(self, data: dict) -> dict:
        # Keep every field that was not mapped into a fixed LogEntry attribute.
        # This lets the UI still expose source-specific values for filtering,
        # grouping, and inspection.
        known_keys = (
            self.TIMESTAMP_KEYS
            | self.USERNAME_KEYS
            | self.IP_KEYS
            | self.STATUS_KEYS
            | self.METHOD_KEYS
            | self.PATH_KEYS
            | self.LEVEL_KEYS
            | self.MESSAGE_KEYS
        )

        extra = {}

        for key, value in data.items():
            if self._is_known_key(key, known_keys):
                continue
            extra[key] = value

        return extra

    def _is_known_key(self, key: str, known_keys: set[str]) -> bool:
        # Flattened keys that end in a known field name should not be copied
        # into `extra`, because they already contributed to a normalized field.
        if key in known_keys:
            return True

        for known_key in known_keys:
            if key.endswith(f".{known_key}") or key.endswith(f"@{known_key}"):
                return True

        return False
