import logging
import pandas as pd

logger = logging.getLogger(__name__)


def aggregate_workout_summary(workouts_df: pd.DataFrame) -> pd.DataFrame:
    """One row per workout: total volume, sets and exercises (warmups excluded)."""
    working_sets = workouts_df[workouts_df["set_type"] != "warmup"]

    summary = (
        working_sets
        .groupby(["workout_id", "workout_title", "workout_date", "workout_duration_minutes"])
        .agg(
            total_volume_kg=("volume_kg", "sum"),
            total_sets=("set_index", "count"),
            total_exercises=("exercise_title", "nunique"),
        )
        .reset_index()
        .sort_values("workout_date", ascending=False)
    )

    summary["total_volume_kg"] = summary["total_volume_kg"].round(2)
    logger.info(f"Aggregated {len(summary)} workout summaries")
    return summary


def aggregate_weekly_volume(workouts_df: pd.DataFrame, templates_df: pd.DataFrame) -> pd.DataFrame:
    """Total volume per ISO week per primary muscle group (warmups excluded)."""
    df = workouts_df.merge(
        templates_df[["id", "primary_muscle_group"]],
        left_on="exercise_template_id",
        right_on="id",
        how="left",
    )

    df["workout_date"] = pd.to_datetime(df["workout_date"])
    df["week_start"] = df["workout_date"].dt.to_period("W").apply(lambda p: p.start_time.date())

    working_sets = df[df["set_type"] != "warmup"]

    weekly = (
        working_sets
        .groupby(["week_start", "primary_muscle_group"])
        .agg(
            total_volume_kg=("volume_kg", "sum"),
            total_sets=("set_index", "count"),
        )
        .reset_index()
        .sort_values(["week_start", "primary_muscle_group"])
    )

    logger.info(f"Aggregated weekly volume: {len(weekly)} rows")
    return weekly


def aggregate_exercise_progression(workouts_df: pd.DataFrame) -> pd.DataFrame:
    """Max weight and total volume per exercise per date (warmups excluded)."""
    working_sets = workouts_df[
        (workouts_df["set_type"] != "warmup") &
        workouts_df["weight_kg"].notna() &
        workouts_df["reps"].notna()
    ]

    progression = (
        working_sets
        .groupby(["workout_date", "exercise_title", "exercise_template_id"])
        .agg(
            max_weight_kg=("weight_kg", "max"),
            total_volume_kg=("volume_kg", "sum"),
            total_sets=("set_index", "count"),
            total_reps=("reps", "sum"),
        )
        .reset_index()
        .sort_values(["exercise_title", "workout_date"])
    )

    logger.info(f"Aggregated exercise progression: {len(progression)} rows")
    return progression


def aggregate_muscle_group_summary(workouts_df: pd.DataFrame, templates_df: pd.DataFrame) -> pd.DataFrame:
    """Total volume, sets and workouts per primary muscle group (warmups excluded)."""
    df = workouts_df.merge(
        templates_df[["id", "primary_muscle_group"]],
        left_on="exercise_template_id",
        right_on="id",
        how="left",
    )

    working_sets = df[df["set_type"] != "warmup"]

    summary = (
        working_sets
        .groupby("primary_muscle_group")
        .agg(
            total_volume_kg=("volume_kg", "sum"),
            total_sets=("set_index", "count"),
            total_workouts=("workout_id", "nunique"),
        )
        .reset_index()
        .sort_values("total_volume_kg", ascending=False)
    )

    summary["total_volume_kg"] = summary["total_volume_kg"].round(2)
    logger.info(f"Aggregated muscle group summary: {len(summary)} groups")
    return summary


def run(silver_data: dict) -> dict:
    workouts_df = silver_data["workouts"]
    templates_df = silver_data["exercise_templates"]

    return {
        "workout_summary": aggregate_workout_summary(workouts_df),
        "weekly_volume": aggregate_weekly_volume(workouts_df, templates_df),
        "exercise_progression": aggregate_exercise_progression(workouts_df),
        "muscle_group_summary": aggregate_muscle_group_summary(workouts_df, templates_df),
    }
