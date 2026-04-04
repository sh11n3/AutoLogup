from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QAbstractItemView
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
        self.resize(1400, 850)

        self.controller = AppController(LogService())

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
        top_container.setStyleSheet("""
            QWidget {
                background-color: #1f2937;
                border-radius: 12px;
            }
        """)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 12, 12, 12)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.file_loader)
        top_bar.addWidget(self.filter_input)
        top_container.setLayout(top_bar)

        self.table = QTableWidget(0, 1)
        self.table.clear()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Log"])

        # Kein ...
        self.table.setTextElideMode(Qt.ElideNone)

        # Keine Umbrüche
        self.table.setWordWrap(False)

        # Scrollen
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Verhalten
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Header
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Interactive)

        # Monospace-Font für Logs
        font = QFont("Consolas")
        font.setPointSize(10)
        self.table.setFont(font)

        # Startbreite
        self.table.setColumnWidth(0, 2000)

        self.stats_label = QLabel("No data loaded")

        main_layout.addWidget(top_container)
        main_layout.addWidget(self.table)
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
                border-radius: 12px;
                gridline-color: #374151;
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

        self.populate_table(logs)
        self.stats_label.setText(
            f"Loaded {len(file_paths)} files, {len(logs)} entries"
        )

    def populate_table(self, logs):
        self.table.setRowCount(0)

        for log in logs[:500]:
            row = self.table.rowCount()
            self.table.insertRow(row)

            raw_text = log.raw if log.raw else ""
            log_item = QTableWidgetItem(raw_text)
            self.table.setItem(row, 0, log_item)

        self.table.resizeRowsToContents()
        self._update_log_column_width(logs[:500])

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

        # etwas Puffer dazu
        max_width += 40

        # harte Obergrenze gegen extreme Ausreißer
        max_width = min(max_width, 20000)

        # sinnvolle Mindestbreite
        max_width = max(max_width, 1200)

        self.table.setColumnWidth(0, max_width)