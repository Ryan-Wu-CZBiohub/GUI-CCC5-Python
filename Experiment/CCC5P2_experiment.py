""" 
Experiment description:
First test for Type II diabetes cells (TC-6) in CCC5. The goal is
to reconfirm some of the previous results and add a little bit of
new experiments with different time interval of feeding. Another
goal is to test the functionality of the new chip CCC5p2. 
This script is designed to run a specific experiment for the CCC5P2 project.

Program flow:

"""

import json
import time
import datetime
from threading import Event
from typing import List, Dict
from PySide6.QtCore import QThreadPool, Slot, QRunnable, QTimer
import sys
import os
import traceback
try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()  # Fallback if __file__ is undefined

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
from Connection.Connection import Connection

## === Experiment Configuration ===
inputValve = [24] + list(range(46, 27, -1))  # 24, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45
OS = list(range(0 , 201))
valveID = {
    "mux": [26, 23, 22, 21, 20, 19, 18, 17],   # multiplexer valves
    "purge": 27,                               # purge valve
    "fresh" : 24,                              # fresh medium valve
    "bypass": [14, 11, 8, 5, 2],               # bypass valves
    "chamberIn": [
        [16, 15],
        [13, 12],
        [10, 9],
        [7, 6],
        [4, 3]                                 # chamber inlet valves
    ],
    "muxIn": 25                                # multiplexer inlet valve
}
# Waiting & Feeding Timings in seconds
Timings = {
    "purgeTime1": 5,
    "purgeTime2": 10,
    "purgeTime3": 5,
    "prefillTime": 10,
    "feedTime": 8,
}


def generateExperimentMatrix() -> List[List[int]]:
    expMatrix = []
    offset_num = 0

    def addSchedule(row_num, in_num, time_points):
        nonlocal offset_num
        for col_num in range(1, 17):
            offset_num += 1
            for time in time_points:
                time_min = time + OS[offset_num - 1]
                input_idx = in_num[col_num - 1]
                input_valve = inputValve[input_idx - 1]
                expMatrix.append([time_min, input_valve, row_num, col_num, 2, 0])

    # Row 1: every 6 hours
    addSchedule(1, 
                [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 5, 8, 10, 11, 14], 
                [0, 360, 720, 1080, 1440, 1800, 2160, 2520, 2880, 3240]
    )
    # Row 2: every 8 hours
    addSchedule(2, 
                [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 5, 8, 10, 11, 13], 
                [0, 480, 960, 1440, 1920, 2880, 3360, 4320]
    )
    # Row 3: mixed 6/6/12 hours
    addSchedule(3, 
                [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 5, 8, 10, 11, 13], 
                [0, 360, 720, 1440, 1800, 2160, 2880, 3240, 3600, 4320]
    )
    # Row 4: 8 and 16 hours intervals
    addSchedule(4, 
                [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 5, 8, 10, 11, 13], 
                [0, 480, 1440, 1920, 2880, 3360, 4320]
    )
    # Row 5: 12 hours intervals
    addSchedule(5, 
                [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 5, 8, 10, 11, 13], 
                [0, 720, 1440, 2160, 2880, 3600, 4320]
    )

    expMatrix.sort(key=lambda row: row[0])  # Sort by time
    return expMatrix

def setMuxValves(connection: Connection, mux_valves: List[int], index: int):
    states = {vid: 0 for vid in mux_valves}
    if 0 <= index < len(mux_valves):
        states[mux_valves[index]] = 1
    connection.setValveStates(states)

def runExperimentMatrix(connection: Connection, matrix_mat: List[List[int]], delay_min: float = 60, bypass_on: bool = False):
    log = []
    now = datetime.datetime.now()
    exp_matrix_adj = [[now + datetime.timedelta(minutes=row[0] + delay_min)] + row[1:] for row in matrix_mat]

    for row in exp_matrix_adj:
        scheduled_time , input_valve, row_num, col_num, side, _ = row
        while datetime.datetime.now() < scheduled_time:
            time.sleep(0.5)

        # TODO: Pause check

        row_idx = row_num - 1
        mux_idx = col_num - 1
        valves = valveID

        # Mux setup
        setMuxValves(connection, valves["mux"], mux_idx)

        # Open bypass & path
        connection.setValveState(valves["bypass"][row_idx], True)
        connection.setValveState(input_valve, True)
        connection.setValveState(valves["muxIn"], True)
        connection.setValveState(valves["purge"], True)
        time.sleep(Timings["purgeTime1"])

        # Stop purge & wait
        connection.setValveState(valves["purge"], False)
        time.sleep(Timings["prefillTime"])

        # Close bypass during feeding
        if not bypass_on:
            connection.setValveState(valves["bypass"][row_idx], False)

        # Feed the chamber
        left, right = valves["chamberIn"][row_idx]
        if side == 0:
            connection.setValveState(left, True)
        elif side == 1:
            connection.setValveState(right, True)
        elif side == 2:
            connection.setValveState(left, True)
            connection.setValveState(right, True)

        time.sleep(Timings["feedTime"])

        # Stop feeding
        connection.setValveState(left, False)
        connection.setValveState(right, False)
        connection.setValveState(valves["bypass"][row_idx], True)
        connection.setValveState(input_valve, False)
        time.sleep(1)

        # Purge the chamber with refresh medium
        connection.setValveState(valves["purge"], True)
        connection.setValveState(valves["fresh"], True)
        time.sleep(Timings["purgeTime2"])
        connection.setValveState(valves["purge"], False)
        time.sleep(Timings["purgeTime3"])

        # Cleanup
        connection.setValveState(valves["fresh"], False)
        connection.setValveState(valves["muxIn"], False)
        setMuxValves(connection, valves["mux"], -1)  # Close all mux valves
        for bypass_valve in valves["bypass"]:
            connection.setValveState(bypass_valve, False)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = [input_valve, row_num, col_num, side, timestamp]
        log.append(log_entry)
        print(f"{timestamp} → Feed Input Valve {input_valve} → Row {row_num}, Column {col_num}, Side {side}")

    return log

def saveExperimentMatrixToJson(filename: str, matrix: List[List[int]]):
    with open(filename, 'w') as f:
        json.dump({'matrix': matrix}, f, indent=2)
        print(f"Saved experiment matrix to {filename}")

def loadExperimentMatrixFromJson(filename: str) -> List[List[int]]:
    with open(filename, 'r') as f:
        data = json.load(f)
        return data.get('matrix', [])
    
def runFromGui(gui, delay_min: float = 0):
    try:
        print("Type of gui:", type(gui))
        print("Has control_box:", hasattr(gui, "control_box"))
        print("Has logMessage:", hasattr(gui, "logMessage"))

        gui.logMessage("Starting experiment in background...")
        runner = ExperimentRunner(gui, delay_min=delay_min)
        QThreadPool.globalInstance().start(runner)

    except Exception as e:
        error_msg = f"Error running experiment: {e}"
        tb = traceback.format_exc()
        gui.logMessage(error_msg)
        gui.logMessage(tb)
        print(tb)


class ExperimentRunner(QRunnable):
    def __init__(self, gui, delay_min=0):
        super().__init__()
        self.gui = gui
        self.delay_min = delay_min
        self._pause_event = Event()
        self._pause_event.set()  # Start in unpaused state

    @Slot()
    def run(self):
        try:
            from Experiment.CCC5P2_experiment import generateExperimentMatrix, runExperimentMatrix

            matrix = generateExperimentMatrix()
            connection = self.gui.control_box
            log = runExperimentMatrix(connection, matrix, delay_min=self.delay_min, bypass_on=False)
            
            print(f"[Runner] Queuing log: {msg}")
            # Safely log completion message
            QTimer.singleShot(0, lambda: self.gui.logMessage("Experiment completed."))

            # Safely log each feed entry
            for row in log:
                msg = f"Row {row[1]} Col {row[2]}, Side {row[3]} - Input Valve {row[0]} fed at {row[4]}"
                # print statement for debugging

                print(msg)
                QTimer.singleShot(0, lambda m=msg: self.gui.logMessage(m))

        except Exception as e:
            tb = traceback.format_exc()
            QTimer.singleShot(0, lambda: self.gui.logMessage(f"Experiment failed: {e}"))
            QTimer.singleShot(0, lambda: self.gui.logMessage(tb))
        
    def pause(self):
        """Pause the experiment."""
        self._pause_event.clear()
        QTimer.singleShot(0, lambda: self.gui.logMessage("Experiment paused."))

    def resume(self):
        """Resume the experiment."""
        self._pause_event.set()
        QTimer.singleShot(0, lambda: self.gui.logMessage("Experiment resumed."))

    def is_paused(self):
        """Check if the experiment is paused."""
        return not self._pause_event.is_set()    


def main():
    use_test = False

    if use_test:
        expMatrix = [
            [0, 46, 1, 1, 2, 0],
            [1, 46, 1, 2, 2, 0],
            [2, 46, 1, 3, 2, 0],
            [3, 46, 1, 4, 2, 0],
        ]
    else:
        expMatrix = generateExperimentMatrix()
        saveExperimentMatrixToJson("CCC5p2_ExpMatrix.json", expMatrix)

    connect = Connection()
    connect.scanForDevices()

    log = runExperimentMatrix(connect, expMatrix, delay_min=0, bypass_on=False)
    # log = runExperimentMatrix(connect, test_matrix, delay_min=0, bypass_on=False)

    with open('CCC5p2_ExpLog_Test.json', 'w') as f:
        json.dump({'expLog': log}, f, indent=2)
    print("Experiment completed and logged.")

if __name__ == '__main__':
    main()