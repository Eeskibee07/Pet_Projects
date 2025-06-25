# app.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit,
    QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem,
    QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QKeyEvent

# Import your first utility widget
from utilities.url_to_markdown import UrlToMarkdownWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Utility App")
        self.init_ui()

    def init_ui(self):
        # Use maximized window for development instead of fullscreen
        self.setWindowState(Qt.WindowMaximized)

        # Main container for the app
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main vertical layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # Top bar container (search + exit)
        top_bar_container = QWidget()
        top_bar_container.setFixedHeight(50)

        top_bar_layout = QHBoxLayout(top_bar_container)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        top_bar_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search or ask...")
        self.search_bar.setFixedHeight(36)
        self.search_bar.setFixedWidth(400)
        top_bar_layout.addWidget(self.search_bar)

        self.exit_button = QPushButton("✕")
        self.exit_button.setFixedSize(30, 30)
        self.exit_button.clicked.connect(self.close)
        top_bar_layout.addWidget(self.exit_button)

        # Add top bar to main layout
        main_layout.addWidget(top_bar_container)

        # Add the utility widget
        self.utility_widget = UrlToMarkdownWidget()
        main_layout.addWidget(self.utility_widget)

        # Stretch any remaining space (optional)
        main_layout.addStretch()

        # Enable dark mode
        self.enable_dark_mode()

    def enable_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.setPalette(dark_palette)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
