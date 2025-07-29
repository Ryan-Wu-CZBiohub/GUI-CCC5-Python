from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, \
    QListWidget, QListWidgetItem, QSpinBox, QComboBox, QHBoxLayout, QSizePolicy, QButtonGroup, QMenu, QInputDialog, QSpacerItem, QStackedLayout
from PySide6.QtCore import QTimer, QSize, Qt, QMimeData
from PySide6.QtGui import QDrag
from typing import Optional, List
import time
import math


from Connection.Connection import Connection
from Control.Panel_Controller import ValveController, PumpController


class ValveSlots(QWidget):
    def __init__(self, row, col, valve_panel):
        super().__init__()
        self.row = row
        self.col = col
        self.valve_panel = valve_panel
        self.layout = QStackedLayout(self)
        self.setLayout(self.layout)
        self.setFixedSize(self.valve_panel.valve_width, self.valve_panel.valve_height)

    def setValveButton(self, button: QPushButton):
        self.clearSlot()
        button.setFixedSize(
            self.valve_panel.valve_width,
            self.valve_panel.valve_height
        )
        self.layout.addWidget(button)

    def clearSlot(self):
        while self.layout.count():
            w = self.layout.widget(0)
            self.layout.removeWidget(w)
            w.setParent(None)


class ValvePanel(QWidget):
    def __init__(self, valve_panel=None, logger=None, control_box=None):
        super().__init__()
        self.logger = logger
        self.setStyleSheet("background-color: black; color: white;")
        
        self.control_box = control_box
        self.valve_controller = ValveController(self, logger=self.logger, control_box=self.control_box)
        
        valve_panel_layout = QVBoxLayout()

        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(0)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        valve_panel_layout.addLayout(self.grid_layout)

        self.deleted_buttons = []

        # Control buttons for all valves
        control_all_layout = QHBoxLayout()
        self.toggle_all_on_btn = QPushButton("All Valves - OPEN")
        self.toggle_all_on_btn.setCheckable(True)
        self.toggle_all_on_btn.setMinimumSize(50, 50)
        self.toggle_all_on_btn.setFixedSize(200, 30)
        self.toggle_all_on_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_on_btn.toggled.connect(self.valve_controller.valveOnAll)
        control_all_layout.addWidget(self.toggle_all_on_btn)
        valve_panel_layout.addLayout(control_all_layout)

        self.toggle_all_off_btn = QPushButton("All Valves - CLOSE")
        self.toggle_all_off_btn.setCheckable(True)
        self.toggle_all_off_btn.setMinimumSize(50, 50)
        self.toggle_all_off_btn.setFixedSize(200, 30)
        self.toggle_all_off_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.toggle_all_off_btn.toggled.connect(self.valve_controller.valveOffAll) 
        control_all_layout.addWidget(self.toggle_all_off_btn)

        self.reset_all_btn = QPushButton("Reset All Valves")
        self.reset_all_btn.setMinimumSize(50, 50)
        self.reset_all_btn.setFixedSize(200, 30)
        self.reset_all_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.reset_all_btn.clicked.connect(self.resetAllValves)
        control_all_layout.addWidget(self.reset_all_btn)

        # Set up the grid for valve slots
        self.grid_layout.setSpacing(0)
        self.valve_width = 70
        self.valve_height = 25
        self.rows = 21  # Number of rows in the grid
        self.cols = 12  # Number of columns in the grid
        self.slot_grid = {}
        
        for i in range(self.rows):
            for j in range(self.cols):
                slot = ValveSlots(i, j, self)
                self.grid_layout.addWidget(slot, i, j)
                self.slot_grid[(i, j)] = slot

        valve_id = 0        
        for i in range(self.rows):
            for j in range(self.cols):
                if valve_id >= 48:    #### Change this to the number of valves you want ####
                    break
        
                btn = DraggableValveButton(f"{valve_id} - CLOSE", valve_id, self)
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(self.showValveContextMenu)
                btn.setFixedSize(self.valve_width, self.valve_height)
                btn.setProperty("valve_id", valve_id)
                btn.setCheckable(True)
                btn.setEnabled(True)
                btn.setVisible(True)
                btn.setMinimumSize(75, 50)
                btn.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")
                btn.toggled.connect(self.handleValveToggle)

                self.slot_grid[(i, j)].setValveButton(btn)
                self.valve_controller.buttons[valve_id] = btn
                self.valve_controller.positions[valve_id] = (i, j)

                valve_id += 1
            if valve_id >= 48:    #### Change this to the number of valves you want
                break

        self.setLayout(valve_panel_layout)

    def handleValveToggle(self):
        """Handle the toggle action for a valve button."""
        button = self.sender()
        self.valve_controller.valveToggle(button)

    def showValveContextMenu(self, pos):
        """Show context menu for valve button actions."""
        button = self.sender()
        valve_id = button.property("valve_id")

        menu = QMenu(self)

        # Add more actions to the context menu here
        delete_action = menu.addAction("Delete")
        move_action = menu.addAction("Move")

        action = menu.exec_(button.mapToGlobal(pos))

        if action == delete_action:
            button.setEnabled(False)
            self.deleted_buttons.append((valve_id, button))
            self.valve_controller.buttons.pop(valve_id, None)
            self.valve_controller.positions.pop(valve_id, None)
            self.grid_layout.removeWidget(button)
            button.setParent(None)

        elif action == move_action:
            self.moveValveDialog(button, valve_id)

    def moveValveDialog(self, button, valve_id):
        """Open a dialog to move the valve button to a new position."""
        row, ok1 = QInputDialog.getInt(self, "Move Valve", "New Row (1-15):", 1, 1, 15)
        col, ok2 = QInputDialog.getInt(self, "Move Valve", "New Column (1-12):", 1, 1, 12)

        if ok1 and ok2:
            self.repositionValveButton(button, row - 1, col - 1)

    def repositionValveButton(self, button, new_row, new_col):
        """Reposition the valve button to a new grid slot."""
        valve_id = button.property("valve_id")

        old_pos = self.valve_controller.positions.get(valve_id)
        if old_pos:
            self.slot_grid[old_pos].clearSlot()

        self.slot_grid[(new_row, new_col)].setValveButton(button)
        self.valve_controller.positions[valve_id] = (new_row, new_col)

        self.valve_controller.buttons[valve_id] = button

    def resetAllValves(self):
        """Reset all valves to their default state and position."""
        for slot in self.slot_grid.values():
            slot.clearSlot()

        for valve_id, button in self.valve_controller.buttons.items():
            button.setEnabled(True)
            button.setChecked(False)
            button.setText(f"{valve_id} - CLOSE")
            button.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")

            row, col = divmod(valve_id, self.cols)
            self.slot_grid[(row, col)].setValveButton(button)

        for valve_id, button in self.deleted_buttons:
            button.setEnabled(True)
            button.setChecked(False)
            button.setText(f"{valve_id} - CLOSE")
            button.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")

            row, col = divmod(valve_id, self.cols)
            self.slot_grid[(row, col)].setValveButton(button)
            self.valve_controller.buttons[valve_id] = button
            self.valve_controller.positions[valve_id] = (row, col)

            button.setParent(self)
            button.show()

        self.deleted_buttons.clear()

        for valve_id, button in self.valve_controller.buttons.items():
            default_row, default_col = divmod(valve_id, self.cols)
            self.slot_grid[(default_row, default_col)].setValveButton(button)

            button.setChecked(False)
            button.setEnabled(True)
            button.setVisible(True)
            button.setText(f"{valve_id} - CLOSE")
            button.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")
            self.valve_controller.positions[valve_id] = (default_row, default_col)

        self.updateStatus("All valves reset.")    

    def updateStatus(self, message):
        """Update the status log with a new message."""
        if self.logger:
            self.logger(message)

    def clearAllSlots(self):
        """Clear all slots in the valve panel."""
        for slot in self.slot_grid.values():
            slot.clearSlot()
        self.valve_controller.buttons.clear()
        self.valve_controller.positions.clear()
        self.deleted_buttons.clear()
        self.updateStatus("All slots cleared.")


class DraggableValveButton(QPushButton):
    def __init__(self, text, valve_id, parent=None):
        super().__init__(text, parent)
        self.valve_id = valve_id
        self.setAcceptDrops(True)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(self.valve_id))
            drag.setMimeData(mime_data)
            drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_valve_id = int(event.mimeData().text())
        target_valve_id = self.valve_id
        self.parent().swapValves(source_valve_id, target_valve_id)
        event.acceptProposedAction()


# Not used in the current context, but kept for potential future use
class PumpPanel(QWidget):
    def __init__(self, logger=None, control_box=None):
        super().__init__()
        self.logger = logger
        self.pump_controller = PumpController(self, logger=self.logger)
        layout = QVBoxLayout()
        for pump_id in range(1, 4):
            btn = QPushButton(f"Pump {pump_id} - CLOSE")
            btn.setCheckable(True)
            btn.setMinimumSize(50, 50)
            btn.setProperty("pump_id", pump_id)
            btn.setStyleSheet(f"color: black; background-color: {self.pump_controller.btn_off_color};")
            btn.toggled.connect(self.handlePumpToggle)
            layout.addWidget(btn)
            self.pump_controller.buttons.append(btn)
        self.setLayout(layout)

    def handlePumpToggle(self):
        """Handle the toggle action for a pump button."""
        button = self.sender()
        self.pump_controller.pumpToggle(button)

    def updateStatus(self, message):
        """Update the status log with a new message."""
        if self.logger:
            self.logger(message)

# Not used in the current context, but kept for potential future use
class PortPanel(QWidget):
    def __init__(self, logger=None, control_box=None):
        super().__init__()
        self.control_box = control_box if control_box is not None else Connection()
        self.logger = logger
        self.setObjectName("PortPanel")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Device list ---
        self.device_list = QListWidget()
        main_layout.addWidget(QLabel("Connected Devices:"))
        main_layout.addWidget(self.device_list)

        self.solenoids_start_number = QSpinBox()
        self.solenoids_start_number.setMaximum(1000)
        self.solenoids_start_number.setMinimum(0)

        # --- Device info ---
        device_info_layout = QGridLayout()
        main_layout.addLayout(device_info_layout)

        self.enable_usb_box = ChoiceBox()
        device_info_layout.addWidget(QLabel("Enabled"), 0 , 0)
        device_info_layout.addWidget(self.enable_usb_box, 0 , 1)

        #  --- Buttons ---
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Ports")
        self.connect_btn = QPushButton("Connect")
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.connect_btn)
        main_layout.addLayout(button_layout)

        # --- Connections ---
        self.refresh_btn.clicked.connect(self.refreshDeviceList)

        # --- Initial scan
        self.refreshDeviceList()

    def refreshDeviceList(self):
        """Refresh the list of available serial ports."""
        self.device_list.clear()
        port_infos = Connection.listAvailablePorts()

        for port_info in port_infos:
            text = f"{port_info.device} - {port_info.description or 'Unknown'}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, port_info.device)
            self.device_list.addItem(item)

            if self.logger:
                self.logger(text)

# Not used in the current context, but kept for potential future use
class ChoiceBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItem("YES")
        self.addItem("NO")

    def IsTrue(self):
        return self.currentText() == "YES"

    def SetTrue(self, isTrue: bool):
        self.setCurrentText("YES" if isTrue else "NO")
    