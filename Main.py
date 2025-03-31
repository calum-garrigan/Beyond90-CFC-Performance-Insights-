import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Player Performance Dashboard", layout="wide")

st.title("📊 Player Performance Dashboard")
st.markdown("""
Welcome to your personalized performance dashboard. Use the tabs below to explore how you’ve been training, recovering, and improving. 
Each section provides visual feedback to help you and your support team make the best decisions.
""")

# Load Data
@st.cache_data
def load_data():
    try:
        gps_df = pd.read_csv("CFC GPS Data.csv", parse_dates=["date"], encoding='utf-8')
    except UnicodeDecodeError:
        gps_df = pd.read_csv("CFC GPS Data.csv", parse_dates=["date"], encoding='latin1')
    except FileNotFoundError:
        st.error("❌ 'CFC GPS Data.csv' not found. Please make sure it's in the same directory.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    phys_df = pd.read_csv("CFC Physical Capability Data_.csv", parse_dates=["testDate"])
    recovery_df = pd.read_csv("CFC Recovery status Data.csv", parse_dates=["sessionDate"])
    priority_df = pd.read_csv("CFC Individual Priority Areas.csv", parse_dates=["Target set", "Review Date"])

    # Convert HR columns to minutes safely
    hr_cols = ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms']
    for col in hr_cols:
        if col in gps_df.columns:
            gps_df[col] = pd.to_timedelta(gps_df[col], errors='coerce').dt.total_seconds() / 60

    return gps_df, phys_df, recovery_df, priority_df

gps_df, phys_df, recovery_df, priority_df = load_data()

# Treat nulls as missing data for 'value' in recovery_df
recovery_df['value'] = recovery_df['value'].where(pd.notnull(recovery_df['value']), None)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📍 GPS Metrics",
    "🏋️ Physical Capability",
    "😴 Recovery Status",
    "🎯 Priority Goals",
    "📊 Player Summary",
    "📅 Match Summary"
])

# ---------------- GPS METRICS ----------------
with tab1:
    st.header("📍 GPS Performance Metrics")
    col1, col2 = st.columns(2)
    with col1:
        season = st.selectbox("Filter by Season", gps_df['season'].dropna().unique())
    filtered = gps_df[gps_df['season'] == season]

    with st.expander("📏 Distance Metrics"):
        fig = px.line(filtered, x='date', y=['distance', 'distance_over_21', 'distance_over_24', 'distance_over_27'],
                      title="Distance Over Time", labels={"value": "Distance (m)"})
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("⚡ Acceleration & Deceleration"):
        fig2 = px.line(filtered, x='date', y=['accel_decel_over_2_5', 'accel_decel_over_3_5', 'accel_decel_over_4_5'],
                       title="Accel/Decel Events")
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🚀 Peak Speed & Session Time"):
        fig3 = px.line(filtered, x='date', y='peak_speed', title="Peak Speed Over Time (km/h)")
        fig4 = px.bar(filtered, x='date', y='day_duration', title="Session Duration (Minutes)")
        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)

    with st.expander("❤️ Heart Rate Zones"):
        hr_cols = [col for col in ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms'] if col in filtered.columns]
        if hr_cols:
            fig5 = px.area(filtered, x='date', y=hr_cols, title="Heart Rate Zones (mins)")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.warning("Heart rate zone columns are missing from the dataset.")

# (rest of code remains unchanged)
