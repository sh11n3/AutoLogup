from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QListWidget,
    QListWidgetItem, QToolButton
)
from PySide6.QtCore import Qt


class GroupWindow(QWidget):
    def __init__(self, logs, on_group_selected):
        super().__init__()

        # The parent window passes in the currently visible logs together with
        # a callback that should be triggered once the user picks one group.
        self.on_group_selected = on_group_selected
        self.setWindowTitle("Grouping")
        self.resize(400, 600)

        self.logs = logs

        self.setup_ui()

    def setup_ui(self):
        # Keep the grouping dialog intentionally simple: field selector on top,
        # grouped values below, and a minimal header for closing the dialog.
        layout = QVBoxLayout()
        layout.setSpacing(10)

        top_bar = QHBoxLayout()

        title = QLabel("Group Logs")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        close_btn = QToolButton()
        close_btn.setText("âœ•")
        close_btn.clicked.connect(self.close)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)

        # Changing the selected field rebuilds the grouped value list below.
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self.update_grouping)

        # Each list item represents one distinct field value with its count.
        self.list_widget = QListWidget()

        layout.addLayout(top_bar)
        layout.addWidget(self.combo)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)
        self.list_widget.itemClicked.connect(self.on_item_clicked)

        self.load_fields()

    def load_fields(self):
        # Build the list of fields the user can group by. This includes the
        # normalized built-in fields and every dynamic field found in `extra`.
        fields = set()

        for log in self.logs:
            # Always expose the standard normalized fields, even if some of
            # them happen to be empty in the current dataset.
            fields.update([
                "timestamp", "username", "ip",
                "status", "method", "path", "level"
            ])

            # Dynamic fields are preserved during normalization and should be
            # available for grouping as well.
            if log.extra:
                fields.update(log.extra.keys())

        self.combo.addItems(sorted(fields))

        self.update_grouping()

    def update_grouping(self):
        field = self.combo.currentText()

        grouped = defaultdict(int)

        # Count how many visible logs share the same value for the chosen field.
        for log in self.logs:
            value = self.get_value(log, field)
            grouped[value] += 1

        self.list_widget.clear()

        # Sort by frequency so the most relevant groups appear first.
        sorted_items = sorted(grouped.items(), key=lambda x: x[1], reverse=True)

        for value, count in sorted_items:
            item = QListWidgetItem(f"{value} ({count})")
            self.list_widget.addItem(item)

    def get_value(self, log, field):
        # Prefer normalized attributes first because they are the canonical
        # fields used throughout the rest of the application.
        if hasattr(log, field):
            val = getattr(log, field)
            return val if val else "(empty)"

        if log.extra and field in log.extra:
            return log.extra[field]

        return "(empty)"

    def on_item_clicked(self, item):
        # The visible label contains both the raw value and the count, so split
        # the value back out before handing it to the callback.
        text = item.text()
        value = text.rsplit("(", 1)[0].strip()
        field = self.combo.currentText()

        if self.on_group_selected:
            self.on_group_selected(field, value)

        self.close()
