"""
InsightFlow Data Ingestion Module
Reads NDJSON files and parses IoT records
"""

import json

from config import RAW_DATA_FILE

# ==========================================
# INGEST DATA
# ==========================================

def ingest_data():
    """Read NDJSON file and return parsed records"""

    if not RAW_DATA_FILE.exists():

        print(f"❌ Raw data file not found: {RAW_DATA_FILE}")

        return []

    records = []

    malformed_count = 0

    try:

        with open(RAW_DATA_FILE, "r") as f:

            for line_number, line in enumerate(f, start=1):

                line = line.strip()

                if not line:
                    continue

                try:

                    record = json.loads(line)

                    records.append(record)

                except json.JSONDecodeError as e:

                    malformed_count += 1

                    print(
                        f"⚠️ Malformed JSON at line {line_number}: {e}"
                    )

                    continue

        print(f"\n{'─' * 60}")

        print(f"📥 Ingestion Complete")

        print(f"📄 File: {RAW_DATA_FILE}")

        print(f"✅ Parsed records: {len(records)}")

        print(f"⚠️ Malformed records skipped: {malformed_count}")

        print(f"{'─' * 60}\n")

        return records

    except Exception as e:

        print(f"❌ Error reading NDJSON file: {e}")

        return []

# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    records = ingest_data()

    print(f"Successfully ingested {len(records)} records")
