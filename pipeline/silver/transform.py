import logging
import pandas as pd

logger = logging.getLogger(__name__)


def transform_workouts(workouts: list) -> pd.DataFrame:
    """Flatten raw workouts into one row per set."""
    rows = []

    for workout in workouts:
        workout_id = workout.get("id")
        workout_title = workout.get("title")

        start_time = pd.to_datetime(workout.get("start_time"), utc=True)
        end_time = pd.to_datetime(workout.get("end_time"), utc=True)
        duration_minutes = (
            round((end_time - start_time).total_seconds() / 60, 1)
            if start_time and end_time
            else None
        )

        for exercise in workout.get("exercises", []):
            for s in exercise.get("sets", []):
                weight_kg = s.get("weight_kg")
                reps = s.get("reps")

                rows.append({
                    "workout_id": workout_id,
                    "workout_title": workout_title,
                    "workout_date": start_time.date() if start_time else None,
                    "workout_duration_minutes": duration_minutes,
                    "exercise_index": exercise.get("index"),
                    "exercise_title": exercise.get("title"),
                    "exercise_template_id": exercise.get("exercise_template_id"),
                    "set_index": s.get("index"),
                    "set_type": s.get("type"),
                    "weight_kg": weight_kg,
                    "reps": reps,
                    "duration_seconds": s.get("duration_seconds"),
                    "volume_kg": round(weight_kg * reps, 2) if weight_kg and reps else None,
                })

    logger.info(f"Transformed {len(workouts)} workouts into {len(rows)} sets")
    return pd.DataFrame(rows)


def transform_exercise_templates(templates: list) -> pd.DataFrame:
    """Normalize exercise templates into a flat table."""
    rows = []

    for t in templates:
        rows.append({
            "id": t.get("id"),
            "title": t.get("title"),
            "type": t.get("type"),
            "primary_muscle_group": t.get("primary_muscle_group"),
            "secondary_muscle_groups": ", ".join(t.get("secondary_muscle_groups") or []),
            "equipment": t.get("equipment"),
            "is_custom": t.get("is_custom"),
        })

    logger.info(f"Transformed {len(rows)} exercise templates")
    return pd.DataFrame(rows)


def run(bronze_data: dict) -> dict:
    workouts_df = transform_workouts(bronze_data.get("workouts", []))
    templates_df = transform_exercise_templates(bronze_data.get("exercise_templates", []))

    return {
        "workouts": workouts_df,
        "exercise_templates": templates_df,
    }
