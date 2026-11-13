
import pandas as pd
import os


def is_true(value):
    """Safely check whether a value is True."""
    return pd.notna(value) and bool(value)


def detect_exceptions(df):

    results = []

    for _, row in df.iterrows():

        batch_id = row["batch_id"]
        reasons = []
        risk = "LOW"

        # ----------------------------------
        # HIGH-RISK CONDITIONS
        # ----------------------------------

        if is_true(row["missing_delivery"]):
            reasons.append("Missing delivery record")
            risk = "HIGH"

        if is_true(row["temperature_excursion"]):
            reasons.append("Temperature excursion detected")
            risk = "HIGH"

        if pd.notna(row["loss_rate_percent"]):
            if row["loss_rate_percent"] > 5:
                reasons.append("High recorded weight loss")
                risk = "HIGH"

        if pd.notna(row["delay_hours"]):
            if row["delay_hours"] >= 2:
                reasons.append("Major delivery delay")
                risk = "HIGH"

        if is_true(row["negative_or_invalid_quantity"]):
            reasons.append("Invalid or negative quantity")
            risk = "HIGH"

        # Damage and rejection cannot exceed received quantity
        if pd.notna(row["received_weight_kg"]):

            damage = row["damaged_weight_kg"]
            rejection = row["rejected_weight_kg"]

            if pd.notna(damage) and pd.notna(rejection):

                if damage + rejection > row["received_weight_kg"]:
                    reasons.append(
                        "Damage and rejection exceed received quantity"
                    )
                    risk = "HIGH"

        # ----------------------------------
        # MEDIUM-RISK CONDITIONS
        # ----------------------------------

        if is_true(row["missing_packing"]):
            reasons.append("Missing packing record")

            if risk == "LOW":
                risk = "MEDIUM"

        if is_true(row["missing_temperature"]):
            reasons.append("Missing temperature readings")

            if risk == "LOW":
                risk = "MEDIUM"

        if is_true(row["missing_transit"]):
            reasons.append("Missing transit record")

            if risk == "LOW":
                risk = "MEDIUM"

        if is_true(row["packing_inconsistency"]):
            reasons.append("Packing quantity inconsistency")

            if risk == "LOW":
                risk = "MEDIUM"

        if pd.notna(row["delay_hours"]):
            if 0 < row["delay_hours"] < 2:
                reasons.append("Minor delivery delay")

                if risk == "LOW":
                    risk = "MEDIUM"

        # ----------------------------------
        # CREATE BATCH RESULT
        # ----------------------------------

        results.append({
            "batch_id": batch_id,
            "crop": row["crop"],
            "risk_level": risk,
            "exception_count": len(reasons),
            "exception_details": "; ".join(reasons),
            "loss_rate_percent": row["loss_rate_percent"],
            "delay_hours": row["delay_hours"],
            "excursion_count": row["excursion_count"]
        })

    return pd.DataFrame(results)


def generate_exception_report():

    # Load processed batch data
    df = pd.read_csv("reports/batch_summary.csv")

    # Detect exceptions
    risk_report = detect_exceptions(df)

    # Keep only batches with exceptions
    exception_report = risk_report[
        risk_report["risk_level"] != "LOW"
    ].copy()

    # Sort by risk
    priority = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    exception_report["priority"] = (
        exception_report["risk_level"].map(priority)
    )

    exception_report = exception_report.sort_values(
        by=["priority", "exception_count"],
        ascending=[True, False]
    )

    exception_report = exception_report.drop(
        columns=["priority"]
    )

    # Save both reports
    os.makedirs("reports", exist_ok=True)

    risk_report.to_csv(
        "reports/batch_risk_assessment.csv",
        index=False
    )

    exception_report.to_csv(
        "reports/exception_report.csv",
        index=False
    )

    # ----------------------------------
    # DISPLAY RESULTS
    # ----------------------------------

    print("\n========== EXCEPTION REPORT ==========")

    print("\nTotal batches:", len(risk_report))

    print(
        "High risk:",
        (risk_report["risk_level"] == "HIGH").sum()
    )

    print(
        "Medium risk:",
        (risk_report["risk_level"] == "MEDIUM").sum()
    )

    print(
        "Low risk:",
        (risk_report["risk_level"] == "LOW").sum()
    )

    print("\nBATCH EXCEPTION DETAILS:")

    print(exception_report.to_string(index=False))

    print("\nException reports generated successfully!")


if __name__ == "__main__":
    generate_exception_report()
