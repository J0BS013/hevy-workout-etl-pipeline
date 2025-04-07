import pandas as pd
import os

def save_to_csv(data, path, filename):
    os.makedirs(path, exist_ok=True)
    df = pd.DataFrame(data)
    filepath = os.path.join(path, f"{filename}.csv")
    df.to_csv(filepath, index=False)
    print(f"💾 CSV saved in: {filepath}")

def save_to_parquet(data, path, filename):
    os.makedirs(path, exist_ok=True)
    df = pd.DataFrame(data)
    filepath = os.path.join(path, f"{filename}.parquet")
    df.to_parquet(filepath, index=False)
    print(f"💾 Parquet saved in: {filepath}")
