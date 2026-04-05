from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt, QRect


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.mode = "contains"

    def set_search(self, text: str, mode: str):
        self.search_text = text.lower()
        self.mode = mode

    def row_has_match(self, text: str) -> bool:
        if not self.search_text:
            return False

        text_lower = text.lower()

        if self.mode == "exact":
            return self.search_text in text_lower.split()
        else:
            return self.search_text in text_lower

    def paint(self, painter: QPainter, option, index):
        painter.save()

        text = index.data()
        if not text:
            text = ""

        # 👉 Hintergrund (Selection korrekt)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
        else:
            painter.fillRect(option.rect, option.palette.base())
            text_color = option.palette.text().color()

        # 👉 FILE COLOR STRIPE
        file_color = index.data(Qt.UserRole)
        if file_color:
            stripe_rect = QRect(option.rect.left(), option.rect.top(), 6, option.rect.height())
            painter.fillRect(stripe_rect, QColor(file_color))

        # 👉 Text Rendering vorbereiten
        painter.setPen(text_color)

        x = option.rect.left() + 10
        y = option.rect.top() + option.fontMetrics.ascent() + 2

        if not self.search_text:
            painter.drawText(x, y, text)
            painter.restore()
            return

        text_lower = text.lower()
        search = self.search_text

        i = 0

        while i < len(text):
            match_index = -1

            if self.mode == "exact":
                words = text_lower.split()
                if search in words:
                    match_index = text_lower.find(search, i)
            else:
                match_index = text_lower.find(search, i)

            if match_index == -1:
                # Rest normal zeichnen
                painter.drawText(x, y, text[i:])
                break

            # 👉 Teil vor Match
            before = text[i:match_index]
            painter.drawText(x, y, before)
            x += option.fontMetrics.horizontalAdvance(before)

            # 👉 Highlight Teil
            match_text = text[match_index:match_index + len(search)]

            rect_width = option.fontMetrics.horizontalAdvance(match_text)

            highlight_rect = QRect(
                x,
                option.rect.top(),
                rect_width,
                option.rect.height()
            )

            painter.fillRect(highlight_rect, QColor("#facc15"))
            painter.setPen(QColor("#000000"))
            painter.drawText(x, y, match_text)

            painter.setPen(text_color)

            x += rect_width
            i = match_index + len(search)

        painter.restore()