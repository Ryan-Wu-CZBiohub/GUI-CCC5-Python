''' Custom GUI Class for CCC5 Control Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtGui import QIcon

# Importing the custom valve controls functions
from Functions.Valve_Controls import ValveController

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Window")
        self.setWindowIcon(QIcon("Media/Logos/CZI-CZ-Biohub-Mark-CHI-Color-RGB.png"))
        self.resize(1600, 900)

        # Initialize the ValveController
        self.valve_controller = ValveController()

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Background palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))    # White background
        central_widget.setAutoFillBackground(True)
        central_widget.setPalette(palette)

        # Create grid of toggle buttons (8 rows, 12 columns = 96 buttons)
        grid_layout = QVBoxLayout()
        for i in range(8):
            row_layout = QHBoxLayout()
            for j in range(12):
                valve_id = i * 12 + j + 1
                btn = QPushButton(str(valve_id))
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50) 
                btn.setStyleSheet(f"background-color: {self.valve_controller.off_color.name()}")
                btn.toggled.connect(self.handle_valve_toggle)

                # Track the button in the ValveController
                self.valve_controller.buttons.append(btn)

                row_layout.addWidget(btn)
            grid_layout.addLayout(row_layout)

        main_layout.addLayout(grid_layout)


    def handle_valve_toggle(self):
        button = self.sender()
        self.valve_controller.toggle_valve(button)

    
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
            self.valve_controller.valve_close_all()  # Close all valves
            print("Closing the application...")
            event.accept()
        else:
            print("Close event ignored.")
            event.ignore()



if __name__ == "__main__":
    app = QApplication([])
    window = GUI()
    window.show()
    app.exec()  # Start the application event loop