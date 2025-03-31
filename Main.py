import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Player Performance Dashboard", layout="wide")

st.title("🏟️ Player Performance Dashboard")
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
    return gps_df, phys_df, recovery_df, priority_df

# Convert HR columns to minutes
for col in ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms']:
    gps_df[col] = pd.to_timedelta(gps_df[col]).dt.total_seconds() / 60

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
        hr_cols = ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms']
        fig5 = px.area(filtered, x='date', y=hr_cols, stackgroup='one', title="Heart Rate Zones (mins)")
        st.plotly_chart(fig5, use_container_width=True)

# ---------------- PHYSICAL CAPABILITY ----------------
with tab2:
    st.header("🏋️ Physical Capability Metrics")
    subtab1, subtab2 = st.tabs(["📈 Trends Over Time", "🧭 Radar Overview"])

    with subtab1:
        view_by = st.selectbox("Group Benchmark % by:", ["movement", "quality", "expression"])
        fig = px.line(phys_df, x='testDate', y='benchmarkPct', color=view_by,
                      title=f"Benchmark % Over Time by {view_by.capitalize()}")
        st.plotly_chart(fig, use_container_width=True)

    with subtab2:
        latest = phys_df[phys_df['testDate'] == phys_df['testDate'].max()]
        radar_df = latest.groupby('movement')['benchmarkPct'].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_df['benchmarkPct'],
            theta=radar_df['movement'],
            fill='toself',
            name='Movement Profile'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                          title="Radar View – Movement Benchmark %")
        st.plotly_chart(fig, use_container_width=True)

# ---------------- RECOVERY STATUS ----------------
with tab3:
    st.header("😴 Recovery Status")
    subtab1, subtab2 = st.tabs(["📉 Recovery Trends", "📡 Radar Profile"])

    with subtab1:
        recovery_df.dropna(subset=["value"], inplace=True)
        pivot = recovery_df.pivot(index="sessionDate", columns="category", values="value")
        st.line_chart(pivot)

    with subtab2:
        latest = recovery_df[recovery_df['sessionDate'] == recovery_df['sessionDate'].max()]
        radar_df = latest.groupby('category')['value'].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=radar_df['value'],
            theta=radar_df['category'],
            fill='toself',
            name='Recovery Profile'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[-1, 1])),
                          title="Recovery Radar Profile")
        st.plotly_chart(fig, use_container_width=True)

    emboss = recovery_df[recovery_df['category'] == 'total']
    if not emboss.empty:
        latest_score = emboss.sort_values(by='sessionDate')['value'].iloc[-1]
        st.metric("🔵 Emboss Baseline Score (Overall Recovery)", f"{latest_score:.2f}")

# ---------------- PRIORITY GOALS ----------------
with tab4:
    st.header("🎯 Individual Priority Areas")
    for _, row in priority_df.iterrows():
        with st.expander(f"{row['Category']} – {row['Area']}"):
            st.markdown(f"**🎯 Target:** {row['Target']}")
            st.markdown(f"**📅 Set:** {row['Target set'].date()} | **Review:** {row['Review Date'].date()}")
            st.markdown(f"**📌 Type:** {row['Performance Type']}")
            status = row["Tracking"]
            if status == "On Track":
                st.success("✅ On Track")
            elif status == "Achieved":
                st.success("🏁 Goal Achieved")
            else:
                st.warning("⚠️ Needs Review")

# ---------------- PLAYER SUMMARY ----------------
with tab5:
    st.header("📊 Player Snapshot Summary")

    st.markdown("### 🔍 Quick Highlights")
    latest_gps = gps_df.sort_values(by='date').iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Peak Speed (km/h)", f"{latest_gps['peak_speed']:.1f}")
    col2.metric("Total Distance", f"{latest_gps['distance']:.0f} m")
    col3.metric("Session Duration", f"{latest_gps['day_duration']} min")

    st.markdown("### 🧠 Smart Insights")
    top_game = gps_df.sort_values(by='distance', ascending=False).iloc[0]
    st.info(f"Your highest match load this season was vs. {top_game['opposition_full']} ({top_game['distance']:.0f}m)")

    avg_sleep = recovery_df[recovery_df['category'] == 'sleep_duration']
    if not avg_sleep.empty:
        recent_sleep = avg_sleep.sort_values('sessionDate').tail(7)['value'].mean()
        if recent_sleep < 6.5:
            st.warning("📍 Sleep dropped below 6.5 hrs last week — plan for extra recovery!")

    st.markdown("### 📆 Latest Data Dates")
    st.markdown(f"- GPS: `{gps_df['date'].max().date()}`")
    st.markdown(f"- Physical Test: `{phys_df['testDate'].max().date()}`")
    st.markdown(f"- Recovery: `{recovery_df['sessionDate'].max().date()}`")

# ---------------- MATCH SUMMARY ----------------
with tab6:
    st.header("📅 Match Summary")
    match_df = gps_df[gps_df['opposition_full'].notna()]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(match_df, x='opposition_full', y='distance', title="📏 Total Distance by Match", text='distance')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(match_df, x='opposition_full', y='peak_speed', size='distance', color='distance',
                         title="🚀 Peak Speed by Match")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🏃‍♂️ High-Speed Running")
    fig = px.bar(match_df, x='opposition_full', y='distance_over_27',
                 title="High-Speed Running Distance (>27 km/h) by Match")
    st.plotly_chart(fig, use_container_width=True)
