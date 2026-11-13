
import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Reproducible sample data
random.seed(42)

os.makedirs("data", exist_ok=True)

# Crop-specific illustrative temperature limits
crop_limits = {
    "Tomatoes": (8, 12),
    "Grapes": (0, 4),
    "Onions": (0, 5),
    "Apples": (0, 4),
    "Mangoes": (10, 13)
}

crops = list(crop_limits.keys())

batches = []
packing = []
temperature = []
transit = []
delivery = []

base_date = datetime(2026, 10, 1)

for i in range(1, 31):

    batch_id = f"B{i:03d}"
    crop = random.choice(crops)

    initial_weight = random.randint(500, 1500)

    min_temp, max_temp = crop_limits[crop]

    harvest_date = base_date + timedelta(days=i)

    # 1. BATCH RECORD
    batches.append({
        "batch_id": batch_id,
        "crop": crop,
        "harvest_date": harvest_date.strftime("%Y-%m-%d"),
        "initial_weight_kg": initial_weight,
        "min_temp_c": min_temp,
        "max_temp_c": max_temp
    })

    # 2. PACKING RECORD
    packing_rejected = random.randint(2, 20)
    packed_weight = initial_weight - packing_rejected

    # Intentionally inconsistent packing record for testing
    if batch_id == "B028":
        packing_rejected += 3

    packing.append({
        "batch_id": batch_id,
        "packing_date": (harvest_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "packed_weight_kg": packed_weight,
        "packing_rejected_kg": packing_rejected
    })

    # 3. TEMPERATURE RECORDS
    # B030 intentionally has no temperature readings
    if batch_id != "B030":

        for j in range(5):

            reading_time = harvest_date + timedelta(
                hours=6 * j
            )

            temp_value = round(
                random.uniform(min_temp, max_temp), 1
            )

            # Introduce temperature excursions
            if batch_id in ["B003", "B008", "B014", "B021"] and j == 2:
                temp_value = max_temp + random.randint(3, 7)

            temperature.append({
                "reading_id": f"R{len(temperature) + 1:03d}",
                "batch_id": batch_id,
                "timestamp": reading_time.strftime("%Y-%m-%d %H:%M"),
                "temperature_c": temp_value
            })

    # 4. TRANSIT RECORD
    departure = harvest_date + timedelta(days=2)

    expected_arrival = departure + timedelta(hours=8)

    delay_hours = 0

    if batch_id in ["B003", "B007", "B014", "B019", "B025"]:
        delay_hours = random.randint(2, 6)
    else:
        delay_hours = random.randint(0, 1)

    actual_arrival = expected_arrival + timedelta(hours=delay_hours)

    transit.append({
        "batch_id": batch_id,
        "vehicle_id": f"TRUCK{(i % 5) + 1:02d}",
        "departure_time": departure.strftime("%Y-%m-%d %H:%M"),
        "expected_arrival": expected_arrival.strftime("%Y-%m-%d %H:%M"),
        "actual_arrival": actual_arrival.strftime("%Y-%m-%d %H:%M")
    })

    # 5. DELIVERY RECORD
    transit_loss = random.randint(1, 35)

    # Higher loss for selected batches
    if batch_id in ["B008", "B014", "B021"]:
        transit_loss += 40

    received_weight = packed_weight - transit_loss

    damaged_weight = random.randint(2, 15)
    rejected_weight = random.randint(1, 10)

    # B029 intentionally has no delivery record
    if batch_id != "B029":

        delivery.append({
            "batch_id": batch_id,
            "delivery_date": actual_arrival.strftime("%Y-%m-%d"),
            "received_weight_kg": received_weight,
            "damaged_weight_kg": damaged_weight,
            "rejected_weight_kg": rejected_weight
        })


# Convert records into DataFrames and save CSV files
pd.DataFrame(batches).to_csv("data/batches.csv", index=False)

pd.DataFrame(packing).to_csv("data/packing.csv", index=False)

pd.DataFrame(temperature).to_csv("data/temperature.csv", index=False)

pd.DataFrame(transit).to_csv("data/transit.csv", index=False)

pd.DataFrame(delivery).to_csv("data/delivery.csv", index=False)


print("====================================")
print("AGRICULTURAL DATASET GENERATED")
print("====================================")
print("Total batches:", len(batches))
print("Packing records:", len(packing))
print("Temperature readings:", len(temperature))
print("Transit records:", len(transit))
print("Delivery records:", len(delivery))
print("All CSV files saved inside the data folder.")
print("====================================")
