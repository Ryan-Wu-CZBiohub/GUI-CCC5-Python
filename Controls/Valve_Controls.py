''' Custom Valve Controls Functions for GUI-CCC5 Application '''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout, QTextEdit, QLabel
)
from PySide6.QtGui import QColor
from datetime import datetime

from Controls.Pump_Controls import PumpPanel, PumpController
from Connection.Control_Box import ControlBox


class ValvePanel(QWidget):
    def __init__(self, valve_panel=None, logger=None, control_box=None):
        super().__init__()
        self.logger = logger
        self.control_box = control_box
        self.valve_controller = ValveController(self, logger=self.logger, control_box=self.control_box)
        main_layout = QVBoxLayout()

        # Button for toggling all
        controlAll_layout = QHBoxLayout()
        self.toggle_all_on_btn = QPushButton("All Valves - ON")
        self.toggle_all_on_btn.setCheckable(True)
        self.toggle_all_on_btn.setMinimumSize(50, 50)
        self.toggle_all_on_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_on_btn.toggled.connect(self.valve_controller.valveOnAll)
        controlAll_layout.addWidget(self.toggle_all_on_btn)
        main_layout.addLayout(controlAll_layout)
        self.toggle_all_off_btn = QPushButton("All Valves - OFF")
        self.toggle_all_off_btn.setCheckable(True)
        self.toggle_all_off_btn.setMinimumSize(50, 50)
        self.toggle_all_off_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_off_btn.toggled.connect(self.valve_controller.valveOffAll) 
        
        controlAll_layout.addWidget(self.toggle_all_off_btn)

        # Buttons for each individual valves
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
                self.valve_controller.buttons.append(btn)
            main_layout.addLayout(row_layout)
        self.setLayout(main_layout)


    def handleValveToggle(self):
        button = self.sender()
        self.valve_controller.valveToggle(button)

    
    def updateStatus(self, message):
        if self.logger:
            self.logger(message)


class ValveController:
    def __init__(self, valve_panel=None, logger=None, control_box=None):
        self.on_color = QColor(135, 185, 245)       # Blue for "OPEN"
        self.off_color = QColor(255, 255, 55)       # Yellow for "CLOSE"
        self.buttons = []                           # List to hold button references

        self.valve_panel = valve_panel
        self.logger = logger
        self.control_box = control_box


    def valveToggle(self, button: QPushButton):
        """Handle individual valve toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        color = self.on_color if is_on else self.off_color

        valve_id = button.property("valve_id")
        button.setText(f"Valve {valve_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color.name()};")

        msg = f"Valve {valve_id} {state}"
        print(msg)
    
        if self.logger:
            self.logger(msg)

        if self.control_box:
            # Send command to control box
            self.control_box.setValveState(valve_id, is_on)
            self.control_box.flush()
        else:
            print("ControlBox not connected or not available.")


    def valveOnAll(self):
        """Open all valves by toggling all buttons on."""
        self.control_box.setAllValvesOn()
        
        for btn in self.buttons:
            btn.setChecked(True) 
        print("All valves ON")


    def valveOffAll(self):
        """Close all valves by toggling all buttons off."""
        self.control_box.setAllValvesOff()
        
        for btn in self.buttons:
            btn.setChecked(False) 
        print("All valves OFF")
