import csv
import io
import requests
from config import Config


class RedashClient:
    def __init__(self, config: Config):
        self.base_url = config.redash_url.rstrip("/")
        self.api_key = config.redash_api_key

    def fetch_query_csv(self, query_id: int) -> list[dict]:
        """Fetch query results as CSV and return as list of dicts."""
        url = f"{self.base_url}/api/queries/{query_id}/results.csv"
        headers = {"Authorization": f"Key {self.api_key}"}

        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))
        return list(reader)

    def fetch_from_csv_file(self, file_path: str) -> list[dict]:
        """Load data from a local CSV file (for testing without Redash)."""
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
