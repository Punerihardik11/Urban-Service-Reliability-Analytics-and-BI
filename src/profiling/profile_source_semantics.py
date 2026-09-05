from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "metadata"
    / "dataset_metadata.json"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "profiling"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SOURCE
# ============================================================

DATASET_ID = "erm2-nwe9"

API_URL = (
    f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
)


# ============================================================
# PROVISIONAL PROJECT SCOPE
# ============================================================

SCOPE_START = "2026-01-01T00:00:00.000"
SCOPE_END = "2026-09-01T00:00:00.000"

BASE_WHERE = (
    f"created_date >= '{SCOPE_START}' "
    f"AND created_date < '{SCOPE_END}'"
)


# ============================================================
# HTTP HELPERS
# ============================================================

def api_get(params: dict) -> list[dict]:
    response = requests.get(
        API_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()
    return response.json()


def api_count(extra_condition: str | None = None) -> int:
    where = BASE_WHERE

    if extra_condition:
        where += f" AND ({extra_condition})"

    result = api_get(
        {
            "$select": "count(*) as row_count",
            "$where": where,
        }
    )

    return int(result[0]["row_count"])


def pct(part: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(part / total * 100, 2)


# ============================================================
# 1 — SOURCE SCHEMA
# ============================================================

print("\n" + "=" * 75)
print("1 — SOURCE SCHEMA")
print("=" * 75)

if not METADATA_PATH.exists():
    raise FileNotFoundError(
        f"Metadata file not found: {METADATA_PATH}\n"
        "Run src/ingestion/verify_api.py first."
    )


with METADATA_PATH.open("r", encoding="utf-8") as f:
    metadata = json.load(f)


schema_rows = []

for column in metadata.get("columns", []):
    schema_rows.append(
        {
            "display_name": column.get("name"),
            "api_field": column.get("fieldName"),
            "data_type": column.get("dataTypeName"),
            "description": column.get("description"),
        }
    )


schema_df = pd.DataFrame(schema_rows)

schema_path = OUTPUT_DIR / "source_schema.csv"
schema_df.to_csv(schema_path, index=False)

print(f"Columns in live metadata: {len(schema_df)}")
print(f"Saved → {schema_path}")


# ============================================================
# 2 — CORE SCOPE SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("2 — PROVISIONAL 2026 YTD SCOPE")
print("=" * 75)

summary = api_get(
    {
        "$select": (
            "count(*) as row_count,"
            "min(created_date) as min_created_date,"
            "max(created_date) as max_created_date"
        ),
        "$where": BASE_WHERE,
    }
)[0]


total_rows = int(summary["row_count"])

print(f"Rows:               {total_rows:,}")
print(f"Minimum created:    {summary.get('min_created_date')}")
print(f"Maximum created:    {summary.get('max_created_date')}")


# ============================================================
# 3 — STATUS DISTRIBUTION
# ============================================================

print("\n" + "=" * 75)
print("3 — STATUS DISTRIBUTION")
print("=" * 75)

statuses = api_get(
    {
        "$select": "status,count(*) as row_count",
        "$where": BASE_WHERE,
        "$group": "status",
        "$order": "count(*) DESC",
        "$limit": 100,
    }
)


for row in statuses:
    count = int(row["row_count"])

    print(
        f"{str(row.get('status')):25s} "
        f"{count:>12,} "
        f"{pct(count, total_rows):>7.2f}%"
    )


# ============================================================
# 4 — FIELD POPULATION
# ============================================================

print("\n" + "=" * 75)
print("4 — IMPORTANT FIELD POPULATION")
print("=" * 75)


population_conditions = {
    "due_date":
        "due_date IS NOT NULL",

    "closed_date":
        "closed_date IS NOT NULL",

    "resolution_description":
        "resolution_description IS NOT NULL",

    "resolution_action_updated_date":
        "resolution_action_updated_date IS NOT NULL",

    "borough":
        "borough IS NOT NULL",

    "incident_zip":
        "incident_zip IS NOT NULL",

    "latitude":
        "latitude IS NOT NULL",

    "longitude":
        "longitude IS NOT NULL",

    "community_board":
        "community_board IS NOT NULL",

    "council_district":
        "council_district IS NOT NULL",

    "descriptor":
        "descriptor IS NOT NULL",

    "descriptor_2":
        "descriptor_2 IS NOT NULL",
}


population_results = {}


for field, condition in population_conditions.items():

    count = api_count(condition)

    population_results[field] = {
        "populated_rows": count,
        "population_pct": pct(count, total_rows),
    }

    print(
        f"{field:35s} "
        f"{count:>12,} "
        f"{pct(count, total_rows):>7.2f}%"
    )


# ============================================================
# 5 — LIFECYCLE CONSISTENCY
# ============================================================

print("\n" + "=" * 75)
print("5 — STATUS / CLOSED-DATE RELATIONSHIP")
print("=" * 75)


lifecycle_checks = {

    "Closed status WITH closed_date":
        "status = 'Closed' AND closed_date IS NOT NULL",

    "Closed status WITHOUT closed_date":
        "status = 'Closed' AND closed_date IS NULL",

    "Non-Closed WITH closed_date":
        "status <> 'Closed' AND closed_date IS NOT NULL",

    "Non-Closed WITHOUT closed_date":
        "status <> 'Closed' AND closed_date IS NULL",
}


lifecycle_results = {}


for label, condition in lifecycle_checks.items():

    count = api_count(condition)

    lifecycle_results[label] = count

    print(
        f"{label:40s}: "
        f"{count:>12,}"
    )


# ============================================================
# 6 — AGENCY PROFILE
# ============================================================

print("\n" + "=" * 75)
print("6 — TOP AGENCIES")
print("=" * 75)

agencies = api_get(
    {
        "$select":
            "agency,agency_name,count(*) as row_count",

        "$where":
            BASE_WHERE,

        "$group":
            "agency,agency_name",

        "$order":
            "count(*) DESC",

        "$limit":
            25,
    }
)


for row in agencies:

    print(
        f"{str(row.get('agency')):8s} "
        f"{int(row['row_count']):>12,}  "
        f"{row.get('agency_name')}"
    )


all_agencies = api_get(
    {
        "$select": "agency,count(*) as row_count",
        "$where": BASE_WHERE,
        "$group": "agency",
        "$limit": 5000,
    }
)

print(f"\nDistinct agency codes: {len(all_agencies)}")


# ============================================================
# 7 — COMPLAINT / PROBLEM PROFILE
# ============================================================

print("\n" + "=" * 75)
print("7 — TOP SERVICE PROBLEMS")
print("=" * 75)

problems = api_get(
    {
        "$select":
            "complaint_type,count(*) as row_count",

        "$where":
            BASE_WHERE,

        "$group":
            "complaint_type",

        "$order":
            "count(*) DESC",

        "$limit":
            25,
    }
)


for row in problems:

    print(
        f"{int(row['row_count']):>12,}  "
        f"{row.get('complaint_type')}"
    )


all_problems = api_get(
    {
        "$select":
            "complaint_type,count(*) as row_count",

        "$where":
            BASE_WHERE,

        "$group":
            "complaint_type",

        "$limit":
            5000,
    }
)

print(f"\nDistinct service problems: {len(all_problems)}")


# ============================================================
# 8 — DUE DATE USAGE BY AGENCY
# ============================================================

print("\n" + "=" * 75)
print("8 — DUE DATE USAGE")
print("=" * 75)

due_date_count = population_results["due_date"]["populated_rows"]

print(
    f"Overall due_date population: "
    f"{due_date_count:,} / {total_rows:,} "
    f"({pct(due_date_count, total_rows):.2f}%)"
)


if due_date_count > 0:

    due_by_agency = api_get(
        {
            "$select":
                "agency,count(*) as row_count",

            "$where":
                BASE_WHERE
                + " AND due_date IS NOT NULL",

            "$group":
                "agency",

            "$order":
                "count(*) DESC",

            "$limit":
                25,
        }
    )

    print("\nAgencies contributing populated due dates:")

    for row in due_by_agency:
        print(
            f"{str(row.get('agency')):8s} "
            f"{int(row['row_count']):>12,}"
        )


# ============================================================
# 9 — RECENT DAILY COUNTS
# ============================================================

print("\n" + "=" * 75)
print("9 — RECENT DAILY REQUEST COUNTS")
print("=" * 75)

scope_end_dt = datetime.fromisoformat(
    SCOPE_END.replace("T00:00:00.000", "")
)

recent_daily_counts = []


for days_back in range(10, 0, -1):

    day_start = scope_end_dt - timedelta(days=days_back)
    day_end = day_start + timedelta(days=1)

    start_string = day_start.strftime(
        "%Y-%m-%dT00:00:00.000"
    )

    end_string = day_end.strftime(
        "%Y-%m-%dT00:00:00.000"
    )

    result = api_get(
        {
            "$select":
                "count(*) as row_count",

            "$where":
                f"created_date >= '{start_string}' "
                f"AND created_date < '{end_string}'",
        }
    )

    count = int(result[0]["row_count"])

    recent_daily_counts.append(
        {
            "date": day_start.strftime("%Y-%m-%d"),
            "requests": count,
        }
    )

    print(
        f"{day_start.strftime('%Y-%m-%d')}: "
        f"{count:>10,}"
    )


# ============================================================
# 10 — SAVE MACHINE-READABLE PROFILE
# ============================================================

report = {

    "scope": {
        "start": SCOPE_START,
        "candidate_end": SCOPE_END,
        "row_count": total_rows,
        "min_created_date":
            summary.get("min_created_date"),
        "max_created_date":
            summary.get("max_created_date"),
    },

    "statuses": statuses,

    "field_population":
        population_results,

    "lifecycle_checks":
        lifecycle_results,

    "distinct_agencies":
        len(all_agencies),

    "distinct_service_problems":
        len(all_problems),

    "recent_daily_counts":
        recent_daily_counts,
}


report_path = (
    OUTPUT_DIR
    / "source_semantic_profile.json"
)

with report_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        report,
        f,
        indent=2,
        ensure_ascii=False,
    )


print("\n" + "=" * 75)
print("SOURCE SEMANTIC PROFILE COMPLETE")
print("=" * 75)

print(f"Saved → {report_path}")
print(f"Saved → {schema_path}")