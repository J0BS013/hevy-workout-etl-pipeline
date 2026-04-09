import logging
import requests
from config import API_URL, headers

logger = logging.getLogger(__name__)


def _fetch_all_pages(endpoint: str, data_key: str, page_size: int = 10) -> list:
    """Fetch all pages from a paginated Hevy API endpoint."""
    all_records = []
    page = 1

    while True:
        url = f"{API_URL}/{endpoint}?page={page}&pageSize={page_size}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error {response.status_code} on /{endpoint} page {page}: {response.text}")
            break

        data = response.json()
        records = data.get(data_key, [])
        all_records.extend(records)

        page_count = data.get("page_count", 1)
        logger.info(f"Fetched /{endpoint} page {page}/{page_count} ({len(records)} records)")

        if page >= page_count:
            break

        page += 1

    return all_records


def get_workouts() -> list:
    logger.info("Extracting workouts...")
    return _fetch_all_pages("workouts", "workouts")


def get_exercise_templates() -> list:
    logger.info("Extracting exercise templates...")
    return _fetch_all_pages("exercise_templates", "exercise_templates")


def run() -> dict:
    return {
        "workouts": get_workouts(),
        "exercise_templates": get_exercise_templates(),
    }
