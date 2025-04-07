# 🏋️‍♂️ Hevy Workout ETL Pipeline

This project is an **ETL (Extract, Transform, Load)** pipeline designed to interact with the **Hevy API**, fetch workout and exercise data, process it, and store it in **CSV** and **Parquet** formats for future analysis.

🔗 Visit [GPTOnline.ai](https://gptonline.ai/pt/) for more projects like this!

---

## ✨ Features

- 🔄 Extracts workout and exercise data from the Hevy API
- 💾 Saves the data in **CSV** and **Parquet** formats
- 📂 Data structured into layers: **Bronze**, **Silver**, and **Gold**
- 🧱 Modular design for easy maintenance and future scalability

---

## ⚙️ Requirements

- Python 3.9+
- A valid Hevy API Key (`HEVY_API_KEY`)
- Python packages:
  - `pandas==2.2.3`
  - `python-dotenv==1.1.0`
  - `requests==2.32.3`

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/hevy-workout-etl-pipeline.git
cd hevy-workout-etl-pipeline
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the root directory with the following content:

```env
HEVY_API_KEY=your_api_key_here
```

---

## 🔌 Test API Connection

Run the config file to ensure the API is accessible:

```bash
python config.py
```

✅ If successful, you'll see a success message with the API response.

---

## ▶️ How to Use

### Run the Bronze Pipeline

The **Bronze** layer fetches raw data from the API and stores it in `data/bronze`.

```bash
python main.py
```

Expected output:

```
🔄 Starting Bronze Pipeline
💾 CSV saved in: data/bronze/workouts.csv
💾 Parquet saved in: data/bronze/workouts.parquet
💾 CSV saved in: data/bronze/exercise_templates.csv
💾 Parquet saved in: data/bronze/exercise_templates.parquet
✅ Bronze Pipeline completed successfully
```

---

## 📁 Project Structure

```
hevy-workout-etl-pipeline/
│
├── config.py            # API and path configuration
├── main.py              # Main script to run the pipeline
├── utils/               # Utility functions like save_to_csv/parquet
├── bronze/              # Bronze layer: raw data
│   └── bronze_layer.py
├── data/
│   ├── bronze/          # Raw data (CSV and Parquet)
│   ├── silver/          # Transformed data (to be developed)
│   └── gold/            # Final analytics data (to be developed)
├── .env                 # Contains the API Key
└── requirements.txt     # Project dependencies
```

---

## 📚 About the Hevy API

This project uses the following endpoints from the Hevy API:

- `/workouts`
- `/exercise_templates`

Authentication header:

```python
headers = {
    'api-key': HEVY_API_KEY,
    'accept': 'application/json'
}
```

More details at the [official Hevy documentation](https://www.hevyapp.com/).

---

## 🏗️ Project Status

🔨 **In Progress**

- ✅ Bronze Layer: Implemented
- 🧼 Silver Layer: To be developed (data cleaning and transformation)
- 📊 Gold Layer: To be developed (aggregations and analytics)