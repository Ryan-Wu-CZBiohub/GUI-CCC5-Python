from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox
)
from PySide6.QtGui import QPalette, QColor, QFont

class CCC5GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Window")
        self.resize(1600, 900)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Background palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))    # White background
        central_widget.setAutoFillBackground(True)
        central_widget.setPalette(palette)

        # Font settings
        font20 = QFont()
        font20.setPointSize(20)
        self.setFont(font20)

        # Button color states
        self.on_color = QColor(0, 255, 0)       # Green for "OPEN"
        self.off_color = QColor(255, 0, 0)      # Red for "CLOSE"

        # Create grid of toggle buttons (8 rows, 12 columns = 96 buttons)
        self.buttons = []
        grid_layout = QVBoxLayout()
        for i in range(8):
            row_layout = QHBoxLayout()
            row_buttons = []
            for j in range(12):
                btn = QPushButton(f"{i * 12 + j + 1}")
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50) 
                btn.setStyleSheet(f"background-color: {self.off_color.name()};")
                btn.toggled.connect(self.on_button_toggled)
                row_layout.addWidget(btn)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
            grid_layout.addLayout(row_layout)

        # Add the grid layout to the main layout
        main_layout.addLayout(grid_layout)


    def on_button_toggled(self, checked):
        button = self.sender()
        color = self.on_color if checked else self.off_color
        button.setStyleSheet(f"background-color: {color.name()};")

    
    def PromptForClose(self):
        reply = QMessageBox.question(
            self, 'Confirm Close',
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes


    def closeEvent(self, event):
        if self.PromptForClose():
            self.cleanup()
            event.accept()
            print("Closing the application...")
        else:
            event.ignore()
            print("Close event ignored.")



if __name__ == "__main__":
    app = QApplication([])
    window = CCC5GUI()
    window.show()
    app.exec()  # Start the application event loop