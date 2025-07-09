''' Custom Valve Controls Functions for GUI-CCC5 Application '''

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor

class ValveController:
    def __init__(self):
        self.on_color = QColor(0, 255, 0)       # Green for "OPEN"
        self.off_color = QColor(255, 0, 0)      # Red for "CLOSE"
        self.buttons = []                       # List to hold button references


    def toggleValve(self, button: QPushButton):
        """Handle individual valve toggle."""
        state = "opened" if button.isChecked() else "closed"
        color = self.on_color if button.isChecked() else self.off_color
        button.setStyleSheet(f"background-color: {color.name()};")
        print(f"Valve {button.text()} {state}")


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
