import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Player Performance Dashboard", layout="wide")

# Add logo and title
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg", width=60)
with col_title:
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

    hr_cols = ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms']
    for col in hr_cols:
        if col in gps_df.columns:
            gps_df[col] = pd.to_timedelta(gps_df[col], errors='coerce').dt.total_seconds() / 60

    return gps_df, phys_df, recovery_df, priority_df

gps_df, phys_df, recovery_df, priority_df = load_data()
recovery_df['value'] = recovery_df['value'].where(pd.notnull(recovery_df['value']), None)

def format_safe_date(val):
    try:
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except:
        return "Invalid or missing date"

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
    filtered = gps_df[gps_df['season'] == season].sort_values(by='date')

    with st.expander("📏 Distance Metrics"):
        fig = px.line(filtered, x='date', y=['distance', 'distance_over_21', 'distance_over_24', 'distance_over_27'],
                      title="Distance Over Time", labels={"value": "Distance (m)"})
        fig.update_layout(xaxis_title="Date")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("⚡ Acceleration & Deceleration"):
        fig2 = px.line(filtered, x='date', y=['accel_decel_over_2_5', 'accel_decel_over_3_5', 'accel_decel_over_4_5'],
                       title="Accel/Decel Events")
        fig2.update_layout(xaxis_title="Date")
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🚀 Peak Speed & Session Time"):
        fig3 = px.line(filtered, x='date', y='peak_speed', title="Peak Speed Over Time (km/h)")
        fig3.update_layout(xaxis_title="Date")
        fig4 = px.bar(filtered, x='date', y='day_duration', title="Session Duration (Minutes)")
        fig4.update_layout(xaxis_title="Date")
        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)

    with st.expander("❤️ Heart Rate Zones"):
        hr_cols = [col for col in ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms'] if col in filtered.columns]
        if hr_cols:
            fig5 = px.area(filtered, x='date', y=hr_cols, title="Heart Rate Zones (mins)")
            fig5.update_layout(xaxis_title="Date")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.warning("Heart rate zone columns are missing from the dataset.")

# ---------------- PHYSICAL CAPABILITY ----------------
with tab2:
    st.header("🏋️ Physical Capability Metrics")
    subtab1, subtab2 = st.tabs(["📈 Trends Over Time", "🧭 Radar Overview"])

    with subtab1:
        view_by = st.selectbox("Group Benchmark % by:", ["movement", "quality", "expression"])
        fig = px.line(phys_df, x='testDate', y='benchmarkPct', color=view_by,
                      title=f"Benchmark % Over Time by {view_by.capitalize()}")
        fig.update_layout(xaxis_title="Test Date")
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
        pivot = recovery_df.groupby(['sessionDate', 'category'])['value'].mean().unstack()
        pivot = pivot.sort_index()
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
        if latest_score < -0.3:
            color = "#FFA500"  # orange
            emoji = "⚠️"
            status_text = "Fatigue or insufficient recovery likely."
        elif latest_score > 0.3:
            color = "#00C851"  # green
            emoji = "🟢"
            status_text = "You're well recovered."
        else:
            color = "#33B5E5"  # blue
            emoji = "✅"
            status_text = "You're balanced."

        st.markdown(f"<h4 style='color:{color}'>{emoji} Emboss Baseline Score (Overall Recovery): {latest_score:.2f}</h4>", unsafe_allow_html=True)
        st.markdown(f"""
**What it means:**  
The Emboss Baseline Score reflects your overall physiological readiness.  
- ✅ Around `0` means you're balanced.  
- ⚠️ Below `-0.3` suggests fatigue or insufficient recovery.  
- 🟢 Above `+0.3` means you're likely well recovered.  

**Current Status:** {status_text}  

**Tip:** Combine this with recent sleep and workload data to guide your next session's intensity.
""")
