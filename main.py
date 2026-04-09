import logging
import os

from config import BRONZE_PATH, SILVER_PATH, GOLD_PATH, ANALYTICS_PATH
from pipeline.bronze import extract
from pipeline.silver import transform
from pipeline.gold import aggregate
from pipeline.analytics import stats
from pipeline.quality import checks
from utils.storage import save_to_parquet
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def run_pipeline():
    # ── BRONZE ──────────────────────────────────────────────────────────────
    logger.info("=== BRONZE: Extracting raw data from API ===")
    os.makedirs(BRONZE_PATH, exist_ok=True)

    bronze_data = extract.run()
    checks.check_bronze(bronze_data)

    for name, records in bronze_data.items():
        if records:
            save_to_parquet(pd.DataFrame(records), BRONZE_PATH, name)
        else:
            logger.warning(f"No data returned for: {name}")

    # ── SILVER ──────────────────────────────────────────────────────────────
    logger.info("=== SILVER: Transforming and flattening data ===")
    os.makedirs(SILVER_PATH, exist_ok=True)

    silver_data = transform.run(bronze_data)
    checks.check_silver(silver_data)

    for name, df in silver_data.items():
        save_to_parquet(df, SILVER_PATH, name)

    # ── GOLD ────────────────────────────────────────────────────────────────
    logger.info("=== GOLD: Aggregating analytics ===")
    os.makedirs(GOLD_PATH, exist_ok=True)

    gold_data = aggregate.run(silver_data)
    checks.check_gold(gold_data)

    for name, df in gold_data.items():
        save_to_parquet(df, GOLD_PATH, name)

    # ── ANALYTICS ───────────────────────────────────────────────────────────
    logger.info("=== ANALYTICS: Running statistical analysis ===")
    os.makedirs(ANALYTICS_PATH, exist_ok=True)

    analytics_data = stats.run(gold_data)

    for name, df in analytics_data.items():
        save_to_parquet(df, ANALYTICS_PATH, name)

    logger.info("=== Pipeline completed successfully ===")


if __name__ == "__main__":
    try:
        run_pipeline()
    except checks.DataQualityError as e:
        logger.error(f"Data quality check failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
