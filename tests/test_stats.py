import pytest
import pandas as pd
from pipeline.analytics.stats import (
    compute_exercise_progression,
    compute_personal_records,
    compute_volume_trend,
    compute_consistency,
)


class TestExerciseProgressionStats:

    def test_skips_exercises_with_fewer_than_3_sessions(self, gold_data):
        """Exercises with < 3 sessions must not appear in results."""
        df = compute_exercise_progression(gold_data["exercise_progression"])
        # fixture only has 1 session per exercise — result must be empty
        assert len(df) == 0

    def test_returns_required_columns(self, progression_with_trend):
        df = compute_exercise_progression(progression_with_trend)
        expected = {
            "exercise_title", "sessions", "slope_kg_per_week",
            "r_squared", "p_value", "is_significant", "trend",
            "total_gain_kg", "first_max_weight_kg", "last_max_weight_kg",
        }
        assert expected.issubset(set(df.columns))

    def test_detects_upward_trend(self, progression_with_trend):
        df = compute_exercise_progression(progression_with_trend)
        assert len(df) == 1
        row = df.iloc[0]
        assert row["slope_kg_per_week"] > 0
        assert row["trend"] == "improving"
        assert row["is_significant"] == True

    def test_r_squared_between_0_and_1(self, progression_with_trend):
        df = compute_exercise_progression(progression_with_trend)
        r2 = df.iloc[0]["r_squared"]
        assert 0.0 <= r2 <= 1.0

    def test_p_value_between_0_and_1(self, progression_with_trend):
        df = compute_exercise_progression(progression_with_trend)
        p = df.iloc[0]["p_value"]
        assert 0.0 <= p <= 1.0

    def test_total_gain_matches_first_and_last(self, progression_with_trend):
        df = compute_exercise_progression(progression_with_trend)
        row = df.iloc[0]
        expected_gain = round(row["last_max_weight_kg"] - row["first_max_weight_kg"], 1)
        assert row["total_gain_kg"] == pytest.approx(expected_gain)


class TestPersonalRecords:

    def test_first_session_is_always_a_pr(self, progression_with_trend):
        prs = compute_personal_records(progression_with_trend)
        first_date = progression_with_trend["workout_date"].min()
        assert first_date in prs["workout_date"].values

    def test_pr_count_matches_increasing_series(self, progression_with_trend):
        """Every session in an always-increasing series must be a PR."""
        prs = compute_personal_records(progression_with_trend)
        bench_prs = prs[prs["exercise_title"] == "Bench Press"]
        assert len(bench_prs) == len(progression_with_trend)

    def test_no_pr_when_weight_stays_flat(self):
        """Only the first session should be a PR when weight never increases."""
        flat = pd.DataFrame([
            {"workout_date": pd.Timestamp("2024-01-01"), "exercise_title": "Squat",
             "exercise_template_id": "SQ", "max_weight_kg": 100.0,
             "total_volume_kg": 500.0, "total_sets": 3, "total_reps": 15},
            {"workout_date": pd.Timestamp("2024-01-08"), "exercise_title": "Squat",
             "exercise_template_id": "SQ", "max_weight_kg": 100.0,
             "total_volume_kg": 500.0, "total_sets": 3, "total_reps": 15},
            {"workout_date": pd.Timestamp("2024-01-15"), "exercise_title": "Squat",
             "exercise_template_id": "SQ", "max_weight_kg": 100.0,
             "total_volume_kg": 500.0, "total_sets": 3, "total_reps": 15},
        ])
        prs = compute_personal_records(flat)
        assert len(prs) == 1

    def test_required_columns_present(self, progression_with_trend):
        prs = compute_personal_records(progression_with_trend)
        assert {"exercise_title", "workout_date", "weight_kg"}.issubset(set(prs.columns))


class TestVolumeTrend:

    def test_returns_single_row(self, gold_data):
        df = compute_volume_trend(gold_data["weekly_volume"])
        assert len(df) <= 1  # may be empty if < 3 weeks

    def test_required_columns_present(self, progression_with_trend):
        # Build a minimal weekly_volume from progression fixture
        weekly = pd.DataFrame([
            {"week_start": pd.Timestamp("2024-01-01"), "primary_muscle_group": "chest", "total_volume_kg": 1200, "total_sets": 3},
            {"week_start": pd.Timestamp("2024-01-08"), "primary_muscle_group": "chest", "total_volume_kg": 1300, "total_sets": 3},
            {"week_start": pd.Timestamp("2024-01-15"), "primary_muscle_group": "chest", "total_volume_kg": 1400, "total_sets": 3},
        ])
        df = compute_volume_trend(weekly)
        expected = {"slope_kg_per_week", "r_squared", "p_value", "is_significant", "trend"}
        assert expected.issubset(set(df.columns))

    def test_returns_empty_for_fewer_than_3_weeks(self):
        weekly = pd.DataFrame([
            {"week_start": pd.Timestamp("2024-01-01"), "primary_muscle_group": "chest", "total_volume_kg": 1000, "total_sets": 3},
        ])
        df = compute_volume_trend(weekly)
        assert df.empty


class TestConsistency:

    def test_returns_single_row(self, gold_data):
        df = compute_consistency(gold_data["workout_summary"])
        assert len(df) == 1

    def test_consistency_score_between_0_and_100(self, gold_data):
        df = compute_consistency(gold_data["workout_summary"])
        score = df.iloc[0]["consistency_score"]
        assert 0.0 <= score <= 100.0

    def test_required_columns_present(self, gold_data):
        df = compute_consistency(gold_data["workout_summary"])
        expected = {
            "avg_workouts_per_week", "consistency_score",
            "longest_streak_weeks", "total_active_weeks",
        }
        assert expected.issubset(set(df.columns))

    def test_longest_streak_is_positive(self, gold_data):
        df = compute_consistency(gold_data["workout_summary"])
        assert df.iloc[0]["longest_streak_weeks"] >= 1
