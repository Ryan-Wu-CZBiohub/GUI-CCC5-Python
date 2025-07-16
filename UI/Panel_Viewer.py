from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, \
    QListWidget, QListWidgetItem, QSpinBox, QComboBox, QHBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer, QSize, Qt
from typing import Optional, List
import time
import math


from Controls.Controls import ValveController, PumpController



class ValvePanel(QWidget):
    def __init__(self, valve_panel=None, logger=None, control_box=None):
        super().__init__()
        self.logger = logger
        self.setStyleSheet("background-color: black; color: white;")
        
        self.control_box = control_box
        self.valve_controller = ValveController(self, logger=self.logger, control_box=self.control_box)
        
        valve_panel_layout = QVBoxLayout()
        

        # Button for toggling all
        control_all_layout = QHBoxLayout()
        self.toggle_all_on_btn = QPushButton("All Valves - ON")
        self.toggle_all_on_btn.setCheckable(True)
        self.toggle_all_on_btn.setMinimumSize(50, 50)
        self.toggle_all_on_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_on_btn.toggled.connect(self.valve_controller.valveOnAll)
        control_all_layout.addWidget(self.toggle_all_on_btn)
        valve_panel_layout.addLayout(control_all_layout)
        self.toggle_all_off_btn = QPushButton("All Valves - OFF")
        self.toggle_all_off_btn.setCheckable(True)
        self.toggle_all_off_btn.setMinimumSize(50, 50)
        self.toggle_all_off_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_off_btn.toggled.connect(self.valve_controller.valveOffAll) 
        
        control_all_layout.addWidget(self.toggle_all_off_btn)
        valve_panel_layout.addWidget(BorderSpacer(False))

        # Buttons for each individual valves
        for i in range(8):
            row_layout = QHBoxLayout()
            for j in range(12):
                valve_id = i * 12 + j + 1
                btn = QPushButton(f"Valve {valve_id} - OFF")
                btn.setCheckable(True)
                btn.setMinimumSize(50, 50)
                btn.setProperty("valve_id", valve_id)
                btn.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")
                btn.toggled.connect(self.handleValveToggle)
                row_layout.addWidget(btn)
                self.valve_controller.buttons.append(btn)
            valve_panel_layout.addLayout(row_layout)
        self.setLayout(valve_panel_layout)


    def handleValveToggle(self):
        button = self.sender()
        self.valve_controller.valveToggle(button)

    
    def updateStatus(self, message):
        if self.logger:
            self.logger(message)


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
            btn.setStyleSheet(f"color: black; background-color: {self.pump_controller.btn_off_color};")
            btn.toggled.connect(self.handlePumpToggle)
            layout.addWidget(btn)
            self.pump_controller.buttons.append(btn)
        self.setLayout(layout)


    def handlePumpToggle(self):
        button = self.sender()
        self.pump_controller.pumpToggle(button)


    def updateStatus(self, message):
        """Update the status log with a new message."""
        if self.logger:
            self.logger(message)



class PortPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("PortPanel")

        port_control_panel = QVBoxLayout()
        self.setLayout(port_control_panel)

        self.device_list = QListWidget()
        # self.device_list.currentRowChanged.connect(self.onDeviceSelected)

        self.solenoids_start_number = QSpinBox()
        self.solenoids_start_number.setMaximum(1000)
        self.solenoids_start_number.setMinimum(0)

        device_info_layout = QGridLayout()
        port_control_panel.addLayout(device_info_layout)
        self.enable_usb_box = ChoiceBox()
        device_info_layout.addWidget(QLabel("Enabled"), 0 , 0)
        device_info_layout.addWidget(self.enable_usb_box, 0 , 1)
        device_info_layout.addWidget(QLabel("Solenoids Start Number"), 1, 0)
        device_info_layout.addWidget(self.solenoids_start_number, 1, 1)

        self.solenoids_start_number = QSpinBox()
        self.solenoids_start_number.setRange(0, 1000)
        self.solenoids_start_number.setValue(0)
        self.solenoids_start_number.setSingleStep(1)

        












class ChoiceBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItem("YES")
        self.addItem("NO")

    def IsTrue(self):
        return self.currentText() == "YES"

    def SetTrue(self, isTrue: bool):
        self.setCurrentText("YES" if isTrue else "NO")


class BorderSpacer(QLabel):
    def __init__(self, vertical):
        super().__init__()
        self.setStyleSheet("""background-color: #999999""")
        if vertical:
            self.setFixedWidth(1)
        else:
            self.setFixedHeight(1)

