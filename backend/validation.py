"""
InsightFlow Validation Module
Validates IoT skin analytics records
"""

import json

from config import (
    REQUIRED_FIELDS,
    VALIDATION_RULES,
    VALIDATION_LOG_FILE
)

# ==========================================
# VALIDATE SINGLE RECORD
# ==========================================

def validate_record(record):
    """
    Validate one IoT record

    Returns:
        (True, None)
        OR
        (False, error_message)
    """

    # ======================================
    # REQUIRED FIELDS
    # ======================================

    for field in REQUIRED_FIELDS:

        if field not in record:

            return (
                False,
                f"MISSING_REQUIRED_FIELD: {field}"
            )

        if record[field] is None:

            return (
                False,
                f"NULL_FIELD: {field}"
            )

    # ======================================
    # READING OBJECT
    # ======================================

    if not isinstance(record.get("reading"), dict):

        return (
            False,
            "INVALID_READING: must be object"
        )

    reading = record["reading"]

    # ======================================
    # TYPE CHECKS
    # ======================================

    if not isinstance(record.get("device_id"), str):

        return (
            False,
            f"WRONG_TYPE: device_id must be string"
        )

    if not isinstance(record.get("customer_id"), str):

        return (
            False,
            f"WRONG_TYPE: customer_id must be string"
        )

    if not isinstance(record.get("timestamp"), str):

        return (
            False,
            "WRONG_TYPE: timestamp must be string"
        )

    # ======================================
    # ID FORMAT VALIDATION
    # ======================================

    if not record.get("device_id", "").startswith("SKIN-PRO-"):

        return (
            False,
            "MALFORMED_ID: invalid device_id"
        )

    if not record.get("customer_id", "").startswith("USER-"):

        return (
            False,
            "MALFORMED_ID: invalid customer_id"
        )

    # ======================================
    # SENSOR VALIDATION
    # ======================================

    for field, rules in VALIDATION_RULES.items():

        if field not in reading:

            return (
                False,
                f"MISSING_SENSOR_FIELD: {field}"
            )

        val = reading[field]

        if val is None:

            return (
                False,
                f"NULL_SENSOR_VALUE: {field}"
            )

        if not isinstance(val, (int, float)):

            return (
                False,
                f"WRONG_TYPE: {field} must be numeric"
            )

        if not (rules["min"] <= val <= rules["max"]):

            return (
                False,
                f"OUT_OF_RANGE: {field}={val}"
            )

    return True, None

# ==========================================
# VALIDATE MULTIPLE RECORDS
# ==========================================

def validate_records(records):
    """
    Validate all records

    Returns:
        valid_records
        invalid_records
    """

    valid = []

    invalid = []

    seen = set()

    for index, record in enumerate(records):

        try:

            is_valid, error = validate_record(record)

            if is_valid:

                # ==================================
                # DUPLICATE DETECTION
                # ==================================

                key = json.dumps(
                    record,
                    sort_keys=True
                )

                if key in seen:

                    invalid.append({

                        "index": index,

                        "record": record,

                        "error": "DUPLICATE_RECORD",

                        "hint": record.get(
                            "_fault",
                            ""
                        )
                    })

                    continue

                seen.add(key)

                valid.append(record)

            else:

                invalid.append({

                    "index": index,

                    "record": record,

                    "error": error,

                    "hint": record.get(
                        "_fault",
                        ""
                    )
                })

        except Exception as e:

            invalid.append({

                "index": index,

                "record": record,

                "error": f"VALIDATION_EXCEPTION: {e}",

                "hint": record.get(
                    "_fault",
                    ""
                )
            })

    print(f"\n{'─' * 60}")

    print("🛡️ Validation Complete")

    print(f"✅ Valid records: {len(valid)}")

    print(f"❌ Invalid records: {len(invalid)}")

    print(f"{'─' * 60}\n")

    return valid, invalid

# ==========================================
# SAVE VALIDATION LOG
# ==========================================

def save_validation_log(valid, invalid):
    """Save validation summary"""

    log = {

        "valid_count": len(valid),

        "invalid_count": len(invalid),

        "total": len(valid) + len(invalid),

        "invalid_records": invalid[:50]
    }

    try:

        with open(VALIDATION_LOG_FILE, "w") as f:

            json.dump(
                log,
                f,
                indent=2,
                default=str
            )

        print(
            f"✅ Validation log saved → {VALIDATION_LOG_FILE}"
        )

    except Exception as e:

        print(
            f"❌ Failed saving validation log: {e}"
        )

# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    from ingestion import ingest_data

    records = ingest_data()

    valid, invalid = validate_records(records)

    save_validation_log(valid, invalid)

    print(
        f"🚀 Validation complete: {len(valid)} valid / {len(invalid)} invalid"
    )
