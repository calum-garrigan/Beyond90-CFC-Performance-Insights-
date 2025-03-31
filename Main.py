import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Player Performance Dashboard", layout="wide")

# --- Logo and Title ---
col1, col2 = st.columns([1, 8])  # Adjust proportions as needed
with col1:
    st.image("Chelsea_Logo_Final.png", width=300)  # Make sure this file is in the same folder
with col2:
    st.title("Player Performance Dashboard")
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
        sorted_phys = phys_df.sort_values(by='testDate')
        fig = px.line(sorted_phys, x='testDate', y='benchmarkPct', color=view_by,
                      title=f"Benchmark % Over Time by {view_by.capitalize()}")
        fig.update_layout(xaxis_title="Date")
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
        pivot = recovery_df.drop_duplicates(subset=['sessionDate', 'category'])
        pivot = pivot.pivot(index="sessionDate", columns="category", values="value")
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
            st.error(f"⚠️ Emboss Baseline Score (Overall Recovery): {latest_score:.2f}")
            st.markdown("**Current Status:** You may be fatigued. Prioritize rest or lighter training.")
        elif latest_score > 0.3:
            st.success(f"🟢 Emboss Baseline Score (Overall Recovery): {latest_score:.2f}")
            st.markdown("**Current Status:** You're well recovered. Ready to go!")
        else:
            st.info(f"✅ Emboss Baseline Score (Overall Recovery): {latest_score:.2f}")
            st.markdown("**Current Status:** You're balanced.")

        st.markdown("""
**What it means:**  
The Emboss Baseline Score reflects your overall physiological readiness.  
- ✅ Around `0` means you're balanced.  
- ⚠️ Below `-0.3` suggests fatigue or insufficient recovery.  
- 🟢 Above `+0.3` means you're likely well recovered.  

**Tip:** Combine this with recent sleep and workload data to guide your next session's intensity.
""")

# ---------------- PRIORITY GOALS ----------------
with tab4:
    st.header("🎯 Individual Priority Areas")
    for _, row in priority_df.iterrows():
        with st.expander(f"{row['Category']} – {row['Area']}"):
            st.markdown(f"**🎯 Target:** {row['Target']}")
            st.markdown(f"**📅 Set:** {format_safe_date(row['Target set'])} | **Review:** {format_safe_date(row['Review Date'])}")
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
    top_game = gps_df[gps_df['opposition_full'].notna()].sort_values(by='distance', ascending=False).iloc[0]
    st.info(f"Your highest match load this season was vs. {top_game['opposition_full']} ({top_game['distance']:.0f}m)")

    avg_sleep = recovery_df[recovery_df['category'] == 'sleep_duration']
    if not avg_sleep.empty:
        recent_sleep = avg_sleep.sort_values('sessionDate').tail(7)['value'].mean()
        if recent_sleep < 6.5:
            st.warning("📍 Sleep dropped below 6.5 hrs last week — plan for extra recovery!")

    st.markdown("### 📆 Latest Data Dates")
    gps_latest = gps_df['date'].max()
    phys_latest = phys_df['testDate'].max()
    recovery_latest = recovery_df['sessionDate'].max()

    st.markdown(f"- GPS: `{format_safe_date(gps_latest)}`")
    st.markdown(f"- Physical Test: `{format_safe_date(phys_latest)}`")
    st.markdown(f"- Recovery: `{format_safe_date(recovery_latest)}`")

# ---------------- MATCH SUMMARY ----------------
with tab6:
    st.header("📅 Match Summary")
    match_df = gps_df[gps_df['opposition_full'].notna()].sort_values(by='date')

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

# ---------------- PERFORMANCE RANK FLOW ----------------
with st.container():
    st.markdown("## 🔄 Rank Flow Overview (Your Best Performances by Match)")

    rank_metrics = {
        "Total Distance": "distance",
        "Peak Speed": "peak_speed",
        "High-Speed Distance": "distance_over_27",
        "Session Duration": "day_duration"
    }

    selected_metrics = st.multiselect(
        "Select metrics to visualize ranking across matches:",
        options=list(rank_metrics.keys()),
        default=["Total Distance", "Peak Speed"]
    )

    if selected_metrics:
        rank_df = gps_df[['date', 'opposition_full'] + [rank_metrics[m] for m in selected_metrics]].copy()
        rank_df = rank_df.dropna()

        # Sort by date for consistent order
        rank_df = rank_df.sort_values('date')
        rank_df['match'] = rank_df['date'].dt.strftime('%d %b %Y') + ' vs ' + rank_df['opposition_full']

        # Calculate ranks
        for metric_name in selected_metrics:
            col = rank_metrics[metric_name]
            rank_df[f'{col}_rank'] = rank_df[col].rank(method='min', ascending=False)

        melted = pd.melt(
            rank_df,
            id_vars=['match'],
            value_vars=[f"{rank_metrics[m]}_rank" for m in selected_metrics],
            var_name="Metric",
            value_name="Rank"
        )
        # Clean up metric names
        metric_map = {f"{rank_metrics[m]}_rank": m for m in selected_metrics}
        melted["Metric"] = melted["Metric"].map(metric_map)

        fig = px.line(
            melted,
            x="match",
            y="Rank",
            color="Metric",
            markers=True,
            title="📈 Performance Rank by Match"
        )
        fig.update_yaxes(autorange="reversed", title="Rank (1 = Best)")
        fig.update_layout(xaxis_title="Match", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least one metric to view rank progression.")

