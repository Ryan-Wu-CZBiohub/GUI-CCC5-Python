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
valveInput = [24] + list(range(46, 27, -1))   
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


def generateExperimentMatrix(time_scale=1.0) -> List[List[int]]:
    expMatrix = []
    offset_num = 0

    def addSchedule(row_num, in_num, time_points):
        nonlocal offset_num
        for col_num in range(1, 17):
            offset_num += 1
            for time in time_points:
                time_min = (time + OS[offset_num - 1]) * time_scale
                input_idx = in_num[col_num - 1]
                input_valve = valveInput[input_idx - 1]
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
    """Set the state of the multiplexer valves based on the index."""
    states = {vid: 0 for vid in mux_valves}
    if 0 <= index < len(mux_valves):
        states[mux_valves[index]] = 1
    connection.setValveStates(states)

def adjusted_sleep(duration: float, test_mode: bool):
    """Sleep for the given duration, sped up in test mode."""
    if test_mode:
        time.sleep(duration / 100.0)
    else:
        time.sleep(duration)

def runExperimentMatrix(connection: Connection, matrix_mat: List[List[int]], delay_min: float = 60, bypass_on: bool = False, test_mode: bool = False) -> List[List[int]]:
    """Run the experiment matrix on the given connection."""
    log = []
    start_time = datetime.datetime.now()
    now = start_time
    delta_fn = (lambda t: datetime.timedelta(seconds=t)) if test_mode else (lambda t: datetime.timedelta(minutes=t))
    exp_matrix_adj = [[now + delta_fn(row[0] + delay_min)] + row[1:] for row in matrix_mat]

    for row in exp_matrix_adj:
        scheduled_time , input_valve, row_num, col_num, side, _ = row
        sleep_step = 0.5 if not test_mode else 0.01
        while datetime.datetime.now() < scheduled_time:
            time.sleep(sleep_step)

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
        # time.sleep(Timings["purgeTime1"])
        adjusted_sleep(Timings["purgeTime1"], test_mode)

        # Stop purge & wait
        connection.setValveState(valves["purge"], False)
        # time.sleep(Timings["prefillTime"])
        adjusted_sleep(Timings["prefillTime"], test_mode)

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

        # time.sleep(Timings["feedTime"])
        adjusted_sleep(Timings["feedTime"], test_mode)

        # Stop feeding
        connection.setValveState(left, False)
        connection.setValveState(right, False)
        connection.setValveState(valves["bypass"][row_idx], True)
        connection.setValveState(input_valve, False)
        # time.sleep(1)
        adjusted_sleep(1, test_mode)

        # Purge the chamber with refresh medium
        connection.setValveState(valves["purge"], True)
        connection.setValveState(valves["fresh"], True)
        # time.sleep(Timings["purgeTime2"])
        adjusted_sleep(Timings["purgeTime2"], test_mode)
        connection.setValveState(valves["purge"], False)
        # time.sleep(Timings["purgeTime3"])
        adjusted_sleep(Timings["purgeTime3"], test_mode)

        # Cleanup
        connection.setValveState(valves["fresh"], False)
        connection.setValveState(valves["muxIn"], False)
        setMuxValves(connection, valves["mux"], -1)  # Close all mux valves
        for bypass_valve in valves["bypass"]:
            connection.setValveState(bypass_valve, False)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.append({
            "type": "feed",
            "valve": input_valve,
            "row": row_num,
            "col": col_num,
            "side": side,
            "timestamp": timestamp
        })
        print(f"{timestamp} → Feed Input Valve {input_valve} → Row {row_num}, Column {col_num}, Side {side}")

    # Final cleanup
    print("Experiment completed. Closing all valves...")
    for vid in set(valveInput + valveID["mux"] + [valveID["purge"], valveID["fresh"], valveID["muxIn"]] + valveID["bypass"] + sum(valveID["chamberIn"], [])):
        connection.setValveState(vid, False)

    end_time = datetime.datetime.now()
    log.append({
        "type": "experiment_end",
        "timestamp": end_time.strftime('%Y-%m-%d %H:%M:%S')
    })

    metadata = {
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "duration_sec": (end_time - start_time).total_seconds(),
        "delay_min": delay_min,
        "bypass_on": bypass_on,
        "test_mode": test_mode,
        "num_feeds": len([e for e in log if e["type"] == "feed"])
    }

    return {
        "metadata": metadata,
        "expLog": log
    }

def saveExperimentMatrixToJson(filename: str, matrix: List[List[int]]):
    """Save the experiment matrix to a JSON file."""
    with open(filename, 'w') as f:
        f.write('{\n  "matrix": [\n')
        for i, row in enumerate(matrix):
            line = '    ' + json.dumps(row)
            if i < len(matrix) - 1:
                line += ','
            f.write(line + '\n')
        f.write('  ]\n}')
    print(f"Saved experiment matrix to {filename}")

def loadExperimentMatrixFromJson(filename: str) -> List[List[int]]:
    """Load the experiment matrix from a JSON file."""
    with open(filename, 'r') as f:
        data = json.load(f)
        return data.get('matrix', [])
    
def runFromGui(gui, delay_min: float = 0):
    """Run the experiment from the GUI, using a background thread."""
    try:
        if gui.experiment_runner and gui.experiment_runner.isRunning():
            gui.logMessage("Experiment is already running.")
            return
        
        print("Type of gui:", type(gui))
        print("Has control_box:", hasattr(gui, "control_box"))
        print("Has logMessage:", hasattr(gui, "logMessage"))

        gui.logMessage("Starting experiment in background...")
        runner = ExperimentRunner(gui, delay_min=delay_min, test_mode=False)  # test_mode set here

    except Exception as e:
        error_msg = f"Error running experiment: {e}"
        tb = traceback.format_exc()
        gui.logMessage(error_msg)
        gui.logMessage(tb)
        print(tb)


class ExperimentRunner(QRunnable):
    def __init__(self, gui, delay_min=0, test_mode=False):
        super().__init__()
        self.gui = gui
        self.delay_min = delay_min
        self._pause_event = Event()
        self._pause_event.set()  # Start in unpaused state
        self._is_running = True
        self.test_mode = test_mode

    @Slot()
    def run(self):
        try:
            from Experiment.CCC5P2_experiment import generateExperimentMatrix, runExperimentMatrix
            
            time_scale = 1 / 100 if self.test_mode else 1.0  # Scale down the experiment time by 60x for testing
            test_mode = self.test_mode

            expMatrix = generateExperimentMatrix(time_scale=time_scale)
            saveExperimentMatrixToJson("CCC5p2_ExpMatrix.json", expMatrix)
            connection = self.gui.control_box
            
            expResults = runExperimentMatrix(
                connection,
                expMatrix,
                delay_min=self.delay_min,
                bypass_on=False,
                test_mode=test_mode
            )

            with open('CCC5p2_ExpLog.json', 'w') as f:
                json.dump(expResults, f, indent=2)
            
            QTimer.singleShot(0, lambda: self.gui.logMessage("Experiment completed."))

        except Exception as e:
            tb = traceback.format_exc()
            QTimer.singleShot(0, lambda: self.gui.logMessage(f"Experiment failed: {e}"))
            QTimer.singleShot(0, lambda: self.gui.logMessage(tb))

        finally:
            self._is_running = False
        
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
    
    def isRunning(self):
        """Check if the experiment is running."""
        return self._is_running


def main():
    test_mode = True  # Set to True for testing, False for actual run

    if test_mode:
        expMatrix = generateExperimentMatrix(time_scale=1/100)  # Scale down to seconds for testing
        print("First 5 scheduled times:")
        for row in expMatrix[:5]:
            print(f"{row[0]:.2f} seconds")
        saveExperimentMatrixToJson("CCC5p2_ExpMatrix_Test.json", expMatrix)
    else:
        expMatrix = generateExperimentMatrix()
        saveExperimentMatrixToJson("CCC5p2_ExpMatrix_Test.json", expMatrix)

    connect = Connection()
    connect.scanForDevices()

    expResults = runExperimentMatrix(connect, expMatrix, delay_min=0, bypass_on=False, test_mode=test_mode)

    with open('CCC5p2_ExpLog_Test.json', 'w') as f:
        json.dump(expResults, f, indent=2)

if __name__ == '__main__':
    main()