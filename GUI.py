"""Custom GUI Class for CCC5 Control Application"""

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMenuBar,
    QSizePolicy,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QGridLayout,
    QTextEdit,
    QLabel,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QDialog,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThreadPool, QMetaObject, QTimer, Signal, QObject, Slot
from PySide6.QtGui import QPalette, QColor, QIcon, QTextCursor, QKeySequence, QPixmap
from datetime import datetime
import os
import json

from Connection.Connection import Connection, Device
from Control.Panel_Controller import ValveController, PumpController
from UI.Panel_Viewer import ValvePanel, PumpPanel, PortPanel
from Experiment.CCC5P2_experiment import ExperimentRunner


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_window()
        self.initialize_controllers()
        self.setup_layout()
        self.create_menu_bar()
        self.create_dock_widgets()
        self.experiment_runner = None

    def main_window(self):
        """Main window settings."""
        self.setWindowTitle("Command Window")
        self.setWindowIcon(QIcon("Media/Logos/CZI-CZ-Biohub-Mark-CHI-Color-RGB.png"))
        self.resize(1600, 900)
        self.setMinimumSize(1600, 900)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(230, 230, 230))

    def initialize_controllers(self):
        """Initialize the controllers and panels for the application."""
        self.control_box = Connection()
        print("GUI control_box ID:", id(self.control_box))
        self.control_box.scanForDevices()
        self.valve_panel = ValvePanel(
            logger=self.logMessage, control_box=self.control_box
        )
        self.valve_controller = ValveController(control_box=self.control_box)

        # self.pump_controller = PumpController(control_box=self.control_box)
        # self.port_panel = PortPanel(logger=self.logMessage, control_box=self.control_box)

    def setup_layout(self):
        """Setup the main layout of the application."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout(central_widget)
        central_layout.addStretch(1)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

    def create_menu_bar(self):
        """Create the menu bar for the application."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        open_action = file_menu.addAction("Open")
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.openFile)

        save_action = file_menu.addAction("Load")
        save_action.setShortcut(QKeySequence("Ctrl+L"))
        save_action.triggered.connect(self.loadFile)

        save_as_action = file_menu.addAction("Save")
        save_as_action.setShortcut(QKeySequence("Ctrl+S"))
        save_as_action.triggered.connect(self.saveFileAs)

        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)

    def create_dock_widgets(self):
        """Create the dock widgets for the application."""
        # Valve control panel
        valve_widget = QWidget()
        valve_layout = QVBoxLayout(valve_widget)
        valve_layout.setContentsMargins(5, 5, 5, 5)
        valve_layout.addWidget(self.valve_panel)

        valve_dock = QDockWidget("Valve Controls", self)
        valve_dock.setWidget(valve_widget)
        valve_dock.setFloating(False)
        # valve_dock.setMinimumWidth(1300)
        valve_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        valve_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
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

        # Status log panel
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
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
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

        scripts_dock = QDockWidget("Experiment Script", self)
        scripts_dock.setWidget(self.scripts_panel)
        scripts_dock.setFloating(False)
        scripts_dock.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        scripts_dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            # | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.RightDockWidgetArea, scripts_dock)
        self.resizeDocks([valve_dock, scripts_dock], [int(self.width() * 0.75), int(self.width() * 0.25)], Qt.Horizontal)
        self.splitDockWidget(
            status_dock, scripts_dock, Qt.Vertical
        )
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
                with open(file_name, "r") as file:
                    self.script_code = file.read()
                self.loaded_script_path = file_name
                self.run_script_button.setEnabled(True)
                self.logMessage(f"{file_name} loaded successfully.")
            except Exception as e:
                self.logMessage(f"Error loading script: {e}")
                self.run_script_button.setEnabled(False)

    def runScript(self):
        """Run the loaded experiment script."""
        if not hasattr(self, "script_code") or not self.script_code:
            self.logMessage("No script loaded.")
            return

        try:
            script_globals = {"gui": self}
            exec(self.script_code, script_globals)

            self.logMessage(f"Running {self.loaded_script_path} from script...")
            runner = ExperimentRunner(self, test_mode=False)
            QThreadPool.globalInstance().start(runner)

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.logMessage(f"Error running script: {e}")
            self.logMessage(tb)
    @Slot(str)
    def logMessage(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[MainWindow] logMessage triggered: {message}")  # Debug print
        self.status_box.append(f"{timestamp} {message}")
        self.status_box.moveCursor(QTextCursor.End)

    def _appendToStatus(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_box.append(f"{timestamp} {message}")
        self.status_box.moveCursor(QTextCursor.End)

    def promptForClose(self):
        """Prompt the user for confirmation before closing the application."""
        reply = QMessageBox.question(
            self,
            "Confirm Close",
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.valve_controller.valveOffAll()
            self.control_box.disconnectAll()
            return True
        return False

    def closeEvent(self, event):
        """Handle the close event of the main window."""
        if self.promptForClose():
            print("Closing the application...")
            event.accept()
        else:
            print("Close event ignored.")
            event.ignore()

    # menu functions
    def openFile(self):
        """Open a file and display its content in a preview window."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*)"
        )
        if not file_name:
            return

        try:
            ext = os.path.splitext(file_name)[1].lower()

            preview_window = QWidget(self)
            preview_window.setWindowTitle(f"Preview: {os.path.basename(file_name)}")
            preview_window.setAttribute(Qt.WA_DeleteOnClose)
            preview_window.setWindowFlag(Qt.Window)
            layout = QVBoxLayout(preview_window)

            if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                pixmap = QPixmap(file_name)
                if pixmap.isNull():
                    raise Exception("Failed to load image.")
                label = QLabel()
                label.setPixmap(pixmap)
                label.setScaledContents(True)
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                label.setMinimumSize(400, 300)
                layout.addWidget(label)
            else:
                with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                text_edit = QTextEdit()
                text_edit.setPlainText(content)
                text_edit.setReadOnly(True)
                layout.addWidget(text_edit)

            preview_window.resize(1600, 900)
            preview_window.show()

            self.logMessage(f"Opened preview: {file_name}")

        except Exception as e:
            self.logMessage(f"Error opening file: {e}")

    def saveFileAs(self):
        """Save the current valve layout to a file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Valve Layout",
            "",
            "Valve Layout Files (*.json);;All Files (*)"
        )
        if not file_name:
            return

        try:
            layout_data = {
                "valves": {
                    str(valve_id): list(pos)
                    for valve_id, pos in self.valve_panel.valve_controller.positions.items()
                }
            }
            with open(file_name, "w") as f:
                json.dump(layout_data, f, indent=2)

            self.logMessage(f"Valve layout saved to: {file_name}")
        except Exception as e:
            self.logMessage(f"Error saving layout: {e}")

    def loadFile(self):
        """Load a valve layout from a file."""
        file_name, _ = QFileDialog.getOpenFileName(
        self,
        "Open Valve Layout",
        "",
        "Valve Layout Files (*.json);;All Files (*)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r") as f:
                layout_data = json.load(f)

            if "valves" not in layout_data:
                raise ValueError("Invalid layout file format.")
            
            self.valve_panel.resetAllValves()  # Clear existing buttons

            for valve_id_str, position in layout_data["valves"].items():
                valve_id = int(valve_id_str)
                row, col = position

                button = self.valve_panel.valve_controller.buttons.get(valve_id)
                if button:
                    # Clear old position
                    old_row, old_col = self.valve_panel.valve_controller.positions[valve_id]
                    self.valve_panel.slot_grid[(old_row, old_col)].clearSlot()
                    
                    # Set to new position
                    self.valve_panel.slot_grid[(row, col)].setValveButton(button)
                    self.valve_panel.valve_controller.positions[valve_id] = (row, col)

            self.logMessage(f"Valve layout loaded from: {file_name}")

        except Exception as e:
            self.logMessage(f"Error loading layout: {e}")

    def resizeEvent(self, event):
        """Resize the main window and adjust dock widgets."""
        super().resizeEvent(event)

        valve_dock = self.findChild(QDockWidget, "Valve Controls")
        scripts_dock = self.findChild(QDockWidget, "Experiment Script")
        status_dock = self.findChild(QDockWidget, "Status Log")

        if valve_dock and scripts_dock:
            self.resizeDocks(
                [valve_dock, scripts_dock],
                [int(self.width() * 0.80), int(self.width() * 0.20)],
                Qt.Horizontal
            )
        if status_dock:
            self.resizeDocks(
                [status_dock],
                [int(self.height() * 0.25)],
                Qt.Vertical
            )

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()  # Start the application event loop
