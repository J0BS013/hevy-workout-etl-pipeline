import os
import requests
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


# API Config

HEVY_API_KEY = os.getenv("HEVY_API_KEY")
API_URL = 'https://api.hevyapp.com/v1'

headers = {
    'api-key': HEVY_API_KEY,
    'accept': 'application/json'
}

# Paths

DATA_PATH = "data"
BRONZE_PATH = os.path.join(DATA_PATH, "bronze")
SILVER_PATH = os.path.join(DATA_PATH, "silver")
GOLD_PATH = os.path.join(DATA_PATH, "gold")
ANALYTICS_PATH = os.path.join(DATA_PATH, "analytics")


def test_connection():
    """Test the connection to the Hevy API by fetching a list of routines."""
    url = f"{API_URL}/routines?page=1&pageSize=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ Successfully connected to the Hevy API!")
        print("Response:", response.json())
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    test_connection()