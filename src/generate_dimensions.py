"""
generate_dimensions.py

Builds the eight dimension tables for the support ticket SLA analysis.
Writes one CSV per dimension into data/raw/.

Data is synthetic. No client or production data is used.
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Fixed seeds: guarantee anyone running this script gets identical data.
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

fake = Faker("en_IN")
Faker.seed(RANDOM_SEED)

# Locate data/raw relative to this file, so the script works from any folder.
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Three years of history.
START_DATE = date(2023, 1, 1)
END_DATE = date(2025, 12, 31)

ENGINEER_COUNT = 60


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# Simplified: fixed-date Indian public holidays only (month, day).
FIXED_HOLIDAYS = [(1, 26), (8, 15), (10, 2), (12, 25)]

# ITIL: priority is derived from impact x urgency, not entered directly.
IMPACT_URGENCY_MATRIX = {
    ("High",   "High"):   "P1",
    ("High",   "Medium"): "P2",
    ("High",   "Low"):    "P3",
    ("Medium", "High"):   "P2",
    ("Medium", "Medium"): "P3",
    ("Medium", "Low"):    "P4",
    ("Low",    "High"):   "P3",
    ("Low",    "Medium"): "P4",
    ("Low",    "Low"):    "P4",
}

# SLA targets in minutes. Response and resolution are separate clocks.
SLA_TARGETS = {
    "P1": {"name": "Critical", "response": 15,  "resolution": 240},
    "P2": {"name": "High",     "response": 30,  "resolution": 480},
    "P3": {"name": "Medium",   "response": 60,  "resolution": 1440},
    "P4": {"name": "Low",      "response": 240, "resolution": 4320},
}

CATEGORIES = [
    ("Network",     "Connectivity"),
    ("Network",     "VPN"),
    ("Network",     "Firewall"),
    ("Application", "Login / SSO"),
    ("Application", "Performance"),
    ("Application", "Data Error"),
    ("Application", "Integration Failure"),
    ("Access",      "Account Provisioning"),
    ("Access",      "Permissions"),
    ("Access",      "Password Reset"),
    ("Hardware",    "Laptop"),
    ("Hardware",    "Peripheral"),
    ("Database",    "Query Performance"),
    ("Database",    "Data Correction"),
    ("Database",    "Job Failure"),
]

# (group_name, tier, region, shift_model)
ASSIGNMENT_GROUPS = [
    ("Service Desk",           1, "India",  "24x7"),
    ("Desktop Support",        1, "India",  "Business Hours"),
    ("Access Management",      1, "India",  "Business Hours"),
    ("Network Operations",     2, "India",  "24x7"),
    ("Application Support L2", 2, "India",  "24x7"),
    ("Database Support",       2, "India",  "Business Hours"),
    ("Vendor Liaison",         2, "Europe", "Business Hours"),
    ("Application Support L3", 3, "Europe", "Business Hours"),
    ("Infrastructure L3",      3, "US",     "Business Hours"),
]

CHANNELS = ["Phone", "Email", "Self-service Portal", "Auto-generated Alert", "Chat"]

REGIONS = [
    ("India",   "Asia/Kolkata"),
    ("Europe",  "Europe/London"),
    ("US East", "America/New_York"),
    ("APAC",    "Asia/Singapore"),
]

ROOT_CAUSES = [
    "Network Failure",
    "Software Bug",
    "Configuration Error",
    "User Error",
    "Hardware Failure",
    "Third-party Outage",
    "Capacity / Resource Limit",
    "Change-related",
    "Unknown / Not Reproducible",
]


# ---------------------------------------------------------------------------
# Dimension builders
# ---------------------------------------------------------------------------

def build_dim_date(start: date, end: date) -> pd.DataFrame:
    """One row per calendar day between start and end inclusive."""
    rows = []
    current = start

    while current <= end:
        is_weekend = current.isoweekday() >= 6
        is_holiday = (current.month, current.day) in FIXED_HOLIDAYS

        rows.append({
            "date_key": int(current.strftime("%Y%m%d")),
            "full_date": current.isoformat(),
            "day_of_week": current.isoweekday(),
            "day_name": current.strftime("%A"),
            "iso_year": current.isocalendar().year,
            "week_of_year": current.isocalendar().week,
            "month": current.month,
            "month_name": current.strftime("%B"),
            "quarter": (current.month - 1) // 3 + 1,
            "year": current.year,
            "is_weekend": int(is_weekend),
            "is_holiday": int(is_holiday),
            "is_working_day": int(not is_weekend and not is_holiday),
        })

        current += timedelta(days=1)

    return pd.DataFrame(rows)


def build_dim_priority() -> pd.DataFrame:
    """One row per impact/urgency combination."""
    rows = []

    for key, (combo, code) in enumerate(IMPACT_URGENCY_MATRIX.items(), start=1):
        impact, urgency = combo
        targets = SLA_TARGETS[code]

        rows.append({
            "priority_key": key,
            "impact": impact,
            "urgency": urgency,
            "priority_code": code,
            "priority_name": targets["name"],
            "response_sla_minutes": targets["response"],
            "resolution_sla_minutes": targets["resolution"],
        })

    return pd.DataFrame(rows)


def build_dim_category() -> pd.DataFrame:
    rows = [
        {"category_key": i, "category": cat, "subcategory": sub}
        for i, (cat, sub) in enumerate(CATEGORIES, start=1)
    ]
    return pd.DataFrame(rows)


def build_dim_assignment_group() -> pd.DataFrame:
    rows = [
        {
            "group_key": i,
            "group_name": name,
            "tier": tier,
            "region": region,
            "shift_model": shift,
        }
        for i, (name, tier, region, shift) in enumerate(ASSIGNMENT_GROUPS, start=1)
    ]
    return pd.DataFrame(rows)


def build_dim_engineer(count: int) -> pd.DataFrame:
    seniorities = ["Junior", "Mid", "Senior", "Lead"]
    weights = [0.35, 0.40, 0.20, 0.05]

    rows = []
    for i in range(1, count + 1):
        rows.append({
            "engineer_key": i,
            "engineer_name": fake.name(),
            "seniority": random.choices(seniorities, weights=weights)[0],
        })

    return pd.DataFrame(rows)


def build_dim_channel() -> pd.DataFrame:
    rows = [
        {"channel_key": i, "channel_name": name}
        for i, name in enumerate(CHANNELS, start=1)
    ]
    return pd.DataFrame(rows)


def build_dim_region() -> pd.DataFrame:
    rows = [
        {"region_key": i, "region_name": name, "timezone": tz}
        for i, (name, tz) in enumerate(REGIONS, start=1)
    ]
    return pd.DataFrame(rows)


def build_dim_root_cause() -> pd.DataFrame:
    rows = [
        {"root_cause_key": i, "root_cause_name": name}
        for i, name in enumerate(ROOT_CAUSES, start=1)
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Build every dimension and write it to data/raw/ as CSV."""
    dimensions = {
        "dim_date": build_dim_date(START_DATE, END_DATE),
        "dim_priority": build_dim_priority(),
        "dim_category": build_dim_category(),
        "dim_assignment_group": build_dim_assignment_group(),
        "dim_engineer": build_dim_engineer(ENGINEER_COUNT),
        "dim_channel": build_dim_channel(),
        "dim_region": build_dim_region(),
        "dim_root_cause": build_dim_root_cause(),
    }

    print(f"Writing to: {OUTPUT_DIR}\n")

    for name, df in dimensions.items():
        path = OUTPUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  {name:24} {len(df):6,} rows  ->  {path.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()