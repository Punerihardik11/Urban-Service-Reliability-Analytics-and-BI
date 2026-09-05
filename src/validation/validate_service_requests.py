from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "validation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# BUSINESS CONSTANTS
# ============================================================

VALID_STATUSES = {
    "Closed",
    "Open",
    "In Progress",
    "Assigned",
    "Pending",
    "Started",
    "Unspecified",
}

VALID_BOROUGHS = {
    "BROOKLYN",
    "QUEENS",
    "BRONX",
    "MANHATTAN",
    "STATEN ISLAND",
    "Unspecified",
}

UNRESOLVED_STATUSES = {
    "Open",
    "In Progress",
    "Assigned",
    "Pending",
    "Started",
    "Unspecified",
}


# Broad NYC bounding box.
#
# IMPORTANT:
# Outside this range means "needs investigation",
# not automatically invalid.
NYC_LAT_MIN = 40.45
NYC_LAT_MAX = 40.95

NYC_LON_MIN = -74.30
NYC_LON_MAX = -73.65


# Fixed analytical snapshot.
#
# Our dataset excludes Aug 30 because it was incomplete.
SNAPSHOT_TS = pd.Timestamp(
    "2026-08-30 00:00:00"
)


# ============================================================
# HELPERS
# ============================================================

def normalize_label(value) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.casefold()


def save_frames(
    frames: list[pd.DataFrame],
    filename: str,
) -> None:

    if not frames:
        return

    output = pd.concat(
        frames,
        ignore_index=True,
    )

    output.to_parquet(
        OUTPUT_DIR / filename,
        index=False,
    )


# ============================================================
# INPUT FILES
# ============================================================

part_files = sorted(
    BRONZE_DIR.glob("part_*.json.gz")
)

if not part_files:
    raise RuntimeError(
        "No Bronze files found."
    )


# ============================================================
# ACCUMULATORS
# ============================================================

total_rows = 0

status_closed_matrix = Counter()

invalid_status_counts = Counter()
unexpected_borough_counts = Counter()

due_date_by_agency = Counter()

problem_agencies = defaultdict(set)

problem_normalization = defaultdict(set)
descriptor_normalization = defaultdict(set)

negative_duration_frames = []
closed_without_date_frames = []
nonclosed_with_date_frames = []
extreme_duration_frames = []
outside_geo_frames = []
zip_issue_frames = []

zero_duration_count = 0
zero_duration_samples = []

missing_both_coordinates = 0
partial_coordinate_rows = 0
outside_nyc_bbox_count = 0

invalid_zip_count = 0

fingerprint_arrays = []


# Fields used only for anomaly exports.
ANOMALY_FIELDS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "status",
    "borough",
    "incident_zip",
    "incident_address",
    "latitude",
    "longitude",
    "resolution_description",
]


# ============================================================
# PASS 1
# ============================================================

print("\n" + "=" * 78)
print("NYC 311 SERVICE REQUEST QUALITY AUDIT")
print("=" * 78)

print(f"Bronze files: {len(part_files)}")


for file_number, file_path in enumerate(
    part_files,
    start=1,
):

    print(
        f"\n[{file_number:02d}/{len(part_files):02d}] "
        f"{file_path.name}"
    )

    df = pd.read_json(
        file_path,
        lines=True,
        compression="gzip",
        dtype=False,
    )

    total_rows += len(df)

    # --------------------------------------------------------
    # DATETIME PARSING
    # --------------------------------------------------------

    created = pd.to_datetime(
        df.get("created_date"),
        errors="coerce",
    )

    closed = pd.to_datetime(
        df.get("closed_date"),
        errors="coerce",
    )

    status = (
        df["status"]
        .fillna("<NULL>")
        .astype(str)
    )

    # --------------------------------------------------------
    # STATUS × CLOSED DATE
    # --------------------------------------------------------

    closed_present = closed.notna()

    for (
        status_value,
        has_closed_date
    ), count in (
        pd.DataFrame(
            {
                "status": status,
                "has_closed_date": closed_present,
            }
        )
        .value_counts()
        .items()
    ):

        status_closed_matrix[
            (
                str(status_value),
                bool(has_closed_date),
            )
        ] += int(count)

    # --------------------------------------------------------
    # UNEXPECTED STATUS
    # --------------------------------------------------------

    invalid_status = (
        ~status.isin(VALID_STATUSES)
    )

    if invalid_status.any():

        invalid_status_counts.update(
            status[
                invalid_status
            ]
            .value_counts()
            .to_dict()
        )

    # --------------------------------------------------------
    # CLOSED WITHOUT CLOSED DATE
    # --------------------------------------------------------

    mask = (
        status.eq("Closed")
        &
        closed.isna()
    )

    if mask.any():

        closed_without_date_frames.append(
            df.loc[
                mask,
                [
                    c
                    for c in ANOMALY_FIELDS
                    if c in df.columns
                ],
            ].copy()
        )

    # --------------------------------------------------------
    # NON-CLOSED WITH CLOSED DATE
    # --------------------------------------------------------

    mask = (
        ~status.eq("Closed")
        &
        closed.notna()
    )

    if mask.any():

        nonclosed_with_date_frames.append(
            df.loc[
                mask,
                [
                    c
                    for c in ANOMALY_FIELDS
                    if c in df.columns
                ],
            ].copy()
        )

    # --------------------------------------------------------
    # RESOLUTION DURATION
    # --------------------------------------------------------

    valid_duration = (
        created.notna()
        &
        closed.notna()
    )

    resolution_hours = pd.Series(
        np.nan,
        index=df.index,
    )

    resolution_hours.loc[
        valid_duration
    ] = (
        (
            closed[valid_duration]
            -
            created[valid_duration]
        )
        .dt.total_seconds()
        /
        3600
    )

    negative_mask = (
        resolution_hours < 0
    )

    if negative_mask.any():

        anomaly = df.loc[
            negative_mask,
            [
                c
                for c in ANOMALY_FIELDS
                if c in df.columns
            ],
        ].copy()

        anomaly["resolution_hours"] = (
            resolution_hours[
                negative_mask
            ].values
        )

        negative_duration_frames.append(
            anomaly
        )

    # Zero-duration does not automatically mean error.
    zero_mask = (
        resolution_hours == 0
    )

    zero_duration_count += int(
        zero_mask.sum()
    )

    if (
        zero_mask.any()
        and
        sum(
            len(x)
            for x in zero_duration_samples
        ) < 500
    ):

        sample = df.loc[
            zero_mask,
            [
                c
                for c in ANOMALY_FIELDS
                if c in df.columns
            ],
        ].head(100)

        zero_duration_samples.append(
            sample
        )

    # Very long duration:
    # audit, don't delete.
    extreme_mask = (
        resolution_hours
        >
        180 * 24
    )

    if extreme_mask.any():

        anomaly = df.loc[
            extreme_mask,
            [
                c
                for c in ANOMALY_FIELDS
                if c in df.columns
            ],
        ].copy()

        anomaly["resolution_days"] = (
            resolution_hours[
                extreme_mask
            ].values
            /
            24
        )

        extreme_duration_frames.append(
            anomaly
        )

    # --------------------------------------------------------
    # REQUEST AGE FOR UNRESOLVED REQUESTS
    # --------------------------------------------------------

    unresolved_mask = status.isin(
        UNRESOLVED_STATUSES
    )

    # We don't save these yet.
    # This is simply validating that the snapshot calculation
    # will be possible later.
    request_age_days = (
        (
            SNAPSHOT_TS
            -
            created
        )
        .dt.total_seconds()
        /
        86400
    )

    # --------------------------------------------------------
    # BOROUGH
    # --------------------------------------------------------

    borough = (
        df["borough"]
        .fillna("<NULL>")
        .astype(str)
    )

    unexpected_borough = (
        ~borough.isin(
            VALID_BOROUGHS
        )
    )

    if unexpected_borough.any():

        unexpected_borough_counts.update(
            borough[
                unexpected_borough
            ]
            .value_counts()
            .to_dict()
        )

    # --------------------------------------------------------
    # ZIP FORMAT
    # --------------------------------------------------------

    if "incident_zip" in df.columns:

        zip_series = (
            df["incident_zip"]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\.0$",
                "",
                regex=True,
            )
        )

        zip_present = (
            zip_series.notna()
        )

        valid_zip_format = (
            zip_series
            .str.match(
                r"^\d{5}$",
                na=False,
            )
        )

        bad_zip = (
            zip_present
            &
            ~valid_zip_format
        )

        invalid_zip_count += int(
            bad_zip.sum()
        )

        if bad_zip.any():

            zip_issue_frames.append(
                df.loc[
                    bad_zip,
                    [
                        c
                        for c in ANOMALY_FIELDS
                        if c in df.columns
                    ],
                ].copy()
            )

    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

    latitude = pd.to_numeric(
        df.get("latitude"),
        errors="coerce",
    )

    longitude = pd.to_numeric(
        df.get("longitude"),
        errors="coerce",
    )

    both_missing = (
        latitude.isna()
        &
        longitude.isna()
    )

    partial_coordinates = (
        latitude.isna()
        ^
        longitude.isna()
    )

    missing_both_coordinates += int(
        both_missing.sum()
    )

    partial_coordinate_rows += int(
        partial_coordinates.sum()
    )

    coordinates_present = (
        latitude.notna()
        &
        longitude.notna()
    )

    outside_bbox = (
        coordinates_present
        &
        (
            (latitude < NYC_LAT_MIN)
            |
            (latitude > NYC_LAT_MAX)
            |
            (longitude < NYC_LON_MIN)
            |
            (longitude > NYC_LON_MAX)
        )
    )

    outside_nyc_bbox_count += int(
        outside_bbox.sum()
    )

    if outside_bbox.any():

        outside_geo_frames.append(
            df.loc[
                outside_bbox,
                [
                    c
                    for c in ANOMALY_FIELDS
                    if c in df.columns
                ],
            ].copy()
        )

    # --------------------------------------------------------
    # DUE DATE BY AGENCY
    # --------------------------------------------------------

    if (
        "due_date" in df.columns
        and
        "agency" in df.columns
    ):

        due_present = (
            df["due_date"].notna()
        )

        if due_present.any():

            due_date_by_agency.update(
                df.loc[
                    due_present,
                    "agency",
                ]
                .fillna("<NULL>")
                .astype(str)
                .value_counts()
                .to_dict()
            )

    # --------------------------------------------------------
    # AGENCY × SERVICE RELATIONSHIP
    # --------------------------------------------------------

    for problem, agency in zip(
        df["complaint_type"],
        df["agency"],
    ):

        if (
            pd.notna(problem)
            and
            pd.notna(agency)
        ):

            problem_agencies[
                str(problem)
            ].add(
                str(agency)
            )

    # --------------------------------------------------------
    # LABEL NORMALIZATION COLLISIONS
    # --------------------------------------------------------

    for raw_value in (
        df["complaint_type"]
        .dropna()
        .unique()
    ):

        normalized = normalize_label(
            raw_value
        )

        if normalized:

            problem_normalization[
                normalized
            ].add(
                str(raw_value)
            )

    if "descriptor" in df.columns:

        for raw_value in (
            df["descriptor"]
            .dropna()
            .unique()
        ):

            normalized = normalize_label(
                raw_value
            )

            if normalized:

                descriptor_normalization[
                    normalized
                ].add(
                    str(raw_value)
                )

    # --------------------------------------------------------
    # DUPLICATE-LOOKING FINGERPRINT
    # --------------------------------------------------------
    #
    # This is NOT treated as proof of duplication.
    #
    # It identifies distinct Unique Keys that are otherwise
    # identical across a conservative service-request fingerprint.

    fingerprint_fields = [
        "created_date",
        "agency",
        "complaint_type",
        "descriptor",
        "incident_zip",
        "incident_address",
        "latitude",
        "longitude",
    ]

    available_fingerprint_fields = [
        field
        for field in fingerprint_fields
        if field in df.columns
    ]

    fingerprint_df = (
        df[
            available_fingerprint_fields
        ]
        .copy()
        .fillna("<NULL>")
        .astype(str)
    )

    hashes = pd.util.hash_pandas_object(
        fingerprint_df,
        index=False,
    ).to_numpy(
        dtype="uint64"
    )

    fingerprint_arrays.append(
        hashes
    )


# ============================================================
# DUPLICATE-LOOKING HASH CHECK
# ============================================================

print("\n" + "=" * 78)
print("1 — DUPLICATE-LOOKING REQUEST CHECK")
print("=" * 78)

all_hashes = np.concatenate(
    fingerprint_arrays
)

unique_hashes, hash_counts = np.unique(
    all_hashes,
    return_counts=True,
)

duplicate_hash_mask = (
    hash_counts > 1
)

duplicate_fingerprint_values = int(
    duplicate_hash_mask.sum()
)

rows_in_duplicate_fingerprints = int(
    hash_counts[
        duplicate_hash_mask
    ].sum()
)

print(
    f"Repeated request fingerprints: "
    f"{duplicate_fingerprint_values:,}"
)

print(
    f"Rows in repeated fingerprints: "
    f"{rows_in_duplicate_fingerprints:,}"
)

print(
    "\nThese are audit candidates, NOT confirmed duplicate requests."
)


# ============================================================
# LIFECYCLE MATRIX
# ============================================================

print("\n" + "=" * 78)
print("2 — STATUS × CLOSED DATE")
print("=" * 78)


lifecycle_rows = []

for (
    status_value,
    has_closed_date
), count in sorted(
    status_closed_matrix.items()
):

    lifecycle_rows.append(
        {
            "status": status_value,
            "has_closed_date":
                has_closed_date,
            "row_count":
                count,
        }
    )

    print(
        f"{status_value:20s} "
        f"closed_date={str(has_closed_date):5s} "
        f"{count:>12,}"
    )


lifecycle_df = pd.DataFrame(
    lifecycle_rows
)

lifecycle_df.to_csv(
    OUTPUT_DIR
    / "status_closed_date_matrix.csv",
    index=False,
)


# ============================================================
# CATEGORY NORMALIZATION COLLISIONS
# ============================================================

problem_collisions = [
    {
        "normalized_value":
            normalized,

        "raw_values":
            " | ".join(
                sorted(values)
            ),

        "raw_value_count":
            len(values),
    }

    for normalized, values
    in problem_normalization.items()

    if len(values) > 1
]


descriptor_collisions = [
    {
        "normalized_value":
            normalized,

        "raw_values":
            " | ".join(
                sorted(values)
            ),

        "raw_value_count":
            len(values),
    }

    for normalized, values
    in descriptor_normalization.items()

    if len(values) > 1
]


pd.DataFrame(
    problem_collisions
).to_csv(
    OUTPUT_DIR
    / "complaint_type_normalization_collisions.csv",
    index=False,
)


pd.DataFrame(
    descriptor_collisions
).to_csv(
    OUTPUT_DIR
    / "descriptor_normalization_collisions.csv",
    index=False,
)


# ============================================================
# AGENCY × PROBLEM RELATIONSHIPS
# ============================================================

problem_agency_rows = []

for problem, agencies in (
    problem_agencies.items()
):

    problem_agency_rows.append(
        {
            "complaint_type":
                problem,

            "agency_count":
                len(agencies),

            "agencies":
                " | ".join(
                    sorted(agencies)
                ),
        }
    )


problem_agency_df = (
    pd.DataFrame(
        problem_agency_rows
    )
    .sort_values(
        [
            "agency_count",
            "complaint_type",
        ],
        ascending=[
            False,
            True,
        ],
    )
)


problem_agency_df.to_csv(
    OUTPUT_DIR
    / "complaint_type_agency_relationships.csv",
    index=False,
)


# ============================================================
# SAVE ROW-LEVEL ANOMALIES
# ============================================================

save_frames(
    negative_duration_frames,
    "negative_resolution_duration.parquet",
)

save_frames(
    closed_without_date_frames,
    "closed_without_closed_date.parquet",
)

save_frames(
    nonclosed_with_date_frames,
    "nonclosed_with_closed_date.parquet",
)

save_frames(
    extreme_duration_frames,
    "resolution_over_180_days.parquet",
)

save_frames(
    outside_geo_frames,
    "outside_nyc_bbox.parquet",
)

save_frames(
    zip_issue_frames,
    "invalid_zip_format.parquet",
)

save_frames(
    zero_duration_samples,
    "zero_duration_sample.parquet",
)


# ============================================================
# SUMMARY
# ============================================================

closed_without_date_count = (
    status_closed_matrix[
        (
            "Closed",
            False,
        )
    ]
)


nonclosed_with_date_count = sum(
    count

    for (
        status_value,
        has_closed_date
    ), count

    in status_closed_matrix.items()

    if (
        status_value != "Closed"
        and
        has_closed_date
    )
)


summary = {

    "total_rows":
        total_rows,

    "lifecycle": {
        "closed_without_closed_date":
            int(
                closed_without_date_count
            ),

        "nonclosed_with_closed_date":
            int(
                nonclosed_with_date_count
            ),

        "unexpected_status_rows":
            int(
                sum(
                    invalid_status_counts.values()
                )
            ),
    },

    "geography": {
        "unexpected_borough_rows":
            int(
                sum(
                    unexpected_borough_counts.values()
                )
            ),

        "missing_both_coordinates":
            int(
                missing_both_coordinates
            ),

        "partial_coordinate_rows":
            int(
                partial_coordinate_rows
            ),

        "outside_broad_nyc_bbox":
            int(
                outside_nyc_bbox_count
            ),

        "invalid_zip_format":
            int(
                invalid_zip_count
            ),
    },

    "duration": {
        "zero_duration_rows":
            int(
                zero_duration_count
            ),
    },

    "due_date": {
        "population_by_agency":
            dict(
                due_date_by_agency
            ),
    },

    "category_consistency": {
        "complaint_type_normalization_collisions":
            len(
                problem_collisions
            ),

        "descriptor_normalization_collisions":
            len(
                descriptor_collisions
            ),
    },

    "duplicate_looking_requests": {
        "repeated_fingerprint_values":
            duplicate_fingerprint_values,

        "rows_in_repeated_fingerprints":
            rows_in_duplicate_fingerprints,

        "important_note":
            (
                "Fingerprint repetition is an audit signal "
                "and is not proof of duplicate service requests."
            ),
    },
}


summary_path = (
    OUTPUT_DIR
    / "validation_summary.json"
)


with summary_path.open(
    "w",
    encoding="utf-8",
) as f:

    json.dump(
        summary,
        f,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 78)
print("3 — QUALITY AUDIT SUMMARY")
print("=" * 78)

print(
    f"Total rows:                     "
    f"{total_rows:,}"
)

print(
    f"Closed without closed_date:     "
    f"{closed_without_date_count:,}"
)

print(
    f"Non-Closed with closed_date:    "
    f"{nonclosed_with_date_count:,}"
)

print(
    f"Unexpected status rows:         "
    f"{sum(invalid_status_counts.values()):,}"
)

print(
    f"Unexpected borough rows:        "
    f"{sum(unexpected_borough_counts.values()):,}"
)

print(
    f"Missing both coordinates:       "
    f"{missing_both_coordinates:,}"
)

print(
    f"Partial coordinate pairs:       "
    f"{partial_coordinate_rows:,}"
)

print(
    f"Outside broad NYC bbox:         "
    f"{outside_nyc_bbox_count:,}"
)

print(
    f"Invalid ZIP formats:            "
    f"{invalid_zip_count:,}"
)

print(
    f"Zero-duration closures:         "
    f"{zero_duration_count:,}"
)

print(
    f"Complaint normalization clashes:"
    f" {len(problem_collisions):,}"
)

print(
    f"Descriptor normalization clashes:"
    f" {len(descriptor_collisions):,}"
)

print(
    f"Repeated request fingerprints:  "
    f"{duplicate_fingerprint_values:,}"
)

print(
    f"Rows in repeated fingerprints:  "
    f"{rows_in_duplicate_fingerprints:,}"
)

print("\nDue Date population by agency:")

for agency, count in (
    due_date_by_agency.most_common()
):

    print(
        f"  {agency:10s} "
        f"{count:>10,}"
    )


print("\n" + "=" * 78)
print("QUALITY AUDIT COMPLETE")
print("=" * 78)

print(f"Saved → {summary_path}")