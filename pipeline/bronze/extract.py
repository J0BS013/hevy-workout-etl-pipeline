"""Fail-fast, paginated extraction from the Hevy API."""

import logging
import time
from uuid import uuid4

import requests

from config import API_URL, headers

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_RETRIES = 3
RECOVERABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class ExtractionError(RuntimeError):
    """Raised when an endpoint cannot be extracted completely and safely."""


def _fetch_all_pages(
    endpoint: str,
    data_key: str,
    page_size: int = 10,
    *,
    session: requests.Session | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = 1.0,
    sleep=time.sleep,
    run_id: str | None = None,
) -> list:
    """Fetch every required page or raise without returning partial data.

    Retries are limited to transient HTTP statuses and request exceptions. A
    successful return is possible only after every advertised page was read.
    """
    active_session = session or requests.Session()
    extraction_run_id = run_id or str(uuid4())
    all_records: list = []
    page = 1
    expected_pages: int | None = None

    while expected_pages is None or page <= expected_pages:
        url = f"{API_URL}/{endpoint}?page={page}&pageSize={page_size}"
        response = None
        last_error: Exception | None = None
        duration_ms = 0.0

        for attempt in range(max_retries + 1):
            started_at = time.perf_counter()
            try:
                response = active_session.get(url, headers=headers, timeout=timeout_seconds)
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            except requests.RequestException as error:
                last_error = error
            else:
                if response.status_code == 200:
                    break
                if response.status_code not in RECOVERABLE_STATUS_CODES:
                    raise ExtractionError(
                        f"Non-recoverable HTTP {response.status_code} for /{endpoint} page {page}"
                    )
                last_error = ExtractionError(
                    f"Recoverable HTTP {response.status_code} for /{endpoint} page {page}"
                )

            if attempt == max_retries:
                raise ExtractionError(
                    f"Failed to fetch /{endpoint} page {page} after {max_retries + 1} attempts"
                ) from last_error

            delay = backoff_seconds * (2**attempt)
            logger.warning(
                "hevy_extract_retry run_id=%s endpoint=%s page=%s attempt=%s delay_seconds=%s error=%s duration_ms=%s",
                extraction_run_id, endpoint, page, attempt + 1, delay, last_error,
                round((time.perf_counter() - started_at) * 1000, 2),
            )
            sleep(delay)

        if response is None:  # Defensive guard for static type checkers.
            raise ExtractionError(f"No response returned for /{endpoint} page {page}")
        try:
            payload = response.json()
        except ValueError as error:
            raise ExtractionError(f"Invalid JSON for /{endpoint} page {page}") from error
        if not isinstance(payload, dict) or data_key not in payload:
            raise ExtractionError(f"Invalid schema for /{endpoint} page {page}: missing '{data_key}'")
        if not isinstance(payload[data_key], list):
            raise ExtractionError(f"Invalid schema for /{endpoint} page {page}: '{data_key}' is not a list")
        if "page_count" not in payload or not isinstance(payload["page_count"], int):
            raise ExtractionError(f"Invalid schema for /{endpoint} page {page}: missing integer page_count")
        if payload["page_count"] < page or payload["page_count"] < 1:
            raise ExtractionError(f"Invalid page_count for /{endpoint} page {page}")
        if expected_pages is not None and payload["page_count"] != expected_pages:
            raise ExtractionError(f"page_count changed during /{endpoint} extraction")

        expected_pages = payload["page_count"]
        records = payload[data_key]
        all_records.extend(records)
        logger.info(
            "hevy_extract_page run_id=%s endpoint=%s page=%s pages_expected=%s records=%s status=%s duration_ms=%s",
            extraction_run_id, endpoint, page, expected_pages, len(records), response.status_code, duration_ms,
        )
        page += 1

    logger.info(
        "hevy_extract_complete run_id=%s endpoint=%s pages_received=%s pages_expected=%s records=%s",
        extraction_run_id, endpoint, page - 1, expected_pages, len(all_records),
    )
    return all_records


def get_workouts(**kwargs) -> list:
    logger.info("Extracting workouts...")
    return _fetch_all_pages("workouts", "workouts", **kwargs)


def get_exercise_templates(**kwargs) -> list:
    logger.info("Extracting exercise templates...")
    return _fetch_all_pages("exercise_templates", "exercise_templates", **kwargs)


def run(*, session: requests.Session | None = None, **fetch_kwargs) -> dict:
    """Extract both required endpoints before downstream persistence begins."""
    run_id = str(uuid4())
    active_session = session or requests.Session()
    return {
        "workouts": get_workouts(session=active_session, run_id=run_id, **fetch_kwargs),
        "exercise_templates": get_exercise_templates(session=active_session, run_id=run_id, **fetch_kwargs),
    }
