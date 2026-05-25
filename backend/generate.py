"""
InsightFlow IoT Data Generator
Generates NDJSON skin analytics events with controlled faults
"""

import json
import random
from datetime import datetime

from config import (
    TOTAL_RECORDS,
    FAULT_RATE,
    FAULT_WEIGHTS,
    RAW_DATA_FILE
)

# ==========================================
# RECOMMENDATION ENGINE
# ==========================================

def get_recommendation(moisture, sebum, ph, concern):
    """Generate skincare recommendation"""

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

# ==========================================
# VALID EVENT GENERATOR
# ==========================================

def generate_valid_event():
    """Generate valid IoT skin event"""

    moisture = round(random.uniform(5.0, 75.0), 2)

    sebum = round(random.uniform(0.1, 1.0), 2)

    ph = round(random.uniform(4.0, 7.0), 1)

    concern = random.choice([
        "Acne",
        "Dryness",
        "Aging",
        "Redness",
        "None"
    ])

    product = get_recommendation(
        moisture,
        sebum,
        ph,
        concern
    )

    return {

        "device_id": f"SKIN-PRO-{random.randint(100, 999)}",

        "customer_id": f"USER-{random.randint(1000, 9999)}",

        "timestamp": datetime.now().isoformat(),

        "reading": {

            "skin_moisture_pct": moisture,

            "sebum_level_index": sebum,

            "skin_ph": ph,

            "ambient_temp_c": round(
                random.uniform(22.0, 38.0),
                2
            ),

            "ambient_humidity_pct": random.randint(15, 90),

            "primary_concern": concern,
        },

        "recommendation": {

            "suggested_product": product,

            "routine_step": (
                "Treatment"
                if moisture < 25 or sebum > 0.8
                else "Prevention"
            ),
        },
    }

# ==========================================
# FAULT INJECTION
# ==========================================

def inject_missing_field(event):
    """Inject missing required field"""

    target = random.choice([
        "device_id",
        "customer_id",
        "timestamp",
        "reading"
    ])

    faulty = dict(event)

    del faulty[target]

    faulty["_fault"] = f"missing_field:{target}"

    return faulty

# ------------------------------------------

def inject_out_of_range(event):
    """Inject out-of-range values"""

    faulty = json.loads(json.dumps(event))

    field, bad_value = random.choice([

        ("skin_moisture_pct", random.choice([-5.0, 150.0])),

        ("sebum_level_index", random.choice([-0.5, 3.5])),

        ("skin_ph", random.choice([-1.0, 16.0])),

        ("ambient_temp_c", random.choice([-99.0, 999.0])),

        ("ambient_humidity_pct", random.choice([-20, 200])),
    ])

    faulty["reading"][field] = bad_value

    faulty["_fault"] = f"out_of_range:{field}={bad_value}"

    return faulty

# ------------------------------------------

def inject_wrong_type(event):
    """Inject wrong datatype"""

    faulty = json.loads(json.dumps(event))

    mutations = [

        lambda e: e["reading"].__setitem__(
            "skin_moisture_pct",
            "HIGH"
        ),

        lambda e: e["reading"].__setitem__(
            "sebum_level_index",
            "oily"
        ),

        lambda e: e["reading"].__setitem__(
            "skin_ph",
            None
        ),

        lambda e: e.__setitem__(
            "device_id",
            98765
        ),

        lambda e: e.__setitem__(
            "customer_id",
            True
        ),
    ]

    random.choice(mutations)(faulty)

    faulty["_fault"] = "wrong_type"

    return faulty

# ------------------------------------------

def inject_malformed_id(event):
    """Inject malformed IDs"""

    faulty = dict(event)

    mutation = random.choice([

        ("device_id", ""),

        ("device_id", "SKIN_PRO_" + str(random.randint(1, 9))),

        ("customer_id", "USR" + str(random.randint(1, 99))),

        ("customer_id", None),
    ])

    field, bad_value = mutation

    faulty[field] = bad_value

    faulty["_fault"] = (
        f"malformed_id:{field}={bad_value!r}"
    )

    return faulty

# ------------------------------------------

def inject_duplicate(event):
    """Inject duplicate record"""

    faulty = json.loads(json.dumps(event))

    faulty["_fault"] = "duplicate"

    return faulty

# ==========================================
# INJECTOR MAP
# ==========================================

INJECTORS = {

    "missing_field": inject_missing_field,

    "out_of_range": inject_out_of_range,

    "wrong_type": inject_wrong_type,

    "malformed_id": inject_malformed_id,

    "duplicate": inject_duplicate,
}

# ==========================================
# DATASET GENERATOR
# ==========================================

def generate_data():
    """Generate complete dataset"""

    fault_pool = list(FAULT_WEIGHTS.keys())

    fault_cumulative = []

    running = 0.0

    for fault_name in fault_pool:

        running += FAULT_WEIGHTS[fault_name]

        fault_cumulative.append(running)

    def pick_fault_type():

        r = random.random()

        for idx, threshold in enumerate(fault_cumulative):

            if r <= threshold:

                return fault_pool[idx]

        return fault_pool[-1]

    records = []

    valid_pool = []

    fault_summary = {
        key: 0 for key in fault_pool
    }

    fault_summary["valid"] = 0

    for _ in range(TOTAL_RECORDS):

        base = generate_valid_event()

        # Inject faults
        if random.random() < FAULT_RATE:

            fault_type = pick_fault_type()

            if fault_type == "duplicate" and not valid_pool:

                fault_type = "missing_field"

            if fault_type == "duplicate":

                record = inject_duplicate(
                    random.choice(valid_pool)
                )

            else:

                record = INJECTORS[fault_type](base)

            fault_summary[fault_type] += 1

        else:

            record = base

            valid_pool.append(base)

            fault_summary["valid"] += 1

        records.append(record)

    # Save NDJSON
    with open(RAW_DATA_FILE, "w") as f:

        for record in records:

            f.write(json.dumps(record) + "\n")

    # Console summary
    print(f"\n{'─' * 60}")

    print(
        f"Generated {TOTAL_RECORDS} records → {RAW_DATA_FILE}"
    )

    print(f"{'─' * 60}")

    print(
        f"Valid records: {fault_summary['valid']}"
    )

    total_faulty = sum(
        v for k, v in fault_summary.items()
        if k != "valid"
    )

    print(f"Faulty records: {total_faulty}")

    print(f"{'─' * 60}")

    for fault_name in fault_pool:

        print(
            f"{fault_name:<25} {fault_summary[fault_name]}"
        )

    print(f"{'─' * 60}\n")

    return fault_summary, records

# ==========================================
# MAIN TEST
# ==========================================

if __name__ == "__main__":

    generate_data()