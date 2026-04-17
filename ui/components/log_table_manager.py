from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QTableWidgetItem

from ui.components.highlight_delegate import HighlightDelegate


class LogTableManager:
    FILE_HEADER_PREFIX = "=== FILE: "

    # Rotate row colors by source file so mixed datasets remain visually readable
    # without needing multiple tabs or separate tables.
    FILE_COLOR_THEMES = [
        ("#0b1830", "#132445", "#3b82f6"),
        ("#0d2416", "#153520", "#22c55e"),
        ("#221033", "#34184d", "#a855f7"),
        ("#301a0b", "#452613", "#f97316"),
        ("#2d0f14", "#45161f", "#ef4444"),
        ("#0d2628", "#15383b", "#14b8a6"),
    ]

    def __init__(self, table):
        self.table = table
        # These lookup maps hide the fact that the visible table contains extra
        # synthetic header rows that do not correspond to real log entries.
        self.row_to_log_index = {}
        self.log_index_to_row = {}

    def populate_table(self, logs):
        visible_logs = logs or []

        # Rebuild the visible table from scratch every time the dataset changes.
        # This keeps grouping, filtering, and file headers in sync in one place.
        self.row_to_log_index = {}
        self.log_index_to_row = {}
        self.table.setRowCount(0)

        file_index_map = self._build_file_index_map(visible_logs)
        file_row_counter = {}
        last_source = None

        for log_index, log in enumerate(visible_logs):
            source_file = log.source_file or ""

            # Insert a synthetic file header row whenever the visible source file
            # changes while walking the dataset.
            if source_file != last_source:
                header_row = self.table.rowCount()
                self.table.insertRow(header_row)
                self.table.setItem(header_row, 0, self._create_header_item(source_file))
                last_source = source_file

            row = self.table.rowCount()
            self.table.insertRow(row)

            row_in_file = file_row_counter.get(source_file, 0)
            file_index = file_index_map.get(source_file, 0)
            item = self._create_log_item(log.raw or "", file_index, row_in_file)

            self.table.setItem(row, 0, item)
            self.row_to_log_index[row] = log_index
            self.log_index_to_row[log_index] = row
            file_row_counter[source_file] = row_in_file + 1

        self.table.resizeRowsToContents()
        self._update_log_column_width(visible_logs)
        self.table.viewport().update()

    def first_actual_log_row(self):
        # Return the first real data row, not one of the synthetic file headers.
        for row in range(self.table.rowCount()):
            if row in self.row_to_log_index:
                return row
        return None

    def get_log_for_row(self, row: int, logs):
        log_index = self.row_to_log_index.get(row)
        if log_index is None or log_index >= len(logs):
            return None
        return logs[log_index]

    def get_row_for_log_index(self, log_index: int):
        return self.log_index_to_row.get(log_index)

    def _create_header_item(self, source_file: str):
        # Header rows exist only for readability in the table and should never
        # be treated like real log entries.
        file_name = Path(source_file).name if source_file else "(unknown file)"
        item = QTableWidgetItem(f"{self.FILE_HEADER_PREFIX}{file_name} ===")
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setData(HighlightDelegate.BG_ROLE, "#1e293b")
        item.setData(HighlightDelegate.STRIPE_ROLE, "#93c5fd")
        return item

    def _create_log_item(self, raw_text: str, file_index: int, row_in_file: int):
        # Use alternating shades inside one file and a stable accent color per
        # file group to make long mixed tables easier to scan.
        item = QTableWidgetItem(raw_text)
        item.setToolTip(raw_text)

        dark_bg, light_bg, stripe = self.FILE_COLOR_THEMES[file_index % len(self.FILE_COLOR_THEMES)]
        row_bg = light_bg if row_in_file % 2 else dark_bg

        item.setData(HighlightDelegate.BG_ROLE, row_bg)
        item.setData(HighlightDelegate.STRIPE_ROLE, stripe)
        return item

    def _build_file_index_map(self, logs):
        # Assign each visible source file a stable color index for the current
        # render pass of the table.
        file_index_map = {}
        next_index = 0

        for log in logs:
            source_file = log.source_file or ""
            if source_file not in file_index_map:
                file_index_map[source_file] = next_index
                next_index += 1

        return file_index_map

    def _update_log_column_width(self, logs):
        if not logs:
            self.table.setColumnWidth(0, 1200)
            return

        # Size the raw-log column from the widest visible entry, but clamp it to
        # a reasonable range so very long rows do not make the table unusable.
        metrics = QFontMetrics(self.table.font())
        max_width = metrics.horizontalAdvance(f"{self.FILE_HEADER_PREFIX}EXAMPLE ===")

        for log in logs:
            text_width = metrics.horizontalAdvance(log.raw or "")
            if text_width > max_width:
                max_width = text_width

        max_width += 40
        max_width = max(max_width, 1200)
        max_width = min(max_width, 50000)

        self.table.setColumnWidth(0, max_width)
