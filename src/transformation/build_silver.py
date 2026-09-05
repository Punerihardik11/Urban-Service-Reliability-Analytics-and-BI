from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_DIR = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "raw"
    / "311_2026_ytd"
)

MANIFEST_PATH = (
    BRONZE_DIR
    / "extraction_manifest.json"
)

SILVER_DIR = (
    PROJECT_ROOT
    / "data"
    / "silver"
    / "service_requests_2026_ytd"
)

SILVER_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# SOURCE MANIFEST
# ============================================================

with MANIFEST_PATH.open(
    "r",
    encoding="utf-8",
) as f:
    manifest = json.load(f)


EXPECTED_ROWS = int(
    manifest["extracted_rows"]
)


# Extraction timestamp gives us our observed-data snapshot.
extraction_utc = pd.Timestamp(
    manifest["extraction_finished_at_utc"]
)

snapshot_nyc = (
    extraction_utc
    .tz_convert("America/New_York")
    .tz_localize(None)
)


print("\n" + "=" * 78)
print("BUILD NYC 311 SILVER DATASET")
print("=" * 78)

print(f"Expected Bronze rows: {EXPECTED_ROWS:,}")
print(f"Snapshot timestamp:   {snapshot_nyc}")


# ============================================================
# BUSINESS CONSTANTS
# ============================================================

UNRESOLVED_STATUSES = {
    "Open",
    "In Progress",
    "Assigned",
    "Pending",
    "Started",
    "Unspecified",
}


# ============================================================
# SOURCE FIELDS
# ============================================================

KEEP_FIELDS = [
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
    "police_precinct",
    "latitude",
    "longitude",
    "incident_address",
    "open_data_channel_type",
]


# ============================================================
# COUNTERS
# ============================================================

input_rows = 0
output_rows = 0

future_closed_count = 0
negative_duration_count = 0
lifecycle_mismatch_count = 0
valid_resolution_count = 0

part_files = sorted(
    BRONZE_DIR.glob("part_*.json.gz")
)


# ============================================================
# TRANSFORMATION
# ============================================================

for part_number, file_path in enumerate(
    part_files,
    start=1,
):

    print(
        f"\n[{part_number:02d}/{len(part_files):02d}] "
        f"{file_path.name}"
    )

    df = pd.read_json(
        file_path,
        lines=True,
        compression="gzip",
        dtype=False,
    )

    input_rows += len(df)

    # --------------------------------------------------------
    # ENSURE EXPECTED COLUMNS
    # --------------------------------------------------------

    for field in KEEP_FIELDS:
        if field not in df.columns:
            df[field] = pd.NA

    silver = df[KEEP_FIELDS].copy()

    # --------------------------------------------------------
    # RENAME BUSINESS FIELDS
    # --------------------------------------------------------

    silver = silver.rename(
        columns={
            "created_date": "created_at",
            "closed_date": "closed_at",
            "complaint_type": "service_problem",
            "descriptor": "problem_detail",
            "descriptor_2": "additional_detail",
        }
    )

    # --------------------------------------------------------
    # TYPES
    # --------------------------------------------------------

    silver["unique_key"] = pd.to_numeric(
        silver["unique_key"],
        errors="coerce",
    ).astype("Int64")

    datetime_fields = [
        "created_at",
        "closed_at",
        "due_date",
        "resolution_action_updated_date",
    ]

    for field in datetime_fields:
        silver[field] = pd.to_datetime(
            silver[field],
            errors="coerce",
        )

    silver["latitude"] = pd.to_numeric(
        silver["latitude"],
        errors="coerce",
    )

    silver["longitude"] = pd.to_numeric(
        silver["longitude"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # CLEAN ZIP
    # --------------------------------------------------------

    zip_raw = (
        silver["incident_zip"]
        .astype("string")
        .str.strip()
        .str.replace(
            r"\.0$",
            "",
            regex=True,
        )
    )

    silver["incident_zip_clean"] = (
        zip_raw.where(
            zip_raw.str.match(
                r"^\d{5}$",
                na=False,
            )
        )
    )

    # --------------------------------------------------------
    # CURRENT LIFECYCLE
    # --------------------------------------------------------

    silver["is_closed"] = (
        silver["status"]
        .eq("Closed")
    )

    silver["is_backlog"] = (
        silver["status"]
        .isin(UNRESOLVED_STATUSES)
    )

    # --------------------------------------------------------
    # LIFECYCLE QUALITY
    # --------------------------------------------------------

    closed_date_present = (
        silver["closed_at"].notna()
    )

    silver["lifecycle_mismatch_flag"] = (
        (
            silver["is_closed"]
            &
            ~closed_date_present
        )
        |
        (
            ~silver["is_closed"]
            &
            closed_date_present
        )
    )

    lifecycle_mismatch_count += int(
        silver[
            "lifecycle_mismatch_flag"
        ].sum()
    )

    # --------------------------------------------------------
    # RAW DURATION
    # --------------------------------------------------------

    raw_resolution_hours = (
        (
            silver["closed_at"]
            -
            silver["created_at"]
        )
        .dt.total_seconds()
        /
        3600
    )

    silver["negative_duration_flag"] = (
        raw_resolution_hours < 0
    )

    negative_duration_count += int(
        silver[
            "negative_duration_flag"
        ].sum()
    )

    # --------------------------------------------------------
    # FUTURE CLOSED DATE
    # --------------------------------------------------------

    silver["future_closed_date_flag"] = (
        silver["closed_at"].notna()
        &
        (
            silver["closed_at"]
            >
            snapshot_nyc
        )
    )

    future_closed_count += int(
        silver[
            "future_closed_date_flag"
        ].sum()
    )

    # --------------------------------------------------------
    # VALID RESOLUTION DURATION
    # --------------------------------------------------------

    silver["resolution_duration_valid"] = (
        silver["is_closed"]
        &
        silver["created_at"].notna()
        &
        silver["closed_at"].notna()
        &
        ~silver["negative_duration_flag"]
        &
        ~silver["future_closed_date_flag"]
    )

    silver["resolution_hours"] = (
        raw_resolution_hours.where(
            silver[
                "resolution_duration_valid"
            ]
        )
    )

    silver["resolution_days"] = (
        silver["resolution_hours"]
        /
        24
    )

    valid_resolution_count += int(
        silver[
            "resolution_duration_valid"
        ].sum()
    )

    # --------------------------------------------------------
    # DURATION FLAGS
    # --------------------------------------------------------

    silver["zero_duration_flag"] = (
        silver["resolution_duration_valid"]
        &
        silver["resolution_hours"].eq(0)
    )

    silver["extreme_duration_flag"] = (
        silver["resolution_duration_valid"]
        &
        silver["resolution_days"].gt(180)
    )

    # --------------------------------------------------------
    # BACKLOG AGE
    # --------------------------------------------------------

    age_days = (
        (
            snapshot_nyc
            -
            silver["created_at"]
        )
        .dt.total_seconds()
        /
        86400
    )

    silver["request_age_days"] = (
        age_days.where(
            silver["is_backlog"]
        )
    )

    # --------------------------------------------------------
    # TEMPORAL FEATURES
    # --------------------------------------------------------

    silver["created_calendar_date"] = (
        silver["created_at"].dt.date
    )

    silver["created_hour"] = (
        silver["created_at"].dt.hour
    )

    silver["created_day_of_week"] = (
        silver["created_at"]
        .dt.day_name()
    )

    silver["created_day_of_week_num"] = (
        silver["created_at"]
        .dt.dayofweek
    )

    silver["created_month"] = (
        silver["created_at"]
        .dt.to_period("M")
        .astype(str)
    )

    silver["created_month_name"] = (
        silver["created_at"]
        .dt.month_name()
    )

    silver["created_week_start"] = (
        silver["created_at"]
        -
        pd.to_timedelta(
            silver["created_at"].dt.dayofweek,
            unit="D",
        )
    ).dt.normalize()

    # --------------------------------------------------------
    # GEOGRAPHY FLAGS
    # --------------------------------------------------------

    silver["has_coordinates"] = (
        silver["latitude"].notna()
        &
        silver["longitude"].notna()
    )

    # Validation found no coordinate pairs outside
    # the broad NYC boundary.
    silver["has_valid_coordinates"] = (
        silver["has_coordinates"]
    )

    silver["has_valid_zip"] = (
        silver[
            "incident_zip_clean"
        ].notna()
    )

    silver["borough_unspecified_flag"] = (
        silver["borough"]
        .eq("Unspecified")
    )

    # --------------------------------------------------------
    # RESOLUTION BAND
    # --------------------------------------------------------

    bins = [
        -np.inf,
        1,
        6,
        24,
        72,
        168,
        336,
        720,
        2160,
        np.inf,
    ]

    labels = [
        "<1 hour",
        "1-6 hours",
        "6-24 hours",
        "1-3 days",
        "3-7 days",
        "7-14 days",
        "14-30 days",
        "30-90 days",
        "90+ days",
    ]

    silver["resolution_duration_band"] = pd.cut(
        silver["resolution_hours"],
        bins=bins,
        labels=labels,
        right=False,
    )

    # --------------------------------------------------------
    # BACKLOG AGE BAND
    # --------------------------------------------------------

    backlog_bins = [
        -np.inf,
        1,
        3,
        7,
        14,
        30,
        90,
        np.inf,
    ]

    backlog_labels = [
        "<1 day",
        "1-3 days",
        "3-7 days",
        "7-14 days",
        "14-30 days",
        "30-90 days",
        "90+ days",
    ]

    silver["backlog_age_band"] = pd.cut(
        silver["request_age_days"],
        bins=backlog_bins,
        labels=backlog_labels,
        right=False,
    )

    # --------------------------------------------------------
    # WRITE PART
    # --------------------------------------------------------

    output_path = (
        SILVER_DIR
        / f"part_{part_number:05d}.parquet"
    )

    silver.to_parquet(
        output_path,
        index=False,
        compression="snappy",
    )

    output_rows += len(silver)

    print(
        f"Input {len(df):,}"
        f" → Silver {len(silver):,}"
        f" | cumulative {output_rows:,}"
    )


# ============================================================
# MANIFEST
# ============================================================

manifest_out = {
    "source_rows": EXPECTED_ROWS,
    "input_rows_scanned": input_rows,
    "silver_rows_written": output_rows,
    "row_count_match": (
        EXPECTED_ROWS
        ==
        input_rows
        ==
        output_rows
    ),
    "parts_written": len(part_files),
    "snapshot_timestamp_nyc": str(
        snapshot_nyc
    ),
    "valid_resolution_rows": (
        valid_resolution_count
    ),
    "lifecycle_mismatch_rows": (
        lifecycle_mismatch_count
    ),
    "negative_duration_rows": (
        negative_duration_count
    ),
    "future_closed_date_rows": (
        future_closed_count
    ),
}


manifest_output_path = (
    SILVER_DIR
    / "silver_manifest.json"
)


with manifest_output_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        manifest_out,
        f,
        indent=2,
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 78)
print("SILVER BUILD SUMMARY")
print("=" * 78)

print(
    f"Bronze expected:          "
    f"{EXPECTED_ROWS:,}"
)

print(
    f"Bronze scanned:           "
    f"{input_rows:,}"
)

print(
    f"Silver written:           "
    f"{output_rows:,}"
)

print(
    f"Row-count match:          "
    f"{EXPECTED_ROWS == input_rows == output_rows}"
)

print(
    f"Valid resolution rows:    "
    f"{valid_resolution_count:,}"
)

print(
    f"Lifecycle mismatch rows:  "
    f"{lifecycle_mismatch_count:,}"
)

print(
    f"Negative duration rows:   "
    f"{negative_duration_count:,}"
)

print(
    f"Future closed-date rows:  "
    f"{future_closed_count:,}"
)

print(
    f"Parts written:            "
    f"{len(part_files)}"
)

print(
    f"\nManifest → "
    f"{manifest_output_path}"
)


if not (
    EXPECTED_ROWS
    ==
    input_rows
    ==
    output_rows
):
    raise RuntimeError(
        "Silver row-count reconciliation failed."
    )


print("\nSILVER BUILD PASSED")