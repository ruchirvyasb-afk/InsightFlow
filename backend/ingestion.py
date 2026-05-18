"""Ingestion module - reads NDJSON and parses records"""
import json
from config import RAW_DATA_FILE


def ingest_data():
    """Read NDJSON file and return list of records"""
    if not RAW_DATA_FILE.exists():
        return []
    
    records = []
    try:
        with open(RAW_DATA_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"[INGEST] Skipped malformed JSON: {e}")
                        continue
        print(f"[INGEST] Read {len(records)} records from {RAW_DATA_FILE}")
        return records
    except Exception as e:
        print(f"[INGEST] Error reading file: {e}")
        return []


if __name__ == "__main__":
    records = ingest_data()
    print(f"Successfully ingested {len(records)} records")
