# prefill.py
from multiprocessing import connection
import os
import sys

# Add parent directory to sys.path so imports like 'Experiment_Config' work
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd() 
from time import sleep
from threading import Event
from PySide6.QtCore import QRunnable, QTimer
from Experiment_Config import VALVE_ID
from Experiment.CCC5P2_experiment import setMuxValvesForPrefill

def runPrefillCoating(connection, scr_update=None, stop_event=None, feed_time=100, cycles=2):
    """
    Run prefill coating:
    - All chambers open
    - MuxIn open
    - Fresh input open
    - Bypass closed
    - Feed each column for 100s, 2 cycles
    - End: all valves open, fresh closed
    """
    if scr_update is None:
        scr_update = lambda msg: None  # Do nothing

    scr_update("Starting prefill coating...")
    ...

    # initial valve setup
    connection.setValveState(VALVE_ID["muxIn"], True)
    connection.setValveState(VALVE_ID["fresh"], True)
    connection.setValveStates({vid: False for vid in VALVE_ID["bypass"]})
    connection.setValveStates({vid: True for pair in VALVE_ID["chamberIn"] for vid in pair})

    sleep(5)

    # Coating process
    for cycle in range(cycles):
        for col in range(1, 17):
            if stop_event and stop_event.is_set():
                scr_update("Prefill coating stopped by user.")
                return
            setMuxValvesForPrefill(connection, VALVE_ID["mux"], col)
            scr_update(f"Cycle {cycle+1}: Coating column {col}")
            sleep(feed_time)

    sleep(5)
    
    # final cleanup
    scr_update("Prefill coating complete. Opening all valves, closing fresh_in.")
    connection.setValveStates({vid: True for vid in range(48)})
    connection.setValveState(VALVE_ID["fresh"], False)

class PrefillCoatingRunner(QRunnable):
    def __init__(self, gui, feed_time=100, cycles=2):
        super().__init__()
        self.gui = gui
        self.feed_time = feed_time
        self.cycles = cycles
        self._stop_event = Event()
        self._is_running = True

    def stop(self):
        self._stop_event.set()

    def isRunning(self):
        return self._is_running

    def run(self):
        try:
            runPrefillCoating(
                connection=self.gui.control_box,
                scr_update=self.gui.logMessage,
                stop_event=self._stop_event,
                feed_time=self.feed_time,
                cycles=self.cycles
            )
            QTimer.singleShot(0, lambda: self.gui.logMessage("Prefill coating completed."))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            QTimer.singleShot(0, lambda: self.gui.logMessage(f"Prefill coating failed: {e}"))
            QTimer.singleShot(0, lambda: self.gui.logMessage(tb))
        finally:
            self._is_running = False


if __name__ == "__main__":
    from Connection.Connection import Connection

    try:
        conn = Connection()
        conn.scanForDevices()

        runPrefillCoating(
            connection=conn,
            scr_update=print,
            stop_event=None,
            feed_time=5,
            cycles=1
        )
    except Exception as e:
        import traceback
        print("Prefill run failed:", e)
        print(traceback.format_exc())