
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Agricultural Cold-Chain Monitor",
    page_icon="🌾",
    layout="wide"
)

sns.set_theme(style="whitegrid", palette="viridis")


# ==========================================
# LOAD DATA
# ==========================================

@st.cache_data
def load_data():

    batches = pd.read_csv("reports/batch_summary.csv")
    risks = pd.read_csv("reports/batch_risk_assessment.csv")
    exceptions = pd.read_csv("reports/exception_report.csv")
    temperature = pd.read_csv("reports/processed_temperature.csv")
    crop_loss = pd.read_csv("reports/crop_loss_analysis.csv")

    temperature["timestamp"] = pd.to_datetime(
        temperature["timestamp"], errors="coerce"
    )

    batches["harvest_date"] = pd.to_datetime(
        batches["harvest_date"], errors="coerce"
    )

    return batches, risks, exceptions, temperature, crop_loss


# ==========================================
# CHECK DATA AVAILABILITY
# ==========================================

required_files = [
    "reports/batch_summary.csv",
    "reports/batch_risk_assessment.csv",
    "reports/exception_report.csv",
    "reports/processed_temperature.csv",
    "reports/crop_loss_analysis.csv"
]

missing_files = [
    file for file in required_files
    if not os.path.exists(file)
]

if missing_files:
    st.error("Required processed data files are missing.")
    st.write(missing_files)
    st.stop()

batch_df, risk_df, exception_df, temp_df, crop_df = load_data()


# ==========================================
# APPLICATION HEADER
# ==========================================

st.title("🌾 Agricultural Cold-Chain Loss Monitoring")

st.markdown(
    "### Post-Harvest Monitoring and Exception Detection System"
)

st.caption(
    "Monitor agricultural batches, recorded weight loss, "
    "temperature excursions and delivery performance."
)

st.divider()


# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("🌾 Cold-Chain Monitor")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard Overview",
        "Batch Tracking",
        "Loss Analysis",
        "Temperature Monitoring",
        "Exception Report"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "Monitor batch performance and identify "
    "post-harvest operational exceptions."
)


# ==========================================
# COMMON FILTERS
# ==========================================

st.sidebar.subheader("Data Filters")

crop_options = sorted(batch_df["crop"].dropna().unique())

selected_crops = st.sidebar.multiselect(
    "Select Crop",
    crop_options,
    default=crop_options
)

filtered_df = batch_df[
    batch_df["crop"].isin(selected_crops)
].copy()

risk_filtered = risk_df[
    risk_df["batch_id"].isin(filtered_df["batch_id"])
].copy()

exception_filtered = exception_df[
    exception_df["batch_id"].isin(filtered_df["batch_id"])
].copy()


# ==========================================
# PAGE 1: DASHBOARD OVERVIEW
# ==========================================

if page == "Dashboard Overview":

    st.header("Dashboard Overview")

    total_batches = len(filtered_df)

    valid_loss = filtered_df[
        filtered_df["loss_rate_percent"].notna()
    ]

    avg_loss = (
        valid_loss["loss_rate_percent"].mean()
        if not valid_loss.empty else 0
    )

    total_exceptions = len(exception_filtered)

    delayed_batches = (
        filtered_df["delay_hours"].fillna(0) > 0
    ).sum()

    high_risk = (
        risk_filtered["risk_level"] == "HIGH"
    ).sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Batches", total_batches)

    col2.metric("Average Recorded Loss", f"{avg_loss:.2f}%")

    col3.metric("Delayed Batches", int(delayed_batches))

    col4.metric("Exception Batches", total_exceptions)

    col5.metric("High Risk Batches", int(high_risk))

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Crop-wise Recorded Loss")

        crop_data = valid_loss.groupby("crop").agg(
            initial=("initial_weight_kg", "sum"),
            received=("received_weight_kg", "sum")
        ).reset_index()

        crop_data["loss_percent"] = (
            (crop_data["initial"] - crop_data["received"])
            / crop_data["initial"]
        ) * 100

        fig, ax = plt.subplots(figsize=(8, 4))

        sns.barplot(
            data=crop_data,
            x="crop",
            y="loss_percent",
            ax=ax
        )

        ax.set_ylabel("Recorded Loss (%)")
        ax.set_xlabel("Crop")

        plt.xticks(rotation=25)
        plt.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    with right:

        st.subheader("Batch Risk Distribution")

        risk_counts = risk_filtered["risk_level"].value_counts()

        risk_counts = risk_counts.reindex(
            ["LOW", "MEDIUM", "HIGH"],
            fill_value=0
        )

        fig, ax = plt.subplots(figsize=(7, 4))

        ax.pie(
            risk_counts.values,
            labels=risk_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.4}
        )

        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Recent Batch Records")

    st.dataframe(
        filtered_df[
            [
                "batch_id",
                "crop",
                "initial_weight_kg",
                "received_weight_kg",
                "loss_rate_percent"
            ]
        ].head(10),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# PAGE 2: BATCH TRACKING
# ==========================================

elif page == "Batch Tracking":

    st.header("Batch Tracking")

    if filtered_df.empty:

        st.warning("No batches found for the selected crop filters.")

    else:

        selected_batch = st.selectbox(
            "Select Batch ID",
            filtered_df["batch_id"].tolist()
        )

        batch = filtered_df[
            filtered_df["batch_id"] == selected_batch
        ].iloc[0]

        risk = risk_filtered[
            risk_filtered["batch_id"] == selected_batch
        ]

        st.subheader(f"Batch Details: {selected_batch}")

        c1, c2, c3 = st.columns(3)

        c1.metric("Crop", batch["crop"])

        c2.metric(
            "Initial Weight",
            f'{batch["initial_weight_kg"]:.1f} kg'
        )

        c3.metric(
            "Recorded Loss",
            f'{batch["loss_rate_percent"]:.2f}%'
            if pd.notna(batch["loss_rate_percent"])
            else "Unavailable"
        )

        st.divider()

        st.subheader("Quantity Tracking Through Stages")

        stages = pd.DataFrame({
            "Stage": ["Harvested", "Packed", "Received"],
            "Weight (kg)": [
                batch["initial_weight_kg"],
                batch["packed_weight_kg"],
                batch["received_weight_kg"]
            ]
        })

        st.dataframe(
            stages,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Batch Operational Information")

        details = {
            "Packing Loss (kg)": batch["packing_loss_kg"],
            "Transit/Handling Loss (kg)": batch["transit_handling_loss_kg"],
            "Damaged Weight (kg)": batch["damaged_weight_kg"],
            "Rejected Weight (kg)": batch["rejected_weight_kg"],
            "Accepted Weight (kg)": batch["accepted_weight_kg"],
            "Delivery Delay (hours)": batch["delay_hours"]
        }

        st.table(pd.DataFrame(
            list(details.items()),
            columns=["Parameter", "Value"]
        ))

        if not risk.empty:

            risk_row = risk.iloc[0]

            st.subheader("Batch Risk Assessment")

            st.write("Risk Level:", risk_row["risk_level"])

            st.write(
                "Detected Exceptions:",
                risk_row["exception_count"]
            )

            st.write(
                "Exception Details:",
                risk_row["exception_details"]
            )


# ==========================================
# PAGE 3: LOSS ANALYSIS
# ==========================================

elif page == "Loss Analysis":

    st.header("Agricultural Weight Loss Analysis")

    st.subheader("Batch-wise Recorded Loss")

    loss_data = filtered_df.dropna(
        subset=["loss_rate_percent"]
    ).nlargest(10, "loss_rate_percent")

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=loss_data,
        x="batch_id",
        y="loss_rate_percent",
        ax=ax
    )

    ax.set_ylabel("Recorded Loss (%)")
    ax.set_xlabel("Batch ID")

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Crop-wise Loss Comparison")

    valid = filtered_df[
        filtered_df["received_weight_kg"].notna()
    ]

    crop_data = valid.groupby("crop").agg(
        initial=("initial_weight_kg", "sum"),
        received=("received_weight_kg", "sum")
    ).reset_index()

    crop_data["loss_percent"] = (
        (crop_data["initial"] - crop_data["received"])
        / crop_data["initial"]
    ) * 100

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=crop_data.sort_values(
            "loss_percent", ascending=False
        ),
        x="crop",
        y="loss_percent",
        ax=ax
    )

    ax.set_ylabel("Recorded Loss (%)")

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Detailed Loss Records")

    st.dataframe(
        filtered_df[
            [
                "batch_id",
                "crop",
                "packing_loss_kg",
                "transit_handling_loss_kg",
                "overall_recorded_loss_kg",
                "loss_rate_percent"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# PAGE 4: TEMPERATURE MONITORING
# ==========================================

elif page == "Temperature Monitoring":

    st.header("Temperature Monitoring")

    available_batches = sorted(
        filtered_df["batch_id"].tolist()
    )

    if available_batches:

        selected_batch = st.selectbox(
            "Choose Batch for Temperature Monitoring",
            available_batches
        )

        batch_info = filtered_df[
            filtered_df["batch_id"] == selected_batch
        ].iloc[0]

        readings = temp_df[
            temp_df["batch_id"] == selected_batch
        ].dropna(subset=["timestamp", "temperature_c"])

        st.write("Crop:", batch_info["crop"])

        st.write(
            f'Acceptable temperature: '
            f'{batch_info["min_temp_c"]}°C to '
            f'{batch_info["max_temp_c"]}°C'
        )

        if readings.empty:

            st.warning(
                "No temperature readings available for this batch."
            )

        else:

            fig, ax = plt.subplots(figsize=(11, 5))

            sns.lineplot(
                data=readings.sort_values("timestamp"),
                x="timestamp",
                y="temperature_c",
                marker="o",
                ax=ax
            )

            ax.axhline(
                batch_info["min_temp_c"],
                linestyle="--",
                label="Minimum Limit"
            )

            ax.axhline(
                batch_info["max_temp_c"],
                linestyle="--",
                label="Maximum Limit"
            )

            excursions = readings[
                (readings["temperature_c"] < batch_info["min_temp_c"]) |
                (readings["temperature_c"] > batch_info["max_temp_c"])
            ]

            if not excursions.empty:

                ax.scatter(
                    excursions["timestamp"],
                    excursions["temperature_c"],
                    color="red",
                    s=90,
                    label="Excursion"
                )

            ax.set_ylabel("Temperature (°C)")
            ax.set_xlabel("Date and Time")
            ax.legend()

            plt.xticks(rotation=30)
            plt.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            st.subheader("Temperature Readings")

            st.dataframe(
                readings[
                    [
                        "timestamp",
                        "temperature_c"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


# ==========================================
# PAGE 5: EXCEPTION REPORT
# ==========================================

elif page == "Exception Report":

    st.header("Batch Exception Report")

    st.write(
        "Identify batches requiring operational attention."
    )

    if exception_filtered.empty:

        st.success("No exceptions found for the selected filters.")

    else:

        high = (
            exception_filtered["risk_level"] == "HIGH"
        ).sum()

        medium = (
            exception_filtered["risk_level"] == "MEDIUM"
        ).sum()

        c1, c2 = st.columns(2)

        c1.metric("High Risk", int(high))
        c2.metric("Medium Risk", int(medium))

        st.subheader("Exception Details")

        st.dataframe(
            exception_filtered,
            use_container_width=True,
            hide_index=True
        )

        csv_data = exception_filtered.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Exception Report",
            data=csv_data,
            file_name="agricultural_exception_report.csv",
            mime="text/csv"
        )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Agricultural Cold-Chain Loss Monitoring System | "
    "Developed using Python, Pandas, Matplotlib, "
    "Seaborn and Streamlit"
)
