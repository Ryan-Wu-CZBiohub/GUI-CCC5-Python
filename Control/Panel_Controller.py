''' Custom Valve and Pump Control Functions for GUI-CCC5 Application '''

from PySide6.QtWidgets import QPushButton, QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import QRunnable, QThreadPool

from Connection.Connection import Connection


class ValveController:
    def __init__(self, valve_panel=None, logger=None, control_box: Connection = None):
        self.btn_on_color = "rgb(255, 255, 55)"     # Yellow for "OPEN"
        self.btn_off_color = "rgb(230, 230, 230)"   # Light gray for "CLOSED"
        self.buttons = {}
        self.positions = {} 
        self.valve_panel = valve_panel
        self.logger = logger
        self.control_box = control_box


    def valveToggle(self, button: QPushButton):
        """Handle individual valve toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        color = self.btn_on_color if is_on else self.btn_off_color

        valve_id = button.property("valve_id")
        button.setText(f"Valve {valve_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color};")

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


    # def valveOnAll(self):
    #     """Open all valves by toggling all buttons on."""
    #     # for btn in self.buttons:
    #     for btn in self.buttons.values():
    #         btn.setChecked(True) 
    #     QApplication.processEvents()  # Ensure UI updates immediately    
    #     print("All valves ON")

    #     # Update control box state
    #     if self.control_box:
    #         for valve_id in self.control_box.getConnectedValveIds():
    #             self.control_box.setValveState(valve_id, True)

    #         task = FlushTask(self.control_box.flush)
    #         QThreadPool.globalInstance().start(task)  # Run flush in a separate thread

        

    # def valveOffAll(self):
    #     """Close all valves by toggling all buttons off."""
    #     # for btn in self.buttons:
    #     for btn in self.buttons.values():
    #         btn.setChecked(False) 
    #     QApplication.processEvents()
    #     print("All valves OFF")


    #     if self.control_box:
    #         for valve_id in self.control_box.getConnectedValveIds():
    #             self.control_box.setValveState(valve_id, False)
    #         # self.control_box.flush()

    #         task = FlushTask(self.control_box.flush)
    #         QThreadPool.globalInstance().start(task)  # Run flush in a separate thread

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
        self.btn_on_color = "rgb(255, 255, 55)"     # Yellow for "OPEN"
        self.btn_off_color = "rgb(230, 230, 230)"   # Light gray for "CLOSED"
        self.buttons = []                           # List to hold button references
        self.pump_panel = pump_panel
        self.logger = logger

    def pumpToggle(self, button: QPushButton):
        """Handle individual pump toggle."""
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
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
        print("All pumps ON")


    def pumpOffAll(self):
        """Turn off all pumps by toggling all buttons off."""
        for btn in self.buttons:
            if btn.isVisible() and btn.isEnabled() and btn.isChecked():
                btn.setChecked(False)
        print("All pumps OFF")


class FlushTask(QRunnable):
    def __init__(self, flush_function):
        super().__init__()
        self.flush_function = flush_function

    def run(self):
        self.flush_function()