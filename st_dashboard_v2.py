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
    st.markdown("- **Recommendations:** summarizes the key business takeaways and operational next steps")

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
        Ridership rises and falls broadly alongside temperature across the year, indicating that demand pressure is strongly seasonal. Citi Bike should expect the
        greatest supply strain during warmer months, while winter brings a clear drop in overall usage.
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
            Demand is highly uneven across the Citi Bike network. In this sample, the top 50% of start stations account for about 90% of trips, indicating that most 
            ridership is concentrated in a smaller, higher-volume share of stations.
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
            This map compares higher-volume and lower-volume start stations across the network.
            The higher-volume half appears more concentrated in Citi Bike’s core service area,
            while lower-volume stations are more dispersed across the broader coverage area.
            Together, these patterns suggest that supply and inventory management may be a more
            immediate operational priority than broad station expansion. At the same time, some
            higher-volume stations near the edges of current coverage may point to targeted
            expansion opportunities in the future.
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
            This map highlights the 20 busiest start stations, with point size reflecting
            trip volume. It helps identify the specific locations most likely to require
            closer monitoring for bike availability, faster rebalancing, and stronger
            supply planning during periods of peak demand.
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
            This ranking makes it easier to compare the busiest start stations directly and identify which locations may deserve the highest priority for monitoring, 
            rebalancing, and bike availability planning.
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
        This map highlights the strongest trip corridors in the Citi Bike network.
        It is filtered to show only the highest-volume route activity so that the
        most concentrated patterns are easier to see.
        """
    )

    map_path = PROJECT_ROOT / "outputs" / "cbsd_kepler_trips_top100_configured.html"

    with open(map_path, "r", encoding="utf-8") as f:
        map_html = f.read()

    map_path = f"""
        <div style="width: 100%; min-width: 100%;">
          {cbsd_kepler_trips_top100_configured.html}
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

    components.html(map_html, height=900, scrolling=True)

    st.markdown("### Key takeaway")
    st.markdown(
        """
        The heaviest trip activity is concentrated in a relatively small number of
        Manhattan-centered corridors rather than being spread evenly across the full
        network. This supports the broader finding that Citi Bike demand is geographically
        concentrated, which suggests supply pressure may be better addressed through
        targeted rebalancing and station-level planning in the busiest areas.
        """
    )

    st.markdown("### Why this matters")
    st.markdown(
        """
        The station rankings page shows where demand is highest at the station level,
        while this map adds geographic context by showing how those trips cluster into
        core travel corridors. Together, these views suggest that expanding or
        redistributing supply should focus first on the areas where demand is most
        consistently concentrated.
        """
    )

# -----------------------------
# Final Recommendations page
# -----------------------------

elif page == "Recommendations":
    st.header("Conclusion and recommendations")

    st.markdown(
        """
        The analysis suggests that Citi Bike demand is not evenly distributed across
        the network. Ridership appears to be shaped by seasonality, station-level
        differences in demand, and a stronger concentration of higher-volume stations
        within the core service area.
        """
    )

    st.markdown("### Recommendations")

    st.markdown(
        """
        **1. Focus operations on the higher-volume half of the station network**  
        The top 50% of start stations account for about 90% of sampled trips, which
        suggests that most ridership is flowing through a smaller, higher-volume half
        of the station network. Citi Bike should prioritize these stations for bike
        availability monitoring, rebalancing, and operational attention.
        """
    )

    st.markdown(
        """
        **2. Increase rebalancing and bike availability during warmer months**  
        Ridership generally rises alongside temperature, which suggests that supply
        pressure is more likely during spring, summer, and early fall. Seasonal
        planning should reflect this by increasing bike availability and rebalancing
        activity during higher-demand periods.
        """
    )

    st.markdown(
        """
        **3. Prioritize supply and inventory management before broad station expansion**  
        The network appears to have broad geographic coverage already, but demand is
        not equally intense across that coverage. This suggests that improving bike
        availability at higher-volume stations is likely to create more immediate
        operational value than adding large numbers of new stations across the network.
        """
    )

    st.markdown(
        """
        **4. Use edge-of-network high performers as signals for future expansion**  
        While broad expansion does not appear to be the first priority, some
        higher-volume stations near the edges of current coverage may point to areas
        where targeted expansion could make sense in the future.
        """
    )

    st.markdown("### Limitation")
    st.markdown(
        """
        One important limitation of this analysis is that it uses trip and demand
        patterns, but does not include direct data on how many bikes were stocked at
        each station at a given time. That means the dashboard helps identify likely
        pressure points, but cannot directly measure stockouts or the exact size of
        supply gaps.
        """
    )

    st.markdown("### Overall takeaway")
    st.markdown(
        """
        Overall, the findings support a targeted operating strategy: concentrate
        rebalancing and bike availability efforts on higher-volume stations, plan
        for stronger demand during warmer months, and treat station expansion as a
        selective future lever rather than the first solution.
        """
    )
    recommendations_image = Image.open("CitiBike2.jpg")
    st.image(recommendations_image)