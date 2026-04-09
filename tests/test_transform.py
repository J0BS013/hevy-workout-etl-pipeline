import pytest
import pandas as pd
from pipeline.silver.transform import transform_workouts, transform_exercise_templates


class TestTransformWorkouts:

    def test_row_count_equals_total_sets(self, raw_workouts):
        """Each set must produce exactly one row."""
        df = transform_workouts(raw_workouts)
        # workout-1: 3 sets | workout-2: 2 + 1 sets = 6 total
        assert len(df) == 6

    def test_required_columns_present(self, raw_workouts):
        df = transform_workouts(raw_workouts)
        expected = {
            "workout_id", "workout_title", "workout_date", "workout_duration_minutes",
            "exercise_title", "exercise_template_id", "set_index", "set_type",
            "weight_kg", "reps", "duration_seconds", "volume_kg",
        }
        assert expected.issubset(set(df.columns))

    def test_volume_calculation(self, raw_workouts):
        """volume_kg must equal weight_kg * reps for weighted sets."""
        df = transform_workouts(raw_workouts)
        weighted = df.dropna(subset=["weight_kg", "reps"])
        expected = (weighted["weight_kg"] * weighted["reps"]).round(2)
        pd.testing.assert_series_equal(weighted["volume_kg"], expected, check_names=False)

    def test_volume_is_null_for_duration_sets(self, raw_workouts):
        """Sets with no weight/reps (e.g. stretching) must have null volume_kg."""
        df = transform_workouts(raw_workouts)
        duration_sets = df[df["duration_seconds"].notna() & df["weight_kg"].isna()]
        assert duration_sets["volume_kg"].isna().all()

    def test_duration_minutes_is_correct(self, raw_workouts):
        """workout-1 is 90 min (10:00 → 11:30)."""
        df = transform_workouts(raw_workouts)
        duration = df[df["workout_id"] == "workout-1"]["workout_duration_minutes"].iloc[0]
        assert duration == pytest.approx(90.0, abs=0.5)

    def test_no_null_workout_ids(self, raw_workouts):
        df = transform_workouts(raw_workouts)
        assert df["workout_id"].isna().sum() == 0

    def test_no_null_workout_dates(self, raw_workouts):
        df = transform_workouts(raw_workouts)
        assert df["workout_date"].isna().sum() == 0

    def test_set_types_are_valid(self, raw_workouts):
        df = transform_workouts(raw_workouts)
        valid_types = {"warmup", "normal", "failure"}
        assert set(df["set_type"].unique()).issubset(valid_types)

    def test_empty_input_returns_empty_dataframe(self):
        df = transform_workouts([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestTransformExerciseTemplates:

    def test_row_count_equals_input(self, raw_templates):
        df = transform_exercise_templates(raw_templates)
        assert len(df) == len(raw_templates)

    def test_required_columns_present(self, raw_templates):
        df = transform_exercise_templates(raw_templates)
        expected = {"id", "title", "type", "primary_muscle_group",
                    "secondary_muscle_groups", "equipment", "is_custom"}
        assert expected.issubset(set(df.columns))

    def test_secondary_groups_joined_as_string(self, raw_templates):
        """secondary_muscle_groups list must be joined with ', '."""
        df = transform_exercise_templates(raw_templates)
        bench_row = df[df["id"] == "BENCH001"].iloc[0]
        assert bench_row["secondary_muscle_groups"] == "triceps, shoulders"

    def test_empty_secondary_groups_gives_empty_string(self, raw_templates):
        df = transform_exercise_templates(raw_templates)
        stretch_row = df[df["id"] == "STRETCH001"].iloc[0]
        assert stretch_row["secondary_muscle_groups"] == ""

    def test_empty_input_returns_empty_dataframe(self):
        df = transform_exercise_templates([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
