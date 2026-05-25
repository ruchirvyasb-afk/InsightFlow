"""
InsightFlow Data Transformation Module
Flattens nested IoT records and derives analytics columns
"""

import json

from config import TRANSFORMED_DATA_FILE

# ==========================================
# DERIVED METRICS
# ==========================================

def derive_skin_state(moisture, sebum):
    """Derive skin state from moisture + sebum"""

    try:

        moisture = float(moisture)

        sebum = float(sebum)

    except Exception:

        return "Unknown"

    if moisture < 30 and sebum < 0.3:

        return "Dry"

    elif moisture > 50 and sebum > 0.6:

        return "Oily"

    else:

        return "Normal"

# ------------------------------------------

def derive_dryness_index(moisture, sebum):
    """
    Derive dryness index (0-1 scale)

    Lower moisture = higher dryness
    Higher sebum slightly reduces dryness
    """

    try:

        moisture = float(moisture)

        sebum = float(sebum)

    except Exception:

        return 0

    dryness = (
        ((100 - moisture) / 100) * 0.9
        - (sebum * 0.1)
    )

    return round(
        max(0, min(1, dryness)),
        3
    )

# ==========================================
# TRANSFORM SINGLE RECORD
# ==========================================

def transform_record(record):
    """
    Flatten nested IoT record
    Add derived analytics columns
    """

    reading = record.get("reading", {})

    recommendation = record.get("recommendation", {})

    moisture = reading.get("skin_moisture_pct", 0)

    sebum = reading.get("sebum_level_index", 0)

    flat = {

        # Core identifiers
        "device_id": record.get("device_id"),

        "customer_id": record.get("customer_id"),

        "timestamp": record.get("timestamp"),

        # Sensor metrics
        "skin_moisture_pct": moisture,

        "sebum_level_index": sebum,

        "skin_ph": reading.get("skin_ph"),

        "ambient_temp_c": reading.get("ambient_temp_c"),

        "ambient_humidity_pct": reading.get(
            "ambient_humidity_pct"
        ),

        "primary_concern": reading.get(
            "primary_concern"
        ),

        # Recommendation fields
        "suggested_product": recommendation.get(
            "suggested_product"
        ),

        "routine_step": recommendation.get(
            "routine_step"
        ),

        # Derived analytics
        "skin_state": derive_skin_state(
            moisture,
            sebum
        ),

        "dryness_index": derive_dryness_index(
            moisture,
            sebum
        ),
    }

    return flat

# ==========================================
# TRANSFORM MULTIPLE RECORDS
# ==========================================

def transform_records(valid_records):
    """Transform all validated records"""

    transformed = []

    failed = 0

    for idx, record in enumerate(valid_records):

        try:

            flat = transform_record(record)

            transformed.append(flat)

        except Exception as e:

            failed += 1

            print(
                f"⚠️ Failed transforming record {idx}: {e}"
            )

    print(f"\n{'─' * 60}")

    print("🔄 Transformation Complete")

    print(f"✅ Successfully transformed: {len(transformed)}")

    print(f"⚠️ Failed transforms: {failed}")

    print(f"{'─' * 60}\n")

    return transformed

# ==========================================
# SAVE TRANSFORMED DATA
# ==========================================

def save_transformed_data(transformed_records):
    """Save transformed records as JSON"""

    try:

        with open(TRANSFORMED_DATA_FILE, "w") as f:

            json.dump(
                transformed_records,
                f,
                indent=2,
                default=str
            )

        print(
            f"✅ Saved transformed data → {TRANSFORMED_DATA_FILE}"
        )

    except Exception as e:

        print(f"❌ Failed saving transformed data: {e}")

# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    from ingestion import ingest_data

    from validation import validate_records

    records = ingest_data()

    valid, invalid = validate_records(records)

    transformed = transform_records(valid)

    save_transformed_data(transformed)

    print(
        f"🚀 Pipeline complete: {len(transformed)} rows ready for dashboard"
    )
