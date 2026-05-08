import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Deadly Data Lookup", layout="wide")

# -----------------------------
# Basic styling
# -----------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.metric-card {
    background-color: #111827;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-bottom: 12px;
}
.metric-label {
    font-size: 14px;
    color: #9ca3af;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 34px;
    font-weight: 700;
    color: white;
}
.badge-red {
    display: inline-block;
    background: #7f1d1d;
    color: #fecaca;
    padding: 8px 14px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
}
.badge-blue {
    display: inline-block;
    background: #1e3a8a;
    color: #bfdbfe;
    padding: 8px 14px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 14px;
}
.info-card {
    background-color: #0f172a;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-top: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Load data
# -----------------------------
df = pd.read_csv("county_year_panel.csv")
summary = pd.read_csv("county_summary.csv")

df["county_fips"] = df["county_fips"].astype(str).str.zfill(5)
summary["county_fips"] = summary["county_fips"].astype(str).str.zfill(5)

numeric_cols = [
    "PM25", "PM25_state_avg", "PM25_national_avg",
    "DSLPM", "DSLPM_state_avg", "DSLPM_national_avg",
    "PTRAF", "PTRAF_state_avg", "PTRAF_national_avg",
    "RESP", "RESP_state_avg", "RESP_national_avg",
    "PWDIS", "PWDIS_state_avg", "PWDIS_national_avg",
    "OZONE", "OZONE_state_avg", "OZONE_national_avg",
    "year"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

for col in ["before_avg", "present_avg", "abs_change", "pct_change"]:
    if col in summary.columns:
        summary[col] = pd.to_numeric(summary[col], errors="coerce")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("Search")
states = sorted(df["state"].dropna().unique())
selected_state = st.sidebar.selectbox("State", states)

df_state = df[df["state"] == selected_state].copy()
counties = sorted(df_state["county"].dropna().unique())
selected_county = st.sidebar.selectbox("County", counties)

county_df = df_state[df_state["county"] == selected_county].copy()
county_summary = summary[
    (summary["state"] == selected_state) & (summary["county"] == selected_county)
].copy()

# -----------------------------
# Title
# -----------------------------
st.title("Deadly Data: County Pollution Lookup")
st.caption("Explore how pollution burden changed across counties over time, with state and national comparisons.")

st.subheader(f"{selected_county}, {selected_state}")

# -----------------------------
# Group badge
# -----------------------------
if not county_df.empty:
    group_val = county_df["group"].iloc[0]
    if group_val == "DC-heavy":
        st.markdown('<span class="badge-red">DC-heavy county</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-blue">Non-DC county</span>', unsafe_allow_html=True)

# -----------------------------
# Latest values
# -----------------------------
latest_year = county_df["year"].max()
latest = county_df[county_df["year"] == latest_year].copy()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">PM2.5</div>
        <div class="metric-value">{latest["PM25"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">Diesel PM</div>
        <div class="metric-value">{latest["DSLPM"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">Traffic Proximity</div>
        <div class="metric-value">{latest["PTRAF"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">Respiratory Hazard</div>
        <div class="metric-value">{latest["RESP"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">Wastewater</div>
        <div class="metric-value">{latest["PWDIS"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="metric-card">
        <div class="metric-label">Ozone</div>
        <div class="metric-value">{latest["OZONE"].iloc[0]:.3f}</div>
    </div>
    ''', unsafe_allow_html=True)

# -----------------------------
# Indicator selection
# -----------------------------
indicator_map = {
    "PM2.5": ("PM25", "PM25_state_avg", "PM25_national_avg"),
    "Diesel PM": ("DSLPM", "DSLPM_state_avg", "DSLPM_national_avg"),
    "Traffic Proximity": ("PTRAF", "PTRAF_state_avg", "PTRAF_national_avg"),
    "Respiratory Hazard": ("RESP", "RESP_state_avg", "RESP_national_avg"),
    "Wastewater": ("PWDIS", "PWDIS_state_avg", "PWDIS_national_avg"),
    "Ozone": ("OZONE", "OZONE_state_avg", "OZONE_national_avg")
}

indicator_label = st.selectbox("Indicator", list(indicator_map.keys()))
county_col, state_col, national_col = indicator_map[indicator_label]

latest_county = latest[county_col].iloc[0]
latest_state = latest[state_col].iloc[0]
latest_national = latest[national_col].iloc[0]

state_relation = "above" if latest_county > latest_state else "below" if latest_county < latest_state else "equal to"
national_relation = "above" if latest_county > latest_national else "below" if latest_county < latest_national else "equal to"

st.markdown(
    f'''
    <div class="info-card">
    <b>Latest-year comparison:</b> {indicator_label} in <b>{selected_county}</b> is
    <b>{state_relation}</b> the state average and <b>{national_relation}</b> the national average.
    </div>
    ''',
    unsafe_allow_html=True
)

# -----------------------------
# Trend chart
# -----------------------------
plot_df = county_df[["year", county_col, state_col, national_col]].copy()
plot_df = plot_df.rename(columns={
    county_col: "County",
    state_col: "State Average",
    national_col: "National Average"
})

plot_long = plot_df.melt(
    id_vars="year",
    value_vars=["County", "State Average", "National Average"],
    var_name="Series",
    value_name="Value"
)

fig = px.line(
    plot_long.sort_values("year"),
    x="year",
    y="Value",
    color="Series",
    markers=True,
    title=f"{indicator_label}: {selected_county} vs State vs National"
)

fig.update_layout(
    legend_title_text="Series",
    xaxis_title="Year",
    yaxis_title="Value"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Summary section
# -----------------------------
st.markdown("## Summary")

show_summary = county_summary[county_summary["indicator"] == county_col]
if not show_summary.empty:
    row = show_summary.iloc[0]

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Before Average", f"{row['before_avg']:.3f}")
    with s2:
        st.metric("Present Average", f"{row['present_avg']:.3f}")
    with s3:
        st.metric("Percent Change", f"{row['pct_change']:.2f}%")

    direction = row["direction"]
    if direction == "Improved":
        st.success(
            f"{indicator_label} improved in {selected_county}. "
            f"It moved from {row['before_avg']:.3f} to {row['present_avg']:.3f}."
        )
    elif direction == "Worsened":
        st.error(
            f"{indicator_label} worsened in {selected_county}. "
            f"It moved from {row['before_avg']:.3f} to {row['present_avg']:.3f}."
        )
    else:
        st.info(f"{indicator_label} showed little or no change in {selected_county}.")

    comparison_df = pd.DataFrame({
        "Measure": ["Before Average", "Present Average", "Absolute Change", "Percent Change", "Direction"],
        "Value": [
            round(row["before_avg"], 3),
            round(row["present_avg"], 3),
            round(row["abs_change"], 3),
            f"{row['pct_change']:.2f}%",
            row["direction"]
        ]
    })

    st.markdown("### Before vs Present")
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# -----------------------------
# Raw data
# -----------------------------
st.markdown("## Raw county-year data")
st.dataframe(county_df, use_container_width=True)
