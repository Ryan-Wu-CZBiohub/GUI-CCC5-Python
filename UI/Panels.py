'''Custom GUI Class for Pump Control Panel'''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMenuBar, QSizePolicy, QStatusBar, QToolBar, QMessageBox, QGridLayout
)


class PumpPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        for pump_id in range(1, 4):
            btn = QPushButton(f"Pump {pump_id} - OFF")
            btn.setCheckable(True)
            btn.setMinimumSize(50, 50)
            btn.setProperty("pump_id", pump_id)
            btn.setStyleSheet("color: black; background-color: lightgray;")
            layout.addWidget(btn)
        self.setLayout(layout)


    def handlePumpToggle(self):
        button = self.sender()
        is_on = button.isChecked()
        state = "ON" if is_on else "OFF"
        pump_id = button.property("pump_id")
        button.setText(f"Pump {pump_id} - {state}")
        color = "green" if is_on else "red"
        button.setStyleSheet(f"color: black; background-color: {color};")
        print(f"Pump {pump_id} turned {state}")
