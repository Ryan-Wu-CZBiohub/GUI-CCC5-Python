from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout, QTextEdit, QLabel
)
from PySide6.QtGui import QColor
from datetime import datetime

class PumpPanel(QWidget):
    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger
        self.pump_controller = PumpController(self, logger=self.logger)
        layout = QVBoxLayout()
        for pump_id in range(1, 4):
            btn = QPushButton(f"Pump {pump_id} - OFF")
            btn.setCheckable(True)
            btn.setMinimumSize(50, 50)
            btn.setProperty("pump_id", pump_id)
            btn.setStyleSheet(f"color: black; background-color: {self.pump_controller.off_color.name()};")
            btn.toggled.connect(self.handlePumpToggle)
            layout.addWidget(btn)
            self.pump_controller.buttons.append(btn)
        self.setLayout(layout)


    def handlePumpToggle(self):
        button = self.sender()
        self.pump_controller.togglePump(button)


    def updateStatus(self, message):
        """Update the status log with a new message."""
        if self.logger:
            self.logger(message)


class PumpController:
    def __init__(self, pump_panel=None, logger=None):
        self.on_color = QColor(135, 185, 245)       # Blue for "ON"
        self.off_color = QColor(255, 255, 55)       # Yellow for "OFF"
        self.buttons = []                           # List to hold button references

        self.pump_panel = pump_panel
        self.logger = logger

    def togglePump(self, button: QPushButton):
        """Handle individual pump toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        color = self.on_color if is_on else self.off_color

        pump_id = button.property("pump_id")
        button.setText(f"Pump {pump_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color.name()};")
         
        msg = f"Pump {pump_id} {state}"
        print(msg)

        if self.logger:
            self.logger(msg)

    def pumpOnAll(self):
        """Turn on all pumps by toggling all buttons on."""
        for btn in self.buttons:
            if not btn.isChecked():
                btn.setChecked(True)
        print("All pumps ON")


    def pumpOffAll(self):
        """Turn off all pumps by toggling all buttons off."""
        for btn in self.buttons:
            if btn.isChecked():
                btn.setChecked(False)
        print("All pumps OFF")