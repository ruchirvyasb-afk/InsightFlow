import json
from config import REQUIRED_FIELDS, VALIDATION_RULES, VALIDATION_LOG_FILE


def validate_record(record):
    """
    Validate a single record.
    Returns: (is_valid, error_message)
    """
    # Check required top-level fields
    for field in REQUIRED_FIELDS:
        if field not in record:
            return False, f"MISSING_REQUIRED_FIELD: {field}"
        if record[field] is None:
            return False, f"NULL_FIELD: {field}"

    # Check reading object
    if not isinstance(record.get("reading"), dict):
        return False, f"INVALID_READING: not a dict"

    reading = record["reading"]

    # Type checks
    if not isinstance(record.get("device_id"), str):
        return False, f"WRONG_TYPE: device_id must be string, got {type(record.get('device_id')).__name__}"
    if not isinstance(record.get("customer_id"), str):
        return False, f"WRONG_TYPE: customer_id must be string, got {type(record.get('customer_id')).__name__}"
    if not isinstance(record.get("timestamp"), str):
        return False, f"WRONG_TYPE: timestamp must be string"

    # ID format validation
    if not record.get("device_id", "").startswith("SKIN-PRO-"):
        return False, f"MALFORMED_ID: device_id must start with 'SKIN-PRO-'"
    if not record.get("customer_id", "").startswith("USER-"):
        return False, f"MALFORMED_ID: customer_id must start with 'USER-'"

    # Sensor range validation
    for field, rules in VALIDATION_RULES.items():
        if field not in reading:
            return False, f"MISSING_SENSOR_FIELD: {field}"
        val = reading[field]
        if val is None:
            return False, f"NULL_SENSOR_VALUE: {field}"
        if not isinstance(val, (int, float)):
            return False, f"WRONG_TYPE: {field} must be numeric, got {type(val).__name__}"
        if not (rules["min"] <= val <= rules["max"]):
            return False, f"OUT_OF_RANGE: {field}={val} (valid: {rules['min']}-{rules['max']})"

    return True, None


def validate_records(records):
    """
    Validate all records.
    Returns: (valid_records, invalid_records_with_errors)
    """
    valid = []
    invalid = []
    seen = set()  # For duplicate detection

    for i, record in enumerate(records):
        is_valid, error = validate_record(record)

        if is_valid:
            # Check for duplicates
            key = json.dumps(record, sort_keys=True)
            if key in seen:
                invalid.append({
                    "index": i,
                    "record": record,
                    "error": "DUPLICATE_RECORD",
                    "hint": record.get("_fault", "")
                })
                continue
            seen.add(key)
            valid.append(record)
        else:
            invalid.append({
                "index": i,
                "record": record,
                "error": error,
                "hint": record.get("_fault", "")
            })

    return valid, invalid


def save_validation_log(valid, invalid):
    """Save validation summary to file"""
    log = {
        "valid_count": len(valid),
        "invalid_count": len(invalid),
        "total": len(valid) + len(invalid),
        "invalid_records": invalid[:50],  # Save first 50 for debugging
    }
    with open(VALIDATION_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, default=str)
    print(f"[VALIDATION] Saved log to {VALIDATION_LOG_FILE}")


if __name__ == "__main__":
    from ingestion import ingest_data
    records = ingest_data()
    valid, invalid = validate_records(records)
    print(f"[VALIDATION] {len(valid)} valid, {len(invalid)} invalid")
    save_validation_log(valid, invalid)
