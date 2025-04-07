import os
import logging
from config import *
from bronze.bronze_layer import get_bronze_data
from utils import save_to_csv, save_to_parquet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# BRONZE LAYER
def run_bronze_pipeline():
    logging.info("🔄 Starting Bronze Pipeline")
    os.makedirs(BRONZE_PATH, exist_ok=True)

    data = get_bronze_data()

    for key, value in data.items():
        if value:
            save_to_csv(value, BRONZE_PATH, key)
            save_to_parquet(value, BRONZE_PATH, key)
        else:
            logging.warning(f"⚠️ No data returned for: {key}")

    logging.info("✅ Bronze Pipeline completed successfully")

if __name__ == "__main__":
    try:
        run_bronze_pipeline()
    except Exception as e:
        print("Error:", e)