"""Transform module - flattens records and derives new columns"""
import json
from config import TRANSFORMED_DATA_FILE


def derive_skin_state(moisture, sebum):
    """Derive skin state from moisture and sebum levels"""
    if moisture < 30 and sebum < 0.3:
        return "Dry"
    elif moisture > 50 and sebum > 0.6:
        return "Oily"
    else:
        return "Normal"


def derive_dryness_index(moisture, sebum):
    """Derive dryness index (0-1 scale)"""
    # Inverse relationship with moisture: lower moisture = higher dryness
    # Higher sebum slightly reduces dryness
    dryness = (100 - moisture) / 100 * 0.9 - (sebum * 0.1)
    return max(0, min(1, dryness))


def transform_record(record):
    """
    Flatten nested record and add derived columns.
    Input: nested IoT record
    Output: flattened record with derived columns
    """
    reading = record.get("reading", {})
    recommendation = record.get("recommendation", {})

    moisture = reading.get("skin_moisture_pct", 0)
    sebum = reading.get("sebum_level_index", 0)

    flat = {
        "device_id": record.get("device_id"),
        "customer_id": record.get("customer_id"),
        "timestamp": record.get("timestamp"),
        # Sensor fields — flattened from nested
        "skin_moisture_pct": moisture,
        "sebum_level_index": sebum,
        "skin_ph": reading.get("skin_ph"),
        "ambient_temp_c": reading.get("ambient_temp_c"),
        "ambient_humidity_pct": reading.get("ambient_humidity_pct"),
        "primary_concern": reading.get("primary_concern"),
        # Recommendation fields
        "suggested_product": recommendation.get("suggested_product"),
        "routine_step": recommendation.get("routine_step"),
        # Derived columns
        "skin_state": derive_skin_state(moisture, sebum),
        "dryness_index": round(derive_dryness_index(moisture, sebum), 3),
    }
    return flat


def transform_records(valid_records):
    """
    Transform all valid records.
    Returns: list of flattened records with derived columns
    """
    transformed = []
    for record in valid_records:
        flat = transform_record(record)
        transformed.append(flat)
    print(f"[TRANSFORM] Flattened {len(transformed)} records")
    return transformed


def save_transformed_data(transformed_records):
    """Save transformed records to JSON"""
    with open(TRANSFORMED_DATA_FILE, "w") as f:
        json.dump(transformed_records, f, indent=2, default=str)
    print(f"[TRANSFORM] Saved to {TRANSFORMED_DATA_FILE}")


if __name__ == "__main__":
    from ingestion import ingest_data
    from validation import validate_records
    
    records = ingest_data()
    valid, invalid = validate_records(records)
    transformed = transform_records(valid)
    save_transformed_data(transformed)
    print(f"[TRANSFORM] Pipeline complete: {len(transformed)} rows ready for dashboard")
