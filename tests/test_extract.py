from collections import deque

import pandas as pd
import pytest
import requests

from pipeline.bronze.extract import ExtractionError, _fetch_all_pages, run
from utils.storage import save_to_parquet


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, outcomes):
        self.outcomes = deque(outcomes)
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append({"url": url, "timeout": timeout})
        outcome = self.outcomes.popleft()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_fetches_a_single_page_with_explicit_timeout():
    session = FakeSession([FakeResponse(200, {"page_count": 1, "workouts": [{"id": "w1"}]})])
    assert _fetch_all_pages("workouts", "workouts", session=session) == [{"id": "w1"}]
    assert session.calls[0]["timeout"] == 15


def test_fetches_multiple_pages():
    session = FakeSession([
        FakeResponse(200, {"page_count": 2, "workouts": [{"id": "w1"}]}),
        FakeResponse(200, {"page_count": 2, "workouts": [{"id": "w2"}]}),
    ])
    assert _fetch_all_pages("workouts", "workouts", session=session) == [{"id": "w1"}, {"id": "w2"}]


def test_retries_a_transient_page_failure():
    session = FakeSession([
        FakeResponse(500),
        FakeResponse(200, {"page_count": 1, "workouts": [{"id": "w1"}]}),
    ])
    delays = []
    assert _fetch_all_pages("workouts", "workouts", session=session, sleep=delays.append) == [{"id": "w1"}]
    assert delays == [1.0]


@pytest.mark.parametrize("outcome", [FakeResponse(500), FakeResponse(429), requests.Timeout("timed out")])
def test_permanent_transient_failure_aborts_without_partial_data(outcome):
    session = FakeSession([outcome, outcome, outcome, outcome])
    with pytest.raises(ExtractionError, match="after 4 attempts"):
        _fetch_all_pages("workouts", "workouts", session=session, sleep=lambda _: None)


def test_non_recoverable_http_status_aborts_immediately():
    session = FakeSession([FakeResponse(401)])
    with pytest.raises(ExtractionError, match="Non-recoverable HTTP 401"):
        _fetch_all_pages("workouts", "workouts", session=session)
    assert len(session.calls) == 1


@pytest.mark.parametrize("payload", [
    {"workouts": []},
    {"page_count": 1},
    {"page_count": 1, "workouts": {}},
])
def test_invalid_pagination_schema_aborts(payload):
    with pytest.raises(ExtractionError, match="Invalid schema"):
        _fetch_all_pages("workouts", "workouts", session=FakeSession([FakeResponse(200, payload)]))


def test_failure_in_second_required_endpoint_prevents_partial_run_result():
    session = FakeSession([
        FakeResponse(200, {"page_count": 1, "workouts": [{"id": "w1"}]}),
        FakeResponse(500), FakeResponse(500), FakeResponse(500), FakeResponse(500),
    ])
    with pytest.raises(ExtractionError):
        run(session=session, sleep=lambda _: None)


def test_atomic_parquet_write_keeps_previous_snapshot_if_promotion_fails(tmp_path, monkeypatch):
    save_to_parquet(pd.DataFrame({"id": ["old"]}), tmp_path, "workouts")
    destination = tmp_path / "workouts.parquet"
    monkeypatch.setattr("utils.storage.os.replace", lambda *_: (_ for _ in ()).throw(OSError("disk error")))
    with pytest.raises(OSError, match="disk error"):
        save_to_parquet(pd.DataFrame({"id": ["new"]}), tmp_path, "workouts")
    assert pd.read_parquet(destination)["id"].tolist() == ["old"]
