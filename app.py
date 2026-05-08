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
    df = pd.read_csv("county_year_panel.csv")

    # Clean column names
    df.columns = df.columns.str.strip()

    return df

df = load_data()

# -----------------------------
# Helper: flexible column matching
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


# -----------------------------
# Match core columns
# -----------------------------
state_col = find_column(df, ["State", "state"])
county_col = find_column(df, ["County", "county"])
year_col = find_column(df, ["Year", "year"])

if state_col is None or county_col is None or year_col is None:
    st.error("The app could not find the State, County, or Year columns.")
    st.write("Columns found in your CSV:")
    st.write(list(df.columns))
    st.stop()

# Rename core columns for easier use
df = df.rename(
    columns={
        state_col: "State",
        county_col: "County",
        year_col: "Year"
    }
)

# -----------------------------
# Match indicator columns
# -----------------------------
indicator_options = {
    "PM2.5": [
        "PM2.5",
        "PM25",
        "PM 2.5",
        "Particulate Matter 2.5",
        "particulate_matter_2_5"
    ],
    "Traffic Proximity": [
        "Traffic Proximity",
        "traffic_proximity",
        "Traffic",
        "traffic proximity"
    ],
    "Wastewater": [
        "Wastewater",
        "wastewater",
        "Waste Water",
        "waste_water"
    ],
    "Diesel PM": [
        "Diesel PM",
        "diesel_pm",
        "Diesel Particulate Matter",
        "Diesel"
    ],
    "Respiratory Hazard": [
        "Respiratory Hazard",
        "respiratory_hazard",
        "Respiratory",
        "resp hazard",
        "resp_hazard"
    ],
    "Ozone": [
        "Ozone",
        "ozone",
        "O3"
    ]
}

indicator_columns = {}

for display_name, possible_names in indicator_options.items():
    matched_col = find_column(df, possible_names)
    indicator_columns[display_name] = matched_col

# Convert indicator columns to numbers
for display_name, actual_col in indicator_columns.items():
    if actual_col is not None:
        df[actual_col] = pd.to_numeric(df[actual_col], errors="coerce")

# Available indicators for the chart
available_indicators = [
    display_name
    for display_name, actual_col in indicator_columns.items()
    if actual_col is not None
]

if len(available_indicators) == 0:
    st.error("No pollution indicator columns were found.")
    st.write("Columns found in your CSV:")
    st.write(list(df.columns))
    st.stop()

# -----------------------------
# Health label logic
# -----------------------------
def get_health_label(county_value, national_value):
    """
    Pollution indicators:
    - Lower than national average = healthier
    - Close to national average = moderate
    - Higher than national average = unhealthy
    """

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
    if county_value < state_avg:
        state_comparison = "below"
    elif county_value > state_avg:
        state_comparison = "above"
    else:
        state_comparison = "equal to"

    if county_value < national_avg:
        national_comparison = "below"
    elif county_value > national_avg:
        national_comparison = "above"
    else:
        national_comparison = "equal to"

    return (
        f"Latest-year comparison: {indicator} in {county_name} is "
        f"{state_comparison} the state average and "
        f"{national_comparison} the national average."
    )


# -----------------------------
# Custom card styling
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

states = sorted(df["State"].dropna().unique())
selected_state = st.sidebar.selectbox("State", states)

counties = sorted(
    df[df["State"] == selected_state]["County"]
    .dropna()
    .unique()
)

selected_county = st.sidebar.selectbox("County", counties)

# -----------------------------
# Filter selected county data
# -----------------------------
county_df = df[
    (df["State"] == selected_state) &
    (df["County"] == selected_county)
].copy()

if county_df.empty:
    st.error("No data found for this county.")
    st.stop()

latest_year = county_df["Year"].max()
latest_county = county_df[county_df["Year"] == latest_year].iloc[0]

state_latest_df = df[
    (df["State"] == selected_state) &
    (df["Year"] == latest_year)
]

national_latest_df = df[df["Year"] == latest_year]

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
# Metric cards: all 6 indicators
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
        actual_col = indicator_columns.get(indicator)

        with cols[col_index]:
            if actual_col is None:
                value_display = "No data"
                health_label = "No data"
                health_icon = "⚪"
                health_color = "#6b7280"
            else:
                county_value = latest_county[actual_col]
                national_avg = national_latest_df[actual_col].mean()

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
selected_indicator = st.selectbox("Indicator", available_indicators)

selected_indicator_col = indicator_columns[selected_indicator]

# -----------------------------
# Latest-year comparison message
# -----------------------------
county_latest_value = latest_county[selected_indicator_col]
state_latest_avg = state_latest_df[selected_indicator_col].mean()
national_latest_avg = national_latest_df[selected_indicator_col].mean()

comparison_message = get_comparison_sentence(
    selected_indicator,
    selected_county,
    county_latest_value,
    state_latest_avg,
    national_latest_avg
)

st.info(comparison_message)

# -----------------------------
# Prepare chart data
# -----------------------------
county_trend = county_df[["Year", selected_indicator_col]].copy()
county_trend["Series"] = "County"
county_trend = county_trend.rename(columns={selected_indicator_col: "Value"})

state_trend = (
    df[df["State"] == selected_state]
    .groupby("Year")[selected_indicator_col]
    .mean()
    .reset_index()
)
state_trend["Series"] = "State Average"
state_trend = state_trend.rename(columns={selected_indicator_col: "Value"})

national_trend = (
    df.groupby("Year")[selected_indicator_col]
    .mean()
    .reset_index()
)
national_trend["Series"] = "National Average"
national_trend = national_trend.rename(columns={selected_indicator_col: "Value"})

chart_df = pd.concat(
    [county_trend, state_trend, national_trend],
    ignore_index=True
)

# -----------------------------
# Chart
# -----------------------------
st.markdown(f"### {selected_indicator}: {selected_county} vs State vs National")

fig = px.line(
    chart_df,
    x="Year",
    y="Value",
    color="Series",
    markers=True,
    title=None
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
    The health label compares the county's latest-year value to the national average.

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
    st.write("This shows which CSV column is being used for each indicator.")
    st.write(indicator_columns)
    st.write("All columns in CSV:")
    st.write(list(df.columns))
