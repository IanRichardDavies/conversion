# Package Imports
import os
import pandas as pd
from dotenv import load_dotenv
from pandas_gbq import read_gbq

load_dotenv()


class DataImporter:
    def __init__(self, source: str, location: str) -> None:
        self.source = source
        self.location = location

    def import_data(self) -> pd.DataFrame:
        if self.source.lower() in ("gbq", "bq", "bigquery"):
            PROJECT_ID = os.getenv("BQ_PROJECT_ID")
            sql = f"SELECT * FROM {self.location};"
            data = pd.read_gbq(sql, project_id=PROJECT_ID, dialect="standard")
        else:
            data = pd.read_csv(f"{self.location}")
        return data
