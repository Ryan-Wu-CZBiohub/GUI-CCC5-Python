''' Custom GUI Class for CCC5 Control Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout, QTextEdit, QLabel
)
from PySide6.QtGui import QPalette, QColor, QIcon
from datetime import datetime

# Importing the custom valve controls functions
from Controls.Valve_Controls import ValvePanel, ValveController
from Controls.Pump_Controls import PumpPanel, PumpController

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Window")
        self.setWindowIcon(QIcon("Media/Logos/CZI-CZ-Biohub-Mark-CHI-Color-RGB.png"))
        self.resize(1600, 900)

        # Initialize the controllers
        self.valve_controller = ValveController()
        self.pump_controller = PumpController()

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

        # Control panels
        self.valve_panel = ValvePanel(logger=self.logMessage)
        main_layout.addWidget(self.valve_panel)
        self.pump_panel = PumpPanel(logger=self.logMessage)
        main_layout.addWidget(self.pump_panel)

        # Status text box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setMinimumHeight(100)
        main_layout.addWidget(QLabel("Status Log:"))
        main_layout.addWidget(self.status_box)


    def logMessage(self, message: str):
        """Log a message to the status box."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_box.append(f"{timestamp} {message}")

    
    def promptForClose(self):
        reply = QMessageBox.question(
            self, 'Confirm Close',
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            action_reply = QMessageBox.question(
                self, "Valve Shutdown",
                "Do you want to close all valves and pumps before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )

            if action_reply == QMessageBox.Yes:
                self.valve_controller.valveOffAll()
                self.pump_controller.pumpOffAll()
            elif action_reply == QMessageBox.No:
                print("Leaving valves and pumps as-is.")
            else:  # Cancel exit
                return False
            return True
        return False
    

    def closeEvent(self, event):
        if self.promptForClose():
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