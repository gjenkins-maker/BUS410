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
    df.columns = df.columns.str.strip()

    # Rename lowercase columns to match the app code
    df = df.rename(
        columns={
            "state": "State",
            "county": "County",
            "year": "Year"
        }
    )

    return df

df = load_data()

# -----------------------------
# Indicator mapping
# -----------------------------
indicators = {
    "PM2.5": {
        "county": "PM25",
        "state": "PM25_state_avg",
        "national": "PM25_national_avg"
    },
    "Traffic Proximity": {
        "county": "PTRAF",
        "state": "PTRAF_state_avg",
        "national": "PTRAF_national_avg"
    },
    "Wastewater": {
        "county": "PWDIS",
        "state": "PWDIS_state_avg",
        "national": "PWDIS_national_avg"
    },
    "Diesel PM": {
        "county": "DSLPM",
        "state": "DSLPM_state_avg",
        "national": "DSLPM_national_avg"
    },
    "Respiratory Hazard": {
        "county": "RESP",
        "state": "RESP_state_avg",
        "national": "RESP_national_avg"
    },
    "Ozone": {
        "county": "OZONE",
        "state": "OZONE_state_avg",
        "national": "OZONE_national_avg"
    }
}

# -----------------------------
# Safety check
# -----------------------------
required_columns = ["State", "County", "Year"]

for indicator, cols in indicators.items():
    required_columns.extend([cols["county"], cols["state"], cols["national"]])

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("The app is missing some required columns.")
    st.write("Missing columns:")
    st.write(missing_columns)
    st.write("Columns found in your CSV:")
    st.write(list(df.columns))
    st.stop()

# -----------------------------
# Convert numbers
# -----------------------------
for indicator, cols in indicators.items():
    df[cols["county"]] = pd.to_numeric(df[cols["county"]], errors="coerce")
    df[cols["state"]] = pd.to_numeric(df[cols["state"]], errors="coerce")
    df[cols["national"]] = pd.to_numeric(df[cols["national"]], errors="coerce")

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

# -----------------------------
# Helper functions
# -----------------------------
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
# Card styling
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
        min-height: 125px;
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
# Filter county data
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
# Metric cards
# -----------------------------
indicator_names = list(indicators.keys())

for row_start in range(0, len(indicator_names), 3):
    cols = st.columns(3)

    for col_index, indicator in enumerate(indicator_names[row_start:row_start + 3]):
        county_col = indicators[indicator]["county"]
        national_col = indicators[indicator]["national"]

        county_value = latest_county[county_col]
        national_value = latest_county[national_col]

        health_label, health_icon, health_color = get_health_label(
            county_value,
            national_value
        )

        if pd.isna(county_value):
            value_display = "No data"
        else:
            value_display = f"{county_value:.3f}"

        with cols[col_index]:
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
selected_indicator = st.selectbox("Indicator", indicator_names)

county_col = indicators[selected_indicator]["county"]
state_col = indicators[selected_indicator]["state"]
national_col = indicators[selected_indicator]["national"]

# -----------------------------
# Latest-year comparison message
# -----------------------------
county_latest_value = latest_county[county_col]
state_latest_avg = latest_county[state_col]
national_latest_avg = latest_county[national_col]

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
county_trend = county_df[["Year", county_col]].copy()
county_trend["Series"] = "County"
county_trend = county_trend.rename(columns={county_col: "Value"})

state_trend = county_df[["Year", state_col]].copy()
state_trend["Series"] = "State Average"
state_trend = state_trend.rename(columns={state_col: "Value"})

national_trend = county_df[["Year", national_col]].copy()
national_trend["Series"] = "National Average"
national_trend = national_trend.rename(columns={national_col: "Value"})

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
    The health label compares the county's latest-year value to the national average.

    | Label | Meaning |
    |---|---|
    | 🟢 Healthy | County value is more than 10% below the national average |
    | 🟡 Moderate | County value is within 10% of the national average |
    | 🔴 Unhealthy | County value is more than 10% above the national average |

    Since these are pollution indicators, lower values are generally better.
    """
)
