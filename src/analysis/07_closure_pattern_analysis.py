from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


# =============================================================================
# CONFIG
# =============================================================================

ROOT = Path(__file__).resolve().parents[2]

SILVER_DIR = ROOT / "data" / "silver" / "service_requests_2026_ytd"
OUTPUT_DIR = ROOT / "outputs" / "analysis" / "day2"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_TOTAL = 2_644_153
EXPECTED_CLOSED = 2_457_717
EXPECTED_VALID_RESOLUTION = 2_457_340

TARGET_SERVICES = [
    "Food Establishment",
    "Smoking or Vaping",
]

MIN_MATERIAL_VALID = 1_000


# =============================================================================
# HELPERS
# =============================================================================

def resolve(
    columns: list[str],
    candidates: list[str],
    label: str,
) -> str:

    for col in candidates:
        if col in columns:
            return col

    raise KeyError(
        f"Could not resolve '{label}'. "
        f"Tried {candidates}.\n"
        f"Available columns:\n{columns}"
    )


def clean_label(
    series: pd.Series,
) -> pd.Series:

    result = (
        series
        .astype("string")
        .str.strip()
        .fillna("Unknown")
    )

    return result.mask(
        result.eq(""),
        "Unknown",
    )


def section(
    title: str,
) -> None:

    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


# =============================================================================
# DISCOVER SILVER
# =============================================================================

parts = sorted(
    SILVER_DIR.glob("part_*.parquet")
)

if not parts:

    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n"
        f"{SILVER_DIR}"
    )


columns = (
    pq.ParquetFile(parts[0])
    .schema_arrow
    .names
)


SERVICE_COL = resolve(
    columns,
    [
        "service_problem",
        "complaint_type",
    ],
    "service problem",
)


STATUS_COL = resolve(
    columns,
    ["status"],
    "status",
)


CREATED_COL = resolve(
    columns,
    [
        "created_at",
        "created_date",
    ],
    "created timestamp",
)


VALID_RES_COL = resolve(
    columns,
    ["resolution_duration_valid"],
    "resolution duration valid",
)


RES_HOURS_COL = resolve(
    columns,
    ["resolution_hours"],
    "resolution hours",
)


section(
    "URBAN SERVICE RELIABILITY - DAY 2 ~60-DAY CLOSURE PATTERN"
)


print(
    f"Silver directory:             "
    f"{SILVER_DIR}"
)

print(
    f"Silver parts:                 "
    f"{len(parts)}"
)

print(
    f"Service column:               "
    f"{SERVICE_COL}"
)

print(
    f"Status column:                "
    f"{STATUS_COL}"
)

print(
    f"Created column:               "
    f"{CREATED_COL}"
)

print(
    f"Valid-resolution flag:        "
    f"{VALID_RES_COL}"
)

print(
    f"Resolution-hours column:      "
    f"{RES_HOURS_COL}"
)


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0
closed_rows = 0
valid_resolution_rows = 0

service_request_counts: Counter = Counter()

valid_parts: list[pd.DataFrame] = []


for i, part in enumerate(
    parts,
    start=1,
):

    print(
        f"[{i:02d}/{len(parts):02d}] "
        f"{part.name}"
    )


    df = pd.read_parquet(
        part,
        columns=[
            SERVICE_COL,
            STATUS_COL,
            CREATED_COL,
            VALID_RES_COL,
            RES_HOURS_COL,
        ],
        engine="pyarrow",
    )


    total_rows += len(df)


    service = clean_label(
        df[SERVICE_COL]
    )


    status = clean_label(
        df[STATUS_COL]
    )


    created = pd.to_datetime(
        df[CREATED_COL],
        errors="coerce",
    )


    resolution_hours = pd.to_numeric(
        df[RES_HOURS_COL],
        errors="coerce",
    )


    # -------------------------------------------------------------------------
    # EXACT DAY 1 VALID RESOLUTION RULE
    # -------------------------------------------------------------------------

    valid_mask = (
        df[VALID_RES_COL]
        .fillna(False)
        .astype(bool)
    )


    is_closed = (
        status
        .str
        .casefold()
        .eq("closed")
    )


    closed_rows += int(
        is_closed.sum()
    )


    valid_resolution_rows += int(
        valid_mask.sum()
    )


    service_request_counts.update(
        service
        .value_counts()
        .to_dict()
    )


    if valid_mask.any():

        valid_part = pd.DataFrame(
            {
                "service_problem":
                    service
                    .loc[valid_mask]
                    .values,

                "created_at":
                    created
                    .loc[valid_mask]
                    .values,

                "resolution_hours":
                    resolution_hours
                    .loc[valid_mask]
                    .values,
            }
        ).dropna(
            subset=[
                "created_at",
                "resolution_hours",
            ]
        )


        valid_parts.append(
            valid_part
        )


# =============================================================================
# RECONCILIATION
# =============================================================================

usable_valid_rows = sum(
    len(part)
    for part in valid_parts
)


section(
    "1 - RECONCILIATION"
)


checks = {

    "Day 1 total match":
        total_rows
        == EXPECTED_TOTAL,

    "Day 1 closed match":
        closed_rows
        == EXPECTED_CLOSED,

    "Day 1 valid-resolution flag match":
        valid_resolution_rows
        == EXPECTED_VALID_RESOLUTION,

    "Usable valid-resolution rows":
        usable_valid_rows
        == EXPECTED_VALID_RESOLUTION,
}


print(
    f"Total Silver rows:              "
    f"{total_rows:,}"
)

print(
    f"Status = Closed rows:           "
    f"{closed_rows:,}"
)

print(
    f"Valid-resolution flag rows:     "
    f"{valid_resolution_rows:,}"
)

print(
    f"Usable valid-resolution rows:   "
    f"{usable_valid_rows:,}"
)

print()


for label, passed in checks.items():

    print(
        f"{label:<38} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    checks.values()
):

    raise RuntimeError(
        "\nSTEP 7 STOPPED: "
        "valid-resolution population does not match "
        "the locked Day 1 Silver state."
    )


# =============================================================================
# BUILD VALID RESOLUTION DATASET
# =============================================================================

res = pd.concat(
    valid_parts,
    ignore_index=True,
)


res[
    "resolution_days"
] = (
    res[
        "resolution_hours"
    ]
    / 24
)


# =============================================================================
# TEST WINDOWS AROUND 60 DAYS
# =============================================================================

windows = {

    "55_65d":
        (55, 65),

    "59_61d":
        (59, 61),

    "59_5_60_5d":
        (59.5, 60.5),

    "59_9_60_1d":
        (59.9, 60.1),
}


for name, (
    low,
    high,
) in windows.items():

    res[
        f"in_{name}"
    ] = (
        res[
            "resolution_days"
        ]
        .between(
            low,
            high,
            inclusive="both",
        )
    )


# =============================================================================
# SERVICE PROFILE
# =============================================================================

agg_map = {

    "valid_resolution_count":
        (
            "resolution_days",
            "size",
        ),

    "median_resolution_days":
        (
            "resolution_days",
            "median",
        ),

    "p75_resolution_days":
        (
            "resolution_days",
            lambda s:
            s.quantile(0.75),
        ),

    "p90_resolution_days":
        (
            "resolution_days",
            lambda s:
            s.quantile(0.90),
        ),
}


for name in windows:

    agg_map[
        f"resolution_{name}_count"
    ] = (
        f"in_{name}",
        "sum",
    )


profile = (
    res
    .groupby(
        "service_problem"
    )
    .agg(
        **agg_map
    )
    .reset_index()
)


profile[
    "request_count"
] = (
    profile[
        "service_problem"
    ]
    .map(
        service_request_counts
    )
    .astype(int)
)


for name in windows:

    profile[
        f"resolution_{name}_share_pct"
    ] = (
        profile[
            f"resolution_{name}_count"
        ]
        / profile[
            "valid_resolution_count"
        ]
        * 100
    )


ordered_cols = [

    "service_problem",
    "request_count",
    "valid_resolution_count",
    "median_resolution_days",
    "p75_resolution_days",
    "p90_resolution_days",
]


for name in windows:

    ordered_cols.extend(
        [
            f"resolution_{name}_count",
            f"resolution_{name}_share_pct",
        ]
    )


profile = profile[
    ordered_cols
]


# =============================================================================
# TARGET SERVICES
# =============================================================================

target_profile = (
    profile.loc[
        profile[
            "service_problem"
        ]
        .isin(
            TARGET_SERVICES
        )
    ]
    .copy()
)


material = (
    profile.loc[
        profile[
            "valid_resolution_count"
        ]
        .ge(
            MIN_MATERIAL_VALID
        )
    ]
    .copy()
)


target = (
    res.loc[
        res[
            "service_problem"
        ]
        .isin(
            TARGET_SERVICES
        )
    ]
    .copy()
)


target[
    "rounded_resolution_day"
] = (
    target[
        "resolution_days"
    ]
    .round()
    .astype(int)
)


target[
    "created_month"
] = (
    target[
        "created_at"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


# =============================================================================
# TARGET DURATION BANDS
# =============================================================================

bins = [

    0,
    30,
    45,
    55,
    58,
    59,
    60,
    61,
    62,
    65,
    90,
    np.inf,
]


labels = [

    "<30d",
    "30-45d",
    "45-55d",
    "55-58d",
    "58-59d",
    "59-60d",
    "60-61d",
    "61-62d",
    "62-65d",
    "65-90d",
    "90+d",
]


target[
    "duration_band"
] = pd.cut(
    target[
        "resolution_days"
    ],
    bins=bins,
    labels=labels,
    right=False,
    include_lowest=True,
)


target_bands = (
    target
    .groupby(
        [
            "service_problem",
            "duration_band",
        ],
        observed=False,
    )
    .size()
    .reset_index(
        name="row_count"
    )
)


target_bands[
    "share_pct"
] = (
    target_bands[
        "row_count"
    ]
    / target_bands
    .groupby(
        "service_problem"
    )[
        "row_count"
    ]
    .transform(
        "sum"
    )
    * 100
)


# =============================================================================
# ROUNDED RESOLUTION DAYS
# =============================================================================

rounded_days = (
    target
    .groupby(
        [
            "service_problem",
            "rounded_resolution_day",
        ]
    )
    .size()
    .reset_index(
        name="row_count"
    )
)


rounded_days[
    "share_pct"
] = (
    rounded_days[
        "row_count"
    ]
    / rounded_days
    .groupby(
        "service_problem"
    )[
        "row_count"
    ]
    .transform(
        "sum"
    )
    * 100
)


# =============================================================================
# PATTERN BY CREATION MONTH
# =============================================================================

monthly = (
    target
    .groupby(
        [
            "service_problem",
            "created_month",
        ]
    )
    .agg(

        valid_resolution_count=(
            "resolution_days",
            "size",
        ),

        median_resolution_days=(
            "resolution_days",
            "median",
        ),

        p90_resolution_days=(
            "resolution_days",
            lambda s:
            s.quantile(0.90),
        ),

        share_59_61d_pct=(
            "resolution_days",
            lambda s:
            (
                s
                .between(
                    59,
                    61,
                    inclusive="both",
                )
                .mean()
                * 100
            ),
        ),
    )
    .reset_index()
)


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

profile.to_csv(
    OUTPUT_DIR
    / "closure_pattern_service_profile.csv",
    index=False,
)


target_profile.to_csv(
    OUTPUT_DIR
    / "closure_pattern_target_services.csv",
    index=False,
)


target_bands.to_csv(
    OUTPUT_DIR
    / "closure_pattern_target_duration_bands.csv",
    index=False,
)


rounded_days.to_csv(
    OUTPUT_DIR
    / "closure_pattern_target_rounded_days.csv",
    index=False,
)


monthly.to_csv(
    OUTPUT_DIR
    / "closure_pattern_target_created_month.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

section(
    "2 - TARGET SERVICES"
)


print(
    target_profile[
        [
            "service_problem",
            "request_count",
            "valid_resolution_count",
            "median_resolution_days",
            "p90_resolution_days",
            "resolution_55_65d_share_pct",
            "resolution_59_61d_share_pct",
            "resolution_59_5_60_5d_share_pct",
            "resolution_59_9_60_1d_share_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "3 - TARGET DURATION BANDS"
)


print(
    target_bands
    .to_string(
        index=False
    )
)


section(
    "4 - MOST COMMON ROUNDED DAYS - TARGET SERVICES"
)


top_rounded = (
    rounded_days
    .sort_values(
        [
            "service_problem",
            "row_count",
        ],
        ascending=[
            True,
            False,
        ],
    )
    .groupby(
        "service_problem",
        group_keys=False,
    )
    .head(12)
)


print(
    top_rounded
    .to_string(
        index=False
    )
)


section(
    "5 - MATERIAL SERVICES MOST CONCENTRATED AROUND 60 DAYS"
)


around_60 = (
    material
    .sort_values(
        [
            "resolution_59_61d_share_pct",
            "valid_resolution_count",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    around_60[
        [
            "service_problem",
            "valid_resolution_count",
            "median_resolution_days",
            "p90_resolution_days",
            "resolution_55_65d_share_pct",
            "resolution_59_61d_share_pct",
            "resolution_59_5_60_5d_share_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


section(
    "6 - TARGET PATTERN BY CREATION MONTH"
)


print(
    monthly
    .sort_values(
        [
            "service_problem",
            "created_month",
        ]
    )
    .to_string(
        index=False
    )
)


# =============================================================================
# SUMMARY
# =============================================================================

summary = [

    "URBAN SERVICE RELIABILITY - DAY 2 ~60-DAY CLOSURE PATTERN",

    "=" * 76,

    "",

    f"Total Silver rows:              "
    f"{total_rows:,}",

    f"Status = Closed rows:           "
    f"{closed_rows:,}",

    f"Valid-resolution flag rows:     "
    f"{valid_resolution_rows:,}",

    f"Usable valid-resolution rows:   "
    f"{usable_valid_rows:,}",

    "",

    "TARGET SERVICES",

    "- Food Establishment",

    "- Smoking or Vaping",

    "",

    "INTERPRETATION RULES",

    "- Uses Silver resolution_duration_valid exactly as Day 1.",

    "- Uses Silver resolution_hours exactly as Day 1.",

    "- Clustering around 60 days is a lifecycle pattern, "
    "not proof of an SLA.",

    "- Closure timing is not assumed to equal actual service fulfillment.",

    "- No causal explanation is assigned from the duration pattern alone.",
]


(
    OUTPUT_DIR
    / "closure_pattern_summary.txt"
).write_text(
    "\n".join(
        summary
    ),
    encoding="utf-8",
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "DAY 2 - STEP 7 ANALYSIS COMPLETE"
)


print(
    f"Outputs -> "
    f"{OUTPUT_DIR}"
)

print()

print(
    "~60-DAY CLOSURE PATTERN ANALYSIS PASSED"
)