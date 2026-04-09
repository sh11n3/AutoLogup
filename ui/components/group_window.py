from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QListWidget,
    QListWidgetItem, QToolButton
)
from PySide6.QtCore import Qt


class GroupWindow(QWidget):
    def __init__(self, logs):
        super().__init__()

        self.setWindowTitle("Grouping")
        self.resize(400, 600)

        self.logs = logs

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 🔹 Top Bar
        top_bar = QHBoxLayout()

        title = QLabel("Group Logs")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.clicked.connect(self.close)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)

        # 🔹 Dropdown
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self.update_grouping)

        # 🔹 Liste
        self.list_widget = QListWidget()

        layout.addLayout(top_bar)
        layout.addWidget(self.combo)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        self.load_fields()

    # 🔥 dynamische Felder erkennen
    def load_fields(self):
        fields = set()

        for log in self.logs:
            # bekannte Felder
            fields.update([
                "timestamp", "username", "ip",
                "status", "method", "path", "level"
            ])

            # dynamische Felder
            if log.extra:
                fields.update(log.extra.keys())

        self.combo.addItems(sorted(fields))

        self.update_grouping()

    def update_grouping(self):
        field = self.combo.currentText()

        grouped = defaultdict(int)

        for log in self.logs:
            value = self.get_value(log, field)
            grouped[value] += 1

        self.list_widget.clear()

        # sortieren nach count DESC
        sorted_items = sorted(grouped.items(), key=lambda x: x[1], reverse=True)

        for value, count in sorted_items:
            item = QListWidgetItem(f"{value} ({count})")
            self.list_widget.addItem(item)

    def get_value(self, log, field):
        # bekannte Felder
        if hasattr(log, field):
            val = getattr(log, field)
            return val if val else "(empty)"

        # extra Felder
        if log.extra and field in log.extra:
            return log.extra[field]

        return "(empty)"