import pytest
import pandas as pd
from pipeline.gold.aggregate import (
    aggregate_workout_summary,
    aggregate_weekly_volume,
    aggregate_exercise_progression,
    aggregate_muscle_group_summary,
)


class TestWorkoutSummary:

    def test_one_row_per_workout(self, silver_workouts):
        df = aggregate_workout_summary(silver_workouts)
        assert len(df) == silver_workouts["workout_id"].nunique()

    def test_warmup_sets_excluded_from_volume(self, silver_workouts):
        """Warmup sets must NOT be counted in total_volume_kg."""
        df = aggregate_workout_summary(silver_workouts)
        # workout-1: 2 working sets (80kg*8 + 80kg*7 = 640 + 560 = 1200kg)
        row = df[df["workout_id"] == "workout-1"].iloc[0]
        assert row["total_volume_kg"] == pytest.approx(1200.0)

    def test_warmup_sets_excluded_from_total_sets(self, silver_workouts):
        """total_sets must not count warmup sets."""
        df = aggregate_workout_summary(silver_workouts)
        row = df[df["workout_id"] == "workout-1"].iloc[0]
        assert row["total_sets"] == 2  # normal + failure only

    def test_volume_is_non_negative(self, silver_workouts):
        df = aggregate_workout_summary(silver_workouts)
        assert (df["total_volume_kg"] >= 0).all()

    def test_required_columns_present(self, silver_workouts):
        df = aggregate_workout_summary(silver_workouts)
        expected = {"workout_id", "workout_title", "workout_date",
                    "total_volume_kg", "total_sets", "total_exercises"}
        assert expected.issubset(set(df.columns))


class TestWeeklyVolume:

    def test_muscle_groups_come_from_templates(self, silver_workouts, silver_templates):
        df = aggregate_weekly_volume(silver_workouts, silver_templates)
        assert "primary_muscle_group" in df.columns
        assert df["primary_muscle_group"].notna().any()

    def test_warmups_excluded(self, silver_workouts, silver_templates):
        """Weekly volume should only reflect working sets."""
        df = aggregate_weekly_volume(silver_workouts, silver_templates)
        # workout-1 chest volume: 80*8 + 80*7 = 1200 (no warmup)
        chest_vol = df[df["primary_muscle_group"] == "chest"]["total_volume_kg"].sum()
        assert chest_vol == pytest.approx(1200.0)

    def test_no_negative_volume(self, silver_workouts, silver_templates):
        df = aggregate_weekly_volume(silver_workouts, silver_templates)
        assert (df["total_volume_kg"] >= 0).all()


class TestExerciseProgression:

    def test_excludes_duration_only_sets(self, silver_workouts):
        """Stretching (no weight/reps) must not appear in progression."""
        df = aggregate_exercise_progression(silver_workouts)
        assert "Stretching" not in df["exercise_title"].values

    def test_excludes_warmup_sets(self, silver_workouts):
        """Max weight must not be pulled from warmup sets."""
        df = aggregate_exercise_progression(silver_workouts)
        bench_row = df[df["exercise_title"] == "Bench Press"].iloc[0]
        # Warmup was 40kg, working max is 80kg
        assert bench_row["max_weight_kg"] == pytest.approx(80.0)

    def test_required_columns_present(self, silver_workouts):
        df = aggregate_exercise_progression(silver_workouts)
        expected = {"workout_date", "exercise_title", "max_weight_kg",
                    "total_volume_kg", "total_sets", "total_reps"}
        assert expected.issubset(set(df.columns))


class TestMuscleGroupSummary:

    def test_volume_is_non_negative(self, silver_workouts, silver_templates):
        df = aggregate_muscle_group_summary(silver_workouts, silver_templates)
        assert (df["total_volume_kg"] >= 0).all()

    def test_sorted_by_volume_descending(self, silver_workouts, silver_templates):
        df = aggregate_muscle_group_summary(silver_workouts, silver_templates)
        volumes = df["total_volume_kg"].tolist()
        assert volumes == sorted(volumes, reverse=True)
