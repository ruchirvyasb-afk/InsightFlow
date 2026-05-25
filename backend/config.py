# ==========================================
# InsightFlow Backend Configuration
# ==========================================

import os
from pathlib import Path

# ==========================================
# BASE PATHS
# ==========================================

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "sample_data"

DATA_DIR.mkdir(exist_ok=True)

# ==========================================
# AWS CONFIGURATION
# ==========================================

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# S3 Buckets
RAW_BUCKET = os.getenv("RAW_BUCKET")
PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET")
ATHENA_BUCKET = os.getenv("ATHENA_BUCKET")
QUERY_RESULTS_BUCKET = os.getenv("QUERY_RESULTS_BUCKET")

# Glue
GLUE_CRAWLER_NAME = os.getenv("GLUE_CRAWLER_NAME")

# Athena
ATHENA_DATABASE = os.getenv("ATHENA_DATABASE", "insightflow_db")

ATHENA_WORKGROUP = os.getenv("ATHENA_WORKGROUP", "primary")

ATHENA_OUTPUT_LOCATION = (
    f"s3://{QUERY_RESULTS_BUCKET}/athena-results/"
    if QUERY_RESULTS_BUCKET
    else None
)

# ==========================================
# DATA GENERATION CONFIG
# ==========================================

TOTAL_RECORDS = 100

FAULT_RATE = 0.20

FAULT_WEIGHTS = {
    "missing_field": 0.30,
    "out_of_range": 0.25,
    "wrong_type": 0.20,
    "malformed_id": 0.15,
    "duplicate": 0.10,
}

# ==========================================
# FILE PATHS
# ==========================================

RAW_DATA_FILE = DATA_DIR / "iot_events.ndjson"

VALIDATION_LOG_FILE = DATA_DIR / "validation_log.json"

TRANSFORMED_DATA_FILE = DATA_DIR / "transformed_data.json"

# ==========================================
# VALIDATION RULES
# ==========================================

VALIDATION_RULES = {
    "skin_moisture_pct": {
        "min": 0,
        "max": 100
    },

    "sebum_level_index": {
        "min": 0,
        "max": 1
    },

    "skin_ph": {
        "min": 0,
        "max": 14
    },

    "ambient_temp_c": {
        "min": -50,
        "max": 60
    },

    "ambient_humidity_pct": {
        "min": 0,
        "max": 100
    },
}

# ==========================================
# REQUIRED FIELDS
# ==========================================

REQUIRED_FIELDS = [
    "device_id",
    "customer_id",
    "timestamp",
    "reading",
    "recommendation"
]

# ==========================================
# STARTUP LOGS
# ==========================================

print("\n========== INSIGHTFLOW CONFIG ==========")

print(f"[CONFIG] Base directory: {BASE_DIR}")

print(f"[CONFIG] Data directory: {DATA_DIR}")

print(f"[CONFIG] AWS Region: {AWS_REGION}")

print(f"[CONFIG] Raw Bucket: {RAW_BUCKET}")

print(f"[CONFIG] Processed Bucket: {PROCESSED_BUCKET}")

print(f"[CONFIG] Athena Bucket: {ATHENA_BUCKET}")

print(f"[CONFIG] Query Results Bucket: {QUERY_RESULTS_BUCKET}")

print(f"[CONFIG] Glue Crawler: {GLUE_CRAWLER_NAME}")

print(f"[CONFIG] Athena Database: {ATHENA_DATABASE}")

print("========================================\n")
