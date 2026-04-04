import json
from xml.dom import minidom

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QAbstractItemView, QTextEdit,
    QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics

from core.controller.app_controller import AppController
from core.services.log_service import LogService
from ui.components.file_loader import FileLoaderButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoLogUp")
        self.resize(1400, 900)

        self.controller = AppController(LogService())
        self.current_logs = []

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.file_loader = FileLoaderButton(self.on_files_loaded)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText(
            "Filter (z.B. status=401 AND ip=1.1.1.1)"
        )

        top_container = QWidget()
        top_container.setObjectName("topContainer")

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 12, 12, 12)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.file_loader)
        top_bar.addWidget(self.filter_input)
        top_container.setLayout(top_bar)

        self.table = QTableWidget(0, 1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Log"])

        self.table.setTextElideMode(Qt.ElideNone)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.table.setAlternatingRowColors(True)
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
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.stats_label)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

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

            QTableWidget {
                background-color: #111827;
                alternate-background-color: #1f2937;
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
        self.stats_label.setText(
            f"Loaded {len(file_paths)} files, {len(logs)} entries"
        )

        if logs:
            self.table.selectRow(0)

    def populate_table(self, logs):
        visible_logs = logs[:500]
        self.table.setRowCount(0)

        for log in visible_logs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            raw_text = log.raw if log.raw else ""
            item = QTableWidgetItem(raw_text)
            item.setToolTip(raw_text)
            self.table.setItem(row, 0, item)

        self.table.resizeRowsToContents()
        self._update_log_column_width(visible_logs)

    def on_table_selection_changed(self):
        selected_indexes = self.table.selectionModel().selectedRows()

        if not selected_indexes:
            self.detail_text.clear()
            return

        row = selected_indexes[0].row()
        visible_logs = self.current_logs[:500]

        if row < 0 or row >= len(visible_logs):
            self.detail_text.clear()
            return

        selected_log = visible_logs[row]
        full_text = selected_log.raw if selected_log.raw else ""
        source_file = selected_log.source_file if selected_log.source_file else ""

        formatted_text = self._format_detail_text(full_text, source_file)
        self.detail_text.setPlainText(formatted_text)

    def _update_log_column_width(self, logs):
        if not logs:
            self.table.setColumnWidth(0, 1200)
            return

        metrics = QFontMetrics(self.table.font())
        max_width = 0

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