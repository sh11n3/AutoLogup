from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.controller.app_controller import AppController
from core.services.log_service import LogService
from ui.components.file_loader import FileLoaderButton
from ui.components.group_window import GroupWindow
from ui.components.highlight_delegate import HighlightDelegate
from ui.components.log_detail_formatter import LogDetailFormatter
from ui.components.log_table_manager import LogTableManager
from ui.components.search_manager import SearchManager


class MainWindow(QMainWindow):
    DEFAULT_DETAIL_TEXT = "Waehle eine Log-Zeile aus, um den vollstaendigen Inhalt zu sehen."

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AutoLogUp")
        self.resize(1400, 900)

        self.controller = AppController(LogService())
        self.current_logs = []

        self.setup_ui()
        self.table_manager = LogTableManager(self.table)
        self.detail_formatter = LogDetailFormatter()
        self.search_manager = SearchManager(
            table=self.table,
            table_manager=self.table_manager,
            search_container=self.search_container,
            search_input=self.search_input,
            search_mode_combo=self.search_mode_combo,
            search_result_label=self.search_result_label,
            highlight_delegate=self.highlight_delegate,
        )
        self._connect_search_signals()
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

        self.group_button = QPushButton("Group")
        self.group_button.clicked.connect(self.open_group_window)

        top_container = QWidget()
        top_container.setObjectName("topContainer")

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 12, 12, 12)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.file_loader)
        top_bar.addWidget(self.filter_input)
        top_bar.addWidget(self.filter_button)
        top_bar.addWidget(self.clear_filter_button)
        top_bar.addWidget(self.group_button)
        top_container.setLayout(top_bar)

        self.search_container = QWidget()
        self.search_container.setObjectName("searchContainer")
        self.search_container.setVisible(False)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 10, 12, 10)
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in visible logs... (Ctrl+F)")

        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["Contains", "Exact"])

        self.search_prev_button = QToolButton()
        self.search_prev_button.setText("Prev")

        self.search_next_button = QToolButton()
        self.search_next_button.setText("Next")

        self.search_result_label = QLabel("0")
        self.search_result_label.setObjectName("searchResultLabel")

        self.search_close_button = QToolButton()
        self.search_close_button.setText("X")

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
        self._reset_detail_panel()

    def _connect_search_signals(self):
        self.search_input.textChanged.connect(self.search_manager.on_search_text_changed)
        self.search_mode_combo.currentIndexChanged.connect(self.search_manager.on_search_mode_changed)
        self.search_prev_button.clicked.connect(self.search_manager.goto_previous_search_match)
        self.search_next_button.clicked.connect(self.search_manager.goto_next_search_match)
        self.search_close_button.clicked.connect(self.search_manager.close_search_bar)

    def setup_shortcuts(self):
        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self.search_manager.open_search_bar)

        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.search_manager.on_escape_pressed)

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

        file_counts = self.controller.get_last_file_entry_counts()
        summary_parts = []
        total_entries = 0

        for path, count in file_counts.items():
            total_entries += count
            summary_parts.append(f"{Path(path).name}: {count}")

        summary_text = " | ".join(summary_parts) if summary_parts else "No parsed entries"
        stats_text = (
            f"Selected {len(file_paths)} files | Parsed entries: {total_entries} | {summary_text}"
        )
        self._show_logs(logs, stats_text)

    def apply_filter(self):
        query = self.filter_input.text().strip()
        filtered_logs = self.controller.filter_logs(query)
        stats_text = (
            f"Filtered: {len(filtered_logs)} / {len(self.controller.all_logs)} entries"
        )
        self._show_logs(filtered_logs, stats_text)

    def clear_filter(self):
        self.filter_input.clear()
        stats_text = f"Loaded {len(self.controller.all_logs)} entries"
        self._show_logs(self.controller.all_logs, stats_text)

    def _show_logs(self, logs, stats_text: str):
        self.current_logs = logs
        self.table_manager.populate_table(logs)
        self._reset_detail_panel()
        self.stats_label.setText(stats_text)
        self.search_manager.set_visible_logs(logs)
        self._select_first_log_row()

    def _reset_detail_panel(self):
        self.detail_text.clear()
        self.detail_text.setPlainText(self.DEFAULT_DETAIL_TEXT)

    def _select_first_log_row(self):
        first_log_row = self.table_manager.first_actual_log_row()
        if first_log_row is not None:
            self.table.selectRow(first_log_row)

    def on_table_selection_changed(self):
        selected_indexes = self.table.selectionModel().selectedRows()

        if not selected_indexes:
            self.detail_text.clear()
            return

        selected_row = selected_indexes[0].row()
        selected_log = self.table_manager.get_log_for_row(selected_row, self.current_logs)
        if selected_log is None:
            self.detail_text.clear()
            return

        self.detail_text.setPlainText(
            self.detail_formatter.format_log_details(selected_log)
        )

    def open_group_window(self):
        if not self.current_logs:
            return

        self.group_window = GroupWindow(
            self.current_logs,
            self.apply_group_filter,
        )
        self.group_window.show()

    def apply_group_filter(self, field, value):
        filtered = []

        for log in self.controller.all_logs:
            val = None

            if hasattr(log, field):
                val = getattr(log, field)
            elif log.extra and field in log.extra:
                val = log.extra[field]

            val = str(val) if val else "(empty)"

            if val == value:
                filtered.append(log)

        self._show_logs(
            filtered,
            f"Grouped by {field} = {value} -> {len(filtered)} entries",
        )
