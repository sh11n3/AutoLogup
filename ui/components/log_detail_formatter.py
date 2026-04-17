import json
from xml.dom import minidom


class LogDetailFormatter:
    def format_log_details(self, log) -> str:
        # Build the full text shown in the detail pane. The output is meant to
        # give a quick overview of normalized fields, any preserved extra fields,
        # and the raw payload in a readable order.
        source_file = log.source_file or ""

        detail_lines = [
            "SOURCE FILE",
            source_file if source_file else "(unknown)",
            "",
            "NORMALIZED FIELDS",
            f"TIME    : {log.timestamp}",
            f"USER    : {log.username}",
            f"IP      : {log.ip}",
            f"STATUS  : {log.status}",
            f"METHOD  : {log.method}",
            f"PATH    : {log.path}",
            f"LEVEL   : {log.level}",
            f"MESSAGE : {log.message}",
            "",
            "EXTRA FIELDS",
        ]

        if log.extra:
            for key in sorted(log.extra.keys()):
                detail_lines.append(f"{key} : {log.extra[key]}")
        else:
            detail_lines.append("(none)")

        detail_lines.extend([
            "",
            "RAW",
            self._format_raw_text(log.raw or "", source_file),
        ])

        return "\n".join(detail_lines)

    def _format_raw_text(self, raw_text: str, source_file: str) -> str:
        lower_source = source_file.lower()

        # Use the source file extension as a lightweight hint for whether the
        # raw payload should be pretty-printed.
        if lower_source.endswith(".json"):
            return self._pretty_json(raw_text)

        if lower_source.endswith(".xml"):
            return self._pretty_xml(raw_text)

        return raw_text

    def _pretty_json(self, raw_text: str) -> str:
        try:
            parsed = json.loads(raw_text)
            return json.dumps(parsed, indent=4, ensure_ascii=False)
        except Exception:
            # If the payload cannot be parsed as JSON, keep the original text
            # instead of hiding information from the user.
            return raw_text

    def _pretty_xml(self, raw_text: str) -> str:
        try:
            parsed = minidom.parseString(raw_text.encode("utf-8"))
            pretty = parsed.toprettyxml(indent="    ")
            lines = [line for line in pretty.splitlines() if line.strip()]
            return "\n".join(lines)
        except Exception:
            # Invalid or partial XML should still be shown as-is so the detail
            # view remains useful even for imperfect data.
            return raw_text
