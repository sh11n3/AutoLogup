from PySide6.QtWidgets import QPushButton, QFileDialog


class FileLoaderButton(QPushButton):
    def __init__(self, callback):
        super().__init__("Load Logs")
        self.callback = callback
        self.clicked.connect(self.open_dialog)

    def open_dialog(self):
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