""" 
This script is designed to run a specific experiment for the CCC5P2 project.

Program flow:

"""

import json
import time
import datetime
from threading import Event
from typing import Callable, List
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
from Experiment_Config import (
    EXPERIMENT_NAME,
    EXPERIMENT_TOTAL_TIME,
    EXPERIMENT_CONFIG,
    INPUT_TO_CONTROL_MAP,
    VALVE_ID,
    EXPERIMENT_TIMING_CONFIG,
    TEST_MODE,
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

def setMuxValves(connection, mux_valves, column_index, scr_update=print, label=""):
    """
    Set MUX valves for CCC5P2 (1–16).

    mux_valves: [26, 23, 22, 21, 20, 19, 18, 17]  # ordered list of MUX valve IDs
    column_index: 1–16 (column number), or 98 (all open), 99 (all closed)
    """
    if len(mux_valves) != 8:
        scr_update("Error: mux_valves must contain exactly 8 valve IDs.")
        return

    try:
        column_index = int(column_index)
    except (TypeError, ValueError):
        scr_update(f"Invalid mux setting for column index (non-integer): {column_index}")
        return

    if column_index not in range(1, 17) and column_index not in (98, 99):
        scr_update(f"Invalid mux setting for column index: {column_index}")
        return

    # Special debug/override modes
    if column_index == 98:
        mux_states = [1] * 8
    elif column_index == 99:
        mux_states = [0] * 8
    else:
        # Column groupings for logical MUX control bits
        columns_1_to_8 = set(range(1, 9))                               # bit 0
        columns_9_to_16 = set(range(9, 17))                             # bit 1
        top_half_columns = set(range(1, 5)) | set(range(9, 13))         # bit 2
        bottom_half_columns = set(range(5, 9)) | set(range(13, 17))     # bit 3
        mux_group_A = {1, 2, 5, 6, 9, 10, 13, 14}                       # bit 4
        mux_group_B = set(range(1, 17)) - mux_group_A                   # bit 5
        odd_columns = set(range(1, 17, 2))                              # bit 6
        even_columns = set(range(2, 17, 2))                             # bit 7

        mux_states = [
            int(column_index in columns_1_to_8),        # bit 0
            int(column_index in columns_9_to_16),       # bit 1
            int(column_index in top_half_columns),      # bit 2
            int(column_index in bottom_half_columns),   # bit 3
            int(column_index in mux_group_A),           # bit 4
            int(column_index in mux_group_B),           # bit 5
            int(column_index in odd_columns),           # bit 6
            int(column_index in even_columns),          # bit 7
        ]


    valve_states = {
        valve_id: bool(state)
        for valve_id, state in zip(mux_valves, mux_states)
    }

    connection.setValveStates(valve_states)
    scr_update(f"MUX set for column {column_index}")

def adjusted_sleep(duration: float, test_mode: bool):
    time.sleep(duration / 180.0 if test_mode else duration)

def runExperimentMatrix(
    connection: Connection,
    matrix_mat: List[List[int]],
    delay_min=60,
    bypass_on=False,
    test_mode=False,
    log_fn: Callable[[str], None] = print
):
    log = []
    start_time = datetime.datetime.now()
    delta = lambda t: datetime.timedelta(seconds=t) if test_mode else datetime.timedelta(minutes=t)
    now = start_time
    schedule = [[now + delta(row[0] + delay_min)] + row[1:] for row in matrix_mat]

    log_file_path = os.path.join(BASE_DIR, 'CCC5p2_ExpLog.json')
    with open(log_file_path, 'w') as log_file:
        # Begin log file
        log_file.write('{\n  "metadata": {\n')
        log_file.write(f'    "experiment_name": "{EXPERIMENT_NAME}",\n')
        log_file.write(f'    "experiment_total_time_min": {EXPERIMENT_TOTAL_TIME},\n')
        log_file.write(f'    "start_time": "{start_time.strftime("%Y-%m-%d %H:%M:%S")}",\n')
        log_file.write(f'    "delay_min": {delay_min},\n')
        log_file.write(f'    "bypass_on": {str(bypass_on).lower()},\n')
        log_file.write(f'    "test_mode": {str(test_mode).lower()}\n')
        log_file.write('  },\n')
        log_file.write('  "log_entries": [\n')  

        def log_mux(column_index, label):
            setMuxValves(connection, VALVE_ID["mux"], column_index, lambda msg: log_fn(f"{label} → {msg}"))

        def validate_column(col):
            try:
                col = int(col)
                if 1 <= col <= 16:
                    return col
                log_fn(f"[WARNING] Invalid column index: {col}")
            except Exception:
                log_fn(f"[ERROR] Non-integer column index: {col}")
            return None

        for i, row in enumerate(schedule):
            scheduled_time, input_valve, row_num, col_num_raw, side, _ = row
            col_num = validate_column(col_num_raw)
            if col_num is None:
                continue

            while datetime.datetime.now() < scheduled_time:
                time.sleep(0.01 if test_mode else 0.5)

            # feeding
            log_mux(col_num, "Feeding")
            connection.setValveState(VALVE_ID["outlet"], True)
            connection.setValveState(VALVE_ID["bypass"][row_num], True)
            connection.setValveState(input_valve, True)
            connection.setValveState(VALVE_ID["muxIn"], True)
            connection.setValveState(VALVE_ID["purge"], True)
            adjusted_sleep(EXPERIMENT_TIMING_CONFIG["purgeTime1"], test_mode)

            # prefill pathways
            connection.setValveState(VALVE_ID["purge"], False)
            adjusted_sleep(EXPERIMENT_TIMING_CONFIG["prefillTime"], test_mode)

            if not bypass_on:
                connection.setValveState(VALVE_ID["bypass"][row_num], False)

            # feed chambers
            left_valve, right_valve = VALVE_ID["chamberIn"][row_num]
            if side == 0:
                connection.setValveState(left_valve, True)
            elif side == 1:
                connection.setValveState(right_valve, True)
            elif side == 2:
                connection.setValveState(left_valve, True)
                connection.setValveState(right_valve, True)
            adjusted_sleep(EXPERIMENT_TIMING_CONFIG["feedTime"], test_mode)

            # cleaning
            log_mux(col_num, "Cleaning")
            connection.setValveState(left_valve, False)
            connection.setValveState(right_valve, False)
            connection.setValveState(VALVE_ID["bypass"][row_num], True)
            connection.setValveState(input_valve, False)
            adjusted_sleep(1, test_mode)

            connection.setValveState(VALVE_ID["purge"], True)
            connection.setValveState(VALVE_ID["fresh"], True)
            adjusted_sleep(EXPERIMENT_TIMING_CONFIG["purgeTime2"], test_mode)

            connection.setValveState(VALVE_ID["purge"], False)
            adjusted_sleep(EXPERIMENT_TIMING_CONFIG["purgeTime3"], test_mode)

            connection.setValveState(VALVE_ID["fresh"], False)
            connection.setValveState(VALVE_ID["muxIn"], False)
            connection.setValveState(VALVE_ID["outlet"], False)
            for vid in VALVE_ID["bypass"]:
                connection.setValveState(vid, False)

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                "type": "feed",
                "valve": input_valve,
                "row": row_num,
                "col": col_num,
                "side": side,
                "timestamp": timestamp
            }
            log.append(log_entry)
            log_fn(f"{timestamp} → Feed Input Valve {input_valve} → Row {row_num}, Column {col_num}, Side {side}")

            log_line = '    ' + json.dumps(log_entry)
            if i < len(schedule) - 1:
                log_line += ','
            log_line += '\n'
            log_file.write(log_line)
            log_file.flush()

        end_time = datetime.datetime.now()

        log_file.write('  ],\n')
        log_file.write('  "summary": {\n')
        log_file.write(f'    "end_time": "{end_time.strftime("%Y-%m-%d %H:%M:%S")}",\n')
        log_file.write(f'    "duration_min": {(end_time - start_time).total_seconds() / 60:.2f},\n')
        log_file.write(f'    "num_feeds": {len(log)}\n')
        log_file.write('  }\n}\n')

    log_fn("Experiment completed. Closing all valves...")
    all_valves = set(range(28, 47)) \
        | set(valve for pair in VALVE_ID["chamberIn"] for valve in pair) \
        | set(VALVE_ID["mux"]) | set(VALVE_ID["bypass"]) \
        | {VALVE_ID["purge"], VALVE_ID["fresh"], VALVE_ID["muxIn"]}

    for vid in all_valves:
        connection.setValveState(vid, False)

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
            "num_feeds": len(log)
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

def runFromGui(gui, delay_min: float = 0, test_mode: bool = False, time_scale: float = 1.0):
    try:
        if gui.experiment_runner and gui.experiment_runner.isRunning():
            gui.logMessage("Experiment is already running.")
            return

        gui.logMessage("Starting experiment in background...")
        runner = ExperimentRunner(gui, delay_min=delay_min, test_mode=TEST_MODE, time_scale=time_scale)
    except Exception as e:
        tb = traceback.format_exc()
        gui.logMessage(f"Error running experiment: {e}")
        gui.logMessage(tb)
        print(tb)

class ExperimentRunner(QRunnable):
    def __init__(self, gui, delay_min=0, test_mode=False, time_scale=1.0):
        super().__init__()
        self.gui = gui
        self.delay_min = delay_min
        self.test_mode = test_mode
        self.time_scale = time_scale
        self._pause_event = Event()
        self._pause_event.set()
        self._is_running = True

    @Slot()
    def run(self):
        # self.gui.logMessage("[DEBUG] ExperimentRunner.run() called")
        try:
            expMatrix = generateExperimentMatrix(time_scale=self.time_scale)
            matrix_file_path = os.path.join(BASE_DIR, 'CCC5p2_ExpMatrix.json')
            saveExperimentMatrixToJson(matrix_file_path, expMatrix)
            # saveExperimentMatrixToJson("CCC5p2_ExpMatrix.json", expMatrix)
            connection = self.gui.control_box
            expResults = runExperimentMatrix(
                connection, expMatrix,
                delay_min=self.delay_min,
                bypass_on=False,
                test_mode=self.test_mode,
                log_fn=self.gui.logMessage,
            )
            # with open('CCC5p2_ExpLog.json', 'w') as f:
            #     json.dump(expResults, f, indent=2)
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
    test_mode = TEST_MODE
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
