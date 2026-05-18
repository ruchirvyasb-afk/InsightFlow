import json
import random
import os
from datetime import datetime, timedelta

output_file = "../sample_data7/iot_events.json"
os.makedirs("../sample_data7", exist_ok=True)

# ─────────────────────────────────────────────
# Fault injection config — tune rates here
# ─────────────────────────────────────────────
TOTAL_RECORDS   = 100
FAULT_RATE      = 0.20   # 20% of records will be faulty

FAULT_WEIGHTS = {
    "missing_field":      0.30,   # Required field removed entirely
    "out_of_range":       0.25,   # Sensor value outside physical bounds
    "wrong_type":         0.20,   # Field has wrong data type
    "malformed_id":       0.15,   # device_id / customer_id format violation
    "duplicate":          0.10,   # Exact copy of a previous valid record
}

# ─────────────────────────────────────────────
# Recommendation engine (unchanged)
# ─────────────────────────────────────────────
def get_recommendation(moisture, sebum, ph, concern):
    if moisture < 25:
        return "Deep Hydration Ceramide Cream"
    if sebum > 0.8:
        return "2% Salicylic Acid Cleanser"
    if ph > 6.2 or ph < 4.5:
        return "pH Balancing Mineral Toner"
    if concern == "Aging":
        return "Retinol Night Serum"
    elif concern == "Redness":
        return "Azelaic Acid Soothing Gel"
    elif concern == "Acne":
        return "Benzoyl Peroxide Spot Treatment"
    return "Daily Lightweight SPF 30 Moisturizer"


# ─────────────────────────────────────────────
# Valid record generator
# ─────────────────────────────────────────────
def generate_valid_event():
    moisture = round(random.uniform(5.0, 75.0), 2)
    sebum    = round(random.uniform(0.1, 1.0), 2)
    ph       = round(random.uniform(4.0, 7.0), 1)
    concern  = random.choice(["Acne", "Dryness", "Aging", "Redness", "None"])
    product  = get_recommendation(moisture, sebum, ph, concern)

    return {
        "device_id":    f"SKIN-PRO-{random.randint(100, 999)}",
        "customer_id":  f"USER-{random.randint(1000, 9999)}",
        "timestamp":    datetime.now().isoformat(),
        "reading": {
            "skin_moisture_pct":    moisture,
            "sebum_level_index":    sebum,
            "skin_ph":              ph,
            "ambient_temp_c":       round(random.uniform(22.0, 38.0), 2),
            "ambient_humidity_pct": random.randint(15, 90),
            "primary_concern":      concern
        },
        "recommendation": {
            "suggested_product": product,
            "routine_step":      "Treatment" if moisture < 25 or sebum > 0.8 else "Prevention"
        }
    }


# ─────────────────────────────────────────────
# Fault injectors — one per fault category
# ─────────────────────────────────────────────

def inject_missing_field(event):
    """Remove a required field entirely — triggers MISSING_REQUIRED_FIELD."""
    target = random.choice([
        "device_id",
        "customer_id",
        "timestamp",
        "reading",
        "recommendation"
    ])
    faulty = dict(event)
    del faulty[target]
    faulty["_fault_hint"] = f"missing_field:{target}"
    return faulty


def inject_out_of_range(event):
    """
    Push a sensor value beyond physical/business bounds.
    Validation should catch these with range checks:
      skin_moisture_pct  valid: 0–100   → inject: -5 or 150
      sebum_level_index  valid: 0–1     → inject: -0.5 or 3.5
      skin_ph            valid: 0–14    → inject: -1 or 16
      ambient_temp_c     valid: -50–60  → inject: -99 or 999
      ambient_humidity_pct valid: 0–100 → inject: -20 or 200
    """
    faulty = json.loads(json.dumps(event))   # deep copy
    field, bad_value = random.choice([
        ("skin_moisture_pct",   random.choice([-5.0, 150.0])),
        ("sebum_level_index",   random.choice([-0.5, 3.5])),
        ("skin_ph",             random.choice([-1.0, 16.0])),
        ("ambient_temp_c",      random.choice([-99.0, 999.0])),
        ("ambient_humidity_pct",random.choice([-20,   200])),
    ])
    faulty["reading"][field] = bad_value
    faulty["_fault_hint"] = f"out_of_range:{field}={bad_value}"
    return faulty


def inject_wrong_type(event):
    """
    Replace a numeric field with a string, or a string field with a number.
    Validation should catch these with type checks.
    """
    faulty = json.loads(json.dumps(event))
    mutation = random.choice([
        # Numeric field → string
        lambda e: e["reading"].__setitem__("skin_moisture_pct", "HIGH"),
        lambda e: e["reading"].__setitem__("sebum_level_index", "oily"),
        lambda e: e["reading"].__setitem__("ambient_temp_c",    "hot"),
        lambda e: e["reading"].__setitem__("skin_ph",           None),
        # String field → number
        lambda e: e.__setitem__("device_id",   98765),
        lambda e: e.__setitem__("customer_id", True),
        lambda e: e["reading"].__setitem__("primary_concern", 42),
    ])
    mutation(faulty)
    faulty["_fault_hint"] = "wrong_type"
    return faulty


def inject_malformed_id(event):
    """
    Break the ID format rules.
    Expected: device_id  = 'SKIN-PRO-NNN'
              customer_id = 'USER-NNNN'
    """
    faulty = dict(event)
    mutation = random.choice([
        ("device_id",   ""),                             # empty string
        ("device_id",   "SKIN_PRO_" + str(random.randint(1, 9))),  # underscores, short
        ("device_id",   "device-" + "x" * 50),          # too long / wrong prefix
        ("customer_id", "USR" + str(random.randint(1, 99))),       # wrong prefix, short
        ("customer_id", f"USER-{random.randint(1,9)}"),  # number too short
        ("customer_id", None),                           # null
    ])
    field, bad_value = mutation
    faulty[field] = bad_value
    faulty["_fault_hint"] = f"malformed_id:{field}={bad_value!r}"
    return faulty


def inject_duplicate(event):
    """Return an exact copy (same content, same timestamp) — triggers DUPLICATE_RECORD."""
    faulty = json.loads(json.dumps(event))
    faulty["_fault_hint"] = "duplicate"
    return faulty


# ─────────────────────────────────────────────
# Main generation loop
# ─────────────────────────────────────────────
FAULT_POOL = list(FAULT_WEIGHTS.keys())
FAULT_CUM  = []
_running   = 0.0
for k in FAULT_POOL:
    _running += FAULT_WEIGHTS[k]
    FAULT_CUM.append(_running)


def pick_fault_type():
    r = random.random()
    for i, threshold in enumerate(FAULT_CUM):
        if r <= threshold:
            return FAULT_POOL[i]
    return FAULT_POOL[-1]


INJECTORS = {
    "missing_field": inject_missing_field,
    "out_of_range":  inject_out_of_range,
    "wrong_type":    inject_wrong_type,
    "malformed_id":  inject_malformed_id,
    "duplicate":     inject_duplicate,
}

records          = []
valid_pool       = []   # kept for duplicate injection
fault_summary    = {k: 0 for k in FAULT_POOL}
fault_summary["valid"] = 0

for i in range(TOTAL_RECORDS):
    base = generate_valid_event()

    if random.random() < FAULT_RATE:
        fault_type = pick_fault_type()

        # Duplicate needs at least one valid record to copy
        if fault_type == "duplicate" and not valid_pool:
            fault_type = "missing_field"

        if fault_type == "duplicate":
            record = inject_duplicate(random.choice(valid_pool))
        else:
            record = INJECTORS[fault_type](base)

        fault_summary[fault_type] += 1
    else:
        record = base
        valid_pool.append(base)
        fault_summary["valid"] += 1

    records.append(record)

# Write — one JSON object per line (NDJSON), matching pipeline expectation
with open(output_file, "w") as f:
    for record in records:
        f.write(json.dumps(record) + "\n")

# ─────────────────────────────────────────────
# Generation summary
# ─────────────────────────────────────────────
total_faulty = sum(v for k, v in fault_summary.items() if k != "valid")
print(f"\n{'─'*45}")
print(f"  Generated {TOTAL_RECORDS} records → {output_file}")
print(f"{'─'*45}")
print(f"  {'valid':<22} {fault_summary['valid']:>4} records")
print(f"  {'faulty (total)':<22} {total_faulty:>4} records")
print(f"{'─'*45}")
for k in FAULT_POOL:
    print(f"    {k:<20} {fault_summary[k]:>3} records")
print(f"{'─'*45}\n")
