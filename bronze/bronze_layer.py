import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add the parent directory to the path
import requests
from config import API_URL, headers

def get_workouts():
    """Fetch workouts from the Hevy API."""
    url = f"{API_URL}/workouts"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_exercise_templates():
    url = f"{API_URL}/exercise_templates"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
def get_bronze_data():
    return {
        "workouts": get_workouts(),
        "exercise_templates": get_exercise_templates()
    }

