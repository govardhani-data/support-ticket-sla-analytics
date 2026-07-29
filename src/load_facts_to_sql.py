"""
load_facts_to_sql.py

Loads the two fact tables into SQL Server.
Dates are parsed explicitly so they arrive as real datetimes, not text.
"""

import urllib.parse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

ODBC_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=localhost\SQLEXPRESS;"
    "DATABASE=SupportTicketDB;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

# Which columns hold dates, per table
DATE_COLUMNS = {
    "fact_ticket": ["created_datetime", "first_response_datetime", "resolved_datetime"],
    "fact_ticket_assignment": ["assigned_datetime", "left_datetime"],
}


def main() -> None:
    url = "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(ODBC_STRING)
    engine = create_engine(url, fast_executemany=True)

    print("Loading fact tables into SupportTicketDB\n")

    for table, date_cols in DATE_COLUMNS.items():
        df = pd.read_csv(DATA_DIR / f"{table}.csv", parse_dates=date_cols)
        df.to_sql(table, engine, if_exists="replace", index=False, chunksize=5_000)
        print(f"  {table:24} {len(df):7,} rows loaded")

    print("\nDone.")


if __name__ == "__main__":
    main()