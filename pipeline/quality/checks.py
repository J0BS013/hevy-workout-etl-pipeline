import logging
import pandas as pd

logger = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Raised when a data quality check fails."""


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise DataQualityError(message)


# ── Bronze ────────────────────────────────────────────────────────────────────

def check_bronze(data: dict) -> None:
    for key, records in data.items():
        _assert(isinstance(records, list), f"Bronze: '{key}' must be a list")
        _assert(len(records) > 0, f"Bronze: '{key}' returned 0 records from the API")

    logger.info(
        f"Bronze quality OK — "
        f"workouts: {len(data['workouts'])} | "
        f"templates: {len(data['exercise_templates'])}"
    )


# ── Silver ────────────────────────────────────────────────────────────────────

def check_silver(silver_data: dict) -> None:
    workouts: pd.DataFrame  = silver_data["workouts"]
    templates: pd.DataFrame = silver_data["exercise_templates"]

    # Required columns exist
    required_workout_cols = {
        "workout_id", "workout_title", "workout_date",
        "exercise_title", "set_type", "weight_kg", "reps", "volume_kg",
    }
    missing = required_workout_cols - set(workouts.columns)
    _assert(not missing, f"Silver workouts missing columns: {missing}")

    # No null identifiers
    null_ids = workouts["workout_id"].isna().sum()
    _assert(null_ids == 0, f"Silver: {null_ids} rows with null workout_id")

    null_dates = workouts["workout_date"].isna().sum()
    _assert(null_dates == 0, f"Silver: {null_dates} rows with null workout_date")

    # Weights and reps must be non-negative where present
    neg_weights = (workouts["weight_kg"].dropna() < 0).sum()
    _assert(neg_weights == 0, f"Silver: {neg_weights} rows with negative weight_kg")

    neg_reps = (workouts["reps"].dropna() < 0).sum()
    _assert(neg_reps == 0, f"Silver: {neg_reps} rows with negative reps")

    neg_volume = (workouts["volume_kg"].dropna() < 0).sum()
    _assert(neg_volume == 0, f"Silver: {neg_volume} rows with negative volume_kg")

    # Exercise templates must have unique IDs
    dupes = templates["id"].duplicated().sum()
    _assert(dupes == 0, f"Silver: {dupes} duplicate exercise template IDs")

    logger.info(
        f"Silver quality OK — "
        f"{len(workouts)} sets | {len(templates)} templates | "
        f"{workouts['workout_id'].nunique()} workouts"
    )


# ── Gold ──────────────────────────────────────────────────────────────────────

def check_gold(gold_data: dict) -> None:
    for name, df in gold_data.items():
        _assert(not df.empty, f"Gold: '{name}' table is empty")

    summary = gold_data["workout_summary"]

    neg_vol = (summary["total_volume_kg"] < 0).sum()
    _assert(neg_vol == 0, f"Gold: {neg_vol} workouts with negative total_volume_kg")

    neg_sets = (summary["total_sets"] < 0).sum()
    _assert(neg_sets == 0, f"Gold: {neg_sets} workouts with negative total_sets")

    logger.info(
        f"Gold quality OK — "
        f"workout_summary: {len(summary)} rows | "
        f"weekly_volume: {len(gold_data['weekly_volume'])} rows | "
        f"exercise_progression: {len(gold_data['exercise_progression'])} rows"
    )
