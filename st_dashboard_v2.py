import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from PIL import Image

# -----------------------------
# Project paths
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# -----------------------------
# Load app-ready data
# -----------------------------
daily_path = DATA_DIR / "cbsd_daily_dashboard_2022_01.csv"
dash_daily = pd.read_csv(daily_path, parse_dates=["date"])

stations_sample_path = DATA_DIR / "cbsd_station_trips_sample.csv"
stations_df = pd.read_csv(stations_sample_path)

# -----------------------------
# Page setup
# -----------------------------

# dashboard page navigation
st.set_page_config(layout="wide")
page = st.sidebar.selectbox(
    "Select an aspect of the analysis",
    [
        "Intro page",
        "Weather and seasonal demand",
        "Most popular start stations",
        "High-volume trip corridors",
        "Recommendations",
    ],
)


# -----------------------------
# Intro Page
# -----------------------------

if page == "Intro page":
    st.title("Citi Bike Strategy Dashboard")

    st.markdown(
        """
        This dashboard was built to identify where Citi Bike may be experiencing supply pressure and what patterns appear to be driving that demand.
        """
    )

    st.markdown(
        """
        The analysis focuses on ridership over time, weather conditions, station usage, and trip corridors to highlight where bike availability and operational
        planning may need to be more targeted.
        """
    )

    st.markdown("- **Weather and seasonal demand:** shows how ridership changes over time and alongside temperature")
    st.markdown("- **Most popular stations:** highlights how demand is concentrated across start stations and where supply pressure may be greatest")
    st.markdown("- **High-volume trip corridors:** maps the 100 most repeated aggregated routes to show where movement is most concentrated")
    st.markdown("- **Recommendations:** summarizes the main operational takeaways and areas for follow-up analysis")

    intro_image = Image.open("CitiBike1.jpg")
    st.image(intro_image)

# -----------------------------
# "Weather and seasonal demand" page
# -----------------------------

elif page == "Weather and seasonal demand":
    st.header("Weather and seasonal demand")

    st.markdown(
        """
        This view compares daily ridership with average daily temperature to show how seasonal weather patterns align with Citi Bike demand.
        """
    )

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

    st.plotly_chart(fig_line, width="stretch")

    st.markdown(
        """
        Ridership rises and falls broadly alongside temperature across the year, which suggests that Citi Bike demand is strongly seasonal. Usage is highest during warmer months 
        and noticeably lower during winter, which may have implications for bike availability, rebalancing, and seasonal operations planning.
        """
    )

# -----------------------------
# "Most Popular Start Stations" page
# -----------------------------

elif page == "Most popular start stations":
    st.header("Most popular start stations")

    season_options = sorted(stations_df["season"].dropna().unique())

    season_filter = st.sidebar.multiselect(
        "Select season(s)",
        options=season_options,
        default=season_options,
    )

    stations_filtered = stations_df[
        stations_df["season"].isin(season_filter)
    ].copy()

    if stations_filtered.empty:
        st.warning("Please select at least one season.")
    else:
        total_trips = int(len(stations_filtered))

        station_counts_all = (
            stations_filtered["start_station_name"]
            .dropna()
            .value_counts()
            .reset_index()
        )
        station_counts_all.columns = ["start_station_name", "trip_count"]

        total_stations = len(station_counts_all)
        top_50pct_station_count = max(1, int(np.ceil(total_stations * 0.50)))

        top_50pct_stations = station_counts_all.head(top_50pct_station_count).copy()
        top_50pct_trip_share = top_50pct_stations["trip_count"].sum() / total_trips

        top20_station_counts = station_counts_all.head(20).copy()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Unique start stations",
                value=f"{total_stations:,}"
            )

        with col2:
            st.metric(
                label="Stations in top 50%",
                value=f"{top_50pct_station_count:,}"
            )

        with col3:
            st.metric(
                label="Trips from top 50% of stations",
                value=f"{top_50pct_trip_share:.1%}"
            )

        st.markdown(
            """
            Demand is clearly uneven across the Citi Bike network. The top 50% of start stations account for about 90% of trips, 
            which suggests that some parts of the network are seeing much heavier demand than others.
            """
        )

        st.markdown("### Higher-volume vs lower-volume station distribution")

        stations_map_path = OUTPUTS_DIR / "cbsd_kepler_stations_configured.html"

        with open(stations_map_path, "r", encoding="utf-8") as f:
            stations_map_html = f.read()

        stations_embed = f"""
        <div style="width: 100%; min-width: 100%;">
          {stations_map_html}
        </div>
        <script>
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 300);
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 1000);
        </script>
        """
        st.caption("Map colors compare higher-volume and lower-volume stations. Hover for station name and trip count.")
        
        components.html(stations_embed, height=900, scrolling=True)

        st.markdown(
            """
            This map shows a clear geographic pattern in station usage. The higher-volume half of stations is located mostly in Manhattan, 
            then Brooklyn, with only a few in Queens and very few in the Bronx. Most of the lower-volume half sits outside Manhattan. 
            The bulk of higher-volume station activity shown here is in Manhattan rather than evenly distributed across the network. 
            This view shows where activity is concentrated, but not why, so it is most useful here as a guide to where closer operational attention may be needed.
            """
        )

        st.markdown("### Top 20 start stations by trip volume")

        top20_map_path = OUTPUTS_DIR / "cbsd_kepler_top20_configured.html"

        with open(top20_map_path, "r", encoding="utf-8") as f:
            top20_map_html = f.read()

        top20_embed = f"""
        <div style="width: 100%; min-width: 100%;">
          {top20_map_html}
        </div>
        <script>
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 300);
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 1000);
        </script>
        """
        
        st.caption("Point size reflects trip volume among the top 20 start stations.")
        
        components.html(top20_embed, height=850, scrolling=True)

        st.markdown(
            """
            This map highlights the 20 busiest start stations, with point size reflecting trip volume. It helps identify the specific locations 
            most likely to require closer monitoring for bike availability, faster rebalancing, and stronger supply planning during peak demand periods.
            """
        )

        fig_bar = px.bar(
            top20_station_counts,
            x="start_station_name",
            y="trip_count",
            title="Top 20 start stations in selected season(s)",
            labels={
                "start_station_name": "Start station",
                "trip_count": "Number of trips",
            },
        )

        fig_bar.update_layout(
            height=650,
            xaxis_tickangle=-45,
        )

        st.plotly_chart(fig_bar, width="stretch")

        st.markdown(
            """
            This ranking provides a closer look at the busiest start stations in the selected season(s). It helps compare how the top stations 
            shift across the year and which locations remain consistently important candidates for closer monitoring, faster rebalancing, 
            and stronger bike availability planning.
            """
        )

        st.caption(
            "Note: KPI and bar chart summaries are based on the dashboard sample, while embedded maps were exported separately for geographic visualization."
        )

# -----------------------------
# High-volume trip corridors
# -----------------------------

elif page == "High-volume trip corridors":
    st.header("High-volume trip corridors")

    st.markdown(
        """
        This map highlights the most repeated aggregated trip corridors in the Citi Bike network. It is filtered to focus on the 
        highest-volume route activity so that the most concentrated movement patterns are easier to see.
        """
    )

    top_trips_map_path = OUTPUTS_DIR / "cbsd_kepler_trips_top100_configured.html"

    with open(top_trips_map_path, "r", encoding="utf-8") as f:
        top_trips_map_html = f.read()

    top_trips_embed = f"""
        <div style="width: 100%; min-width: 100%;">
          {top_trips_map_html}
        </div>
        <script>
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 300);
          setTimeout(function() {{
            window.dispatchEvent(new Event('resize'));
          }}, 1000);
        </script>
        """

    components.html(top_trips_embed, height=900, scrolling=True)

    st.markdown("### Key takeaway")
    st.markdown(
        """
        The strongest trip activity appears in a relatively small number of repeated corridors, many of them in and around Manhattan. 
        This reinforces the broader finding that usage is not spread evenly across the network.
        """
    )

    st.markdown("### Why this matters")
    st.markdown(
        """
        This page adds geographic context to the station-level findings by showing where repeated travel patterns are strongest. 
        It also suggests that strong trip corridors are shaped by more than just waterfront proximity. While some high-volume routes 
        do appear near the water, the broader network already includes many waterfront stations, so future expansion decisions would 
        likely require more location-specific analysis around population density, commuting patterns, tourism activity, transit access, 
        and land use.
        """
    )

# -----------------------------
# Final Recommendations page
# -----------------------------

elif page == "Recommendations":
    st.header("Conclusion and recommendations")

    st.markdown(
        """
        The analysis suggests that Citi Bike demand is not evenly distributed across the network. Ridership appears to be shaped by 
        seasonality, station-level differences in demand, and a clear geographic pattern in where higher-volume stations and repeated 
        trip corridors appear.
        """
    )
    
    st.markdown(
        """
        **1. Focus operations on the higher-volume half of the station network**  
        The top 50% of start stations account for about 90% of trips, which suggests that some parts of the network require much closer 
        operational attention than others. Citi Bike should prioritize these stations for bike availability monitoring, rebalancing, 
        and day-to-day operational planning.
        """
    )
    
    st.markdown(
        """
        **2. Increase rebalancing and bike availability during warmer months**  
        Ridership rises during warmer parts of the year and drops during winter, which suggests that supply pressure is seasonal rather 
        than constant. Citi Bike may benefit from planning more aggressively for bike availability during peak-demand months and using 
        lower-demand periods for maintenance and servicing.
        """
    )
    
    st.markdown(
        """
        **3. Prioritize supply and inventory management before broad station expansion**  
        The network already covers a broad area, but demand is much stronger in some parts of the system than others. That suggests Citi Bike 
        may get more immediate value from improving bike availability at higher-volume stations than from adding large numbers of new stations 
        across the network.
        """
    )
    
    st.markdown(
        """
        **4. Use stronger-performing edge stations as signals for future follow-up analysis**  
        Broad expansion does not appear to be the first priority based on this dashboard alone. Still, some higher-volume stations near 
        the edges of current coverage may point to areas worth studying more closely for future targeted expansion.
        """
    )
    
    st.markdown(
        """
        **Limitation**  
        This dashboard helps identify likely demand pressure points, but it does not include direct bike inventory or stockout data. 
        That means it can highlight where service pressure is most likely, but it cannot directly confirm where bikes were unavailable in real time.
        """
    )
    
    st.markdown(
        """
        Overall, the findings support a focused operating strategy: concentrate rebalancing and bike availability efforts on the busiest 
        stations, plan for stronger demand during warmer months, and treat expansion as a selective future lever rather than the first solution.
        """
    )
    recommendations_image = Image.open("CitiBike2.jpg")
    st.image(recommendations_image)