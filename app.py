import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

GOLD_PATH      = Path("data/gold")
ANALYTICS_PATH = Path("data/analytics")

st.set_page_config(
    page_title="Hevy Workout Analytics",
    page_icon="🏋️",
    layout="wide",
)

# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    required = [
        "workout_summary.parquet",
        "weekly_volume.parquet",
        "exercise_progression.parquet",
        "muscle_group_summary.parquet",
    ]
    missing = [f for f in required if not (GOLD_PATH / f).exists()]
    if missing:
        return None, missing

    workout_summary      = pd.read_parquet(GOLD_PATH / "workout_summary.parquet")
    weekly_volume        = pd.read_parquet(GOLD_PATH / "weekly_volume.parquet")
    exercise_progression = pd.read_parquet(GOLD_PATH / "exercise_progression.parquet")
    muscle_group_summary = pd.read_parquet(GOLD_PATH / "muscle_group_summary.parquet")

    workout_summary["workout_date"]      = pd.to_datetime(workout_summary["workout_date"])
    weekly_volume["week_start"]          = pd.to_datetime(weekly_volume["week_start"])
    exercise_progression["workout_date"] = pd.to_datetime(exercise_progression["workout_date"])

    # Analytics (optional — only if pipeline has been run with analytics layer)
    analytics = {}
    analytics_files = ["exercise_stats", "personal_records", "volume_trend", "consistency"]
    if all((ANALYTICS_PATH / f"{f}.parquet").exists() for f in analytics_files):
        analytics["exercise_stats"]   = pd.read_parquet(ANALYTICS_PATH / "exercise_stats.parquet")
        analytics["personal_records"] = pd.read_parquet(ANALYTICS_PATH / "personal_records.parquet")
        analytics["volume_trend"]     = pd.read_parquet(ANALYTICS_PATH / "volume_trend.parquet")
        analytics["consistency"]      = pd.read_parquet(ANALYTICS_PATH / "consistency.parquet")
        analytics["personal_records"]["workout_date"] = pd.to_datetime(analytics["personal_records"]["workout_date"])
        analytics["exercise_stats"]["first_date"]     = pd.to_datetime(analytics["exercise_stats"]["first_date"])
        analytics["exercise_stats"]["last_date"]      = pd.to_datetime(analytics["exercise_stats"]["last_date"])

    return {
        "workout_summary":      workout_summary,
        "weekly_volume":        weekly_volume,
        "exercise_progression": exercise_progression,
        "muscle_group_summary": muscle_group_summary,
        "analytics":            analytics,
    }, []


data, missing_files = load_data()

# ── Pipeline not yet run ──────────────────────────────────────────────────────

if data is None:
    st.title("🏋️ Hevy Workout Analytics")
    st.error("Gold layer data not found. Run the pipeline first:")
    st.code("python main.py", language="bash")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────

st.sidebar.title("Filters")

max_date = data["workout_summary"]["workout_date"].max()
min_date = data["workout_summary"]["workout_date"].min()

PERIOD_OPTIONS = {
    "Last 3 months": max_date - pd.DateOffset(months=3),
    "Last 6 months": max_date - pd.DateOffset(months=6),
    "Last year":     max_date - pd.DateOffset(years=1),
    "All time":      min_date,
    "Custom":        None,
}

selected_period = st.sidebar.radio("Period", list(PERIOD_OPTIONS.keys()), index=0)

if selected_period == "Custom":
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )
    start_date = pd.Timestamp(date_range[0]) if len(date_range) == 2 else min_date
    end_date   = pd.Timestamp(date_range[1]) if len(date_range) == 2 else max_date
else:
    start_date = PERIOD_OPTIONS[selected_period]
    end_date   = max_date

# Apply date filter
workout_summary = data["workout_summary"].query("workout_date >= @start_date and workout_date <= @end_date")
weekly_volume = data["weekly_volume"].query("week_start >= @start_date and week_start <= @end_date")
exercise_progression = data["exercise_progression"].query("workout_date >= @start_date and workout_date <= @end_date")
muscle_group_summary = (
    weekly_volume
    .groupby("primary_muscle_group")
    .agg(total_volume_kg=("total_volume_kg", "sum"), total_sets=("total_sets", "sum"))
    .reset_index()
    .sort_values("total_volume_kg", ascending=False)
)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("🏋️ Hevy Workout Analytics")
st.caption(f"Data from {start_date.date()} to {end_date.date()}")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💪 Volume", "📈 Progression", "🔬 Analytics"])

# ── TAB 1: Overview ───────────────────────────────────────────────────────────

with tab1:
    total_workouts = len(workout_summary)
    total_volume = workout_summary["total_volume_kg"].sum()
    avg_duration = workout_summary["workout_duration_minutes"].mean()
    top_muscle = data["muscle_group_summary"].iloc[0]["primary_muscle_group"].title() if not data["muscle_group_summary"].empty else "—"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workouts", total_workouts)
    col2.metric("Total Volume", f"{total_volume:,.0f} kg")
    col3.metric("Avg Duration", f"{avg_duration:.0f} min")
    col4.metric("Top Muscle Group", top_muscle)

    st.divider()

    # Workout frequency per week
    ws = workout_summary.copy()
    ws["week_start"] = ws["workout_date"].dt.to_period("W").apply(lambda p: p.start_time)

    freq = ws.groupby("week_start").size().reset_index(name="workouts")

    fig_freq = px.bar(
        freq,
        x="week_start",
        y="workouts",
        title="Workouts per Week",
        labels={"week_start": "Week", "workouts": "Workouts"},
        color_discrete_sequence=["#636EFA"],
    )
    fig_freq.update_layout(showlegend=False)
    st.plotly_chart(fig_freq, width="stretch")

    # Volume per workout
    fig_vol_workout = px.bar(
        workout_summary.sort_values("workout_date"),
        x="workout_date",
        y="total_volume_kg",
        color="workout_title",
        title="Volume per Workout",
        labels={"workout_date": "Date", "total_volume_kg": "Volume (kg)", "workout_title": "Workout"},
        hover_data=["total_sets", "total_exercises", "workout_duration_minutes"],
    )
    st.plotly_chart(fig_vol_workout, width="stretch")


# ── TAB 2: Volume ─────────────────────────────────────────────────────────────

with tab2:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Weekly volume stacked by muscle group
        fig_weekly = px.bar(
            weekly_volume.sort_values("week_start"),
            x="week_start",
            y="total_volume_kg",
            color="primary_muscle_group",
            title="Weekly Volume by Muscle Group",
            labels={
                "week_start": "Week",
                "total_volume_kg": "Volume (kg)",
                "primary_muscle_group": "Muscle Group",
            },
        )
        st.plotly_chart(fig_weekly, width="stretch")

    with col_right:
        # Muscle distribution radar chart
        RADAR_GROUPS = {
            "Back":      ["upper_back", "lats", "traps"],
            "Chest":     ["chest"],
            "Core":      ["abdominals"],
            "Arms":      ["biceps", "triceps", "forearms"],
            "Shoulders": ["shoulders"],
            "Legs":      ["quadriceps", "hamstrings", "glutes", "calves", "adductors", "abductors"],
        }

        radar_values = {}
        for category, muscles in RADAR_GROUPS.items():
            vol = muscle_group_summary[
                muscle_group_summary["primary_muscle_group"].isin(muscles)
            ]["total_volume_kg"].sum()
            radar_values[category] = vol

        radar_df = pd.DataFrame(list(radar_values.items()), columns=["category", "volume"])
        categories = radar_df["category"].tolist()
        values = radar_df["volume"].tolist()
        # Close the polygon
        categories += [categories[0]]
        values += [values[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.25)",
            line=dict(color="#636EFA", width=2),
            name="Volume (kg)",
        ))
        fig_radar.update_layout(
            title="Muscle Distribution",
            polar=dict(
                radialaxis=dict(visible=True, showticklabels=False, gridcolor="rgba(255,255,255,0.1)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_radar, width="stretch")

    # Muscle group summary table
    st.subheader("Muscle Group Summary")
    display_df = muscle_group_summary.copy()
    display_df.columns = ["Muscle Group", "Total Volume (kg)", "Total Sets"]
    display_df["Muscle Group"] = display_df["Muscle Group"].str.title()
    st.dataframe(display_df, width="stretch", hide_index=True)


# ── TAB 3: Progression ────────────────────────────────────────────────────────

with tab3:
    exercises = sorted(exercise_progression["exercise_title"].unique())

    if not exercises:
        st.info("No exercise data available for the selected period.")
    else:
        selected_exercise = st.selectbox("Select exercise", exercises)

        ex_df = exercise_progression[
            exercise_progression["exercise_title"] == selected_exercise
        ].sort_values("workout_date")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Max Weight", f"{ex_df['max_weight_kg'].max():.1f} kg")
        col_b.metric("Total Sets", int(ex_df["total_sets"].sum()))
        col_c.metric("Sessions", len(ex_df))

        # Max weight progression
        fig_prog = go.Figure()

        fig_prog.add_trace(go.Scatter(
            x=ex_df["workout_date"],
            y=ex_df["max_weight_kg"],
            mode="lines+markers",
            name="Max Weight (kg)",
            line=dict(color="#636EFA", width=2),
            marker=dict(size=8),
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Max: %{y} kg<extra></extra>",
        ))

        fig_prog.update_layout(
            title=f"{selected_exercise} — Weight Progression",
            xaxis_title="Date",
            yaxis_title="Weight (kg)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_prog, width="stretch")

        # Session volume — area chart
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(
            x=ex_df["workout_date"],
            y=ex_df["total_volume_kg"],
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0, 204, 150, 0.15)",
            line=dict(color="#00CC96", width=2),
            marker=dict(size=7),
            customdata=ex_df[["total_sets", "total_reps"]].values,
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b><br>"
                "Volume: %{y:.0f} kg<br>"
                "Sets: %{customdata[0]}<br>"
                "Reps: %{customdata[1]}<extra></extra>"
            ),
        ))
        fig_vol.update_layout(
            title=f"{selected_exercise} — Session Volume",
            xaxis_title="Date",
            yaxis_title="Volume (kg)",
            hovermode="x unified",
        )
        st.plotly_chart(fig_vol, width="stretch")


# ── TAB 4: Analytics ──────────────────────────────────────────────────────────

with tab4:
    analytics = data.get("analytics", {})

    if not analytics:
        st.info("Analytics data not found. Re-run the pipeline to generate it:")
        st.code("python main.py", language="bash")
        st.stop()

    # ── KPIs ─────────────────────────────────────────────────────────────────
    consistency = analytics["consistency"].iloc[0]
    volume_trend = analytics["volume_trend"].iloc[0] if not analytics["volume_trend"].empty else None

    TREND_ICON = {"increasing": "📈", "decreasing": "📉", "stable": "➡️",
                  "improving": "📈", "declining": "📉"}

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Consistency Score",
        f"{consistency['consistency_score']:.0f} / 100",
        help="100 = perfectly regular. Based on coefficient of variation of weekly workout frequency.",
    )
    col2.metric("Avg Workouts / Week", f"{consistency['avg_workouts_per_week']:.1f}")
    col3.metric("Longest Streak", f"{consistency['longest_streak_weeks']} weeks")

    if volume_trend is not None:
        trend_icon = TREND_ICON.get(volume_trend["trend"], "➡️")
        col4.metric(
            "Volume Trend",
            f"{trend_icon} {volume_trend['trend'].title()}",
            delta=f"{volume_trend['slope_kg_per_week']:+.0f} kg/week"
            if volume_trend["is_significant"] else "not significant",
        )

    st.divider()

    # ── Volume trend regression ───────────────────────────────────────────────
    if volume_trend is not None:
        st.subheader("📉 Weekly Volume Trend")

        weekly_total = (
            weekly_volume
            .groupby("week_start")["total_volume_kg"]
            .sum()
            .reset_index()
            .sort_values("week_start")
        )

        # Regression line
        x_days = (weekly_total["week_start"] - weekly_total["week_start"].min()).dt.days
        slope_day = volume_trend["slope_kg_per_week"] / 7
        intercept = weekly_total["total_volume_kg"].mean() - slope_day * x_days.mean()
        weekly_total["trend_line"] = slope_day * x_days + intercept

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=weekly_total["week_start"], y=weekly_total["total_volume_kg"],
            mode="lines", name="Weekly Volume",
            line=dict(color="#636EFA", width=1.5), opacity=0.6,
        ))
        fig_trend.add_trace(go.Scatter(
            x=weekly_total["week_start"], y=weekly_total["trend_line"],
            mode="lines", name="Trend (OLS)",
            line=dict(color="#EF553B", width=2, dash="dash"),
        ))
        sig_label = "significant (p < 0.05)" if volume_trend["is_significant"] else "not significant"
        fig_trend.update_layout(
            title=f"Volume Trend — {volume_trend['slope_kg_per_week']:+.1f} kg/week "
                  f"| R²={volume_trend['r_squared']} | {sig_label}",
            xaxis_title="Week", yaxis_title="Volume (kg)", hovermode="x unified",
        )
        st.plotly_chart(fig_trend, width="stretch")

    st.divider()

    # ── Exercise progression stats ────────────────────────────────────────────
    st.subheader("💪 Exercise Progression — Linear Regression")

    ex_stats = analytics["exercise_stats"].copy()

    col_filter1, col_filter2 = st.columns(2)
    only_significant = col_filter1.toggle("Only statistically significant (p < 0.05)", value=True)
    min_sessions = col_filter2.slider("Min sessions", min_value=3, max_value=20, value=5)

    if only_significant:
        ex_stats = ex_stats[ex_stats["is_significant"]]
    ex_stats = ex_stats[ex_stats["sessions"] >= min_sessions]

    if ex_stats.empty:
        st.info("No exercises match the current filters.")
    else:
        # Slope bar chart
        fig_slope = px.bar(
            ex_stats.sort_values("slope_kg_per_week"),
            x="slope_kg_per_week",
            y="exercise_title",
            orientation="h",
            color="trend",
            color_discrete_map={"improving": "#00CC96", "declining": "#EF553B", "stable": "#636EFA"},
            title="Rate of Strength Gain (kg/week)",
            labels={"slope_kg_per_week": "kg / week", "exercise_title": "Exercise", "trend": "Trend"},
            hover_data=["sessions", "r_squared", "p_value", "total_gain_kg"],
        )
        fig_slope.update_layout(height=max(400, len(ex_stats) * 30))
        st.plotly_chart(fig_slope, width="stretch")

        # Detailed table
        with st.expander("Show full table"):
            display_stats = ex_stats[[
                "exercise_title", "trend", "slope_kg_per_week",
                "total_gain_kg", "r_squared", "p_value", "sessions",
            ]].copy()
            display_stats.columns = [
                "Exercise", "Trend", "kg/week", "Total Gain (kg)", "R²", "p-value", "Sessions"
            ]

            def color_trend(val):
                colors = {"improving": "color: #00CC96", "declining": "color: #EF553B", "stable": "color: gray"}
                return colors.get(val, "")

            st.dataframe(
                display_stats.style.map(color_trend, subset=["Trend"]),
                width="stretch",
                hide_index=True,
            )

    st.divider()

    # ── Personal Records ──────────────────────────────────────────────────────
    st.subheader("🏆 Personal Records Timeline")

    prs = analytics["personal_records"].copy()
    prs = prs[prs["workout_date"] >= start_date]

    pr_exercises = ["All"] + sorted(prs["exercise_title"].unique().tolist())
    selected_pr_ex = st.selectbox("Filter by exercise", pr_exercises, key="pr_filter")

    if selected_pr_ex != "All":
        prs = prs[prs["exercise_title"] == selected_pr_ex]

    fig_prs = px.scatter(
        prs.sort_values("workout_date"),
        x="workout_date",
        y="weight_kg",
        color="exercise_title",
        size="weight_kg",
        title="Personal Records Over Time",
        labels={"workout_date": "Date", "weight_kg": "Weight (kg)", "exercise_title": "Exercise"},
        hover_data=["exercise_title", "weight_kg"],
    )
    fig_prs.update_traces(marker=dict(opacity=0.8))
    fig_prs.update_layout(showlegend=selected_pr_ex == "All")
    st.plotly_chart(fig_prs, width="stretch")
