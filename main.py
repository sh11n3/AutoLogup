import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Create the top-level Qt application object, build the main window,
    # and then hand control over to the Qt event loop.
    #
    # Keeping this bootstrap small makes it easy to understand where the
    # desktop app starts and where the actual UI logic begins.
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    # Only launch the desktop application when this file is executed directly.
    # This keeps imports safe for tests, scripts, or future tooling.
    main()
