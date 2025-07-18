from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton, \
    QListWidget, QListWidgetItem, QSpinBox, QComboBox, QHBoxLayout, QSizePolicy, QButtonGroup, QMenu, QInputDialog
from PySide6.QtCore import QTimer, QSize, Qt, QMimeData
from PySide6.QtGui import QDrag
from typing import Optional, List
import time
import math


from Connection.Connection import Connection, Device
from Control.Panel_Controller import ValveController, PumpController



class ValvePanel(QWidget):
    def __init__(self, valve_panel=None, logger=None, control_box=None):
        super().__init__()
        self.logger = logger
        self.setStyleSheet("background-color: black; color: white;")
        
        self.control_box = control_box
        self.valve_controller = ValveController(self, logger=self.logger, control_box=self.control_box)
        
        valve_panel_layout = QVBoxLayout()

        self.grid_layout = QGridLayout()
        valve_panel_layout.addLayout(self.grid_layout)

        self.deleted_buttons = []  # Store deleted buttons for potential reuse

        

        # Control buttons for all valves
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

        self.reset_all_btn = QPushButton("Reset All Valves")
        self.reset_all_btn.setMinimumSize(50, 50)
        self.reset_all_btn.setStyleSheet("color: black; background-color: lightgrey;")
        self.reset_all_btn.clicked.connect(self.resetAllValves)
        control_all_layout.addWidget(self.reset_all_btn)

        # Control buttons for individual valves
        # for i in range(8):
        #     row_layout = QHBoxLayout()
        #     for j in range(12):
        #         valve_id = i * 12 + j
        #         # btn = DraggableValveButton(f"Valve {valve_id} - OFF", valve_id, self)
        #         btn = QPushButton(f"Valve {valve_id} - OFF")
        #         btn.setCheckable(True)
        #         btn.setContextMenuPolicy(Qt.CustomContextMenu)
        #         btn.customContextMenuRequested.connect(self.showValveContextMenu)
        #         btn.setMinimumSize(50, 50)
        #         btn.setProperty("valve_id", valve_id)
        #         btn.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")
        #         btn.toggled.connect(self.handleValveToggle)

        #         row_layout.addWidget(btn)
        #         self.valve_controller.buttons.append(btn)
        #         # self.valve_controller.buttons[valve_id] = btn
        #     valve_panel_layout.addLayout(row_layout)
            
        for i in range(8):
            for j in range(12):
                valve_id = i * 12 + j
                btn = DraggableValveButton(f"Valve {valve_id} - OFF", valve_id, self)
                btn.setCheckable(True)
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.customContextMenuRequested.connect(self.showValveContextMenu)
                btn.setMinimumSize(50, 50)
                btn.setProperty("valve_id", valve_id)
                btn.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")
                btn.toggled.connect(self.handleValveToggle)

                self.grid_layout.addWidget(btn, i, j)
                # self.valve_controller.buttons.append(btn)
                self.valve_controller.buttons[valve_id] = btn
                self.valve_controller.positions[valve_id] = (i, j)

          
        self.setLayout(valve_panel_layout)


    def handleValveToggle(self):
        button = self.sender()
        self.valve_controller.valveToggle(button)

    def showValveContextMenu(self, pos):
        button = self.sender()
        valve_id = button.property("valve_id")

        menu = QMenu(self)

        # Only two options now:
        delete_action = menu.addAction("Delete")
        move_action = menu.addAction("Move...")

        action = menu.exec_(button.mapToGlobal(pos))

        if action == delete_action:
            # Disable and remove the button from grid and tracking
            button.setEnabled(False)
            self.deleted_buttons.append((valve_id, button))
            self.valve_controller.buttons.pop(valve_id, None)
            self.valve_controller.positions.pop(valve_id, None)
            self.grid_layout.removeWidget(button)
            button.setParent(None)  # keeps it in memory

        elif action == move_action:
            self.moveValveDialog(button, valve_id)

    def moveValveDialog(self, button, valve_id):
        row, ok1 = QInputDialog.getInt(self, "Move Valve", "New Row (1-15):", 1, 1, 15)
        col, ok2 = QInputDialog.getInt(self, "Move Valve", "New Column (1-15):", 1, 1, 15)

        if ok1 and ok2:
            self.repositionValveButton(button, row, col)

    def repositionValveButton(self, button, new_row, new_col):
        self.grid_layout.removeWidget(button)
        self.grid_layout.addWidget(button, new_row, new_col)

        # Keep original valve_id
        valve_id = button.property("valve_id")

        # Update only the layout mapping, not the ID or text
        self.valve_controller.positions[valve_id] = (new_row, new_col)

    def resetAllValves(self):
        # Make a copy of deleted buttons so we can safely modify the original list
        for valve_id, button in list(self.deleted_buttons):
            # Restore default state
            button.setEnabled(True)
            button.setChecked(False)
            button.setText(f"Valve {valve_id} - OFF")
            button.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")

            # Determine where to place the button
            row, col = divmod(valve_id, 12)
            self.grid_layout.addWidget(button, row, col)

            # Restore tracking
            self.valve_controller.buttons[valve_id] = button
            self.valve_controller.positions[valve_id] = (row, col)

            button.setParent(self)
            button.show()

        # Clear deleted list after full restore
        self.deleted_buttons.clear()

        # Reset all visible buttons
        for valve_id, button in self.valve_controller.buttons.items():
            button.setChecked(False)
            button.setEnabled(True)
            button.setVisible(True)
            button.setText(f"Valve {valve_id} - OFF")
            button.setStyleSheet(f"color: black; background-color: {self.valve_controller.btn_off_color};")

        self.updateStatus("All valves reset.")

    def updateStatus(self, message):
        if self.logger:
            self.logger(message)


class PumpPanel(QWidget):
    def __init__(self, logger=None, control_box=None):
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

        # self.enable_usb_box = ChoiceBox()
        # device_info_layout.addWidget(QLabel("Enabled"), 0 , 0)
        # device_info_layout.addWidget(self.enable_usb_box, 0 , 1)

         # --- Buttons ---
    #     button_layout = QHBoxLayout()
    #     self.refresh_btn = QPushButton("Refresh Ports")
    #     self.connect_btn = QPushButton("Connect")
    #     button_layout.addWidget(self.refresh_btn)
    #     button_layout.addWidget(self.connect_btn)
    #     main_layout.addLayout(button_layout)

    #     # --- Connections ---
    #     self.refresh_btn.clicked.connect(self.refreshDeviceList)

    #     # --- Initial scan
    #     self.refreshDeviceList()

    # def refreshDeviceList(self):
    #     """Refresh the list of available serial ports."""
    #     self.device_list.clear()
    #     port_infos = Connection.listAvailablePorts()

    #     for port_info in port_infos:
    #         text = f"{port_info.device} - {port_info.description or 'Unknown'}"
    #         item = QListWidgetItem(text)
    #         item.setData(Qt.UserRole, port_info.device)
    #         self.device_list.addItem(item)

    #         if self.logger:
    #             self.logger(text)


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