from __future__ import annotations

import gzip
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ID = "erm2-nwe9"

API_URL = (
    f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "raw"
    / "311_2026_ytd"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


SCOPE_START = "2026-01-01T00:00:00.000"
SCOPE_END = "2026-08-30T00:00:00.000"

WHERE_CLAUSE = (
    f"created_date >= '{SCOPE_START}' "
    f"AND created_date < '{SCOPE_END}'"
)

PAGE_SIZE = 50_000


# ============================================================
# HTTP SESSION WITH RETRIES
# ============================================================

session = requests.Session()

retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504,
    ],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(
    max_retries=retry_strategy
)

session.mount("https://", adapter)


# ============================================================
# HELPERS
# ============================================================

def api_get(params: dict) -> list[dict]:

    response = session.get(
        API_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


def get_expected_count() -> int:

    result = api_get(
        {
            "$select": "count(*) as row_count",
            "$where": WHERE_CLAUSE,
        }
    )

    return int(result[0]["row_count"])


def write_json_gz(
    rows: list[dict],
    output_path: Path,
) -> None:

    with gzip.open(
        output_path,
        mode="wt",
        encoding="utf-8",
    ) as f:

        for row in rows:

            json.dump(
                row,
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            f.write("\n")


# ============================================================
# EXTRACTION
# ============================================================

print("\n" + "=" * 75)
print("NYC 311 BRONZE ACQUISITION")
print("=" * 75)

print(f"Scope start: {SCOPE_START}")
print(f"Scope end:   {SCOPE_END} exclusive")
print(f"Page size:   {PAGE_SIZE:,}")


expected_rows = get_expected_count()

print(f"\nExpected rows: {expected_rows:,}")


offset = 0
part_number = 1

rows_written = 0

parts = []

extraction_started_at = datetime.now(
    timezone.utc
).isoformat()


while offset < expected_rows:

    print(
        f"\nFetching part {part_number:05d} "
        f"| offset {offset:,}"
    )

    started = time.time()

    rows = api_get(
        {
            "$where": WHERE_CLAUSE,

            "$order":
                "created_date ASC, unique_key ASC",

            "$limit":
                PAGE_SIZE,

            "$offset":
                offset,
        }
    )


    if not rows:
        print(
            "API returned zero rows before "
            "expected extraction count."
        )

        break


    part_filename = (
        f"part_{part_number:05d}.json.gz"
    )

    part_path = (
        OUTPUT_DIR
        / part_filename
    )


    write_json_gz(
        rows,
        part_path,
    )


    batch_count = len(rows)

    rows_written += batch_count


    first_created = rows[0].get(
        "created_date"
    )

    last_created = rows[-1].get(
        "created_date"
    )


    first_key = rows[0].get(
        "unique_key"
    )

    last_key = rows[-1].get(
        "unique_key"
    )


    elapsed = time.time() - started


    parts.append(
        {
            "part":
                part_filename,

            "row_count":
                batch_count,

            "offset":
                offset,

            "first_created_date":
                first_created,

            "last_created_date":
                last_created,

            "first_unique_key":
                first_key,

            "last_unique_key":
                last_key,

            "elapsed_seconds":
                round(elapsed, 2),
        }
    )


    print(
        f"Saved {batch_count:,} rows"
        f" | cumulative {rows_written:,}"
        f" | {elapsed:.1f}s"
    )


    offset += batch_count
    part_number += 1


# ============================================================
# VALIDATE EXTRACTION
# ============================================================

extraction_finished_at = datetime.now(
    timezone.utc
).isoformat()


complete = (
    rows_written == expected_rows
)


manifest = {

    "dataset_id":
        DATASET_ID,

    "scope": {
        "created_start":
            SCOPE_START,

        "created_end_exclusive":
            SCOPE_END,
    },

    "page_size":
        PAGE_SIZE,

    "expected_rows":
        expected_rows,

    "extracted_rows":
        rows_written,

    "row_count_match":
        complete,

    "parts_written":
        len(parts),

    "extraction_started_at_utc":
        extraction_started_at,

    "extraction_finished_at_utc":
        extraction_finished_at,

    "parts":
        parts,
}


manifest_path = (
    OUTPUT_DIR
    / "extraction_manifest.json"
)


with manifest_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        manifest,
        f,
        indent=2,
        ensure_ascii=False,
    )


print("\n" + "=" * 75)
print("BRONZE EXTRACTION SUMMARY")
print("=" * 75)

print(
    f"Expected rows:  "
    f"{expected_rows:,}"
)

print(
    f"Extracted rows: "
    f"{rows_written:,}"
)

print(
    f"Parts written:  "
    f"{len(parts):,}"
)

print(
    f"Count match:    "
    f"{complete}"
)

print(
    f"Manifest:       "
    f"{manifest_path}"
)


if not complete:

    raise RuntimeError(
        "Bronze extraction row count "
        "does not match API expectation."
    )


print("\nBRONZE ACQUISITION PASSED")