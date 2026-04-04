from core.models.log_entry import LogEntry


class Normalizer:
    USERNAME_KEYS = {"username", "user", "login", "account", "userid", "user_id"}
    IP_KEYS = {"ip", "ip_address", "client_ip", "source_ip", "src_ip", "remote_addr"}
    STATUS_KEYS = {"status", "status_code", "code", "response_code"}
    METHOD_KEYS = {"method", "http_method", "verb"}
    PATH_KEYS = {"path", "url", "uri", "endpoint", "route", "request_path"}
    LEVEL_KEYS = {"level", "severity", "log_level"}
    MESSAGE_KEYS = {"message", "msg", "event", "description", "details"}
    TIMESTAMP_KEYS = {"timestamp", "time", "datetime", "date", "created_at"}

    def normalize(self, data: dict, raw: str, source_file: str) -> LogEntry:
        lowered = {str(k).strip().lower(): v for k, v in data.items()}

        entry = LogEntry(
            timestamp=self._find_first(lowered, self.TIMESTAMP_KEYS),
            username=self._to_str(self._find_first(lowered, self.USERNAME_KEYS)),
            ip=self._to_str(self._find_first(lowered, self.IP_KEYS)),
            status=self._to_int(self._find_first(lowered, self.STATUS_KEYS)),
            method=self._to_str(self._find_first(lowered, self.METHOD_KEYS)),
            path=self._to_str(self._find_first(lowered, self.PATH_KEYS)),
            level=self._to_str(self._find_first(lowered, self.LEVEL_KEYS)),
            message=self._to_str(self._find_first(lowered, self.MESSAGE_KEYS)),
            raw=raw,
            source_file=source_file,
            extra=self._build_extra(lowered),
        )

        return entry

    def _find_first(self, data: dict, keys: set[str]):
        for key in keys:
            if key in data:
                return data[key]
        return None

    def _to_str(self, value):
        if value is None:
            return None
        return str(value)

    def _to_int(self, value):
        if value is None:
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _build_extra(self, data: dict) -> dict:
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
            if key not in known_keys:
                extra[key] = value

        return extra