
import pandas as pd
import os


def calculate_loss_analysis():

    # Read the master batch summary created in Phase 3
    df = pd.read_csv("reports/batch_summary.csv")

    # ---------------------------------------
    # 1. BATCH-WISE LOSS ANALYSIS
    # ---------------------------------------

    batch_loss = df[[
        "batch_id",
        "crop",
        "initial_weight_kg",
        "packed_weight_kg",
        "received_weight_kg",
        "packing_loss_kg",
        "transit_handling_loss_kg",
        "overall_recorded_loss_kg",
        "loss_rate_percent",
        "damaged_weight_kg",
        "rejected_weight_kg"
    ]].copy()

    # ---------------------------------------
    # 2. CROP-WISE LOSS ANALYSIS
    # ---------------------------------------

    # Only compare batches that have delivery records
    valid = df[df["received_weight_kg"].notna()].copy()

    crop_analysis = valid.groupby("crop").agg(
        total_batches=("batch_id", "nunique"),
        total_initial_weight_kg=("initial_weight_kg", "sum"),
        total_received_weight_kg=("received_weight_kg", "sum"),
        total_recorded_loss_kg=("overall_recorded_loss_kg", "sum"),
        total_damaged_kg=("damaged_weight_kg", "sum"),
        total_rejected_kg=("rejected_weight_kg", "sum")
    ).reset_index()

    # Calculate crop-wise overall recorded loss rate
    crop_analysis["loss_rate_percent"] = (
        crop_analysis["total_recorded_loss_kg"] /
        crop_analysis["total_initial_weight_kg"]
    ) * 100

    crop_analysis = crop_analysis.sort_values(
        by="loss_rate_percent",
        ascending=False
    )

    # ---------------------------------------
    # 3. IDENTIFY HIGHEST LOSS BATCHES
    # ---------------------------------------

    highest_loss = batch_loss.dropna(
        subset=["loss_rate_percent"]
    ).sort_values(
        by="loss_rate_percent",
        ascending=False
    )

    # ---------------------------------------
    # 4. SAVE ANALYSIS REPORTS
    # ---------------------------------------

    os.makedirs("reports", exist_ok=True)

    batch_loss.to_csv(
        "reports/batch_loss_analysis.csv",
        index=False
    )

    crop_analysis.to_csv(
        "reports/crop_loss_analysis.csv",
        index=False
    )

    highest_loss.head(10).to_csv(
        "reports/top_10_loss_batches.csv",
        index=False
    )

    # ---------------------------------------
    # 5. DISPLAY RESULTS
    # ---------------------------------------

    print("\n========== LOSS ANALYSIS ==========")

    print("\nCrop-wise loss analysis:")

    print(
        crop_analysis.round(2).to_string(index=False)
    )

    print("\nTop 10 batches with highest recorded loss:")

    print(
        highest_loss.head(10)[
            ["batch_id", "crop", "overall_recorded_loss_kg",
             "loss_rate_percent"]
        ].round(2).to_string(index=False)
    )

    print("\nLoss analysis reports generated successfully!")


if __name__ == "__main__":
    calculate_loss_analysis()
