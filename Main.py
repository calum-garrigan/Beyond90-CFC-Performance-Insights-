# Paste this code block as a complete working file
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import openai
import os

st.set_page_config(page_title="Player Performance Dashboard", layout="wide")

# --- Logo and Title ---
col1, col2 = st.columns([1, 8])
with col1:
    st.image("Chelsea_Logo_Final.png", width=300)
with col2:
    st.title("Player Performance Dashboard")
    st.markdown("""
    Welcome to your personalized performance dashboard. Use the tabs below to explore how you’ve been training, recovering, and improving.  
    Each section provides visual feedback to help you and your support team make the best decisions.
    """)

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        gps_df = pd.read_csv("CFC GPS Data.csv", parse_dates=["date"], encoding='utf-8')
    except UnicodeDecodeError:
        gps_df = pd.read_csv("CFC GPS Data.csv", parse_dates=["date"], encoding='latin1')
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

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tabs9 = st.tabs([
    "📍 GPS Metrics", "🏋️ Physical Capability", "😴 Recovery Status",
    "🎯 Priority Goals", "📊 Player Summary", "📅 Match Summary", "📐 ACWR Calculator", "Match Comparison", "🤖 Ask the AI"
])

# ---------------- TAB 1: GPS METRICS ----------------
with tab1:
    st.header("📍 GPS Performance Metrics")
    season = st.selectbox("Filter by Season", gps_df['season'].dropna().unique())
    filtered = gps_df[gps_df['season'] == season].sort_values(by='date')

    with st.expander("📏 Distance Metrics"):
        fig = px.line(filtered, x='date', y=['distance', 'distance_over_21', 'distance_over_24', 'distance_over_27'])
        fig.update_layout(title="Distance Over Time", xaxis_title="Date", yaxis_title="Distance (m)")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("⚡ Acceleration & Deceleration"):
        fig = px.line(filtered, x='date', y=['accel_decel_over_2_5', 'accel_decel_over_3_5', 'accel_decel_over_4_5'])
        fig.update_layout(title="Accel/Decel Events", xaxis_title="Date")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("🚀 Peak Speed & Session Time"):
        fig1 = px.line(filtered, x='date', y='peak_speed', title="Peak Speed Over Time (km/h)")
        fig2 = px.bar(filtered, x='date', y='day_duration', title="Session Duration (Minutes)")
        fig1.update_layout(xaxis_title="Date")
        fig2.update_layout(xaxis_title="Date")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("❤️ Heart Rate Zones"):
        hr_cols = [c for c in ['hr_zone_1_hms', 'hr_zone_2_hms', 'hr_zone_3_hms', 'hr_zone_4_hms', 'hr_zone_5_hms'] if c in filtered.columns]
        if hr_cols:
            fig = px.area(filtered, x='date', y=hr_cols, title="Heart Rate Zones (mins)")
            fig.update_layout(xaxis_title="Date")
            st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 2: PHYSICAL CAPABILITY ----------------
with tab2:
    st.header("🏋️ Physical Capability Metrics")
    subtab1, subtab2 = st.tabs(["📈 Trends Over Time", "🧭 Radar Overview"])

    with subtab1:
        view_by = st.selectbox("Group Benchmark % by:", ["movement", "quality", "expression"])
        sorted_phys = phys_df.sort_values(by='testDate')
        fig = px.line(sorted_phys, x='testDate', y='benchmarkPct', color=view_by)
        fig.update_layout(title="Benchmark % Over Time", xaxis_title="Date")
        st.plotly_chart(fig, use_container_width=True)

    with subtab2:
        latest = phys_df[phys_df['testDate'] == phys_df['testDate'].max()]
        radar_df = latest.groupby('movement')['benchmarkPct'].mean().reset_index()
        fig = go.Figure(go.Scatterpolar(
            r=radar_df['benchmarkPct'], theta=radar_df['movement'], fill='toself', name='Movement Profile'
        ))
        fig.update_layout(title="Radar View – Movement Benchmark %", polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)

# ---------------- TAB 3: RECOVERY STATUS ----------------
with tab3:
    st.header("😴 Recovery Status")
    subtab1, subtab2 = st.tabs(["📉 Recovery Trends", "📡 Radar Profile"])

    with subtab1:
        recovery_df.dropna(subset=["value"], inplace=True)
        pivot = recovery_df.drop_duplicates(subset=['sessionDate', 'category'])
        pivot = pivot.pivot(index="sessionDate", columns="category", values="value").sort_index()
        st.line_chart(pivot)

    with subtab2:
        latest = recovery_df[recovery_df['sessionDate'] == recovery_df['sessionDate'].max()]
        radar_df = latest.groupby('category')['value'].mean().reset_index()
        fig = go.Figure(go.Scatterpolar(
            r=radar_df['value'], theta=radar_df['category'], fill='toself'
        ))
        fig.update_layout(title="Recovery Radar Profile", polar=dict(radialaxis=dict(visible=True, range=[-1, 1])))
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

# ---------------- TAB 4: PRIORITY GOALS ----------------
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

# ---------------- TAB 5: PLAYER SUMMARY ----------------
with tab5:
    st.header("📊 Player Snapshot Summary")
    st.markdown("### 🔍 Quick Highlights")

    gps_df_sorted = gps_df.sort_values(by='date')
    latest_gps = gps_df_sorted.iloc[-1]
    latest_gps_match = gps_df_sorted[gps_df_sorted['opposition_full'].notna()].iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Peak Speed (km/h)", f"{latest_gps['peak_speed']:.1f}")
    col2.metric("Total Distance", f"{latest_gps['distance']:.0f} m")
    col3.metric("Session Duration", f"{latest_gps['day_duration']:.1f} min")

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
    

# ---------------- TAB 6: MATCH SUMMARY ----------------
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

# ---------------- ACUTE : CHRONIC WORKLOAD (ACWR) ----------------
with tab7:
    st.header("📐 Acute:Chronic Workload Ratio (ACWR)")
    st.markdown("""
    **ACWR** compares the most recent week's load (acute) with the longer-term average (chronic).
    It's used to monitor injury risk and training spikes.

    Formula:

    `ACWR = Acute Load (7-day sum) / Chronic Load (28-day rolling average)`
    """)

    acwr_metric = st.selectbox("Select Load Metric for ACWR", [
        "distance",
        "distance_over_21",
        "distance_over_24",
        "distance_over_27",
        "accel_decel_over_2_5",
        "accel_decel_over_3_5",
        "accel_decel_over_4_5"
    ], index=3)

    acwr_df = gps_df[['date', acwr_metric]].dropna().sort_values(by='date')
    acwr_df['date'] = pd.to_datetime(acwr_df['date'], errors='coerce')
    acwr_df = acwr_df.dropna(subset=['date'])
    acwr_df.set_index('date', inplace=True)

    acwr_df['acute'] = acwr_df[acwr_metric].rolling(window=7).sum()
    acwr_df['chronic'] = acwr_df[acwr_metric].rolling(window=28).mean()
    acwr_df['ACWR'] = acwr_df['acute'] / acwr_df['chronic']
    acwr_df = acwr_df.dropna().reset_index()

    fig = px.line(acwr_df, x='date', y='ACWR', title=f"ACWR Over Time ({acwr_metric})")
    fig.add_hline(y=0.8, line_dash="dot", line_color="orange", annotation_text="Lower Threshold")
    fig.add_hline(y=1.5, line_dash="dot", line_color="red", annotation_text="Upper Risk Zone")
    fig.update_layout(xaxis_title="Date", yaxis_title="ACWR Ratio")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Guidance:**
    - ✅ **0.8 - 1.3**: Balanced and safe zone
    - ⚠️ **< 0.8**: Undertraining — consider increasing load
    - 🔴 **> 1.5**: Spike risk — potential injury risk from sudden overload

    Always interpret ACWR in context with recovery, sleep, and subjective feedback.
    """)

# ---------------- MATCH COMPARISON TAB ----------------
with tab8:
    st.header("📊 Side-by-Side Match Comparison")
    st.markdown("Compare selected matches for selected metrics.")

    match_df = gps_df[gps_df['opposition_full'].notna()].copy()
    match_df['date'] = pd.to_datetime(match_df['date'], errors='coerce')
    match_df = match_df.dropna(subset=['date'])

    match_df['match_label'] = match_df.apply(lambda row: f"{row['opposition_full']} ({row['date'].strftime('%d/%m/%Y')})", axis=1)

    available_metrics = [
        "peak_speed",
        "distance",
        "distance_over_21",
        "distance_over_24",
        "distance_over_27",
        "accel_decel_over_2_5",
        "accel_decel_over_3_5",
        "accel_decel_over_4_5"
    ]

    match_df = match_df.sort_values(by='date', ascending=False)  # Sort newest to oldest
    match_options = match_df['match_label'].unique().tolist()  # Ensure all unique match entries

    selected_matches = st.multiselect("Select matches to compare:", match_options)
    selected_metrics = st.multiselect("Select metrics to compare:", available_metrics, default=["peak_speed", "distance_over_27"])

    if selected_matches and selected_metrics:
        filtered_df = match_df[match_df['match_label'].isin(selected_matches)][['match_label'] + selected_metrics]
        melted = filtered_df.melt(id_vars='match_label', value_vars=selected_metrics, var_name='Metric', value_name='Value')

        fig = px.bar(melted, x='match_label', y='Value', color='Metric', barmode='group',
                     title="Match Comparison by Selected Metrics")
        fig.update_layout(xaxis_title="Match", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select both matches and metrics to display the comparison.")

# ---------------- AI CHAT TAB ----------------
with tabs9:
    st.header("🤖 Ask the AI")
    st.markdown("Ask anything about your performance data. For example:")
    st.markdown("- How far did I run last week?\n- What was my peak speed in my last game?\n- Am I training too much?")

    user_question = st.text_input("Your question:")
    openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")

    if user_question and openai_api_key:
        # Combine all relevant data
        latest_gps = gps_df.sort_values(by='date', ascending=False).head(5).to_string(index=False)
        latest_phys = phys_df.sort_values(by='testDate', ascending=False).head(5).to_string(index=False)
        latest_recovery = recovery_df.sort_values(by='sessionDate', ascending=False).head(5).to_string(index=False)
        latest_priority = priority_df.sort_values(by='Review Date', ascending=False).head(3).to_string(index=False)

        prompt = f"""
        You are a football performance assistant helping a player understand their performance.
        They asked: \"{user_question}\"

        ---
        GPS Data:
        {latest_gps}

        Physical Capability:
        {latest_phys}

        Recovery:
        {latest_recovery}

        Priority Areas:
        {latest_priority}
        ---

        Respond clearly and helpfully based on the data.
        """

        try:
            openai.api_key = openai_api_key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for interpreting athlete GPS data, physical tests, recovery, and goals."},
                    {"role": "user", "content": prompt},
                ]
            )
            answer = response['choices'][0]['message']['content']
            st.success("AI Response:")
            st.write(answer)

        except Exception as e:
            st.error(f"Error: {e}")
