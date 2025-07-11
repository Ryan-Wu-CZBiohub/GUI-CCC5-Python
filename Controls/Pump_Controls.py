from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout
)
from PySide6.QtGui import QColor

class PumpPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.pump_controller = PumpController()
        layout = QHBoxLayout()
        for pump_id in range(1, 4):
            btn = QPushButton(f"Pump {pump_id} - OFF")
            btn.setCheckable(True)
            btn.setMinimumSize(50, 50)
            btn.setProperty("pump_id", pump_id)
            btn.setStyleSheet(f"color: black; background-color: {self.pump_controller.off_color.name()};")
            btn.toggled.connect(self.handlePumpToggle)
            layout.addWidget(btn)
        self.setLayout(layout)


    def handlePumpToggle(self):
        button = self.sender()
        self.pump_controller.togglePump(button)


class PumpController:
    def __init__(self):
        self.on_color = QColor(135, 185, 245)       # Blue for "ON"
        self.off_color = QColor(255, 255, 55)       # Yellow for "OFF"
        self.buttons = []                           # List to hold button references


    def togglePump(self, button: QPushButton):
        """Handle individual pump toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        color = self.on_color if is_on else self.off_color

        pump_id = button.property("pump_id")
        button.setText(f"Pump {pump_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color.name()};")
        print(f"Pump {pump_id} {state}")
