"""
load_dimensions_to_sql.py

Reads the 8 dimension CSV files from data/raw and loads each one
into SQL Server as a table.
"""

import urllib.parse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# Where the CSV files live
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# How to reach the database
ODBC_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=localhost\SQLEXPRESS;"
    "DATABASE=SupportTicketDB;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

TABLES = [
    "dim_date",
    "dim_priority",
    "dim_category",
    "dim_assignment_group",
    "dim_engineer",
    "dim_channel",
    "dim_region",
    "dim_root_cause",
]


def main() -> None:
    connection_url = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(ODBC_STRING)
    engine = create_engine(connection_url)

    print("Loading tables into SupportTicketDB\n")

    for name in TABLES:
        csv_path = DATA_DIR / f"{name}.csv"
        df = pd.read_csv(csv_path)
        df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"  {name:24} {len(df):6,} rows loaded")

    print("\nDone.")


if __name__ == "__main__":
    main()