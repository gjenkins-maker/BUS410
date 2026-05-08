import streamlit as st
import pandas as pd
import plotly.express as px
import re

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Deadly Data: County Pollution Lookup",
    layout="wide"
)

st.title("Deadly Data: County Pollution Lookup")
st.caption(
    "Explore how pollution burden changed across counties over time, "
    "with state and national comparisons."
)

# -----------------------------
# Load data
# -----------------------------
@st.cache_data
def load_data():
    summary_df = pd.read_csv("county_summary.csv")
    panel_df = pd.read_csv("county_year_panel.csv")

    summary_df.columns = summary_df.columns.str.strip()
    panel_df.columns = panel_df.columns.str.strip()

    return summary_df, panel_df

summary_df, panel_df = load_data()

# -----------------------------
# Helper functions
# -----------------------------
def clean_name(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def find_column(df, possible_names):
    cleaned_columns = {clean_name(col): col for col in df.columns}

    for name in possible_names:
        cleaned_name = clean_name(name)
        if cleaned_name in cleaned_columns:
            return cleaned_columns[cleaned_name]

    for col in df.columns:
        cleaned_col = clean_name(col)
        for name in possible_names:
            cleaned_name = clean_name(name)
            if cleaned_name in cleaned_col or cleaned_col in cleaned_name:
                return col

    return None


def get_health_label(county_value, national_value):
    if pd.isna(county_value) or pd.isna(national_value) or national_value == 0:
        return "No data", "⚪", "#6b7280"

    percent_diff = (county_value - national_value) / national_value

    if percent_diff <= -0.10:
        return "Healthy", "🟢", "#15803d"
    elif percent_diff <= 0.10:
        return "Moderate", "🟡", "#ca8a04"
    else:
        return "Unhealthy", "🔴", "#dc2626"


def get_comparison_sentence(indicator, county_name, county_value, state_avg, national_avg):
    state_comparison = "below" if county_value < state_avg else "above"
    national_comparison = "below" if county_value < national_avg else "above"

    return (
        f"Latest-year comparison: {indicator} in {county_name} is "
        f"{state_comparison} the state average and "
        f"{national_comparison} the national average."
    )

# -----------------------------
# Match core columns
# -----------------------------
summary_state_col = find_column(summary_df, ["State", "state"])
summary_county_col = find_column(summary_df, ["County", "county"])

panel_state_col = find_column(panel_df, ["State", "state"])
panel_county_col = find_column(panel_df, ["County", "county"])
panel_year_col = find_column(panel_df, ["Year", "year"])

summary_df = summary_df.rename(
    columns={
        summary_state_col: "State",
        summary_county_col: "County"
    }
)

panel_df = panel_df.rename(
    columns={
        panel_state_col: "State",
        panel_county_col: "County",
        panel_year_col: "Year"
    }
)

# -----------------------------
# Indicator matching
# -----------------------------
indicator_options = {
    "PM2.5": ["PM2.5", "PM25", "pm25"],
    "Traffic Proximity": ["Traffic Proximity", "traffic_proximity", "traffic"],
    "Wastewater": ["Wastewater", "wastewater", "waste water"],
    "Diesel PM": ["Diesel PM", "diesel_pm", "diesel"],
    "Respiratory Hazard": ["Respiratory Hazard", "respiratory_hazard", "respiratory"],
    "Ozone": ["Ozone", "ozone", "o3"]
}

summary_indicator_columns = {}
panel_indicator_columns = {}

for display_name, possible_names in indicator_options.items():
    summary_indicator_columns[display_name] = find_column(summary_df, possible_names)
    panel_indicator_columns[display_name] = find_column(panel_df, possible_names)

for col in summary_indicator_columns.values():
    if col is not None:
        summary_df[col] = pd.to_numeric(summary_df[col], errors="coerce")

for col in panel_indicator_columns.values():
    if col is not None:
        panel_df[col] = pd.to_numeric(panel_df[col], errors="coerce")

available_chart_indicators = [
    indicator for indicator, col in panel_indicator_columns.items()
    if col is not None
]

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 22px 24px;
        margin-bottom: 16px;
        min-height: 120px;
    }

    .metric-label {
        color: #9ca3af;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .health-pill {
        display: inline-block;
        color: white;
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Search")

states = sorted(summary_df["State"].dropna().unique())
selected_state = st.sidebar.selectbox("State", states)

counties = sorted(
    summary_df[summary_df["State"] == selected_state]["County"]
    .dropna()
    .unique()
)

selected_county = st.sidebar.selectbox("County", counties)

# -----------------------------
# Filter data
# -----------------------------
summary_county_df = summary_df[
    (summary_df["State"] == selected_state) &
    (summary_df["County"] == selected_county)
].copy()

panel_county_df = panel_df[
    (panel_df["State"] == selected_state) &
    (panel_df["County"] == selected_county)
].copy()

if summary_county_df.empty:
    st.error("No summary data found for this county.")
    st.stop()

latest_summary = summary_county_df.iloc[0]

latest_year = panel_county_df["Year"].max()

panel_state_latest_df = panel_df[
    (panel_df["State"] == selected_state) &
    (panel_df["Year"] == latest_year)
]

panel_national_latest_df = panel_df[
    panel_df["Year"] == latest_year
]

# -----------------------------
# Header
# -----------------------------
st.subheader(f"{selected_county}, {selected_state}")

st.markdown(
    """
    <span style="
        background-color:#2d5bd1;
        color:white;
        padding:8px 14px;
        border-radius:20px;
        font-weight:600;
        font-size:14px;
    ">
        Non-DC county
    </span>
    """,
    unsafe_allow_html=True
)

st.write("")

# -----------------------------
# Metric cards using county_summary.csv
# -----------------------------
all_indicators = [
    "PM2.5",
    "Traffic Proximity",
    "Wastewater",
    "Diesel PM",
    "Respiratory Hazard",
    "Ozone"
]

for row_start in range(0, len(all_indicators), 3):
    cols = st.columns(3)

    for col_index, indicator in enumerate(all_indicators[row_start:row_start + 3]):
        actual_col = summary_indicator_columns.get(indicator)

        with cols[col_index]:
            if actual_col is None:
                value_display = "No data"
                health_label = "No data"
                health_icon = "⚪"
                health_color = "#6b7280"
            else:
                county_value = latest_summary[actual_col]
                national_avg = summary_df[actual_col].mean()

                health_label, health_icon, health_color = get_health_label(
                    county_value,
                    national_avg
                )

                if pd.isna(county_value):
                    value_display = "No data"
                else:
                    value_display = f"{county_value:.3f}"

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{indicator}</div>
                    <div class="metric-value">{value_display}</div>
                    <div class="health-pill" style="background-color:{health_color};">
                        {health_icon} {health_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# -----------------------------
# Indicator selector
# -----------------------------
selected_indicator = st.selectbox("Indicator", available_chart_indicators)
selected_indicator_col = panel_indicator_columns[selected_indicator]

# -----------------------------
# Comparison message
# -----------------------------
latest_county_panel = panel_county_df[panel_county_df["Year"] == latest_year].iloc[0]

county_latest_value = latest_county_panel[selected_indicator_col]
state_latest_avg = panel_state_latest_df[selected_indicator_col].mean()
national_latest_avg = panel_national_latest_df[selected_indicator_col].mean()

comparison_message = get_comparison_sentence(
    selected_indicator,
    selected_county,
    county_latest_value,
    state_latest_avg,
    national_latest_avg
)

st.info(comparison_message)

# -----------------------------
# Chart
# -----------------------------
county_trend = panel_county_df[["Year", selected_indicator_col]].copy()
county_trend["Series"] = "County"
county_trend = county_trend.rename(columns={selected_indicator_col: "Value"})

state_trend = (
    panel_df[panel_df["State"] == selected_state]
    .groupby("Year")[selected_indicator_col]
    .mean()
    .reset_index()
)
state_trend["Series"] = "State Average"
state_trend = state_trend.rename(columns={selected_indicator_col: "Value"})

national_trend = (
    panel_df.groupby("Year")[selected_indicator_col]
    .mean()
    .reset_index()
)
national_trend["Series"] = "National Average"
national_trend = national_trend.rename(columns={selected_indicator_col: "Value"})

chart_df = pd.concat(
    [county_trend, state_trend, national_trend],
    ignore_index=True
)

st.markdown(f"### {selected_indicator}: {selected_county} vs State vs National")

fig = px.line(
    chart_df,
    x="Year",
    y="Value",
    color="Series",
    markers=True
)

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    legend_title="Series",
    template="plotly_dark",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Health label guide
# -----------------------------
st.markdown("### Health Label Guide")

st.markdown(
    """
    The health label compares the county's latest value to the national average.

    | Label | Meaning |
    |---|---|
    | 🟢 Healthy | County value is more than 10% below the national average |
    | 🟡 Moderate | County value is within 10% of the national average |
    | 🔴 Unhealthy | County value is more than 10% above the national average |

    Since these are pollution indicators, lower values are generally better.
    """
)

# -----------------------------
# Debug helper
# -----------------------------
with st.expander("Column matching details"):
    st.write("Summary file indicator columns:")
    st.write(summary_indicator_columns)

    st.write("Panel file indicator columns:")
    st.write(panel_indicator_columns)

    st.write("Columns in county_summary.csv:")
    st.write(list(summary_df.columns))

    st.write("Columns in county_year_panel.csv:")
    st.write(list(panel_df.columns))
