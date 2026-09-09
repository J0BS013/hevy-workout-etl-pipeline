import os
import logging
from pathlib import Path
from uuid import uuid4
import pandas as pd

logger = logging.getLogger(__name__)


def save_to_csv(df: pd.DataFrame, path: str, filename: str) -> None:
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, f"{filename}.csv")
    df.to_csv(filepath, index=False)
    logger.info(f"CSV saved: {filepath}")


def save_to_parquet(df: pd.DataFrame, path: str, filename: str) -> None:
    """Write Parquet atomically so a failed write cannot corrupt a snapshot."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / f"{filename}.parquet"
    temporary_path = directory / f".{filename}.{uuid4().hex}.tmp.parquet"
    try:
        df.to_parquet(temporary_path, index=False)
        os.replace(temporary_path, filepath)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    logger.info("Parquet saved atomically: %s", filepath)
