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
EXPECTED_BACKLOG = 186_436

# Diagnostic thresholds only.
# These are NOT SLA or performance thresholds.
MATERIAL_ZIP_REQUESTS = 1_000
MATERIAL_SERVICE_ZIP_REQUESTS = 200


# =============================================================================
# HELPERS
# =============================================================================

def resolve_column(
    columns: list[str],
    candidates: list[str],
    label: str,
) -> str:

    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise KeyError(
        f"Could not resolve '{label}'. "
        f"Tried {candidates}.\n"
        f"Available columns:\n{columns}"
    )


def safe_label(
    series: pd.Series,
    unknown: str = "Unknown",
) -> pd.Series:

    result = series.astype("string").str.strip()

    result = result.fillna(unknown)

    return result.mask(
        result.eq(""),
        unknown,
    )


def pct(
    numerator,
    denominator,
):

    return np.where(
        denominator > 0,
        numerator / denominator * 100,
        np.nan,
    )


def section(title: str) -> None:

    print()
    print("=" * 118)
    print(title)
    print("=" * 118)


def backlog_metric_rows(
    backlog: pd.DataFrame,
    keys: list[str],
) -> pd.DataFrame:

    rows = []

    if len(keys) == 1:
        grouper = keys[0]
    else:
        grouper = keys

    for group_key, group in backlog.groupby(
        grouper,
        dropna=False,
    ):

        if len(keys) == 1:
            group_key = (group_key,)

        ages = group.loc[
            group["backlog_age_days"].notna()
            & group["backlog_age_days"].ge(0),
            "backlog_age_days",
        ]

        backlog_count = len(group)

        backlog_30d = int(
            (ages >= 30).sum()
        )

        backlog_60d = int(
            (ages >= 60).sum()
        )

        backlog_90d = int(
            (ages >= 90).sum()
        )

        backlog_180d = int(
            (ages >= 180).sum()
        )

        row = dict(
            zip(
                keys,
                group_key,
            )
        )

        row.update(
            {
                "backlog_count":
                    backlog_count,

                "valid_backlog_age_count":
                    len(ages),

                "median_backlog_age_days":
                    (
                        float(ages.median())
                        if not ages.empty
                        else np.nan
                    ),

                "p75_backlog_age_days":
                    (
                        float(
                            ages.quantile(0.75)
                        )
                        if not ages.empty
                        else np.nan
                    ),

                "p90_backlog_age_days":
                    (
                        float(
                            ages.quantile(0.90)
                        )
                        if not ages.empty
                        else np.nan
                    ),

                "backlog_30d_plus":
                    backlog_30d,

                "backlog_60d_plus":
                    backlog_60d,

                "backlog_90d_plus":
                    backlog_90d,

                "backlog_180d_plus":
                    backlog_180d,

                "old_backlog_share_60d_plus_pct":
                    (
                        backlog_60d
                        / backlog_count
                        * 100
                        if backlog_count
                        else np.nan
                    ),
            }
        )

        rows.append(row)

    return pd.DataFrame(rows)


def merge_profile(
    request_counts: pd.DataFrame,
    backlog_metrics: pd.DataFrame,
    keys: list[str],
) -> pd.DataFrame:

    result = request_counts.merge(
        backlog_metrics,
        on=keys,
        how="left",
    )

    count_columns = [
        "backlog_count",
        "valid_backlog_age_count",
        "backlog_30d_plus",
        "backlog_60d_plus",
        "backlog_90d_plus",
        "backlog_180d_plus",
    ]

    for col in count_columns:

        result[col] = (
            result[col]
            .fillna(0)
            .astype(int)
        )

    result["backlog_rate_pct"] = (
        result["backlog_count"]
        / result["request_count"]
        * 100
    )

    result["share_of_city_requests_pct"] = (
        result["request_count"]
        / EXPECTED_TOTAL
        * 100
    )

    result["share_of_city_backlog_pct"] = (
        result["backlog_count"]
        / EXPECTED_BACKLOG
        * 100
    )

    return result


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
    pq.ParquetFile(
        parts[0]
    )
    .schema_arrow
    .names
)


BOROUGH_COL = resolve_column(
    columns,
    ["borough"],
    "borough",
)


ZIP_COL = resolve_column(
    columns,
    [
        "incident_zip",
        "zip_code",
    ],
    "incident ZIP",
)


SERVICE_COL = resolve_column(
    columns,
    [
        "service_problem",
        "complaint_type",
    ],
    "service problem",
)


STATUS_COL = resolve_column(
    columns,
    ["status"],
    "status",
)


AGE_COL = resolve_column(
    columns,
    ["request_age_days"],
    "request age",
)


section(
    "URBAN SERVICE RELIABILITY - DAY 2 GEOGRAPHIC HOTSPOTS"
)


print(
    f"Silver directory:        "
    f"{SILVER_DIR}"
)

print(
    f"Silver parts:            "
    f"{len(parts)}"
)

print()

print(
    f"Borough column:          "
    f"{BOROUGH_COL}"
)

print(
    f"ZIP column:              "
    f"{ZIP_COL}"
)

print(
    f"Service column:          "
    f"{SERVICE_COL}"
)

print(
    f"Status column:           "
    f"{STATUS_COL}"
)

print(
    f"Request age column:      "
    f"{AGE_COL}"
)


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0

borough_counts = Counter()
zip_counts = Counter()
service_counts = Counter()
service_zip_counts = Counter()

backlog_parts = []


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
            BOROUGH_COL,
            ZIP_COL,
            SERVICE_COL,
            STATUS_COL,
            AGE_COL,
        ],
        engine="pyarrow",
    )

    total_rows += len(df)

    borough = safe_label(
        df[BOROUGH_COL]
    )

    incident_zip = safe_label(
        df[ZIP_COL]
    )

    service = safe_label(
        df[SERVICE_COL]
    )

    status = safe_label(
        df[STATUS_COL]
    )


    # -------------------------------------------------------------------------
    # LOCKED DAY 1 BUSINESS RULE
    #
    # Current request state comes from Status.
    # Backlog = Status is NOT Closed.
    # -------------------------------------------------------------------------

    is_closed = (
        status
        .str
        .casefold()
        .eq("closed")
    )

    is_backlog = ~is_closed


    closed_rows += int(
        is_closed.sum()
    )

    backlog_rows += int(
        is_backlog.sum()
    )


    # -------------------------------------------------------------------------
    # TOTAL DEMAND COUNTS
    # -------------------------------------------------------------------------

    borough_counts.update(
        borough
        .value_counts()
        .to_dict()
    )

    zip_counts.update(
        incident_zip
        .value_counts()
        .to_dict()
    )

    service_counts.update(
        service
        .value_counts()
        .to_dict()
    )


    service_zip_pairs = pd.DataFrame(
        {
            "service_problem":
                service,

            "incident_zip":
                incident_zip,
        }
    )

    service_zip_counts.update(
        service_zip_pairs
        .value_counts()
        .to_dict()
    )


    # -------------------------------------------------------------------------
    # BACKLOG ROWS
    # -------------------------------------------------------------------------

    backlog_part = pd.DataFrame(
        {
            "borough":
                borough
                .loc[is_backlog]
                .values,

            "incident_zip":
                incident_zip
                .loc[is_backlog]
                .values,

            "service_problem":
                service
                .loc[is_backlog]
                .values,

            "backlog_age_days":
                pd.to_numeric(
                    df.loc[
                        is_backlog,
                        AGE_COL,
                    ],
                    errors="coerce",
                )
                .values,
        }
    )

    backlog_parts.append(
        backlog_part
    )


# =============================================================================
# RECONCILIATION
# =============================================================================

section(
    "1 - RECONCILIATION"
)


checks = {

    "Closed + Backlog = Total":
        closed_rows
        + backlog_rows
        == total_rows,

    "Day 1 total match":
        total_rows
        == EXPECTED_TOTAL,

    "Day 1 closed match":
        closed_rows
        == EXPECTED_CLOSED,

    "Day 1 backlog match":
        backlog_rows
        == EXPECTED_BACKLOG,

    "Borough request sum":
        sum(
            borough_counts.values()
        )
        == total_rows,

    "ZIP request sum":
        sum(
            zip_counts.values()
        )
        == total_rows,

    "Service x ZIP request sum":
        sum(
            service_zip_counts.values()
        )
        == total_rows,
}


print(
    f"Total Silver rows:       "
    f"{total_rows:,}"
)

print(
    f"Closed requests:         "
    f"{closed_rows:,}"
)

print(
    f"Current backlog:         "
    f"{backlog_rows:,}"
)

print(
    f"Backlog rate:            "
    f"{backlog_rows / total_rows * 100:.2f}%"
)

print()


for label, passed in checks.items():

    print(
        f"{label:<30} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    checks.values()
):

    raise RuntimeError(
        "\nDAY 2 STEP 3 STOPPED.\n"
        "Geographic analysis does not reconcile "
        "with the locked Day 1 state."
    )


backlog = pd.concat(
    backlog_parts,
    ignore_index=True,
)


valid_age = (
    backlog["backlog_age_days"].notna()
    & backlog["backlog_age_days"].ge(0)
)


print()

print(
    f"Valid backlog ages:      "
    f"{int(valid_age.sum()):,}"
)

print(
    f"Invalid backlog ages:    "
    f"{int((~valid_age).sum()):,}"
)


if len(backlog) != EXPECTED_BACKLOG:

    raise RuntimeError(
        "Backlog DataFrame count "
        "does not match Day 1."
    )


# =============================================================================
# BUILD REQUEST COUNT TABLES
# =============================================================================

borough_requests = pd.DataFrame(
    [
        {
            "borough":
                key,

            "request_count":
                value,
        }

        for key, value
        in borough_counts.items()
    ]
)


zip_requests = pd.DataFrame(
    [
        {
            "incident_zip":
                key,

            "request_count":
                value,
        }

        for key, value
        in zip_counts.items()
    ]
)


service_requests = pd.DataFrame(
    [
        {
            "service_problem":
                key,

            "service_request_count":
                value,
        }

        for key, value
        in service_counts.items()
    ]
)


service_zip_requests = pd.DataFrame(
    [
        {
            "service_problem":
                service_name,

            "incident_zip":
                zip_name,

            "request_count":
                value,
        }

        for (
            service_name,
            zip_name,
        ), value
        in service_zip_counts.items()
    ]
)


# =============================================================================
# BOROUGH PROFILE
# =============================================================================

borough_profile = merge_profile(
    borough_requests,
    backlog_metric_rows(
        backlog,
        ["borough"],
    ),
    ["borough"],
)


borough_profile = (
    borough_profile
    .sort_values(
        "request_count",
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# ZIP PROFILE
# =============================================================================

zip_profile = merge_profile(
    zip_requests,
    backlog_metric_rows(
        backlog,
        ["incident_zip"],
    ),
    ["incident_zip"],
)


# Preserve every ZIP value.
#
# Only valid 5-digit ZIP values will be used
# for geographic hotspot rankings.

zip_profile[
    "zip_is_valid_5_digit"
] = (
    zip_profile["incident_zip"]
    .astype("string")
    .str
    .fullmatch(
        r"\d{5}",
        na=False,
    )
)


zip_profile = (
    zip_profile
    .sort_values(
        "request_count",
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# SERVICE x ZIP PROFILE
# =============================================================================

service_zip_profile = merge_profile(
    service_zip_requests,
    backlog_metric_rows(
        backlog,
        [
            "service_problem",
            "incident_zip",
        ],
    ),
    [
        "service_problem",
        "incident_zip",
    ],
)


service_backlog = (
    backlog
    .groupby(
        "service_problem"
    )
    .size()
    .reset_index(
        name="service_backlog_count"
    )
)


service_context = (
    service_requests
    .merge(
        service_backlog,
        on="service_problem",
        how="left",
    )
)


service_context[
    "service_backlog_count"
] = (
    service_context[
        "service_backlog_count"
    ]
    .fillna(0)
    .astype(int)
)


zip_context = (
    zip_profile[
        [
            "incident_zip",
            "request_count",
            "backlog_count",
        ]
    ]
    .rename(
        columns={
            "request_count":
                "zip_request_count",

            "backlog_count":
                "zip_backlog_count",
        }
    )
)


service_zip_profile = (
    service_zip_profile
    .merge(
        service_context,
        on="service_problem",
        how="left",
    )
    .merge(
        zip_context,
        on="incident_zip",
        how="left",
    )
)


service_zip_profile[
    "share_of_service_demand_pct"
] = (
    service_zip_profile[
        "request_count"
    ]
    / service_zip_profile[
        "service_request_count"
    ]
    * 100
)


service_zip_profile[
    "share_of_service_backlog_pct"
] = pct(
    service_zip_profile[
        "backlog_count"
    ],
    service_zip_profile[
        "service_backlog_count"
    ],
)


service_zip_profile[
    "share_of_zip_demand_pct"
] = (
    service_zip_profile[
        "request_count"
    ]
    / service_zip_profile[
        "zip_request_count"
    ]
    * 100
)


service_zip_profile[
    "share_of_zip_backlog_pct"
] = pct(
    service_zip_profile[
        "backlog_count"
    ],
    service_zip_profile[
        "zip_backlog_count"
    ],
)


service_zip_profile[
    "zip_is_valid_5_digit"
] = (
    service_zip_profile[
        "incident_zip"
    ]
    .astype("string")
    .str
    .fullmatch(
        r"\d{5}",
        na=False,
    )
)


service_zip_profile = (
    service_zip_profile
    .sort_values(
        [
            "backlog_count",
            "request_count",
        ],
        ascending=False,
    )
    .reset_index(
        drop=True
    )
)


# =============================================================================
# ZIP QUALITY
# =============================================================================

valid_zip_rows = (
    zip_profile.loc[
        zip_profile[
            "zip_is_valid_5_digit"
        ]
    ]
)


other_zip_rows = (
    zip_profile.loc[
        ~zip_profile[
            "zip_is_valid_5_digit"
        ]
    ]
)


zip_quality = pd.DataFrame(
    [
        {
            "category":
                "Valid 5-digit ZIP",

            "distinct_zip_values":
                len(valid_zip_rows),

            "request_count":
                int(
                    valid_zip_rows[
                        "request_count"
                    ].sum()
                ),

            "backlog_count":
                int(
                    valid_zip_rows[
                        "backlog_count"
                    ].sum()
                ),
        },

        {
            "category":
                "Unknown / invalid ZIP format",

            "distinct_zip_values":
                len(other_zip_rows),

            "request_count":
                int(
                    other_zip_rows[
                        "request_count"
                    ].sum()
                ),

            "backlog_count":
                int(
                    other_zip_rows[
                        "backlog_count"
                    ].sum()
                ),
        },
    ]
)


zip_quality[
    "share_of_requests_pct"
] = (
    zip_quality[
        "request_count"
    ]
    / total_rows
    * 100
)


zip_quality[
    "share_of_backlog_pct"
] = (
    zip_quality[
        "backlog_count"
    ]
    / backlog_rows
    * 100
)


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

borough_profile.to_csv(
    OUTPUT_DIR
    / "geography_borough_profile.csv",
    index=False,
)


zip_profile.to_csv(
    OUTPUT_DIR
    / "geography_zip_profile.csv",
    index=False,
)


service_zip_profile.to_csv(
    OUTPUT_DIR
    / "geography_service_zip_profile.csv",
    index=False,
)


zip_quality.to_csv(
    OUTPUT_DIR
    / "geography_zip_quality_summary.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

section(
    "2 - BOROUGH PROFILE"
)


print(
    borough_profile[
        [
            "borough",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "3 - HIGHEST REQUEST-VOLUME ZIP CODES"
)


top_request_zips = (
    zip_profile
    .loc[
        zip_profile[
            "zip_is_valid_5_digit"
        ]
    ]
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(25)
)


print(
    top_request_zips[
        [
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "4 - LARGEST ZIP BACKLOGS"
)


top_backlog_zips = (
    zip_profile
    .loc[
        zip_profile[
            "zip_is_valid_5_digit"
        ]
        & zip_profile[
            "backlog_count"
        ].gt(0)
    ]
    .sort_values(
        "backlog_count",
        ascending=False,
    )
    .head(25)
)


print(
    top_backlog_zips[
        [
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "5 - HIGHEST BACKLOG RATE - MATERIAL ZIP CODES"
)


material_zips = (
    zip_profile
    .loc[
        zip_profile[
            "zip_is_valid_5_digit"
        ]
        & zip_profile[
            "request_count"
        ].ge(
            MATERIAL_ZIP_REQUESTS
        )
        & zip_profile[
            "backlog_count"
        ].gt(0)
    ]
    .sort_values(
        [
            "backlog_rate_pct",
            "backlog_count",
        ],
        ascending=False,
    )
    .head(25)
)


print(
    material_zips[
        [
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "6 - LARGEST 60+ DAY ZIP BACKLOGS"
)


old_zip_backlog = (
    zip_profile
    .loc[
        zip_profile[
            "zip_is_valid_5_digit"
        ]
        & zip_profile[
            "backlog_60d_plus"
        ].gt(0)
    ]
    .sort_values(
        [
            "backlog_60d_plus",
            "backlog_count",
        ],
        ascending=False,
    )
    .head(25)
)


print(
    old_zip_backlog[
        [
            "incident_zip",
            "backlog_count",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "7 - HIGHEST SERVICE x ZIP REQUEST CONCENTRATIONS"
)


top_service_zip_demand = (
    service_zip_profile
    .loc[
        service_zip_profile[
            "zip_is_valid_5_digit"
        ]
    ]
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(30)
)


print(
    top_service_zip_demand[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "share_of_service_demand_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "8 - LARGEST SERVICE x ZIP BACKLOG HOTSPOTS"
)


top_service_zip_backlog = (
    service_zip_profile
    .loc[
        service_zip_profile[
            "zip_is_valid_5_digit"
        ]
        & service_zip_profile[
            "backlog_count"
        ].gt(0)
    ]
    .sort_values(
        [
            "backlog_count",
            "backlog_60d_plus",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    top_service_zip_backlog[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "share_of_service_backlog_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "9 - HIGHEST BACKLOG RATE - MATERIAL SERVICE x ZIP"
)


material_service_zips = (
    service_zip_profile
    .loc[
        service_zip_profile[
            "zip_is_valid_5_digit"
        ]
        & service_zip_profile[
            "request_count"
        ].ge(
            MATERIAL_SERVICE_ZIP_REQUESTS
        )
        & service_zip_profile[
            "backlog_count"
        ].gt(0)
    ]
    .sort_values(
        [
            "backlog_rate_pct",
            "backlog_count",
        ],
        ascending=False,
    )
    .head(30)
)


print(
    material_service_zips[
        [
            "service_problem",
            "incident_zip",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .to_string(
        index=False
    )
)


# =============================================================================

section(
    "10 - ZIP DATA QUALITY"
)


print(
    zip_quality
    .to_string(
        index=False
    )
)


if not other_zip_rows.empty:

    print()

    print(
        "Preserved unknown / invalid ZIP values:"
    )

    print(
        other_zip_rows[
            [
                "incident_zip",
                "request_count",
                "backlog_count",
            ]
        ]
        .sort_values(
            "request_count",
            ascending=False,
        )
        .to_string(
            index=False
        )
    )


# =============================================================================
# SUMMARY
# =============================================================================

summary_lines = [

    "URBAN SERVICE RELIABILITY - DAY 2 GEOGRAPHIC HOTSPOTS",

    "=" * 78,

    "",

    "RECONCILIATION",

    f"Total Silver rows:       "
    f"{total_rows:,}",

    f"Closed requests:         "
    f"{closed_rows:,}",

    f"Current backlog:         "
    f"{backlog_rows:,}",

    f"Backlog rate:            "
    f"{backlog_rows / total_rows * 100:.2f}%",

    f"Valid backlog ages:      "
    f"{int(valid_age.sum()):,}",

    f"Invalid backlog ages:    "
    f"{int((~valid_age).sum()):,}",

    "",

    "INTERPRETATION RULES",

    "- Raw ZIP counts measure request concentration, "
    "not population-adjusted burden.",

    "- Geographic hotspot does not by itself imply "
    "poor local service performance.",

    "- Unknown and invalid ZIP values are preserved.",

    "- Backlog volume, backlog rate and backlog age "
    "remain separate metrics.",

    "- No universal SLA is assumed.",
]


summary_path = (
    OUTPUT_DIR
    / "geographic_hotspots_summary.txt"
)


summary_path.write_text(
    "\n".join(
        summary_lines
    ),
    encoding="utf-8",
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "DAY 2 - STEP 3 ANALYSIS COMPLETE"
)


print(
    "Outputs written:"
)

print(
    OUTPUT_DIR
    / "geography_borough_profile.csv"
)

print(
    OUTPUT_DIR
    / "geography_zip_profile.csv"
)

print(
    OUTPUT_DIR
    / "geography_service_zip_profile.csv"
)

print(
    OUTPUT_DIR
    / "geography_zip_quality_summary.csv"
)

print(
    OUTPUT_DIR
    / "geographic_hotspots_summary.txt"
)

print()

print(
    "GEOGRAPHIC HOTSPOT ANALYSIS PASSED"
)