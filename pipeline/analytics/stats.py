import logging
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def compute_exercise_progression(exercise_progression: pd.DataFrame) -> pd.DataFrame:
    """
    Linear regression of max weight over time per exercise.
    Only includes exercises with >= 3 sessions.
    Outputs slope (kg/week), R², p-value, trend direction.
    """
    results = []

    exercise_progression = exercise_progression.copy()
    exercise_progression["workout_date"] = pd.to_datetime(exercise_progression["workout_date"])

    for exercise, group in exercise_progression.groupby("exercise_title"):
        group = group.sort_values("workout_date").dropna(subset=["max_weight_kg"])

        if len(group) < 3:
            continue

        x = (group["workout_date"] - group["workout_date"].min()).dt.days.values.astype(float)
        y = group["max_weight_kg"].values.astype(float)

        slope, _, r_value, p_value, _ = stats.linregress(x, y)
        slope_per_week = slope * 7

        if p_value < 0.05:
            trend = "improving" if slope_per_week > 0 else "declining"
        else:
            trend = "stable"

        results.append({
            "exercise_title":       exercise,
            "sessions":             len(group),
            "first_date":           group["workout_date"].min(),
            "last_date":            group["workout_date"].max(),
            "first_max_weight_kg":  round(group["max_weight_kg"].iloc[0], 1),
            "last_max_weight_kg":   round(group["max_weight_kg"].iloc[-1], 1),
            "total_gain_kg":        round(group["max_weight_kg"].iloc[-1] - group["max_weight_kg"].iloc[0], 1),
            "slope_kg_per_week":    round(slope_per_week, 3),
            "r_squared":            round(r_value ** 2, 3),
            "p_value":              round(p_value, 4),
            "is_significant":       p_value < 0.05,
            "trend":                trend,
        })

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results).sort_values("slope_kg_per_week", ascending=False)
    logger.info(f"Computed progression stats for {len(df)} exercises")
    return df


def compute_personal_records(exercise_progression: pd.DataFrame) -> pd.DataFrame:
    """
    Identify every session where a new personal record (max weight) was set.
    """
    records = []

    exercise_progression = exercise_progression.copy()
    exercise_progression["workout_date"] = pd.to_datetime(exercise_progression["workout_date"])

    for exercise, group in exercise_progression.groupby("exercise_title"):
        group = group.sort_values("workout_date").dropna(subset=["max_weight_kg"])

        running_max = -np.inf
        for _, row in group.iterrows():
            if row["max_weight_kg"] > running_max:
                running_max = row["max_weight_kg"]
                records.append({
                    "exercise_title": exercise,
                    "workout_date":   row["workout_date"],
                    "weight_kg":      row["max_weight_kg"],
                })

    df = pd.DataFrame(records).sort_values(["exercise_title", "workout_date"])
    logger.info(f"Found {len(df)} personal records across all exercises")
    return df


def compute_volume_trend(weekly_volume: pd.DataFrame) -> pd.DataFrame:
    """
    Linear regression on total weekly volume over time.
    Returns a single-row summary with trend stats.
    """
    weekly_volume = weekly_volume.copy()
    weekly_volume["week_start"] = pd.to_datetime(weekly_volume["week_start"])

    weekly_total = (
        weekly_volume
        .groupby("week_start")["total_volume_kg"]
        .sum()
        .reset_index()
        .sort_values("week_start")
    )

    if len(weekly_total) < 3:
        return pd.DataFrame()

    x = (weekly_total["week_start"] - weekly_total["week_start"].min()).dt.days.values.astype(float)
    y = weekly_total["total_volume_kg"].values.astype(float)

    slope, _, r_value, p_value, _ = stats.linregress(x, y)
    slope_per_week = slope * 7

    if p_value < 0.05:
        trend = "increasing" if slope_per_week > 0 else "decreasing"
    else:
        trend = "stable"

    return pd.DataFrame([{
        "slope_kg_per_week":     round(slope_per_week, 2),
        "r_squared":             round(r_value ** 2, 3),
        "p_value":               round(p_value, 4),
        "is_significant":        p_value < 0.05,
        "trend":                 trend,
        "avg_weekly_volume_kg":  round(float(y.mean()), 2),
        "weeks_analyzed":        len(weekly_total),
    }])


def compute_consistency(workout_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Consistency metrics: avg workouts/week, coefficient of variation, longest streak.
    """
    ws = workout_summary.copy()
    ws["workout_date"] = pd.to_datetime(ws["workout_date"])
    ws["week_start"] = ws["workout_date"].dt.to_period("W").apply(lambda p: p.start_time)

    workouts_per_week = ws.groupby("week_start").size()
    mean_wk = workouts_per_week.mean()
    cv = workouts_per_week.std() / mean_wk if mean_wk > 0 else 0

    # Longest consecutive-week streak
    all_weeks = pd.date_range(
        start=ws["week_start"].min(),
        end=ws["week_start"].max(),
        freq="W-MON",
    )
    active_weeks = set(ws["week_start"].dt.date)

    max_streak = streak = 0
    for week in all_weeks:
        if week.date() in active_weeks:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    return pd.DataFrame([{
        "avg_workouts_per_week":  round(mean_wk, 2),
        "std_workouts_per_week":  round(workouts_per_week.std(), 2),
        "consistency_cv":         round(float(cv), 3),
        "consistency_score":      round(max(0.0, (1 - float(cv)) * 100), 1),
        "longest_streak_weeks":   max_streak,
        "total_active_weeks":     len(workouts_per_week),
        "total_weeks_period":     len(all_weeks),
    }])


def run(gold_data: dict) -> dict:
    exercise_progression = gold_data["exercise_progression"]
    weekly_volume        = gold_data["weekly_volume"]
    workout_summary      = gold_data["workout_summary"]

    return {
        "exercise_stats":   compute_exercise_progression(exercise_progression),
        "personal_records": compute_personal_records(exercise_progression),
        "volume_trend":     compute_volume_trend(weekly_volume),
        "consistency":      compute_consistency(workout_summary),
    }
