import streamlit as st
import pandas as pd
import plotly.express as px

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

    # Rename common lowercase column names to match app code
    rename_map = {
        "state": "State",
        "county": "County",
        "year": "Year",
        "pm25": "PM2.5",
        "pm2.5": "PM2.5",
        "traffic_proximity": "Traffic Proximity",
        "traffic proximity": "Traffic Proximity",
        "wastewater": "Wastewater",
        "diesel_pm": "Diesel PM",
        "diesel pm": "Diesel PM",
        "respiratory_hazard": "Respiratory Hazard",
        "respiratory hazard": "Respiratory Hazard",
        "ozone": "Ozone",
    }

    cleaned_columns = {}
    for col in df.columns:
        lower_col = col.lower().strip()
        if lower_col in rename_map:
            cleaned_columns[col] = rename_map[lower_col]

    df = df.rename(columns=cleaned_columns)

    return df

df = load_data()

# -----------------------------
# Safety check
# -----------------------------
required_columns = ["State", "County", "Year"]

missing_required = [col for col in required_columns if col not in df.columns]

if missing_required:
    st.error("Your CSV is missing required columns.")
    st.write("Missing columns:", missing_required)
    st.write("Columns found in your CSV:", list(df.columns))
    st.stop()

# -----------------------------
# Indicators
# -----------------------------
possible_indicators = [
    "PM2.5",
    "Traffic Proximity",
    "Wastewater",
    "Diesel PM",
    "Respiratory Hazard",
    "Ozone"
]

indicators = [col for col in possible_indicators if col in df.columns]

if len(indicators) == 0:
    st.error("No pollution indicator columns were found.")
    st.write("Columns found in your CSV:", list(df.columns))
    st.stop()

# -----------------------------
# Helper functions
# -----------------------------
def get_health_label(county_value, national_value):
    if pd.isna(county_value) or pd.isna(national_value) or national_value == 0:
        return "No data", "⚪"

    percent_diff = (county_value - national_value) / national_value

    if percent_diff <= -0.10:
        return "Healthy", "🟢"
    elif percent_diff <= 0.10:
        return "Moderate", "🟡"
    else:
        return "Unhealthy", "🔴"


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
# Metric cards with health labels
# -----------------------------
metric_cols = st.columns(3)

for i, indicator in enumerate(indicators):
    county_value = latest_county[indicator]
    national_avg = national_latest_df[indicator].mean()

    health_label, health_icon = get_health_label(county_value, national_avg)

    with metric_cols[i % 3]:
        st.metric(
            label=f"{indicator} {health_icon}",
            value=round(county_value, 3),
            delta=health_label
        )

# -----------------------------
# Indicator selector
# -----------------------------
selected_indicator = st.selectbox("Indicator", indicators)

# -----------------------------
# Latest-year comparison message
# -----------------------------
county_latest_value = latest_county[selected_indicator]
state_latest_avg = state_latest_df[selected_indicator].mean()
national_latest_avg = national_latest_df[selected_indicator].mean()

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
county_trend = county_df[["Year", selected_indicator]].copy()
county_trend["Series"] = "County"
county_trend = county_trend.rename(columns={selected_indicator: "Value"})

state_trend = (
    df[df["State"] == selected_state]
    .groupby("Year")[selected_indicator]
    .mean()
    .reset_index()
)
state_trend["Series"] = "State Average"
state_trend = state_trend.rename(columns={selected_indicator: "Value"})

national_trend = (
    df.groupby("Year")[selected_indicator]
    .mean()
    .reset_index()
)
national_trend["Series"] = "National Average"
national_trend = national_trend.rename(columns={selected_indicator: "Value"})

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
