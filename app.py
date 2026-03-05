import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from urllib.request import urlopen

st.set_page_config(page_title="County Swing Analysis", layout="wide")


@st.cache_data
def load_county_data():
    return pd.read_csv(
        "data/processed/county_swing_dataset.csv",
        dtype={"FIPS": str, "state_fips": str},
    )


@st.cache_data
def load_fixed_effects():
    return pd.read_csv("data/processed/fixed_effects.csv")


@st.cache_data
def load_state_re():
    return pd.read_csv("data/processed/state_random_effects.csv", dtype={"state_fips": str})


@st.cache_data
def load_model_comparison():
    return pd.read_csv("data/processed/model_comparison.csv")


@st.cache_data
def load_interaction_preds():
    return pd.read_csv("data/processed/interaction_predictions.csv")


@st.cache_data
def load_geojson():
    with urlopen(
        "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    ) as resp:
        return json.load(resp)


# --- Load data ---
df = load_county_data()
df_main = df[~df["is_alaska"]].copy()
fe = load_fixed_effects()
state_re = load_state_re()
comp = load_model_comparison()
preds = load_interaction_preds()

# --- Panel 1: Overview ---
st.title("US County-Level Partisan Swing, 2020-2024")
st.markdown(
    """
What county-level demographic and economic conditions predicted the 2020-to-2024
partisan swing? This dashboard presents results from a multilevel model of 3,100+
counties nested within 50 states and DC.
"""
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Mean County Swing", f"+{df_main["swing"].mean()*100:.1f} pp", "toward R")
with col2:
    st.metric("ICC (State-Level Variance)", "30.5%", "of total swing variance")
with col3:
    hispanic_coef = fe.loc[fe["term"] == "pct_hispanic", "estimate"].values[0]
    st.metric("Hispanic Share", f"+{hispanic_coef*10:.2f} pp", "per 10pp Hispanic")
with col4:
    college_coef = fe.loc[fe["term"] == "college_c", "estimate"].values[0]
    st.metric("College Share", f"{college_coef*10:.2f} pp", "per 10pp college")

st.markdown("---")

# --- Panel 2: Caterpillar plot ---
st.subheader("State Random Intercepts")
st.markdown(
    "Each dot shows how much a state's counties swung more (right) or less (left) "
    "than the national model predicts, after controlling for demographics. "
    "States on the right had a stronger-than-expected rightward shift."
)

state_sorted = state_re.sort_values("intercept_re")
fig_cat = go.Figure()
fig_cat.add_trace(go.Scatter(
    x=state_sorted["intercept_re"] * 100,
    y=state_sorted["state_name"],
    mode="markers",
    marker=dict(size=7, color=state_sorted["intercept_re"], colorscale="RdBu_r", cmid=0),
    hovertemplate="%{y}: %{x:.2f} pp<extra></extra>",
))
fig_cat.add_vline(x=0, line_dash="dash", line_color="gray")
fig_cat.update_layout(
    height=900,
    xaxis_title="Random intercept (percentage points)",
    yaxis_title="",
    margin=dict(l=150),
)
st.plotly_chart(fig_cat, width="stretch")

st.markdown("---")

# --- Panel 3: Interaction plot ---
st.subheader("Education Effect by State Economic Conditions")
st.markdown(
    "Does the education-swing relationship depend on state-level unemployment change? "
    "The three lines show the predicted swing at different levels of state unemployment change. "
    "The interaction is not statistically significant (p = 0.48), so the lines are nearly parallel."
)

fig_int = go.Figure()
colors = {"Mean": "#2c3e50", "+1 SD": "#c0392b", "-1 SD": "#2980b9"}
for label in ["Mean", "+1 SD", "-1 SD"]:
    subset = preds[preds["unemp_level"] == label]
    fig_int.add_trace(go.Scatter(
        x=subset["college_pct"],
        y=subset["predicted_swing"] * 100,
        mode="lines",
        name=f"State unemp change: {label}",
        line=dict(color=colors[label], width=2),
    ))

fig_int.update_layout(
    xaxis_title="% with bachelor's degree or higher",
    yaxis_title="Predicted swing (pp, + = more Republican)",
    height=500,
)
st.plotly_chart(fig_int, width="stretch")

st.markdown("---")

# --- Panel 4: Choropleth map ---
st.subheader("County-Level Swing Map")
st.markdown(
    "Red counties swung toward Republicans; blue counties swung toward Democrats. "
    "The map excludes Alaska due to its different county-equivalent reporting structure."
)

counties_geo = load_geojson()

fig_map = px.choropleth(
    df_main,
    geojson=counties_geo,
    locations="FIPS",
    color="swing",
    color_continuous_scale="RdBu_r",
    color_continuous_midpoint=0,
    range_color=[-0.10, 0.10],
    scope="usa",
    hover_name="NAME",
    hover_data={"swing": ":.3f", "FIPS": False},
    labels={"swing": "Swing (R share change)"},
)
fig_map.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=500,
    geo=dict(lakecolor="rgb(255,255,255)"),
)
st.plotly_chart(fig_map, width="stretch")

st.markdown("---")

# --- Panel 5: Exploratory scatter ---
st.subheader("Explore: Demographics vs. Swing")

predictor_options = {
    "% College Educated": "pct_college",
    "% Hispanic": "pct_hispanic",
    "% Black": "pct_black",
    "% White Non-Hispanic": "pct_white_nh",
    "Median Household Income": "median_hh_income",
    "Log Population Density": "log_pop_density",
    "Republican Share 2020": "rep_share_2020",
    "Median Age": "median_age",
}

selected_label = st.selectbox("Select predictor:", list(predictor_options.keys()))
selected_col = predictor_options[selected_label]

plot_df = df_main.dropna(subset=[selected_col, "swing"]).copy()

# Multiply percentage columns for display
display_col = selected_col
if selected_col.startswith("pct_") or selected_col == "rep_share_2020":
    plot_df[f"{selected_col}_pct"] = plot_df[selected_col] * 100
    display_col = f"{selected_col}_pct"
    x_label = f"{selected_label} (%)"
else:
    x_label = selected_label

fig_scatter = px.scatter(
    plot_df,
    x=display_col,
    y="swing",
    hover_name="NAME",
    opacity=0.3,
    trendline="ols",
    labels={display_col: x_label, "swing": "Swing (R share change)"},
)
fig_scatter.update_traces(marker=dict(size=4))
fig_scatter.update_layout(height=500)
st.plotly_chart(fig_scatter, width="stretch")

# Correlation
r = plot_df[selected_col].corr(plot_df["swing"])
st.caption(f"Pearson r = {r:.3f} (n = {len(plot_df):,})")
