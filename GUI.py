''' Custom GUI Class for CCC5 Control Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, 
    QGridLayout, QTextEdit, QLabel, QDockWidget, QFileDialog
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QIcon
from datetime import datetime

# Importing the custom valve controls functions
from Controls.Valve_Controls import ValvePanel, ValveController
from Controls.Pump_Controls import PumpPanel, PumpController


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Command Window")
        self.setWindowIcon(QIcon("Media/Logos/CZI-CZ-Biohub-Mark-CHI-Color-RGB.png"))
        self.resize(1600, 900)
        self.setMinimumSize(1600, 900)

        # Initialize controllers
        self.valve_controller = ValveController()
        self.pump_controller = PumpController()

        # Central widget & dock layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addStretch(1)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # main_layout = QVBoxLayout(central_widget)
        # main_layout.setContentsMargins(0, 0, 0, 0)
        # main_layout.setSpacing(0)

        # Background palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))    # White background
        central_widget.setAutoFillBackground(True)
        central_widget.setPalette(palette)

        # Valve control panel
        self.valve_panel = ValvePanel(logger=self.logMessage)
        valve_dock = QDockWidget("Valve Panel", self)
        valve_dock.setWidget(self.valve_panel)
        valve_dock.setFloating(False)
        valve_dock.setMinimumWidth(1300)
        valve_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        valve_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, valve_dock)

        # Pump control panel
        self.pump_panel = PumpPanel(logger=self.logMessage)
        pump_dock = QDockWidget("Pump Panel", self)
        pump_dock.setWidget(self.pump_panel)
        pump_dock.setFloating(False)
        pump_dock.setMinimumWidth(300)
        pump_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        pump_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, pump_dock)

        # Status log box
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 5, 5, 5)

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        status_layout.addWidget(self.status_box)

        status_dock = QDockWidget("Status Log", self)
        status_dock.setWidget(status_widget)
        status_dock.setFloating(False)
        status_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addDockWidget(Qt.BottomDockWidgetArea, status_dock)

        # Scripts panel
        self.scripts_panel = QWidget()
        scripts_layout = QVBoxLayout(self.scripts_panel)
        scripts_layout.setContentsMargins(5, 5, 5, 5)

        self.load_scripts_button = QPushButton("Load Script")
        self.load_scripts_button.clicked.connect(self.loadScripts)
        scripts_layout.addWidget(self.load_scripts_button)      
        
        # (TODO: add run button or script output)
        scripts_dock = QDockWidget("Experiment Script", self)
        scripts_dock.setWidget(self.scripts_panel)
        scripts_dock.setFloating(False)
        scripts_dock.setMinimumWidth(300)
        scripts_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addDockWidget(Qt.RightDockWidgetArea, scripts_dock)


    def loadScripts(self):
        """Load and execute any experiment scripts."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Script File", "", "Python Files (*.py);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    script_content = file.read()
                exec(script_content, {"gui": self})
                self.logMessage(f"Script '{file_name}' loaded and executed.")
            except Exception as e:
                self.logMessage(f"Error loading script: {e}")


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
                self, "Shutdowns",
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