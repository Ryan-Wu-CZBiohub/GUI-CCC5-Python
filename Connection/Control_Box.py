from typing import Dict, List, Optional
from serial import Serial
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

class ControlBox:
    def __init__(self):
        self.connected = False
        self.serial_ports: Dict[str, Serial] = {}
        self.device_info: Dict[str, ListPortInfo] = {}
        self.valve_state: Dict[int, List[bool]] = {}  # 24 valve states per device


        self.device_states: Dict[str, List[bool]] = {}  # 24 valve states per device
        self.valve_to_port: Dict[int, str] = {}  # Maps valve ID to port

    def scanForDevices(self):
        self.device_info.clear()
        for port in comports():
            self.device_info[port.device] = port
        print("Available devices:")
        for port, info in self.device_info.items():
            print(f"{port}: {info.description}")

    def connectToAllDevices(self):
        valve_offset = 0
        for port in self.device_info:
            try:
                ser = Serial(port, baudrate=115200, timeout=1)
                self.serial_ports[port] = ser
                self.device_states[port] = [False] * 24
                print(f"Connected to {port}")

                for i in range(24):
                    self.valve_to_port[valve_offset + i + 1] = port
                valve_offset += 24
            except Exception as e:
                print(f"Failed to connect to {port}: {e}")

        self.connected = len(self.serial_ports) > 0

    def disconnect(self):
        for port, ser in self.serial_ports.items():
            if ser.is_open:
                ser.close()
                print(f"Disconnected from {port}")
        self.serial_ports.clear()
        self.device_states.clear()
        self.valve_to_port.clear()
        self.connected = False

    def getValveState(self, valve_id: int) -> Optional[bool]:
        port = self.valve_to_port.get(valve_id)
        if port is None:
            return None
        index = (valve_id - 1) % 24
        return self.device_states.get(port, [False]*24)[index]

    def setValveState(self, valve_id: int, state: bool):
        port = self.valve_to_port.get(valve_id)
        if not port:
            print(f"No port assigned for valve {valve_id}")
            return
        index = (valve_id - 1) % 24
        self.device_states[port][index] = state
        print(f"Valve {valve_id} set to {'ON' if state else 'OFF'} on {port}")

    def flush(self):
        for port, ser in self.serial_ports.items():
            states = self.device_states[port]
            a = self._convertToByte(states[0:8])
            b = self._convertToByte(states[8:16])
            c = self._convertToByte(states[16:24])
            ser.write(b'A' + a)
            ser.write(b'B' + b)
            ser.write(b'C' + c)
            ser.flush()
            print(f"Flushed states to {port}")

    def _convertToByte(self, bits: List[bool]) -> bytes:
        value = 0
        for i, bit in enumerate(bits):
            if bit:
                value |= 1 << i
        return bytes([value])

    

    def setAllValvesOff(self, total_valves: int = 96):
        for valve_id in range(1, total_valves + 1):
            self.setValveState(valve_id, False)
        self.flush()
        print("All valves set to OFF.")


    def setAllValvesOn(self, total_valves: int = 96):
        for valve_id in range(1, total_valves + 1):
            self.setValveState(valve_id, True)
        self.flush()
        print("All valves set to ON.")
