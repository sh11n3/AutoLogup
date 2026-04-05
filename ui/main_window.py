import json
from pathlib import Path
from xml.dom import minidom

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QAbstractItemView, QTextEdit,
    QSplitter, QPushButton, QComboBox, QToolButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics, QKeySequence, QShortcut, QColor, QBrush

from core.controller.app_controller import AppController
from core.services.log_service import LogService
from ui.components.file_loader import FileLoaderButton
from ui.components.highlight_delegate import HighlightDelegate


class MainWindow(QMainWindow):
    FILE_COLOR_THEMES = [
        ("#0b1f3a", "#12305a"),
        ("#0d2a1a", "#16402a"),
        ("#2a0d3a", "#40145a"),
        ("#3a1f0b", "#5a3212"),
        ("#3a0b0b", "#5a1212"),
        ("#0b3a3a", "#125a5a"),
        ("#2f2f2f", "#444444"),
    ]

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoLogUp")
        self.resize(1400, 900)

        self.controller = AppController(LogService())
        self.current_logs = []
        self.search_match_rows = []
        self.current_search_match_index = -1

        self.setup_ui()
        self.apply_styles()
        self.setup_shortcuts()

    def setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.file_loader = FileLoaderButton(self.on_files_loaded)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(
            "Filter (z.B. status=401 AND ip=1.1.1.1 | message~failed)"
        )
        self.filter_input.returnPressed.connect(self.apply_filter)

        self.filter_button = QPushButton("Filter")
        self.filter_button.clicked.connect(self.apply_filter)

        self.clear_filter_button = QPushButton("Clear")
        self.clear_filter_button.clicked.connect(self.clear_filter)

        top_container = QWidget()
        top_container.setObjectName("topContainer")

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 12, 12, 12)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.file_loader)
        top_bar.addWidget(self.filter_input)
        top_bar.addWidget(self.filter_button)
        top_bar.addWidget(self.clear_filter_button)
        top_container.setLayout(top_bar)

        self.search_container = QWidget()
        self.search_container.setObjectName("searchContainer")
        self.search_container.setVisible(False)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 10, 12, 10)
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in visible logs... (Ctrl+F)")
        self.search_input.textChanged.connect(self.on_search_text_changed)

        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Contains", "Exact"])
        self.search_mode_combo.currentIndexChanged.connect(self.on_search_mode_changed)

        self.search_prev_button = QToolButton()
        self.search_prev_button.setText("↑")
        self.search_prev_button.clicked.connect(self.goto_previous_search_match)

        self.search_next_button = QToolButton()
        self.search_next_button.setText("↓")
        self.search_next_button.clicked.connect(self.goto_next_search_match)

        self.search_result_label = QLabel("0")
        self.search_result_label.setObjectName("searchResultLabel")

        self.search_close_button = QToolButton()
        self.search_close_button.setText("✕")
        self.search_close_button.clicked.connect(self.close_search_bar)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_mode_combo)
        search_layout.addWidget(self.search_prev_button)
        search_layout.addWidget(self.search_next_button)
        search_layout.addWidget(self.search_result_label)
        search_layout.addWidget(self.search_close_button)

        self.search_container.setLayout(search_layout)

        self.table = QTableWidget(0, 1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Raw Log"])

        self.table.setTextElideMode(Qt.ElideNone)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Interactive)

        table_font = QFont("Consolas")
        table_font.setPointSize(10)
        self.table.setFont(table_font)

        self.highlight_delegate = HighlightDelegate(self.table)
        self.table.setItemDelegateForColumn(0, self.highlight_delegate)

        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)

        detail_container = QWidget()
        detail_container.setObjectName("detailContainer")

        detail_layout = QVBoxLayout()
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(8)

        self.detail_title = QLabel("Log Details")
        self.detail_title.setObjectName("detailTitle")

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setLineWrapMode(QTextEdit.NoWrap)

        detail_font = QFont("Consolas")
        detail_font.setPointSize(10)
        self.detail_text.setFont(detail_font)

        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_text)
        detail_container.setLayout(detail_layout)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(detail_container)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([520, 260])

        self.stats_label = QLabel("No data loaded")

        main_layout.addWidget(top_container)
        main_layout.addWidget(self.search_container)
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.stats_label)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def setup_shortcuts(self):
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self.open_search_bar)

        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.on_escape_pressed)

    def open_search_bar(self):
        self.search_container.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def close_search_bar(self):
        self.search_input.clear()
        self.search_container.setVisible(False)
        self.highlight_delegate.set_search("", "contains")
        self.search_match_rows = []
        self.current_search_match_index = -1
        self.search_result_label.setText("0")
        self.table.viewport().update()
        self.table.setFocus()

    def on_escape_pressed(self):
        if self.search_container.isVisible():
            self.close_search_bar()

    def on_search_text_changed(self, text):
        self.highlight_delegate.set_search(text, self._current_search_mode())
        self._rebuild_search_matches()
        self.table.viewport().update()

    def on_search_mode_changed(self, _index):
        self.highlight_delegate.set_search(self.search_input.text(), self._current_search_mode())
        self._rebuild_search_matches()
        self.table.viewport().update()

    def _current_search_mode(self) -> str:
        return "exact" if self.search_mode_combo.currentText() == "Exact" else "contains"

    def _rebuild_search_matches(self):
        self.search_match_rows = []
        self.current_search_match_index = -1

        search_text = self.search_input.text().strip()
        if not search_text:
            self.search_result_label.setText("0")
            return

        visible_logs = self.current_logs

        for row, log in enumerate(visible_logs):
            raw_text = log.raw if log.raw else ""
            if self.highlight_delegate.row_has_match(raw_text):
                self.search_match_rows.append(row)

        if self.search_match_rows:
            self.current_search_match_index = 0
            self._select_search_match(self.current_search_match_index)

        self._update_search_result_label()

    def _update_search_result_label(self):
        if not self.search_match_rows:
            self.search_result_label.setText("0")
            return

        self.search_result_label.setText(
            f"{self.current_search_match_index + 1}/{len(self.search_match_rows)}"
        )

    def goto_next_search_match(self):
        if not self.search_match_rows:
            return

        self.current_search_match_index += 1
        if self.current_search_match_index >= len(self.search_match_rows):
            self.current_search_match_index = 0

        self._select_search_match(self.current_search_match_index)
        self._update_search_result_label()

    def goto_previous_search_match(self):
        if not self.search_match_rows:
            return

        self.current_search_match_index -= 1
        if self.current_search_match_index < 0:
            self.current_search_match_index = len(self.search_match_rows) - 1

        self._select_search_match(self.current_search_match_index)
        self._update_search_result_label()

    def _select_search_match(self, match_index: int):
        if match_index < 0 or match_index >= len(self.search_match_rows):
            return

        row = self.search_match_rows[match_index]
        h_scroll = self.table.horizontalScrollBar().value()

        self.table.selectRow(row)
        self.table.scrollToItem(
            self.table.item(row, 0),
            QAbstractItemView.PositionAtCenter
        )

        self.table.horizontalScrollBar().setValue(h_scroll)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111827;
            }

            QWidget {
                color: #E5E7EB;
                font-size: 13px;
            }

            QWidget#topContainer {
                background-color: #1f2937;
                border-radius: 12px;
            }

            QWidget#searchContainer {
                background-color: #0f172a;
                border: 1px solid #2563EB;
                border-radius: 12px;
            }

            QWidget#detailContainer {
                background-color: #0f172a;
                border: 1px solid #374151;
                border-radius: 12px;
            }

            QLabel#detailTitle {
                color: #93C5FD;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#searchResultLabel {
                color: #93C5FD;
                font-weight: bold;
                min-width: 55px;
            }

            QPushButton {
                background-color: #1f2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                padding: 10px 16px;
                border-radius: 10px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563EB;
                color: white;
                border: 1px solid #3B82F6;
            }

            QPushButton:pressed {
                background-color: #1D4ED8;
                border: 1px solid #1D4ED8;
            }

            QToolButton {
                background-color: #1f2937;
                color: #E5E7EB;
                border: 1px solid #374151;
                padding: 6px 10px;
                border-radius: 8px;
                font-weight: bold;
                min-width: 26px;
            }

            QToolButton:hover {
                background-color: #2563EB;
                color: white;
                border: 1px solid #3B82F6;
            }

            QLineEdit {
                background-color: #1f2937;
                color: #E5E7EB;
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #374151;
            }

            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #111827;
            }

            QComboBox {
                background-color: #1f2937;
                color: #E5E7EB;
                padding: 8px 12px;
                border-radius: 10px;
                border: 1px solid #374151;
                min-width: 110px;
            }

            QComboBox:hover {
                border: 1px solid #3B82F6;
            }

            QAbstractItemView {
                background-color: #1f2937;
                color: #E5E7EB;
                selection-background-color: #2563EB;
                selection-color: white;
            }

            QTableWidget {
                background-color: #111827;
                border: 1px solid #374151;
                border-radius: 12px;
                selection-background-color: #2563EB;
                selection-color: white;
            }

            QHeaderView::section {
                background-color: #1f2937;
                color: #9CA3AF;
                padding: 8px;
                border: none;
                font-weight: bold;
            }

            QTextEdit {
                background-color: #020617;
                color: #E5E7EB;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 8px;
            }

            QSplitter::handle {
                background-color: #1f2937;
                height: 8px;
            }

            QScrollBar:horizontal {
                background: #1f2937;
                height: 14px;
                margin: 0px;
                border-radius: 7px;
            }

            QScrollBar::handle:horizontal {
                background: #2563EB;
                min-width: 30px;
                border-radius: 7px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #3B82F6;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }

            QScrollBar:vertical {
                background: #1f2937;
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #374151;
                min-height: 30px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical:hover {
                background: #4B5563;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            QLabel {
                color: #9CA3AF;
            }
        """)

    def on_files_loaded(self, file_paths):
        logs = self.controller.load_files(file_paths)
        self.current_logs = logs

        self.populate_table(logs)
        self.detail_text.clear()
        self.detail_text.setPlainText("Wähle eine Log-Zeile aus, um den vollständigen Inhalt zu sehen.")

        file_counts = self.controller.get_last_file_entry_counts()
        summary_parts = []
        total_entries = 0

        for path, count in file_counts.items():
            total_entries += count
            summary_parts.append(f"{Path(path).name}: {count}")

        summary_text = " | ".join(summary_parts) if summary_parts else "No parsed entries"
        self.stats_label.setText(
            f"Selected {len(file_paths)} files | Parsed entries: {total_entries} | {summary_text}"
        )

        self._rebuild_search_matches()

        if logs:
            first_log_row = self._first_actual_log_row()
            if first_log_row is not None:
                self.table.selectRow(first_log_row)

    def apply_filter(self):
        query = self.filter_input.text().strip()
        filtered_logs = self.controller.filter_logs(query)

        self.current_logs = filtered_logs
        self.populate_table(filtered_logs)

        self.detail_text.clear()
        self.detail_text.setPlainText("Wähle eine Log-Zeile aus, um den vollständigen Inhalt zu sehen.")
        self.stats_label.setText(
            f"Filtered: {len(filtered_logs)} / {len(self.controller.all_logs)} entries"
        )

        self._rebuild_search_matches()

        if filtered_logs:
            first_log_row = self._first_actual_log_row()
            if first_log_row is not None:
                self.table.selectRow(first_log_row)

    def clear_filter(self):
        self.filter_input.clear()
        self.current_logs = self.controller.all_logs
        self.populate_table(self.current_logs)

        self.detail_text.clear()
        self.detail_text.setPlainText("Wähle eine Log-Zeile aus, um den vollständigen Inhalt zu sehen.")
        self.stats_label.setText(
            f"Loaded {len(self.controller.all_logs)} entries"
        )

        self._rebuild_search_matches()

        if self.current_logs:
            first_log_row = self._first_actual_log_row()
            if first_log_row is not None:
                self.table.selectRow(first_log_row)

    def populate_table(self, logs):
        visible_logs = logs
        self.table.setRowCount(0)

        file_index_map = self._build_file_index_map(visible_logs)
        file_row_counter = {}

        last_source = None

        for log in visible_logs:
            source_file = log.source_file if log.source_file else ""

            if source_file != last_source:
                header_row = self.table.rowCount()
                self.table.insertRow(header_row)

                file_name = Path(source_file).name if source_file else "(unknown file)"
                header_item = QTableWidgetItem(f"=== FILE: {file_name} ===")
                header_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                header_item.setBackground(QBrush(QColor("#0b1220")))
                header_item.setForeground(QBrush(QColor("#93C5FD")))
                self.table.setItem(header_row, 0, header_item)

                last_source = source_file

            row = self.table.rowCount()
            self.table.insertRow(row)

            raw_text = log.raw if log.raw else ""
            item = QTableWidgetItem(raw_text)
            item.setToolTip(raw_text)

            # 👉 file_index korrekt setzen
            file_index = file_index_map.get(source_file, 0)

            # 👉 Farbe bestimmen
            color_palette = [
                "#3B82F6",  # blau
                "#22C55E",  # grün
                "#A855F7",  # violett
                "#F97316",  # orange
                "#EF4444",  # rot
                "#14B8A6",  # cyan
            ]

            file_color = color_palette[file_index % len(color_palette)]

            # 👉 an Delegate übergeben
            item.setData(Qt.UserRole, file_color)

            file_index = file_index_map.get(source_file, 0)
            row_in_file = file_row_counter.get(source_file, 0)

            bg_color = self._get_row_background_color(file_index, row_in_file)

            self.table.setItem(row, 0, item)

            file_row_counter[source_file] = row_in_file + 1

        self.table.resizeRowsToContents()
        self._update_log_column_width(visible_logs)
        self.table.viewport().update()

    def _first_actual_log_row(self):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and not item.text().startswith("=== FILE: "):
                return row
        return None

    def _build_file_index_map(self, logs):
        file_index_map = {}
        next_index = 0

        for log in logs:
            source_file = log.source_file if log.source_file else ""
            if source_file not in file_index_map:
                file_index_map[source_file] = next_index
                next_index += 1

        return file_index_map

    def _get_row_background_color(self, file_index: int, row_in_file: int) -> QColor:
        dark_color, light_color = self.FILE_COLOR_THEMES[file_index % len(self.FILE_COLOR_THEMES)]
        return QColor(light_color if row_in_file % 2 else dark_color)

    def on_table_selection_changed(self):
        selected_indexes = self.table.selectionModel().selectedRows()

        if not selected_indexes:
            self.detail_text.clear()
            return

        selected_row = selected_indexes[0].row()
        item = self.table.item(selected_row, 0)

        if item is None:
            self.detail_text.clear()
            return

        cell_text = item.text()
        if cell_text.startswith("=== FILE: "):
            self.detail_text.clear()
            return

        visible_logs = self.current_logs

        log_row_index = -1
        current_table_row = -1

        last_source = None
        for idx, log in enumerate(visible_logs):
            source_file = log.source_file if log.source_file else ""

            if source_file != last_source:
                current_table_row += 1
                last_source = source_file

            current_table_row += 1

            if current_table_row == selected_row:
                log_row_index = idx
                break

        if log_row_index == -1:
            self.detail_text.clear()
            return

        selected_log = visible_logs[log_row_index]
        source_file = selected_log.source_file if selected_log.source_file else ""

        detail_lines = []

        detail_lines.append("SOURCE FILE")
        detail_lines.append(source_file if source_file else "(unknown)")
        detail_lines.append("")

        detail_lines.append("NORMALIZED FIELDS")
        detail_lines.append(f"TIME    : {selected_log.timestamp}")
        detail_lines.append(f"USER    : {selected_log.username}")
        detail_lines.append(f"IP      : {selected_log.ip}")
        detail_lines.append(f"STATUS  : {selected_log.status}")
        detail_lines.append(f"METHOD  : {selected_log.method}")
        detail_lines.append(f"PATH    : {selected_log.path}")
        detail_lines.append(f"LEVEL   : {selected_log.level}")
        detail_lines.append(f"MESSAGE : {selected_log.message}")
        detail_lines.append("")

        detail_lines.append("EXTRA FIELDS")
        if selected_log.extra:
            for key in sorted(selected_log.extra.keys()):
                detail_lines.append(f"{key} : {selected_log.extra[key]}")
        else:
            detail_lines.append("(none)")
        detail_lines.append("")

        detail_lines.append("RAW")
        detail_lines.append(self._format_detail_text(selected_log.raw, source_file))

        self.detail_text.setPlainText("\n".join(detail_lines))

    def _update_log_column_width(self, logs):
        if not logs:
            self.table.setColumnWidth(0, 1200)
            return

        metrics = QFontMetrics(self.table.font())
        max_width = metrics.horizontalAdvance("=== FILE: EXAMPLE ===")

        for log in logs:
            raw_text = log.raw if log.raw else ""
            text_width = metrics.horizontalAdvance(raw_text)

            if text_width > max_width:
                max_width = text_width

        max_width += 40
        max_width = max(max_width, 1200)
        max_width = min(max_width, 50000)

        self.table.setColumnWidth(0, max_width)

    def _format_detail_text(self, raw_text: str, source_file: str) -> str:
        lower_source = source_file.lower()

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
            return raw_text

    def _pretty_xml(self, raw_text: str) -> str:
        try:
            parsed = minidom.parseString(raw_text.encode("utf-8"))
            pretty = parsed.toprettyxml(indent="    ")

            lines = []
            for line in pretty.splitlines():
                if line.strip():
                    lines.append(line)

            return "\n".join(lines)
        except Exception:
            return raw_text