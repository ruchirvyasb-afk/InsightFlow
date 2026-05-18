# Configuration for InsightFlow backend
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "sample_data"
DATA_DIR.mkdir(exist_ok=True)

# Data generation config
TOTAL_RECORDS = 100
FAULT_RATE = 0.20

FAULT_WEIGHTS = {
    "missing_field": 0.30,
    "out_of_range": 0.25,
    "wrong_type": 0.20,
    "malformed_id": 0.15,
    "duplicate": 0.10,
}

# File paths
RAW_DATA_FILE = DATA_DIR / "iot_events.ndjson"
VALIDATION_LOG_FILE = DATA_DIR / "validation_log.json"
TRANSFORMED_DATA_FILE = DATA_DIR / "transformed_data.json"

# Validation rules
VALIDATION_RULES = {
    "skin_moisture_pct": {"min": 0, "max": 100},
    "sebum_level_index": {"min": 0, "max": 1},
    "skin_ph": {"min": 0, "max": 14},
    "ambient_temp_c": {"min": -50, "max": 60},
    "ambient_humidity_pct": {"min": 0, "max": 100},
}

# Required fields
REQUIRED_FIELDS = ["device_id", "customer_id", "timestamp", "reading", "recommendation"]

print(f"[CONFIG] Data directory: {DATA_DIR}")
