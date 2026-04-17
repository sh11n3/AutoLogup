from PySide6.QtWidgets import QAbstractItemView


class SearchManager:
    def __init__(
        self,
        table,
        table_manager,
        search_container,
        search_input,
        search_mode_combo,
        search_result_label,
        highlight_delegate,
    ):
        self.table = table
        self.table_manager = table_manager
        self.search_container = search_container
        self.search_input = search_input
        self.search_mode_combo = search_mode_combo
        self.search_result_label = search_result_label
        self.highlight_delegate = highlight_delegate

        # Keep search state in a dedicated helper so the main window does not
        # have to manage match lists, indexes, and navigation itself.
        self.visible_logs = []
        self.search_match_rows = []
        self.current_search_match_index = -1

    def open_search_bar(self):
        # Show the search UI and focus the input immediately so Ctrl+F behaves
        # like users expect from desktop applications.
        self.search_container.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def close_search_bar(self):
        # Reset the visible search controls and the delegate's highlight state
        # together so the table always reflects the actual UI state.
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

    def set_visible_logs(self, logs):
        # Rebuild matches whenever the visible dataset changes because both the
        # content and the corresponding table rows may have shifted.
        self.visible_logs = logs or []
        self._rebuild_search_matches()

    def on_search_text_changed(self, text):
        self.highlight_delegate.set_search(text, self._current_search_mode())
        self._rebuild_search_matches()
        self.table.viewport().update()

    def on_search_mode_changed(self, _index):
        self.highlight_delegate.set_search(self.search_input.text(), self._current_search_mode())
        self._rebuild_search_matches()
        self.table.viewport().update()

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

    def _current_search_mode(self) -> str:
        return "exact" if self.search_mode_combo.currentText() == "Exact" else "contains"

    def _rebuild_search_matches(self):
        self.search_match_rows = []
        self.current_search_match_index = -1

        search_text = self.search_input.text().strip()
        if not search_text:
            self._update_search_result_label()
            return

        # Translate matching log indexes into real table rows. This step matters
        # because the table contains extra file-header rows that are not part of
        # the underlying log list.
        for log_index, log in enumerate(self.visible_logs):
            raw_text = log.raw or ""
            if not self.highlight_delegate.row_has_match(raw_text):
                continue

            table_row = self.table_manager.get_row_for_log_index(log_index)
            if table_row is not None:
                self.search_match_rows.append(table_row)

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

    def _select_search_match(self, match_index: int):
        if match_index < 0 or match_index >= len(self.search_match_rows):
            return

        row = self.search_match_rows[match_index]
        # Preserve the horizontal scroll position so navigating search results
        # does not constantly snap the user back to the left edge.
        h_scroll = self.table.horizontalScrollBar().value()

        self.table.selectRow(row)
        self.table.scrollToItem(
            self.table.item(row, 0),
            QAbstractItemView.PositionAtCenter,
        )

        self.table.horizontalScrollBar().setValue(h_scroll)
