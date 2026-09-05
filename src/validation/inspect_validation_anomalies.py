from __future__ import annotations

from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALIDATION_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "validation"
)

OUTPUT_DIR = (
    VALIDATION_DIR
    / "inspection"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

def load_parquet(filename: str) -> pd.DataFrame:

    path = VALIDATION_DIR / filename

    if not path.exists():
        print(f"\nWARNING: Missing {filename}")
        return pd.DataFrame()

    return pd.read_parquet(path)


def section(title: str) -> None:

    print("\n" + "=" * 82)
    print(title)
    print("=" * 82)


def print_top(
    df: pd.DataFrame,
    columns: list[str],
    n: int = 20,
) -> pd.DataFrame:

    available = [
        col
        for col in columns
        if col in df.columns
    ]

    if not available or df.empty:
        return pd.DataFrame()

    result = (
        df
        .groupby(
            available,
            dropna=False,
        )
        .size()
        .reset_index(
            name="row_count"
        )
        .sort_values(
            "row_count",
            ascending=False,
        )
    )

    print(
        result.head(n).to_string(
            index=False
        )
    )

    return result


# ============================================================
# 1 — NON-CLOSED REQUESTS WITH CLOSED DATE
# ============================================================

section(
    "1 — NON-CLOSED REQUESTS WITH CLOSED DATE"
)

nonclosed = load_parquet(
    "nonclosed_with_closed_date.parquet"
)

print(
    f"Rows: {len(nonclosed):,}"
)


if not nonclosed.empty:

    print("\nBy current status:")

    status_summary = print_top(
        nonclosed,
        ["status"],
    )

    print("\nBy current status + agency:")

    status_agency_summary = print_top(
        nonclosed,
        [
            "status",
            "agency",
        ],
        30,
    )

    print(
        "\nBy current status + service problem:"
    )

    status_problem_summary = print_top(
        nonclosed,
        [
            "status",
            "complaint_type",
        ],
        30,
    )

    print(
        "\nTop agency × service combinations:"
    )

    lifecycle_combo_summary = print_top(
        nonclosed,
        [
            "agency",
            "complaint_type",
            "status",
        ],
        40,
    )


    print("\nExample records:")

    sample_columns = [
        "unique_key",
        "created_date",
        "closed_date",
        "status",
        "agency",
        "complaint_type",
        "descriptor",
        "resolution_description",
    ]

    sample_columns = [
        c
        for c in sample_columns
        if c in nonclosed.columns
    ]

    print(
        nonclosed[
            sample_columns
        ]
        .head(25)
        .to_string(
            index=False
        )
    )


    status_summary.to_csv(
        OUTPUT_DIR
        / "nonclosed_status_summary.csv",
        index=False,
    )

    status_agency_summary.to_csv(
        OUTPUT_DIR
        / "nonclosed_status_agency_summary.csv",
        index=False,
    )

    lifecycle_combo_summary.to_csv(
        OUTPUT_DIR
        / "nonclosed_lifecycle_combinations.csv",
        index=False,
    )


# ============================================================
# 2 — CLOSED WITHOUT CLOSED DATE
# ============================================================

section(
    "2 — CLOSED REQUESTS WITHOUT CLOSED DATE"
)

closed_missing = load_parquet(
    "closed_without_closed_date.parquet"
)

print(
    f"Rows: {len(closed_missing):,}"
)

if not closed_missing.empty:

    print(
        closed_missing.to_string(
            index=False
        )
    )


# ============================================================
# 3 — NEGATIVE RESOLUTION DURATIONS
# ============================================================

section(
    "3 — NEGATIVE RESOLUTION DURATIONS"
)

negative = load_parquet(
    "negative_resolution_duration.parquet"
)

print(
    f"Rows: {len(negative):,}"
)


if not negative.empty:

    print("\nDuration statistics (hours):")

    print(
        negative[
            "resolution_hours"
        ]
        .describe(
            percentiles=[
                0.01,
                0.10,
                0.25,
                0.50,
                0.75,
                0.90,
                0.99,
            ]
        )
        .to_string()
    )


    print("\nBy agency:")

    negative_agency = print_top(
        negative,
        ["agency"],
    )


    print("\nBy service problem:")

    negative_problem = print_top(
        negative,
        ["complaint_type"],
        30,
    )


    print("\nMost negative cases:")

    negative_columns = [
        "unique_key",
        "created_date",
        "closed_date",
        "resolution_hours",
        "agency",
        "complaint_type",
        "descriptor",
        "status",
        "resolution_description",
    ]

    negative_columns = [
        c
        for c in negative_columns
        if c in negative.columns
    ]

    print(
        negative[
            negative_columns
        ]
        .sort_values(
            "resolution_hours"
        )
        .head(25)
        .to_string(
            index=False
        )
    )


    negative_agency.to_csv(
        OUTPUT_DIR
        / "negative_duration_by_agency.csv",
        index=False,
    )


# ============================================================
# 4 — ZERO-DURATION SAMPLE
# ============================================================

section(
    "4 — ZERO-DURATION CLOSURES — SAMPLE"
)

zero = load_parquet(
    "zero_duration_sample.parquet"
)

print(
    f"Sample rows loaded: {len(zero):,}"
)


if not zero.empty:

    print("\nSample distribution by agency/problem:")

    print_top(
        zero,
        [
            "agency",
            "complaint_type",
        ],
        30,
    )


    if "resolution_description" in zero.columns:

        print(
            "\nMost common resolution descriptions "
            "inside the sample:"
        )

        descriptions = (
            zero[
                "resolution_description"
            ]
            .fillna("<NULL>")
            .astype(str)
            .value_counts()
            .head(20)
        )

        print(
            descriptions.to_string()
        )


# ============================================================
# 5 — EXTREME RESOLUTION DURATIONS
# ============================================================

section(
    "5 — RESOLUTION DURATIONS OVER 180 DAYS"
)

extreme = load_parquet(
    "resolution_over_180_days.parquet"
)

print(
    f"Rows: {len(extreme):,}"
)


if not extreme.empty:

    print("\nBy agency:")

    extreme_agency = print_top(
        extreme,
        ["agency"],
    )


    print("\nBy service problem:")

    extreme_problem = print_top(
        extreme,
        ["complaint_type"],
        30,
    )


    print("\nLongest 20 cases:")

    extreme_columns = [
        "unique_key",
        "created_date",
        "closed_date",
        "resolution_days",
        "agency",
        "complaint_type",
        "descriptor",
        "resolution_description",
    ]

    extreme_columns = [
        c
        for c in extreme_columns
        if c in extreme.columns
    ]

    print(
        extreme[
            extreme_columns
        ]
        .sort_values(
            "resolution_days",
            ascending=False,
        )
        .head(20)
        .to_string(
            index=False
        )
    )


# ============================================================
# 6 — GEOGRAPHIC EDGE CASES
# ============================================================

section(
    "6 — GEOGRAPHIC EDGE CASES"
)

outside_geo = load_parquet(
    "outside_nyc_bbox.parquet"
)

invalid_zip = load_parquet(
    "invalid_zip_format.parquet"
)


print(
    f"Outside broad NYC bounding box: "
    f"{len(outside_geo):,}"
)

print(
    f"Invalid ZIP format rows: "
    f"{len(invalid_zip):,}"
)


if not invalid_zip.empty:

    print("\nInvalid ZIP rows:")

    print(
        invalid_zip.to_string(
            index=False
        )
    )


# ============================================================
# 7 — CATEGORY NAMING COLLISIONS
# ============================================================

section(
    "7 — CATEGORY NORMALIZATION COLLISIONS"
)


problem_collision_path = (
    VALIDATION_DIR
    / "complaint_type_normalization_collisions.csv"
)

descriptor_collision_path = (
    VALIDATION_DIR
    / "descriptor_normalization_collisions.csv"
)


if problem_collision_path.exists():

    problem_collision = pd.read_csv(
        problem_collision_path
    )

    print("\nComplaint Type:")

    if problem_collision.empty:
        print("None")

    else:
        print(
            problem_collision.to_string(
                index=False
            )
        )


if descriptor_collision_path.exists():

    descriptor_collision = pd.read_csv(
        descriptor_collision_path
    )

    print("\nDescriptor:")

    if descriptor_collision.empty:
        print("None")

    else:
        print(
            descriptor_collision.to_string(
                index=False
            )
        )


# ============================================================
# COMPLETE
# ============================================================

section(
    "ANOMALY INSPECTION COMPLETE"
)

print(
    f"Inspection summaries saved → {OUTPUT_DIR}"
)