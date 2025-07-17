''' Custom GUI Class for CCC5 Control Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, 
    QGridLayout, QTextEdit, QLabel, QDockWidget, QFileDialog, QMainWindow
    )
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QIcon, QTextCursor
from datetime import datetime

# Importing the custom valve controls functions
from Connection.Connection import Connection, Device
from Control.Panel_Controller import ValveController, PumpController
from UI.Panel_Viewer import ValvePanel, PumpPanel, PortPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Command Window")
        self.setWindowIcon(QIcon("Media/Logos/CZI-CZ-Biohub-Mark-CHI-Color-RGB.png"))
        self.resize(1600, 900)
        self.setMinimumSize(1600, 900)
        # self.setStyleSheet("background-color: rgb(230, 230, 230);")   # light gray background


        # Initialize controllers

        # # Control Box for managing devices
        self.control_box = Connection()
        self.control_box.scanForDevices()

        self.valve_controller = ValveController(control_box=self.control_box)
        self.pump_controller = PumpController(control_box=self.control_box)
        self.port_panel = PortPanel(logger=self.logMessage, control_box=self.control_box)
        

        # Central widget & dock layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addStretch(1)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # main_layout = QVBoxLayout(central_widget)
        # main_layout.setContentsMargins(0, 0, 0, 0)
        # main_layout.setSpacing(0)

        # Background palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(230, 230, 230))

      
        # Valve control panel
        # self.valve_panel = ValvePanel(logger=self.logMessage, control_box=self.control_box)

        valve_widget = QWidget()
        valve_layout = QVBoxLayout(valve_widget)
        valve_layout.setContentsMargins(5, 5, 5, 5)


        self.valve_panel = ValvePanel(logger=self.logMessage, control_box=self.control_box)
        valve_layout.addWidget(self.valve_panel)

        valve_dock = QDockWidget("Valve Controls", self)
        valve_dock.setWidget(valve_widget)
        valve_dock.setFloating(False)
        valve_dock.setMinimumWidth(1300)
        valve_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        valve_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable  
            # | QDockWidget.DockWidgetClosable
        )   
        self.addDockWidget(Qt.LeftDockWidgetArea, valve_dock)

        # # Pump control panel
        # self.pump_panel = PumpPanel(logger=self.logMessage, control_box=self.control_box)
        # pump_dock = QDockWidget("Pump Control Panel", self)
        # pump_dock.setWidget(self.pump_panel)
        # pump_dock.setFloating(False)
        # pump_dock.setMinimumWidth(300)
        # pump_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # pump_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        # self.addDockWidget(Qt.RightDockWidgetArea, pump_dock)

        # Status log box
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 5, 5, 5)

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        status_layout.addWidget(self.status_box)

        status_dock = QDockWidget("Status Log", self)
        status_dock.setWidget(status_widget)
        status_dock.setFloating(False)
        status_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable  
            # | QDockWidget.DockWidgetClosable
        )   
        self.addDockWidget(Qt.RightDockWidgetArea, status_dock)

        # Scripts panel
        self.scripts_panel = QWidget()
        scripts_layout = QVBoxLayout(self.scripts_panel)
        scripts_layout.setContentsMargins(5, 5, 5, 5)

        self.load_scripts_button = QPushButton("Load Script")
        self.load_scripts_button.clicked.connect(self.loadScripts)
        scripts_layout.addWidget(self.load_scripts_button)     

        self.run_script_button = QPushButton("Run Script")
        self.run_script_button.clicked.connect(self.runScript)
        scripts_layout.addWidget(self.run_script_button) 
        
        # (TODO: add run button or script output)
        scripts_dock = QDockWidget("Experiment Script", self)
        scripts_dock.setWidget(self.scripts_panel)
        scripts_dock.setFloating(False)
        scripts_dock.setMinimumWidth(300)
        scripts_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scripts_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable  
            # | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, scripts_dock)

        # Port information panel
        # self.port_panel = PortPanel(logger=self.logMessage, control_box=self.control_box)
        # port_dock = QDockWidget("Port Information", self)
        # port_dock.setWidget(self.port_panel)
        # port_dock.setFloating(False)
        # port_dock.setMinimumWidth(300)
        # port_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # port_dock.setFeatures(
        #     QDockWidget.DockWidgetMovable | 
        #     QDockWidget.DockWidgetFloatable  
            # | QDockWidget.DockWidgetClosable
        # )
        # self.addDockWidget(Qt.RightDockWidgetArea, port_dock)

    def loadScripts(self):
        """Load and execute any experiment scripts."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Script File", "", "Python Files (*.py);;All Files (*)"
        )
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    self.script_code = file.read()
                self.loaded_script_path = file_name
                # self.status_box.clear()
                self.status_box.append("───────────────────────────────")
                self.run_script_button.setEnabled(True)
                self.logMessage(f"{file_name} loaded successfully.")
            except Exception as e:
                self.logMessage(f"Error loading script: {e}")
                self.run_script_button.setEnabled(False)

    def runScript(self):
        """Run the loaded script."""
        if not self.script_code:
            self.logMessage("No script loaded.")
            return
        try:
            exec(self.script_code, {"gui": self})
            name = getattr(self, "loaded_script_path", "Unknown Script")
            self.logMessage(f"{name} executed successfully.")
        except Exception as e:
            self.logMessage(f"Error running script: {e}")

    def logMessage(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_box.append(f"{timestamp} {message}")
        self.status_box.moveCursor(QTextCursor.End)

    
    def promptForClose(self):
        reply = QMessageBox.question(
            self, 'Confirm Close',
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # action_reply = QMessageBox.question(
            #     self, "Shutdowns",
            #     "Do you want to close all valves and pumps before exiting?",
            #     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            #     QMessageBox.Yes2
            # )

            # if action_reply == QMessageBox.Yes:
            #     self.control_box.setAllValvesOff()
            #     self.pump_controller.pumpOffAll()
            # elif action_reply == QMessageBox.No:
            #     print("Leaving valves and pumps as-is.")
            # else:  # Cancel exit
            #     return False
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
    window = MainWindow()
    window.show()
    app.exec()  # Start the application event loop