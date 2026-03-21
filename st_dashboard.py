import streamlit as st
import pandas as pd
from pathlib import Path
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit.components.v1 as components


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Citi Bike Strategy Dashboard", layout="wide")

st.title("Citi Bike Strategy Dashboard")
st.markdown(
    """
This dashboard summarizes Citi Bike ridership patterns in 2022 and explores how demand changes with weather.
Use the charts to identify high-demand stations, seasonal ridership shifts, and where trips concentrate geographically.
"""
)

# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

# -----------------------------
# Load app-ready data
# -----------------------------
daily_path = DATA_DIR / "cbsd_daily_dashboard_2022_01.csv"
dash_daily = pd.read_csv(daily_path, parse_dates=["date"])

# st.write("Preview of dashboard-ready daily dataset:")
# st.dataframe(dash_daily.head(10))

# -----------------------------
# Plotly bar chart: Top 20 start stations
# -----------------------------

# Load top 20 start station data
top20_path = PROJECT_ROOT / "data" / "top20_start_stations_2022_02.csv"
top20 = pd.read_csv(top20_path)

# Build and display the chart
st.header("Top 20 Start Stations 2022")

fig_bar = go.Figure(
    go.Bar(
        x=top20["start_station_name"],
        y=top20["value"],
        marker={"color": top20["value"], "colorscale": "Blues"},
    )
)

fig_bar.update_layout(
    title="Top 20 Most Popular Start Stations",
    xaxis_title="Start station",
    yaxis_title="Trips",
    height=550,
)

# Rotate labels for readability
fig_bar.update_xaxes(tickangle=45)

st.plotly_chart(fig_bar, width='stretch')

# -----------------------------
# Plotly dual-axis line chart: Trips vs Temperature
# -----------------------------
st.header("Trips vs Temperature (Daily)")

fig_line = make_subplots(specs=[[{"secondary_y": True}]])

# Trace 1: trips (primary y-axis)
fig_line.add_trace(
    go.Scatter(
        x=dash_daily["date"],
        y=dash_daily["bike_rides_daily"],
        name="Daily bike rides",
        mode="lines",
    ),
    secondary_y=False,
)

# Trace 2: temperature (secondary y-axis)
fig_line.add_trace(
    go.Scatter(
        x=dash_daily["date"],
        y=dash_daily["tavg_c"],
        name="Avg daily temp (C)",
        mode="lines",
    ),
    secondary_y=True,
)

# Layout + axis labels
fig_line.update_layout(
    title="Daily Trips vs Temperature",
    height=600,
    margin=dict(l=40, r=40, t=80, b=40),
)

fig_line.update_yaxes(title_text="Trips", secondary_y=False)
fig_line.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

st.plotly_chart(fig_line, use_container_width=True)

# -----------------------------
# Kepler.gl map (HTML embed)
# -----------------------------
st.header("Aggregated Bike Trips Map")

map_path = PROJECT_ROOT / "outputs" / "cbsd_kepler_trips_2.html"

with open(map_path, "r", encoding="utf-8") as f:
    map_html = f.read()

components.html(map_html, height=900, scrolling=True)