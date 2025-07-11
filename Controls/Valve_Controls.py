''' Custom Valve Controls Functions for GUI-CCC5 Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout
)
from PySide6.QtGui import QColor

class ValvePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.valve_controller = ValveController()
        layout = QVBoxLayout()
        for i in range(8):
            row_layout = QHBoxLayout()
            for j in range(12):
                valve_id = i * 12 + j + 1
                btn = QPushButton(f"Valve {valve_id} - OFF")
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50)
                btn.setProperty("valve_id", valve_id)
                btn.setStyleSheet(f"color: black; background-color: {self.valve_controller.off_color.name()};")
                btn.toggled.connect(self.handleValveToggle)
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)
        self.setLayout(layout)


    def handleValveToggle(self):
        button = self.sender()
        self.valve_controller.toggleValve(button)


class ValveController:
    def __init__(self):
        self.on_color = QColor(135, 185, 245)       # Blue for "OPEN"
        self.off_color = QColor(255, 255, 55)    # Yellow for "CLOSE"
        self.buttons = []                       # List to hold button references


    def toggleValve(self, button: QPushButton):
        """Handle individual valve toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        color = self.on_color if is_on else self.off_color

        valve_id = button.property("valve_id")
        button.setText(f"Valve {valve_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color.name()};")
        print(f"Valve {valve_id} {state}")


    def valveOnAll(self):
        """Open all valves by toggling all buttons on."""
        for btn in self.buttons:
            if not btn.isChecked():
                btn.setChecked(True)
        print("All valves ON")

    
    def valveOffAll(self):
        """Close all valves by toggling all buttons off."""
        for btn in self.buttons:
            if btn.isChecked():
                btn.setChecked(False)
        print("All valves OFF")

    
