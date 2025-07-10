''' Custom Valve Controls Functions for GUI-CCC5 Application '''

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor

class ValveController:
    def __init__(self):
        self.on_color = QColor(135, 185, 245)       # Blue for "OPEN"
        self.off_color = QColor(255, 255, 55)    # Yellow for "CLOSE"
        self.buttons = []                       # List to hold button references


    def toggleValve(self, button: QPushButton):
        """Handle individual valve toggle."""
        is_open = button.isChecked()
        state = "OPEN" if is_open else "CLOSE"
        color = self.on_color if is_open else self.off_color

        valve_id = button.property("valve_id")
        button.setText(f"{valve_id} - {state}")
        button.setStyleSheet(f"color: black; background-color: {color.name()};")
        print(f"Valve {valve_id} {state}")


    def valveOpenAll(self):
        """Open all valves by toggling all buttons on."""
        for btn in self.buttons:
            if not btn.isChecked():
                btn.setChecked(True)
        print("All valves opened")

    
    def valveCloseAll(self):
        """Close all valves by toggling all buttons off."""
        for btn in self.buttons:
            if btn.isChecked():
                btn.setChecked(False)
        print("All valves closed")

    
