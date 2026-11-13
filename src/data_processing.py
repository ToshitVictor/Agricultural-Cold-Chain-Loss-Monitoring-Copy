
import pandas as pd
import os


# -----------------------------------------
# 1. LOAD ALL FIVE CSV DATASETS
# -----------------------------------------

def load_data():

    batches = pd.read_csv("data/batches.csv")
    packing = pd.read_csv("data/packing.csv")
    temperature = pd.read_csv("data/temperature.csv")
    transit = pd.read_csv("data/transit.csv")
    delivery = pd.read_csv("data/delivery.csv")

    return batches, packing, temperature, transit, delivery


# -----------------------------------------
# 2. CLEAN AND VALIDATE DATA
# -----------------------------------------

def clean_data(batches, packing, temperature, transit, delivery):

    # Remove duplicate batch IDs from master batch records
    batches = batches.drop_duplicates(subset="batch_id")

    # Convert date columns into datetime format
    batches["harvest_date"] = pd.to_datetime(
        batches["harvest_date"], errors="coerce"
    )

    packing["packing_date"] = pd.to_datetime(
        packing["packing_date"], errors="coerce"
    )

    transit["departure_time"] = pd.to_datetime(
        transit["departure_time"], errors="coerce"
    )

    transit["expected_arrival"] = pd.to_datetime(
        transit["expected_arrival"], errors="coerce"
    )

    transit["actual_arrival"] = pd.to_datetime(
        transit["actual_arrival"], errors="coerce"
    )

    temperature["timestamp"] = pd.to_datetime(
        temperature["timestamp"], errors="coerce"
    )

    # Convert numerical columns safely
    numeric_columns = {
        "batches": ["initial_weight_kg", "min_temp_c", "max_temp_c"],
        "packing": ["packed_weight_kg", "packing_rejected_kg"],
        "temperature": ["temperature_c"],
        "delivery": [
            "received_weight_kg",
            "damaged_weight_kg",
            "rejected_weight_kg"
        ]
    }

    for column in numeric_columns["batches"]:
        batches[column] = pd.to_numeric(
            batches[column], errors="coerce"
        )

    for column in numeric_columns["packing"]:
        packing[column] = pd.to_numeric(
            packing[column], errors="coerce"
        )

    temperature["temperature_c"] = pd.to_numeric(
        temperature["temperature_c"], errors="coerce"
    )

    for column in numeric_columns["delivery"]:
        delivery[column] = pd.to_numeric(
            delivery[column], errors="coerce"
        )

    return batches, packing, temperature, transit, delivery


# -----------------------------------------
# 3. PROCESS TEMPERATURE READINGS
# -----------------------------------------

def process_temperature(batches, temperature):

    # Attach acceptable temperature limits to each reading
    temp_data = temperature.merge(
        batches[["batch_id", "min_temp_c", "max_temp_c"]],
        on="batch_id",
        how="left"
    )

    # Check whether temperature is outside acceptable limits
    temp_data["is_excursion"] = (
        (temp_data["temperature_c"] < temp_data["min_temp_c"]) |
        (temp_data["temperature_c"] > temp_data["max_temp_c"])
    )

    # Summarize temperature readings batch-wise
    temp_summary = temp_data.groupby("batch_id").agg(
        reading_count=("temperature_c", "count"),
        excursion_count=("is_excursion", "sum"),
        min_recorded_temp=("temperature_c", "min"),
        max_recorded_temp=("temperature_c", "max")
    ).reset_index()

    return temp_data, temp_summary


# -----------------------------------------
# 4. CREATE MASTER BATCH SUMMARY
# -----------------------------------------

def build_batch_summary(
    batches, packing, temperature, transit, delivery
):

    # Keep a copy of packing data for validation
    packing_data = packing.copy()

    # Merge all batch-related information
    summary = batches.merge(
        packing_data,
        on="batch_id",
        how="left"
    )

    # Process temperature information
    temp_data, temp_summary = process_temperature(
        batches, temperature
    )

    summary = summary.merge(
        temp_summary,
        on="batch_id",
        how="left"
    )

    summary = summary.merge(
        transit,
        on="batch_id",
        how="left"
    )

    summary = summary.merge(
        delivery,
        on="batch_id",
        how="left"
    )

    # -------------------------------------
    # WEIGHT LOSS CALCULATIONS
    # -------------------------------------

    summary["packing_loss_kg"] = (
        summary["initial_weight_kg"] -
        summary["packed_weight_kg"]
    )

    summary["packing_record_difference_kg"] = (
        summary["packing_loss_kg"] -
        summary["packing_rejected_kg"]
    )

    summary["transit_handling_loss_kg"] = (
        summary["packed_weight_kg"] -
        summary["received_weight_kg"]
    )

    summary["overall_recorded_loss_kg"] = (
        summary["initial_weight_kg"] -
        summary["received_weight_kg"]
    )

    summary["loss_rate_percent"] = (
        summary["overall_recorded_loss_kg"] /
        summary["initial_weight_kg"]
    ) * 100

    # Accepted quantity after damage and rejection
    summary["accepted_weight_kg"] = (
        summary["received_weight_kg"] -
        summary["damaged_weight_kg"] -
        summary["rejected_weight_kg"]
    )

    # -------------------------------------
    # DELIVERY DELAY CALCULATION
    # -------------------------------------

    summary["delay_hours"] = (
        summary["actual_arrival"] -
        summary["expected_arrival"]
    ).dt.total_seconds() / 3600

    # Negative delay means early arrival
    summary["delay_hours"] = summary["delay_hours"].clip(lower=0)

    # -------------------------------------
    # MISSING DATA IDENTIFICATION
    # -------------------------------------

    summary["missing_packing"] = (
        summary["packed_weight_kg"].isna()
    )

    summary["missing_delivery"] = (
        summary["received_weight_kg"].isna()
    )

    summary["missing_temperature"] = (
        summary["reading_count"].isna() |
        (summary["reading_count"] == 0)
    )

    summary["missing_transit"] = (
        summary["actual_arrival"].isna() |
        summary["expected_arrival"].isna()
    )

    # Missing temperature data is unknown, not zero excursions
    summary["reading_count"] = summary["reading_count"].fillna(0)

    # -------------------------------------
    # EXCEPTION FLAGS
    # -------------------------------------

    summary["temperature_excursion"] = (
        summary["excursion_count"].fillna(0) > 0
    )

    summary["delivery_delayed"] = (
        summary["delay_hours"] > 0
    )

    summary["high_loss"] = (
        summary["loss_rate_percent"] > 5
    )

    summary["packing_inconsistency"] = (
        summary["packing_record_difference_kg"].abs() > 0.01
    )

    summary["negative_or_invalid_quantity"] = (
        (summary["initial_weight_kg"] <= 0) |
        (summary["packed_weight_kg"] < 0) |
        (summary["received_weight_kg"] < 0) |
        (summary["damaged_weight_kg"] < 0) |
        (summary["rejected_weight_kg"] < 0) |
        (summary["accepted_weight_kg"] < 0) |
        (summary["packing_loss_kg"] < 0) |
        (summary["transit_handling_loss_kg"] < 0)
    )

    return summary, temp_data


# -----------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------

if __name__ == "__main__":

    print("\nLoading agricultural datasets...\n")

    batches, packing, temperature, transit, delivery = load_data()

    batches, packing, temperature, transit, delivery = clean_data(
        batches, packing, temperature, transit, delivery
    )

    summary, temp_data = build_batch_summary(
        batches, packing, temperature, transit, delivery
    )

    # Save processed datasets
    os.makedirs("reports", exist_ok=True)

    summary.to_csv(
        "reports/batch_summary.csv", index=False
    )

    temp_data.to_csv(
        "reports/processed_temperature.csv", index=False
    )

    print("DATA PROCESSING COMPLETED")
    print("--------------------------------")

    print("Total batches:", len(summary))
    print("Missing delivery records:", summary["missing_delivery"].sum())
    print("Missing temperature records:", summary["missing_temperature"].sum())
    print("Temperature exception batches:", summary["temperature_excursion"].sum())
    print("Delayed batches:", summary["delivery_delayed"].sum())

    print("\nBATCH SUMMARY:")
    print(summary[
        ["batch_id", "crop", "initial_weight_kg",
         "received_weight_kg", "loss_rate_percent"]
    ].head(10).to_string(index=False))

    print("\nProcessed files saved in reports folder.")
