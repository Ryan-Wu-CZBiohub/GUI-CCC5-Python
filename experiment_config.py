"""
config.py

This file defines the reusable configuration for the CCC5P2 experiment system.
It includes hardware valve mappings, timing parameters, input-to-valve lookup,
and experiment matrix structure.
"""

# Experiment metadata
EXPERIMENT_NAME = "CCC5P2 Keratinocytes Experiment"
EXPERIMENT_TOTAL_TIME = 1440  # Total experiment time in minutes (24 hours)

# Number of total valves used in the experiment
NUM_TOTAL_VALVES = 48

# Sequence of valve IDs used for input control
VALVE_INPUT_SEQUENCE = [24] + list(range(46, 27, -1))  # Fresh media + inputs 1–18

# Mapping of logical valve roles to physical valve IDs on the chip (1-based indexing)
VALVE_ID = {
    "mux": [26, 23, 22, 21, 20, 19, 18, 17],
    "purge": 27,
    "fresh": 24,
    "bypass": {
        1: 14,
        2: 11,
        3: 8,
        4: 5,
        5: 2
    },
    "chamberIn": {
        1: [16, 15],
        2: [13, 12],
        3: [10, 9],
        4: [7, 6],
        5: [4, 3]
    },
    "muxIn": 25,
    "outlet": 0
}

# TEST MODE
TEST_MODE = False # Set to True for testing

# Coating configuration
COATING_CONFIG = {
    "feedTime": 60,
    "waitTime": 3,
    "cycles": 2
}

# Experiment timing parameters (in seconds)
EXPERIMENT_TIMING_CONFIG = {
    "purgeTime1": 5,
    "purgeTime2": 20,
    "purgeTime3": 15,
    "prefillTime": 10,
    "feedTime": 10,
}

# Optional per-column offset (in minutes) to avoid simultaneous operations
def offset_schedule(index: float) -> float:
    return index * 0.5  # 0.5 minute

# Map input number (0–18) to descriptive name and physical valve ID
INPUT_TO_CONTROL_MAP = {
    0:  {"name": "fresh media",         "valve": 24},
    1:  {"name": "0.3 ng/ml TNF",       "valve": 46},
    2:  {"name": "1 ng/ml TNF",         "valve": 45},
    3:  {"name": "3 ng/ml TNF",         "valve": 44},
    4:  {"name": "10 ng/ml TNF",        "valve": 43},
    5:  {"name": "30 ng/ml TNF",        "valve": 42},
    6:  {"name": "100 ng/ml TNF",       "valve": 41},
    7:  {"name": "1 ng/ml LPS",         "valve": 40},
    8:  {"name": "3 ng/ml LPS",         "valve": 39},
    9:  {"name": "10 ng/ml LPS",        "valve": 38},
    10: {"name": "30 ng/ml LPS",        "valve": 37},
    11: {"name": "100 ng/ml LPS",       "valve": 36},
    12: {"name": "300 ng/ml LPS",       "valve": 35},
    13: {"name": "0.3 ng/ml IL17-A",    "valve": 34},
    14: {"name": "1 ng/ml IL17-A",      "valve": 33},
    15: {"name": "3 ng/ml IL17-A",      "valve": 32},
    16: {"name": "10 ng/ml IL17-A",     "valve": 31},
    17: {"name": "30 ng/ml IL17-A",     "valve": 30},
    18: {"name": "100 ng/ml IL17-A",    "valve": 29},
}

# Core experiment configuration matrix (feeding schedules)
# Each block feeds one row with specific inputs at defined time intervals.
# Adding 1 to EXPERIMENT_TOTAL_TIME to account for Python's 0-based indexing
EXPERIMENT_CONFIG = [
    {
        "row": 1,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 60)),  # Every 60 min
        "column_to_input": {
            1: 1,  2: 2,  3: 3,  4: 4,
            5: 5,  6: 6,  7: 7,  8: 8,
            9: 9, 10: 10, 11: 11, 12: 12,
            13: 13, 14: 14, 15: 15, 16: 16
        }
    },
    {
        "row": 2,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 120)),  # Every 120 min
        "column_to_input": {
            1: 1,  2: 2,  3: 3,  4: 4,
            5: 5,  6: 6,  7: 7,  8: 8,
            9: 9, 10: 10, 11: 11, 12: 12,
            13: 13, 14: 14, 15: 15, 16: 16
        }
    },
    {
        "row": 3,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 240)),  # Every 240 min
        "column_to_input": {
            1: 1,  2: 2,  3: 3,  4: 4,
            5: 5,  6: 6,  7: 7,  8: 8,
            9: 9, 10: 10, 11: 11, 12: 12,
            13: 13, 14: 14, 15: 15, 16: 16
        }
    },
    {
        "row": 4,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 480)),  # Every 480 min
        "column_to_input": {
            1: 1,  2: 2,  3: 3,  4: 4,
            5: 5,  6: 6,  7: 7,  8: 8,
            9: 9, 10: 10, 11: 11, 12: 12,
            13: 13, 14: 14, 15: 15, 16: 16
        }
    },

    # Row 5: IL-17A high-dose and control groups with different feeding frequencies
    {
        "row": 5,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 60)),  # Every hour
        "column_to_input": {
            1: 17, 2: 18, 3: 0, 4: 0
        }
    },
    {
        "row": 5,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 120)),  # Every 2 hours
        "column_to_input": {
            5: 17, 6: 18, 7: 0, 8: 0
        }
    },
    {
        "row": 5,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 240)),  # Every 4 hours
        "column_to_input": {
            9: 17, 10: 18, 11: 0, 12: 0
        }
    },
    {
        "row": 5,
        "intervals": list(range(0, EXPERIMENT_TOTAL_TIME + 1, 480)),  # Every 8 hours
        "column_to_input": {
            13: 17, 14: 18, 15: 0, 16: 0
        }
    }
]