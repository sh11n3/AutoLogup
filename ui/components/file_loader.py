from PySide6.QtWidgets import QPushButton, QFileDialog


class FileLoaderButton(QPushButton):
    def __init__(self, callback):
        super().__init__("Load Logs")
        # Keep this widget focused on opening the file dialog.
        # The actual handling of selected files is delegated back to the window.
        self.callback = callback
        self.clicked.connect(self.open_dialog)

    def open_dialog(self):
        # Offer the known supported formats first, while still leaving an
        # escape hatch for opening arbitrary files when needed.
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Log Files",
            "",
            "All Supported Files (*.log *.txt *.json *.csv *.xml *.sql);;"
            "Log Files (*.log *.txt);;"
            "JSON Files (*.json);;"
            "CSV Files (*.csv);;"
            "XML Files (*.xml);;"
            "SQL Files (*.sql);;"
            "All Files (*)"
        )

        if files:
            self.callback(files)
