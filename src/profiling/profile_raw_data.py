from __future__ import annotations

import gzip
import json
from collections import Counter
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

METADATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "bronze"
    / "metadata"
    / "dataset_metadata.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "profiling"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# IMPORTANT ANALYTICAL FIELDS
# ============================================================

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
    "police_precinct",
    "latitude",
    "longitude",
    "incident_address",
    "open_data_channel_type",
]


# ============================================================
# LOAD MANIFEST + METADATA
# ============================================================

if not MANIFEST_PATH.exists():
    raise FileNotFoundError(
        f"Manifest not found: {MANIFEST_PATH}"
    )


with MANIFEST_PATH.open(
    "r",
    encoding="utf-8",
) as f:
    manifest = json.load(f)


expected_rows = int(
    manifest["extracted_rows"]
)


with METADATA_PATH.open(
    "r",
    encoding="utf-8",
) as f:
    metadata = json.load(f)


source_fields = [
    column.get("fieldName")
    for column in metadata.get("columns", [])
    if column.get("fieldName")
]


# ============================================================
# ACCUMULATORS
# ============================================================

total_rows = 0

null_counts = Counter()
examples = {}

status_counts = Counter()
agency_counts = Counter()
complaint_counts = Counter()
borough_counts = Counter()
channel_counts = Counter()

agency_problem_counts = Counter()

distinct_values = {
    "status": set(),
    "agency": set(),
    "complaint_type": set(),
    "descriptor": set(),
    "borough": set(),
    "incident_zip": set(),
    "location_type": set(),
    "open_data_channel_type": set(),
}

unique_key_arrays = []
resolution_arrays = []

invalid_created_count = 0
invalid_closed_count = 0

negative_resolution_count = 0

duration_over_30_days = 0
duration_over_90_days = 0
duration_over_180_days = 0
duration_over_365_days = 0


# ============================================================
# SOURCE FILES
# ============================================================

part_files = sorted(
    BRONZE_DIR.glob("part_*.json.gz")
)

if not part_files:
    raise RuntimeError(
        f"No Bronze part files found in {BRONZE_DIR}"
    )


print("\n" + "=" * 78)
print("NYC 311 BRONZE LOCAL PROFILING")
print("=" * 78)

print(f"Files found:    {len(part_files)}")
print(f"Expected rows:  {expected_rows:,}")


# ============================================================
# PROCESS EACH BRONZE PART
# ============================================================

for file_number, file_path in enumerate(
    part_files,
    start=1,
):

    print(
        f"\n[{file_number:02d}/{len(part_files):02d}] "
        f"Profiling {file_path.name}"
    )

    df = pd.read_json(
        file_path,
        lines=True,
        compression="gzip",
        dtype=False,
    )

    rows = len(df)
    total_rows += rows

    print(
        f"Rows: {rows:,} "
        f"| cumulative: {total_rows:,}"
    )

    # --------------------------------------------------------
    # NULL COUNTS + EXAMPLES
    # --------------------------------------------------------

    for field in IMPORTANT_FIELDS:

        if field not in df.columns:
            null_counts[field] += rows
            continue

        series = df[field]

        null_counts[field] += int(
            series.isna().sum()
        )

        if field not in examples:

            non_null = series.dropna()

            if not non_null.empty:
                examples[field] = str(
                    non_null.iloc[0]
                )

    # --------------------------------------------------------
    # UNIQUE KEY
    # --------------------------------------------------------

    if "unique_key" in df.columns:

        keys = pd.to_numeric(
            df["unique_key"],
            errors="coerce",
        )

        valid_keys = keys.dropna().astype(
            "int64"
        )

        unique_key_arrays.append(
            valid_keys.to_numpy()
        )

    # --------------------------------------------------------
    # DISTRIBUTIONS
    # --------------------------------------------------------

    def update_counter(
        field: str,
        counter: Counter,
    ) -> None:

        if field not in df.columns:
            return

        values = (
            df[field]
            .fillna("<NULL>")
            .astype(str)
        )

        counter.update(
            values.value_counts().to_dict()
        )


    update_counter(
        "status",
        status_counts,
    )

    update_counter(
        "agency",
        agency_counts,
    )

    update_counter(
        "complaint_type",
        complaint_counts,
    )

    update_counter(
        "borough",
        borough_counts,
    )

    update_counter(
        "open_data_channel_type",
        channel_counts,
    )

    # --------------------------------------------------------
    # DISTINCT VALUES
    # --------------------------------------------------------

    for field in distinct_values:

        if field not in df.columns:
            continue

        values = (
            df[field]
            .dropna()
            .astype(str)
            .unique()
        )

        distinct_values[field].update(
            values
        )

    # --------------------------------------------------------
    # AGENCY × SERVICE PROBLEM
    # --------------------------------------------------------

    if (
        "agency" in df.columns
        and
        "complaint_type" in df.columns
    ):

        combo = (
            df[
                [
                    "agency",
                    "complaint_type",
                ]
            ]
            .fillna("<NULL>")
            .value_counts()
        )

        for key, count in combo.items():
            agency_problem_counts[
                tuple(key)
            ] += int(count)

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    if "created_date" in df.columns:

        created = pd.to_datetime(
            df["created_date"],
            errors="coerce",
        )

        invalid_created_count += int(
            created.isna().sum()
            -
            df["created_date"].isna().sum()
        )

    else:
        created = pd.Series(
            pd.NaT,
            index=df.index,
        )


    if "closed_date" in df.columns:

        closed = pd.to_datetime(
            df["closed_date"],
            errors="coerce",
        )

        invalid_closed_count += int(
            closed.isna().sum()
            -
            df["closed_date"].isna().sum()
        )

    else:
        closed = pd.Series(
            pd.NaT,
            index=df.index,
        )

    # --------------------------------------------------------
    # RESOLUTION DURATION
    # --------------------------------------------------------

    valid_duration = (
        created.notna()
        &
        closed.notna()
    )

    if valid_duration.any():

        resolution_hours = (
            (
                closed[valid_duration]
                -
                created[valid_duration]
            )
            .dt.total_seconds()
            /
            3600
        )

        negative_resolution_count += int(
            (resolution_hours < 0).sum()
        )

        duration_over_30_days += int(
            (
                resolution_hours
                >
                30 * 24
            ).sum()
        )

        duration_over_90_days += int(
            (
                resolution_hours
                >
                90 * 24
            ).sum()
        )

        duration_over_180_days += int(
            (
                resolution_hours
                >
                180 * 24
            ).sum()
        )

        duration_over_365_days += int(
            (
                resolution_hours
                >
                365 * 24
            ).sum()
        )

        resolution_arrays.append(
            resolution_hours.to_numpy(
                dtype="float64"
            )
        )


# ============================================================
# ROW COUNT VALIDATION
# ============================================================

print("\n" + "=" * 78)
print("1 — ROW COUNT VALIDATION")
print("=" * 78)

print(f"Manifest rows: {expected_rows:,}")
print(f"Scanned rows:  {total_rows:,}")
print(
    f"Count match:   "
    f"{total_rows == expected_rows}"
)


# ============================================================
# UNIQUE KEY VALIDATION
# ============================================================

print("\n" + "=" * 78)
print("2 — UNIQUE KEY VALIDATION")
print("=" * 78)

all_keys = np.concatenate(
    unique_key_arrays
)

key_rows = len(all_keys)

unique_keys, key_counts = np.unique(
    all_keys,
    return_counts=True,
)

duplicate_key_rows = int(
    key_counts[
        key_counts > 1
    ].sum()
)

duplicate_key_values = int(
    (key_counts > 1).sum()
)

missing_key_rows = (
    total_rows
    -
    key_rows
)

print(f"Rows with key:          {key_rows:,}")
print(f"Missing/invalid keys:   {missing_key_rows:,}")
print(f"Distinct keys:          {len(unique_keys):,}")
print(f"Duplicate key values:   {duplicate_key_values:,}")
print(f"Rows using dup keys:    {duplicate_key_rows:,}")


# ============================================================
# NULL PROFILE
# ============================================================

print("\n" + "=" * 78)
print("3 — IMPORTANT FIELD NULL PROFILE")
print("=" * 78)


field_profile_rows = []


for field in IMPORTANT_FIELDS:

    null_count = int(
        null_counts[field]
    )

    null_pct = (
        null_count
        /
        total_rows
        *
        100
    )

    field_profile_rows.append(
        {
            "field": field,
            "rows": total_rows,
            "null_count": null_count,
            "null_pct": round(
                null_pct,
                4,
            ),
            "example": examples.get(
                field
            ),
        }
    )

    print(
        f"{field:36s} "
        f"{null_count:>11,} "
        f"{null_pct:>8.2f}%"
    )


field_profile_df = pd.DataFrame(
    field_profile_rows
)

field_profile_path = (
    OUTPUT_DIR
    / "bronze_field_profile.csv"
)

field_profile_df.to_csv(
    field_profile_path,
    index=False,
)


# ============================================================
# STATUS PROFILE
# ============================================================

print("\n" + "=" * 78)
print("4 — STATUS DISTRIBUTION")
print("=" * 78)

for value, count in (
    status_counts.most_common()
):

    print(
        f"{value:25s} "
        f"{count:>12,} "
        f"{count / total_rows * 100:>7.2f}%"
    )


# ============================================================
# RESOLUTION DURATION PROFILE
# ============================================================

print("\n" + "=" * 78)
print("5 — RAW RESOLUTION DURATION PROFILE")
print("=" * 78)


all_resolution_hours = np.concatenate(
    resolution_arrays
)


valid_nonnegative = all_resolution_hours[
    all_resolution_hours >= 0
]


quantiles = {
    "p25_hours":
        np.percentile(
            valid_nonnegative,
            25,
        ),

    "median_hours":
        np.percentile(
            valid_nonnegative,
            50,
        ),

    "p75_hours":
        np.percentile(
            valid_nonnegative,
            75,
        ),

    "p90_hours":
        np.percentile(
            valid_nonnegative,
            90,
        ),

    "p95_hours":
        np.percentile(
            valid_nonnegative,
            95,
        ),

    "p99_hours":
        np.percentile(
            valid_nonnegative,
            99,
        ),
}


print(
    f"Rows with created + closed: "
    f"{len(all_resolution_hours):,}"
)

print(
    f"Negative duration rows:     "
    f"{negative_resolution_count:,}"
)


for label, value in quantiles.items():

    print(
        f"{label:20s}: "
        f"{value:,.2f}"
    )


print(
    f"\n> 30 days:  "
    f"{duration_over_30_days:,}"
)

print(
    f"> 90 days:  "
    f"{duration_over_90_days:,}"
)

print(
    f"> 180 days: "
    f"{duration_over_180_days:,}"
)

print(
    f"> 365 days: "
    f"{duration_over_365_days:,}"
)


# ============================================================
# DISTINCT COUNTS
# ============================================================

print("\n" + "=" * 78)
print("6 — CARDINALITY")
print("=" * 78)


for field, values in distinct_values.items():

    print(
        f"{field:30s}: "
        f"{len(values):,}"
    )


# ============================================================
# TOP AGENCIES
# ============================================================

print("\n" + "=" * 78)
print("7 — TOP 15 AGENCIES")
print("=" * 78)


for value, count in agency_counts.most_common(
    15
):

    print(
        f"{value:10s} "
        f"{count:>12,}"
    )


# ============================================================
# TOP SERVICE PROBLEMS
# ============================================================

print("\n" + "=" * 78)
print("8 — TOP 20 SERVICE PROBLEMS")
print("=" * 78)


for value, count in complaint_counts.most_common(
    20
):

    print(
        f"{count:>12,} "
        f"{value}"
    )


# ============================================================
# BOROUGH DISTRIBUTION
# ============================================================

print("\n" + "=" * 78)
print("9 — BOROUGH DISTRIBUTION")
print("=" * 78)


for value, count in borough_counts.most_common():

    print(
        f"{value:20s} "
        f"{count:>12,}"
    )


# ============================================================
# CHANNEL DISTRIBUTION
# ============================================================

print("\n" + "=" * 78)
print("10 — REQUEST CHANNEL")
print("=" * 78)


for value, count in channel_counts.most_common():

    print(
        f"{value:20s} "
        f"{count:>12,}"
    )


# ============================================================
# AGENCY × SERVICE PROBLEM
# ============================================================

agency_problem_df = pd.DataFrame(
    [
        {
            "agency": agency,
            "complaint_type": problem,
            "request_count": count,
        }
        for (
            agency,
            problem
        ), count
        in agency_problem_counts.items()
    ]
).sort_values(
    "request_count",
    ascending=False,
)


agency_problem_path = (
    OUTPUT_DIR
    / "agency_problem_volume.csv"
)

agency_problem_df.to_csv(
    agency_problem_path,
    index=False,
)


# ============================================================
# SAVE PROFILE SUMMARY
# ============================================================

profile_summary = {

    "row_validation": {
        "manifest_rows":
            expected_rows,

        "scanned_rows":
            total_rows,

        "row_count_match":
            total_rows
            ==
            expected_rows,
    },

    "unique_key": {
        "rows_with_key":
            key_rows,

        "missing_or_invalid_key_rows":
            missing_key_rows,

        "distinct_keys":
            int(len(unique_keys)),

        "duplicate_key_values":
            duplicate_key_values,

        "rows_using_duplicate_keys":
            duplicate_key_rows,
    },

    "timestamp_quality": {
        "invalid_created_date":
            invalid_created_count,

        "invalid_closed_date":
            invalid_closed_count,

        "negative_resolution_duration":
            negative_resolution_count,
    },

    "resolution_duration": {
        **{
            key: round(
                float(value),
                4,
            )
            for key, value
            in quantiles.items()
        },

        "over_30_days":
            duration_over_30_days,

        "over_90_days":
            duration_over_90_days,

        "over_180_days":
            duration_over_180_days,

        "over_365_days":
            duration_over_365_days,
    },

    "cardinality": {
        field: len(values)
        for field, values
        in distinct_values.items()
    },

    "status_counts":
        dict(status_counts),

    "borough_counts":
        dict(borough_counts),

    "channel_counts":
        dict(channel_counts),
}


summary_path = (
    OUTPUT_DIR
    / "bronze_profile_summary.json"
)


with summary_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        profile_summary,
        f,
        indent=2,
        ensure_ascii=False,
    )


print("\n" + "=" * 78)
print("BRONZE PROFILING COMPLETE")
print("=" * 78)

print(f"Saved → {field_profile_path}")
print(f"Saved → {agency_problem_path}")
print(f"Saved → {summary_path}")