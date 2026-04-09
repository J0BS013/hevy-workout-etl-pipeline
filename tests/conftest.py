import pytest
import pandas as pd


# ── Raw API payloads (Bronze format) ─────────────────────────────────────────

@pytest.fixture
def raw_workouts():
    return [
        {
            "id": "workout-1",
            "title": "Upper",
            "description": "",
            "start_time": "2024-01-01T10:00:00+00:00",
            "end_time":   "2024-01-01T11:30:00+00:00",
            "exercises": [
                {
                    "index": 0,
                    "title": "Bench Press",
                    "exercise_template_id": "BENCH001",
                    "superset_id": None,
                    "sets": [
                        {"index": 0, "type": "warmup", "weight_kg": 40.0, "reps": 10, "duration_seconds": None},
                        {"index": 1, "type": "normal", "weight_kg": 80.0, "reps": 8,  "duration_seconds": None},
                        {"index": 2, "type": "failure","weight_kg": 80.0, "reps": 7,  "duration_seconds": None},
                    ],
                }
            ],
        },
        {
            "id": "workout-2",
            "title": "Lower",
            "description": "",
            "start_time": "2024-01-03T10:00:00+00:00",
            "end_time":   "2024-01-03T12:00:00+00:00",
            "exercises": [
                {
                    "index": 0,
                    "title": "Squat",
                    "exercise_template_id": "SQUAT001",
                    "superset_id": None,
                    "sets": [
                        {"index": 0, "type": "warmup", "weight_kg": 60.0,  "reps": 8, "duration_seconds": None},
                        {"index": 1, "type": "normal", "weight_kg": 100.0, "reps": 5, "duration_seconds": None},
                    ],
                },
                {
                    "index": 1,
                    "title": "Stretching",
                    "exercise_template_id": "STRETCH001",
                    "superset_id": None,
                    "sets": [
                        {"index": 0, "type": "normal", "weight_kg": None, "reps": None, "duration_seconds": 300},
                    ],
                },
            ],
        },
    ]


@pytest.fixture
def raw_templates():
    return [
        {
            "id": "BENCH001",
            "title": "Bench Press",
            "type": "weight_reps",
            "primary_muscle_group": "chest",
            "secondary_muscle_groups": ["triceps", "shoulders"],
            "equipment": "barbell",
            "is_custom": False,
        },
        {
            "id": "SQUAT001",
            "title": "Squat",
            "type": "weight_reps",
            "primary_muscle_group": "quadriceps",
            "secondary_muscle_groups": ["glutes", "hamstrings"],
            "equipment": "barbell",
            "is_custom": False,
        },
        {
            "id": "STRETCH001",
            "title": "Stretching",
            "type": "duration",
            "primary_muscle_group": "cardio",
            "secondary_muscle_groups": [],
            "equipment": "none",
            "is_custom": False,
        },
    ]


# ── Silver DataFrames ─────────────────────────────────────────────────────────

@pytest.fixture
def silver_workouts(raw_workouts):
    from pipeline.silver.transform import transform_workouts
    return transform_workouts(raw_workouts)


@pytest.fixture
def silver_templates(raw_templates):
    from pipeline.silver.transform import transform_exercise_templates
    return transform_exercise_templates(raw_templates)


# ── Gold DataFrames ───────────────────────────────────────────────────────────

@pytest.fixture
def gold_data(silver_workouts, silver_templates):
    from pipeline.gold.aggregate import (
        aggregate_workout_summary,
        aggregate_weekly_volume,
        aggregate_exercise_progression,
        aggregate_muscle_group_summary,
    )
    return {
        "workout_summary":      aggregate_workout_summary(silver_workouts),
        "weekly_volume":        aggregate_weekly_volume(silver_workouts, silver_templates),
        "exercise_progression": aggregate_exercise_progression(silver_workouts),
        "muscle_group_summary": aggregate_muscle_group_summary(silver_workouts, silver_templates),
    }


# ── Exercise progression with enough sessions for regression ─────────────────

@pytest.fixture
def progression_with_trend():
    """5 sessions of Bench Press with clear upward trend."""
    return pd.DataFrame([
        {"workout_date": pd.Timestamp("2024-01-01"), "exercise_title": "Bench Press",
         "exercise_template_id": "BENCH001", "max_weight_kg": 80.0,
         "total_volume_kg": 640.0, "total_sets": 3, "total_reps": 24},
        {"workout_date": pd.Timestamp("2024-01-08"), "exercise_title": "Bench Press",
         "exercise_template_id": "BENCH001", "max_weight_kg": 82.5,
         "total_volume_kg": 660.0, "total_sets": 3, "total_reps": 24},
        {"workout_date": pd.Timestamp("2024-01-15"), "exercise_title": "Bench Press",
         "exercise_template_id": "BENCH001", "max_weight_kg": 85.0,
         "total_volume_kg": 680.0, "total_sets": 3, "total_reps": 24},
        {"workout_date": pd.Timestamp("2024-01-22"), "exercise_title": "Bench Press",
         "exercise_template_id": "BENCH001", "max_weight_kg": 87.5,
         "total_volume_kg": 700.0, "total_sets": 3, "total_reps": 24},
        {"workout_date": pd.Timestamp("2024-01-29"), "exercise_title": "Bench Press",
         "exercise_template_id": "BENCH001", "max_weight_kg": 90.0,
         "total_volume_kg": 720.0, "total_sets": 3, "total_reps": 24},
    ])
