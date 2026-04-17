from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QRect


class HighlightDelegate(QStyledItemDelegate):
    # Custom item roles allow the table manager to attach display metadata to
    # each row without having to introduce a dedicated model class.
    BG_ROLE = Qt.UserRole + 1
    STRIPE_ROLE = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.mode = "contains"

    def set_search(self, text: str, mode: str):
        # Cache the current search state in a normalized form so the delegate
        # can use it both for hit detection and custom painting.
        self.search_text = (text or "").lower()
        self.mode = mode

    def row_has_match(self, text: str) -> bool:
        if not self.search_text:
            return False

        text_lower = text.lower()

        # Exact mode matches token boundaries, while contains mode highlights
        # any matching substring inside the row text.
        if self.mode == "exact":
            return self.search_text in text_lower.split()
        return self.search_text in text_lower

    def paint(self, painter: QPainter, option, index):
        painter.save()

        text = index.data(Qt.DisplayRole) or ""

        # Read per-row colors from the custom roles assigned by the table manager.
        bg_hex = index.data(self.BG_ROLE)
        stripe_hex = index.data(self.STRIPE_ROLE)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            bg_color = QColor(bg_hex) if bg_hex else QColor("#111827")
            painter.fillRect(option.rect, bg_color)
            text_color = option.palette.text().color()

        # Draw a colored stripe at the left edge so entries from different
        # source files are easier to tell apart while scanning the table.
        if stripe_hex:
            stripe_rect = QRect(option.rect.left(), option.rect.top(), 8, option.rect.height())
            painter.fillRect(stripe_rect, QColor(stripe_hex))

        painter.setPen(text_color)

        x = option.rect.left() + 14
        y = option.rect.top() + option.fontMetrics.ascent() + 4

        if not self.search_text:
            painter.drawText(x, y, text)
            painter.restore()
            return

        text_lower = text.lower()
        search = self.search_text
        i = 0

        # Paint the text piece by piece so matching fragments can be given
        # their own highlight background.
        while i < len(text):
            if self.mode == "exact":
                idx = self._find_exact(text_lower, search, i)
            else:
                idx = text_lower.find(search, i)

            if idx == -1:
                painter.drawText(x, y, text[i:])
                break

            before = text[i:idx]
            painter.drawText(x, y, before)
            x += option.fontMetrics.horizontalAdvance(before)

            match_text = text[idx:idx + len(search)]
            rect_width = option.fontMetrics.horizontalAdvance(match_text)

            highlight_rect = QRect(
                x,
                option.rect.top() + 2,
                rect_width,
                option.rect.height() - 4
            )

            painter.fillRect(highlight_rect, QColor("#facc15"))
            painter.setPen(QColor("#000000"))
            painter.drawText(x, y, match_text)
            painter.setPen(text_color)

            x += rect_width
            i = idx + len(search)

        painter.restore()

    def _find_exact(self, text_lower: str, search: str, start: int) -> int:
        # Exact mode uses a lightweight word-boundary check instead of a full
        # regex tokenizer. That keeps the delegate fast and easy to reason about.
        idx = text_lower.find(search, start)

        while idx != -1:
            left_ok = idx == 0 or not text_lower[idx - 1].isalnum()
            right_pos = idx + len(search)
            right_ok = right_pos >= len(text_lower) or not text_lower[right_pos].isalnum()

            if left_ok and right_ok:
                return idx

            idx = text_lower.find(search, idx + 1)

        return -1
