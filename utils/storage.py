import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def save_to_csv(df: pd.DataFrame, path: str, filename: str) -> None:
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, f"{filename}.csv")
    df.to_csv(filepath, index=False)
    logger.info(f"CSV saved: {filepath}")


def save_to_parquet(df: pd.DataFrame, path: str, filename: str) -> None:
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, f"{filename}.parquet")
    df.to_parquet(filepath, index=False)
    logger.info(f"Parquet saved: {filepath}")
