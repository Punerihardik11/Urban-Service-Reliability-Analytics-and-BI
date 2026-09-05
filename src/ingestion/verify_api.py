from __future__ import annotations

import json
from pathlib import Path

import requests


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VERIFICATION_DIR = PROJECT_ROOT / "data" / "bronze" / "verification"
METADATA_DIR = PROJECT_ROOT / "data" / "bronze" / "metadata"

VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# NYC OPEN DATA
# ---------------------------------------------------------

DATASET_ID = "erm2-nwe9"

API_URL = (
    f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
)

METADATA_URL = (
    f"https://data.cityofnewyork.us/api/views/{DATASET_ID}"
)


# ---------------------------------------------------------
# IMPORTANT FIELDS WE EXPECT
# ---------------------------------------------------------

IMPORTANT_FIELDS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "descriptor_2",
    "location_type",
    "incident_zip",
    "borough",
    "city",
    "status",
    "due_date",
    "resolution_description",
    "resolution_action_updated_date",
    "community_board",
    "council_district",
    "latitude",
    "longitude",
]


def get_json(url: str, params: dict | None = None):
    """Make a GET request and return parsed JSON."""

    response = requests.get(
        url,
        params=params,
        timeout=60,
    )

    print(f"HTTP {response.status_code}")
    print(f"URL: {response.url}")

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# 1 — VERIFY DATASET METADATA
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("1 — DATASET METADATA")
print("=" * 70)

metadata = get_json(METADATA_URL)

print(f"Dataset ID:      {metadata.get('id')}")
print(f"Dataset name:    {metadata.get('name')}")
print(f"Attribution:     {metadata.get('attribution')}")
print(f"Rows updated at: {metadata.get('rowsUpdatedAt')}")

columns = metadata.get("columns", [])

print(f"Published columns: {len(columns)}")

metadata_path = METADATA_DIR / "dataset_metadata.json"

with metadata_path.open("w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"Saved → {metadata_path}")


# ---------------------------------------------------------
# 2 — VERIFY LIVE DATA ACCESS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("2 — LIVE API SAMPLE")
print("=" * 70)

sample = get_json(
    API_URL,
    params={
        "$limit": 5,
        "$order": "created_date DESC",
    },
)

print(f"\nRows returned: {len(sample)}")

sample_path = VERIFICATION_DIR / "311_api_sample_5.json"

with sample_path.open("w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2, ensure_ascii=False)

print(f"Saved → {sample_path}")


# ---------------------------------------------------------
# 3 — INSPECT RETURNED FIELDS
# ---------------------------------------------------------

if not sample:
    raise RuntimeError("API responded but returned zero sample rows.")

returned_fields = sorted(
    set().union(*(row.keys() for row in sample))
)

print("\nFields observed in sample:")
for field in returned_fields:
    print(f"  {field}")


# ---------------------------------------------------------
# 4 — CHECK IMPORTANT BUSINESS FIELDS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("3 — IMPORTANT FIELD CHECK")
print("=" * 70)

for field in IMPORTANT_FIELDS:

    present_count = sum(
        field in row and row[field] not in (None, "")
        for row in sample
    )

    print(
        f"{field:35s} "
        f"{present_count}/{len(sample)} populated"
    )


# ---------------------------------------------------------
# 5 — DISPLAY SMALL BUSINESS SAMPLE
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("4 — SAMPLE SERVICE REQUESTS")
print("=" * 70)

display_fields = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "complaint_type",
    "descriptor",
    "status",
    "borough",
    "incident_zip",
    "due_date",
]

for index, row in enumerate(sample, start=1):

    print(f"\nREQUEST {index}")

    for field in display_fields:
        print(f"{field:25s}: {row.get(field)}")


# ---------------------------------------------------------
# 6 — COUNT CANDIDATE ANALYTICAL SCOPES
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("5 — CANDIDATE ANALYTICAL SCOPE COUNTS")
print("=" * 70)


candidate_scopes = {

    "Full 2025": (
        "created_date >= '2025-01-01T00:00:00.000' "
        "AND created_date < '2026-01-01T00:00:00.000'"
    ),

    "2026 YTD": (
        "created_date >= '2026-01-01T00:00:00.000' "
        "AND created_date < '2026-09-01T00:00:00.000'"
    ),

    "Recent 6 Months": (
        "created_date >= '2026-03-01T00:00:00.000' "
        "AND created_date < '2026-09-01T00:00:00.000'"
    ),

    "Recent 12 Months": (
        "created_date >= '2025-09-01T00:00:00.000' "
        "AND created_date < '2026-09-01T00:00:00.000'"
    ),
}


scope_results = {}


for scope_name, where_clause in candidate_scopes.items():

    result = get_json(
        API_URL,
        params={
            "$select": "count(*) as row_count",
            "$where": where_clause,
        },
    )

    row_count = int(result[0]["row_count"])

    scope_results[scope_name] = row_count

    print(
        f"{scope_name:20s}: "
        f"{row_count:,} rows"
    )


scope_path = VERIFICATION_DIR / "candidate_scope_counts.json"

with scope_path.open("w", encoding="utf-8") as f:
    json.dump(scope_results, f, indent=2)

print(f"\nSaved → {scope_path}")


# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("API VERIFICATION PASSED")
print("=" * 70)

print(
    "Official NYC 311 source is reachable and "
    "candidate analytical volumes were successfully measured."
)