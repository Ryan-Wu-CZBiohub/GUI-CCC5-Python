from typing import Dict, List, Optional
from serial import Serial
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo
from PySide6.QtCore import QObject, Signal

import json
import os


class Connection(QObject):
    valveStateChanged = Signal(int, bool)

    def __init__(self):
        super().__init__()
        self.valve_states: Dict[int, bool] = {}  # Global valve state map
        self.devices: List[Device] = []          # List of connected Device instances
        config_path = "Connection/Valve_Port_Map.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.PORT_TO_START = json.load(f)
        else:
            print(f"Warning: {config_path} not found.")

    def scanForDevices(self):
        """Scan for available devices and update their states."""
        port_infos = sorted(comports(), key=lambda p: p.device)
        seen_hwids = {d.port_info.hwid for d in self.devices if d.port_info}

        for device in self.devices:
            match = next((p for p in port_infos if device.port_info and p.hwid == device.port_info.hwid), None)
            if match:
                device.port_info = match
                device.available = True
                if device.enabled:
                    device.connect()
            else:
                device.available = False
                device.disconnect()

        for port_info in port_infos:
            if port_info.hwid not in seen_hwids and port_info.hwid != "":
                new_device = Device()
                new_device.port_info = port_info
                new_device.available = True
                new_device.enabled = True 
                port = port_info.device
                if port in self.PORT_TO_START:
                    config = self.PORT_TO_START[port]
                    if isinstance(config, dict):
                        new_device.start_number = config.get("start_number", 0)
                        new_device.polarities = config.get("polarities", [False, False, False])
                    else:
                        # fallback for older format (backward compatibility)
                        new_device.start_number = config
                        new_device.polarities = [False, False, False]
                else:
                    print(f"Port {port} not in PORT_TO_START, assigning defaults")
                    new_device.start_number = 0
                    new_device.polarities = [False, False, False]
        
                new_device.connect()
                self.devices.append(new_device)

        for device in self.devices:
            for i in range(device.start_number, device.start_number + 24):
                self.valve_states[i] = False
        self.flush()

        print("=== Device Port-to-Valve Mapping ===")
        for device in self.devices:
            port = device.port_info.device if device.port_info else "UNKNOWN"
            print(f"{port}: valves {device.start_number} to {device.start_number + 23}")

    @staticmethod
    def listAvailablePorts():
        """List available serial ports with descriptions."""
        port_infos = sorted(comports(), key=lambda p: p.device)
        print("Available serial ports:")
        for port_info in port_infos:
            print(f"{port_info.device} - {port_info.description} ({port_info.hwid})")
        return port_infos

    def disconnectAll(self):
        """Disconnect all devices."""
        for device in self.devices:
            device.disconnect()

    def setValveState(self, number: int, state: bool): 
        """Set the state of a specific valve."""
        self.valve_states[number] = state
        self.flush()
        self.valveStateChanged.emit(number, state)

    def setValveStates(self, state_dict: Dict[int, bool]):
        """Set multiple valve states from a dictionary."""
        for number, state in state_dict.items():
            self.setValveState(number, state)
        self.flush()

    def getValveState(self, number: int) -> bool:
        """Get the state of a specific valve."""
        return self.valve_states.get(number, False)

    def flush(self):
        """Flush the current valve states to all connected devices."""
        for device in self.devices:
            device.setValves(self.valve_states)

    def getConnectedValveIds(self) -> List[int]:
        """Get a list of valve IDs for all connected devices."""
        ids = []
        for device in self.devices:
            if device.enabled and device.isConnected():
                for i in range(device.start_number, device.start_number + 24):
                    ids.append(i)
        return ids


class Device:
    def __init__(self):
        self.port_info: Optional[ListPortInfo] = None
        self.start_number = 0
        self.polarities = [True, True, True]
        self.enabled = False
        self.available = False
        self.serial_port: Optional[Serial] = None
        self.solenoid_states = [False] * 24

    def isConnected(self):
        """Check if the device is connected."""
        return self.serial_port is not None and self.serial_port.is_open

    def connect(self):
        """Connect to the device if not already connected."""
        if self.isConnected() or not self.port_info:
            return
        try:
            self.serial_port = Serial(self.port_info.device, baudrate=115200, timeout=0, write_timeout=0)
            self.serial_port.write(b'!A' + bytes([0]))
            self.serial_port.write(b'!B' + bytes([0]))
            self.serial_port.write(b'!C' + bytes([0]))
            self.serial_port.flush()
            print(f"Connected to {self.port_info.device}")
        except Exception as e:
            print(f"Failed to connect to {self.port_info.device}: {e}")
            self.serial_port = None

    def disconnect(self):
        """Disconnect from the device."""
        if self.isConnected():
            self.serial_port.close()
            print(f"Disconnected from {self.port_info.device}")
        self.serial_port = None

    def setValves(self, global_states: Dict[int, bool]):
        """Set the states of valves based on global states."""
        if not self.enabled or not self.isConnected():
            return

        for i in range(self.start_number, self.start_number + 24):
            self.solenoid_states[i - self.start_number] = global_states.get(i, False)

        polarized = [state != self.polarities[i // 8] for i, state in enumerate(self.solenoid_states)]
        a = convertToByte(polarized[0:8])
        b = convertToByte(polarized[8:16])
        c = convertToByte(polarized[16:24])
        self.write(b'A' + a)
        self.write(b'B' + b)
        self.write(b'C' + c)

    def flush(self):
        """Flush the serial port to ensure all data is sent."""
        if self.serial_port:
            self.serial_port.flush()

    def write(self, data):
        """Write data to the serial port."""
        if self.serial_port:
            try:
                self.serial_port.write(data)
            except Exception as e:
                print(f"Write failed on {self.port_info.device}: {e}")

def convertToByte(bits: List[bool]) -> bytes:
    """Convert a list of boolean values to a single byte."""
    value = 0
    for i, bit in enumerate(bits):
        if bit:
            value |= 1 << i
    return bytes([value])

def refreshDeviceList():
    """Refresh the list of available serial ports."""
    port_infos = sorted(comports(), key=lambda p: p.device)
    print("Available serial ports:")
    for port_info in port_infos:
        print(f"{port_info.device} - {port_info.description} ({port_info.hwid})")
    return port_infos


