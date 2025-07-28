''' Custom Valve and Pump Control Functions for GUI-CCC5 Application '''

from multiprocessing import connection
from PySide6.QtWidgets import QPushButton, QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import QRunnable, QThreadPool, Slot, QTimer
import traceback
from typing import Dict, List
import json
import os, sys
try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()  # Fallback if __file__ is undefined

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
from Connection.Connection import Connection


class ValveController:
    def __init__(self, valve_panel=None, logger=None, control_box: Connection = None):
        self.btn_off_color = "rgb(255, 255, 55)"     # Yellow for "CLOSED"
        self.btn_on_color = "rgb(230, 230, 230)"     # Light gray for "OPEN"
        self.buttons = {}
        self.positions = {} 
        self.valve_panel = valve_panel
        self.logger = logger
        self.control_box = control_box
        self.control_box.valveStateChanged.connect(self.updateButtonState)

    @Slot(int, bool)
    def updateButtonState(self, valve_id: int, state: bool):
        """Safely update valve button visuals from any thread."""
        def apply_update():
            button = self.buttons.get(valve_id)
            if not button:
                return
            
            if button.isChecked() != state:
                button.blockSignals(True)
                button.setChecked(state)
                button.blockSignals(False)

            label = "OPEN" if state else "CLOSE"
            color = self.btn_on_color if state else self.btn_off_color
            button.setText(f"{valve_id} - {label}")
            button.setStyleSheet(f"color: black; background-color: {color};")

        QTimer.singleShot(0, apply_update)  # Schedule update on the main thread

    def valveToggle(self, button: QPushButton, user_triggered: bool = True):
        """Handle individual valve toggle."""
        is_on = button.isChecked()
        state = "OPEN" if is_on else "CLOSE"
        color = self.btn_on_color if is_on else self.btn_off_color

        valve_id = button.property("valve_id")
        button.setText(f"{valve_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color};")

        msg = f"Valve {valve_id} {state}"
        # if user_triggered and self.logger:
        #     print(msg)

        if self.control_box:
            # Send command to control box
            self.control_box.setValveState(valve_id, is_on)
            self.control_box.flush()
        else:
            print("ControlBox not connected or not available.")

    def valveOnAll(self):
        for btn in self.buttons.values():
            if btn.isVisible() and btn.isEnabled() and not btn.isChecked():
                btn.setChecked(True)

    def valveOffAll(self):
        for btn in self.buttons.values():
            if btn.isVisible() and btn.isEnabled() and btn.isChecked():
                btn.setChecked(False)

# Not used in the current context, but kept for potential future use
class PumpController:
    def __init__(self, pump_panel=None, logger=None, control_box: Connection = None):
        self.control_box = control_box if control_box is not None else Connection()
        self.btn_off_color = "rgb(255, 255, 55)"     # Yellow for "CLOSED"
        self.btn_on_color = "rgb(230, 230, 230)"   # Light gray for "OPEN"
        self.buttons = []                           # List to hold button references
        self.pump_panel = pump_panel
        self.logger = logger

    def pumpToggle(self, button: QPushButton):
        """Handle individual pump toggle."""
        is_on = button.isChecked()
        state = "OPEN" if is_on else "CLOSE"
        color = self.btn_on_color if is_on else self.btn_off_color

        pump_id = button.property("pump_id")
        button.setText(f"Pump {pump_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color};")

        msg = f"Pump {pump_id} {state}"
        print(msg)

        if self.logger:
            self.logger(msg)

    def pumpOnAll(self):
        """Turn on all pumps by toggling all buttons on."""
        for btn in self.buttons:
            if btn.isVisible() and btn.isEnabled() and not btn.isChecked():
                btn.setChecked(True)
        print("All pumps OPEN")


    def pumpOffAll(self):
        """Turn off all pumps by toggling all buttons off."""
        for btn in self.buttons:
            if btn.isVisible() and btn.isEnabled() and btn.isChecked():
                btn.setChecked(False)
        print("All pumps CLOSE")


class FlushTask(QRunnable):
    def __init__(self, flush_function):
        super().__init__()
        self.flush_function = flush_function

    def run(self):
        self.flush_function()