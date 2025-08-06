""" 
This script is designed to run a specific experiment for the CCC5P2 project.

Program flow:

"""

import json
import time
import datetime
from threading import Event
from typing import List
from PySide6.QtCore import QThreadPool, Slot, QRunnable, QTimer
import sys
import os
import traceback

try:
    BASE_DIR = os.path.dirname(__file__)
except NameError:
    BASE_DIR = os.getcwd()

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
from Connection.Connection import Connection
from Experiment.experiment_config import (
    EXPERIMENT_NAME,
    EXPERIMENT_TOTAL_TIME,
    EXPERIMENT_CONFIG,
    INPUT_TO_CONTROL_MAP,
    VALVE_ID,
    TIMING_CONFIG,
    offset_schedule
)

def generateExperimentMatrix(time_scale=1.0) -> List[List[int]]:
    # Each entry: [time_min, valve_number, row, column, side, _]
    expMatrix = []
    offset_num = 0
    side = 2
    _ = 0

    for block in EXPERIMENT_CONFIG:
        row = block["row"]
        column_to_input = block["column_to_input"]

        intervals = block.get("intervals", [block.get("interval")])
        if not isinstance(intervals, list):
            raise TypeError(f"'intervals' must be a list: {block}")

        for col, input_idx in column_to_input.items():
            input_info = INPUT_TO_CONTROL_MAP.get(input_idx)
            if not input_info:
                continue
            valve = input_info["valve"]

            for interval in intervals:
                if not isinstance(interval, (int, float)):
                    raise TypeError(f"Interval must be int/float: {interval}")
                time_min = (interval + offset_schedule(offset_num)) * time_scale
                expMatrix.append([time_min, valve, row, col, side, _])

            offset_num += 1

    expMatrix.sort(key=lambda row: row[0])
    return expMatrix

def setMuxValves(connection: Connection, mux_valves: List[int], index: int):
    states = {vid: 0 for vid in mux_valves}
    if 0 <= index < len(mux_valves):
        states[mux_valves[index]] = 1
    connection.setValveStates(states)

def adjusted_sleep(duration: float, test_mode: bool):
    time.sleep(duration / 180.0 if test_mode else duration)

def runExperimentMatrix(connection: Connection, matrix_mat: List[List[int]], delay_min=60, bypass_on=False, test_mode=False):
    log = []
    start_time = datetime.datetime.now()
    delta_fn = (lambda t: datetime.timedelta(seconds=t)) if test_mode else (lambda t: datetime.timedelta(minutes=t))
    now = start_time
    exp_matrix_adj = [[now + delta_fn(row[0] + delay_min)] + row[1:] for row in matrix_mat]

    for row in exp_matrix_adj:
        scheduled_time, input_valve, row_num, col_num, side, _ = row
        sleep_step = 0.5 if not test_mode else 0.01
        while datetime.datetime.now() < scheduled_time:
            time.sleep(sleep_step)

        row_idx = row_num - 1
        mux_idx = col_num - 1

        # Mux setup
        setMuxValves(connection, VALVE_ID["mux"], mux_idx)

        # Open path
        connection.setValveState(VALVE_ID["bypass"][row_idx], True)
        connection.setValveState(input_valve, True)
        connection.setValveState(VALVE_ID["muxIn"], True)
        connection.setValveState(VALVE_ID["purge"], True)
        adjusted_sleep(TIMING_CONFIG["purgeTime1"], test_mode)

        connection.setValveState(VALVE_ID["purge"], False)
        adjusted_sleep(TIMING_CONFIG["prefillTime"], test_mode)

        if not bypass_on:
            connection.setValveState(VALVE_ID["bypass"][row_idx], False)

        left, right = VALVE_ID["chamberIn"][row_idx]
        if side == 0: connection.setValveState(left, True)
        elif side == 1: connection.setValveState(right, True)
        elif side == 2:
            connection.setValveState(left, True)
            connection.setValveState(right, True)

        adjusted_sleep(TIMING_CONFIG["feedTime"], test_mode)

        connection.setValveState(left, False)
        connection.setValveState(right, False)
        connection.setValveState(VALVE_ID["bypass"][row_idx], True)
        connection.setValveState(input_valve, False)
        adjusted_sleep(1, test_mode)

        connection.setValveState(VALVE_ID["purge"], True)
        connection.setValveState(VALVE_ID["fresh"], True)
        adjusted_sleep(TIMING_CONFIG["purgeTime2"], test_mode)
        connection.setValveState(VALVE_ID["purge"], False)
        adjusted_sleep(TIMING_CONFIG["purgeTime3"], test_mode)

        # Cleanup
        connection.setValveState(VALVE_ID["fresh"], False)
        connection.setValveState(VALVE_ID["muxIn"], False)
        setMuxValves(connection, VALVE_ID["mux"], -1)
        for vid in VALVE_ID["bypass"]:
            connection.setValveState(vid, False)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.append({
            "type": "feed", "valve": input_valve, "row": row_num,
            "col": col_num, "side": side, "timestamp": timestamp
        })
        print(f"{timestamp} → Feed Input Valve {input_valve} → Row {row_num}, Column {col_num}, Side {side}")

    # Final cleanup
    print("Experiment completed. Closing all valves...")
    all_valves = {v for v in range(28, 47)} | set(sum(VALVE_ID["chamberIn"], [])) | \
                 set(VALVE_ID["mux"]) | set(VALVE_ID["bypass"]) | \
                 {VALVE_ID["purge"], VALVE_ID["fresh"], VALVE_ID["muxIn"]}
    for vid in all_valves:
        connection.setValveState(vid, False)

    end_time = datetime.datetime.now()
    log.append({
        "type": "experiment_end",
        "timestamp": end_time.strftime('%Y-%m-%d %H:%M:%S')
    })

    return {
        "metadata": {
            "experiment_name": EXPERIMENT_NAME,
            "experiment_total_time_min": EXPERIMENT_TOTAL_TIME,
            "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_min": (end_time - start_time).total_seconds() / 60,
            "delay_min": delay_min,
            "bypass_on": bypass_on,
            "test_mode": test_mode,
            "num_feeds": len([e for e in log if e["type"] == "feed"])
        },
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
    try:
        if gui.experiment_runner and gui.experiment_runner.isRunning():
            gui.logMessage("Experiment is already running.")
            return

        gui.logMessage("Starting experiment in background...")
        runner = ExperimentRunner(gui, delay_min=delay_min, test_mode=False)
    except Exception as e:
        tb = traceback.format_exc()
        gui.logMessage(f"Error running experiment: {e}")
        gui.logMessage(tb)
        print(tb)

class ExperimentRunner(QRunnable):
    def __init__(self, gui, delay_min=0, test_mode=False):
        super().__init__()
        self.gui = gui
        self.delay_min = delay_min
        self.test_mode = test_mode
        self._pause_event = Event()
        self._pause_event.set()
        self._is_running = True

    @Slot()
    def run(self):
        try:
            time_scale = 1/180 if self.test_mode else 1.0
            expMatrix = generateExperimentMatrix(time_scale=time_scale)
            saveExperimentMatrixToJson("CCC5p2_ExpMatrix.json", expMatrix)
            connection = self.gui.control_box
            expResults = runExperimentMatrix(
                connection, expMatrix,
                delay_min=self.delay_min,
                bypass_on=False,
                test_mode=self.test_mode
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

    def pause(self): self._pause_event.clear()
    def resume(self): self._pause_event.set()
    def is_paused(self): return not self._pause_event.is_set()
    def isRunning(self): return self._is_running

def main():
    test_mode = True
    time_scale = 1/100 if test_mode else 1.0
    expMatrix = generateExperimentMatrix(time_scale=time_scale)
    saveExperimentMatrixToJson("CCC5p2_ExpMatrix_Test.json", expMatrix)

    connect = Connection()
    connect.scanForDevices()

    expResults = runExperimentMatrix(connect, expMatrix, delay_min=0, bypass_on=False, test_mode=test_mode)

    with open('CCC5p2_ExpLog_Test.json', 'w') as f:
        json.dump(expResults, f, indent=2)

if __name__ == '__main__':
    main()
