import re

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyle


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.search_mode = "contains"  # "contains" | "exact"

    def set_search(self, search_text: str, search_mode: str):
        self.search_text = search_text or ""
        self.search_mode = search_mode or "contains"

    def paint(self, painter: QPainter, option, index):
        text = index.data(Qt.DisplayRole)
        if text is None:
            text = ""

        painter.save()

        style = option.widget.style() if option.widget else None
        if style:
            style.drawPrimitive(QStyle.PE_PanelItemViewItem, option, painter, option.widget)

        text_rect = option.rect.adjusted(6, 0, -6, 0)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            default_text_color = option.palette.highlightedText().color()
        else:
            default_text_color = option.palette.text().color()

        if not self.search_text.strip():
            painter.setPen(default_text_color)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.TextSingleLine, text)
            painter.restore()
            return

        matches = self._find_matches(text, self.search_text, self.search_mode)

        if not matches:
            painter.setPen(default_text_color)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.TextSingleLine, text)
            painter.restore()
            return

        font_metrics = QFontMetrics(option.font)
        x = text_rect.x()
        baseline_y = text_rect.y() + (text_rect.height() + font_metrics.ascent() - font_metrics.descent()) // 2

        highlight_bg = QColor("#FACC15")
        highlight_fg = QColor("#111827")

        current_pos = 0

        for start, end in matches:
            if start > current_pos:
                normal_text = text[current_pos:start]
                painter.setPen(default_text_color)
                painter.drawText(x, baseline_y, normal_text)
                x += font_metrics.horizontalAdvance(normal_text)

            matched_text = text[start:end]
            match_width = font_metrics.horizontalAdvance(matched_text)

            highlight_rect = QRect(
                x,
                text_rect.y() + 4,
                match_width,
                text_rect.height() - 8
            )
            painter.fillRect(highlight_rect, highlight_bg)
            painter.setPen(highlight_fg)
            painter.drawText(x, baseline_y, matched_text)
            x += match_width

            current_pos = end

        if current_pos < len(text):
            remaining_text = text[current_pos:]
            painter.setPen(default_text_color)
            painter.drawText(x, baseline_y, remaining_text)

        painter.restore()

    def row_has_match(self, text: str) -> bool:
        return len(self._find_matches(text or "", self.search_text, self.search_mode)) > 0

    def _find_matches(self, text: str, search_text: str, search_mode: str) -> list[tuple[int, int]]:
        if not text or not search_text:
            return []

        if search_mode == "contains":
            return self._find_contains_matches(text, search_text)

        if search_mode == "exact":
            return self._find_exact_matches(text, search_text)

        return []

    def _find_contains_matches(self, text: str, search_text: str) -> list[tuple[int, int]]:
        matches = []
        text_lower = text.lower()
        search_lower = search_text.lower()

        start = 0
        while True:
            index = text_lower.find(search_lower, start)
            if index == -1:
                break

            matches.append((index, index + len(search_text)))
            start = index + len(search_text)

        return matches

    def _find_exact_matches(self, text: str, search_text: str) -> list[tuple[int, int]]:
        escaped = re.escape(search_text.strip())
        if not escaped:
            return []

        # whole word / exact phrase boundaries
        pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)

        matches = []
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end()))

        return matches