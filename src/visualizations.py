
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Consistent visualization style
sns.set_theme(style="whitegrid", palette="viridis")

os.makedirs("reports/charts", exist_ok=True)


# ==========================================
# LOAD PROCESSED DATA
# ==========================================

def load_visualization_data():

    batch_df = pd.read_csv("reports/batch_summary.csv")
    crop_df = pd.read_csv("reports/crop_loss_analysis.csv")
    risk_df = pd.read_csv("reports/batch_risk_assessment.csv")
    temp_df = pd.read_csv("reports/processed_temperature.csv")

    temp_df["timestamp"] = pd.to_datetime(
        temp_df["timestamp"], errors="coerce"
    )

    return batch_df, crop_df, risk_df, temp_df


# ==========================================
# 1. BATCH-WISE LOSS BAR CHART
# ==========================================

def plot_batch_loss(df):

    data = df.dropna(
        subset=["loss_rate_percent"]
    ).nlargest(10, "loss_rate_percent")

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=data,
        x="batch_id",
        y="loss_rate_percent",
        ax=ax
    )

    ax.set_title("Top 10 Batches by Recorded Loss Rate")
    ax.set_xlabel("Batch ID")
    ax.set_ylabel("Recorded Loss (%)")

    plt.tight_layout()

    return fig


# ==========================================
# 2. CROP-WISE LOSS COMPARISON
# ==========================================

def plot_crop_loss(df):

    data = df.sort_values(
        "loss_rate_percent",
        ascending=False
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=data,
        x="crop",
        y="loss_rate_percent",
        ax=ax
    )

    ax.set_title("Crop-wise Recorded Loss Comparison")
    ax.set_xlabel("Crop Type")
    ax.set_ylabel("Recorded Loss (%)")

    plt.xticks(rotation=25)
    plt.tight_layout()

    return fig


# ==========================================
# 3. TEMPERATURE MONITORING LINE CHART
# ==========================================

def plot_temperature(temp_df, batch_id, batch_df):

    data = temp_df[
        temp_df["batch_id"] == batch_id
    ].dropna(subset=["timestamp", "temperature_c"])

    if data.empty:
        return None

    batch_info = batch_df[
        batch_df["batch_id"] == batch_id
    ]

    if batch_info.empty:
        return None

    min_temp = batch_info.iloc[0]["min_temp_c"]
    max_temp = batch_info.iloc[0]["max_temp_c"]

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.lineplot(
        data=data.sort_values("timestamp"),
        x="timestamp",
        y="temperature_c",
        marker="o",
        linewidth=2,
        ax=ax
    )

    # Acceptable temperature boundaries
    ax.axhline(
        min_temp,
        linestyle="--",
        label="Minimum acceptable temperature"
    )

    ax.axhline(
        max_temp,
        linestyle="--",
        label="Maximum acceptable temperature"
    )

    # Highlight excursion readings
    excursion_data = data[
        (data["temperature_c"] < min_temp) |
        (data["temperature_c"] > max_temp)
    ]

    if not excursion_data.empty:
        ax.scatter(
            excursion_data["timestamp"],
            excursion_data["temperature_c"],
            color="red",
            s=90,
            label="Temperature excursion",
            zorder=5
        )

    ax.set_title(f"Temperature Monitoring - {batch_id}")
    ax.set_xlabel("Date and Time")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()

    plt.xticks(rotation=30)
    plt.tight_layout()

    return fig


# ==========================================
# 4. DELIVERY DELAY BAR CHART
# ==========================================

def plot_delivery_delay(df):

    data = df.dropna(
        subset=["delay_hours"]
    ).nlargest(10, "delay_hours")

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=data,
        x="batch_id",
        y="delay_hours",
        ax=ax
    )

    ax.axhline(
        2,
        linestyle="--",
        label="Major delay threshold (2 hours)"
    )

    ax.set_title("Delivery Delay by Batch")
    ax.set_xlabel("Batch ID")
    ax.set_ylabel("Delay (Hours)")
    ax.legend()

    plt.tight_layout()

    return fig


# ==========================================
# 5. RISK DISTRIBUTION DONUT CHART
# ==========================================

def plot_risk_distribution(df):

    risk_counts = (
        df["risk_level"]
        .value_counts()
        .reindex(["LOW", "MEDIUM", "HIGH"], fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.pie(
        risk_counts.values,
        labels=risk_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.4}
    )

    ax.set_title("Batch Risk Distribution")

    plt.tight_layout()

    return fig


# ==========================================
# 6. EXCEPTION HEATMAP
# ==========================================

def plot_exception_heatmap(df):

    columns = {
        "High Loss": "high_loss",
        "Temperature": "temperature_excursion",
        "Delay": "delivery_delayed",
        "Missing Delivery": "missing_delivery",
        "Missing Temperature": "missing_temperature",
        "Packing Issue": "packing_inconsistency"
    }

    heatmap_data = df[
        ["batch_id"] + list(columns.values())
    ].copy()

    heatmap_data = heatmap_data.rename(
        columns={v: k for k, v in columns.items()}
    )

    heatmap_data = heatmap_data.set_index("batch_id")

    heatmap_data = heatmap_data.fillna(False).astype(int)

    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(
        heatmap_data,
        cmap="YlOrRd",
        linewidths=0.5,
        cbar=False,
        ax=ax
    )

    ax.set_title("Batch-wise Exception Heatmap")
    ax.set_xlabel("Exception Type")
    ax.set_ylabel("Batch ID")

    plt.tight_layout()

    return fig


# ==========================================
# TEST ALL VISUALIZATIONS
# ==========================================

if __name__ == "__main__":

    batch_df, crop_df, risk_df, temp_df = (
        load_visualization_data()
    )

    charts = {
        "batch_loss": plot_batch_loss(batch_df),
        "crop_loss": plot_crop_loss(crop_df),
        "delivery_delay": plot_delivery_delay(batch_df),
        "risk_distribution": plot_risk_distribution(risk_df),
        "exception_heatmap": plot_exception_heatmap(batch_df)
    }

    # Select B008 to demonstrate a temperature excursion
    charts["temperature"] = plot_temperature(
        temp_df, "B008", batch_df
    )

    for name, fig in charts.items():

        if fig is not None:
            fig.savefig(
                f"reports/charts/{name}.png",
                dpi=150,
                bbox_inches="tight"
            )

            plt.close(fig)

            print(f"Generated: {name}.png")

    print("\nAll visualization charts generated successfully!")
