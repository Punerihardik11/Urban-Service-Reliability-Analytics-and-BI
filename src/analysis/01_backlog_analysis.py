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

# Locked Day 1 reconciliation values.
EXPECTED_TOTAL = 2_644_153
EXPECTED_CLOSED = 2_457_717
EXPECTED_BACKLOG = 186_436


# =============================================================================
# HELPERS
# =============================================================================

def resolve_column(
    available_columns: list[str],
    candidates: list[str],
    logical_name: str,
) -> str:
    """
    Resolve a logical field against possible Silver naming conventions.
    """
    for candidate in candidates:
        if candidate in available_columns:
            return candidate

    raise KeyError(
        f"Could not resolve '{logical_name}'. "
        f"Tried: {candidates}\n"
        f"Available columns:\n{available_columns}"
    )


def safe_label(series: pd.Series, unknown_label: str = "Unknown") -> pd.Series:
    """
    Normalize null/blank labels without changing legitimate category values.
    """
    result = series.astype("string").str.strip()
    result = result.fillna(unknown_label)
    result = result.mask(result.eq(""), unknown_label)
    return result


def percentile(series: pd.Series, q: float) -> float:
    values = series.dropna()

    if values.empty:
        return np.nan

    return float(values.quantile(q))


def print_section(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


# =============================================================================
# DISCOVER SILVER
# =============================================================================

parts = sorted(SILVER_DIR.glob("part_*.parquet"))

if not parts:
    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n{SILVER_DIR}"
    )

first_schema = pq.ParquetFile(parts[0]).schema_arrow
available_columns = first_schema.names

STATUS_COL = resolve_column(
    available_columns,
    ["status"],
    "status",
)

AGE_COL = resolve_column(
    available_columns,
    ["request_age_days"],
    "request age",
)

SERVICE_COL = resolve_column(
    available_columns,
    ["service_problem", "complaint_type"],
    "service problem",
)

print_section("URBAN SERVICE RELIABILITY — DAY 2 BACKLOG ANALYSIS")

print(f"Silver directory:        {SILVER_DIR}")
print(f"Silver parts:            {len(parts)}")
print()
print("Resolved columns:")
print(f"  Status:                {STATUS_COL}")
print(f"  Request age:           {AGE_COL}")
print(f"  Service problem:       {SERVICE_COL}")


# =============================================================================
# SCAN SILVER
#
# We deliberately do not concatenate all 2.64M rows.
#
# Full dataset:
#   only aggregate service counts.
#
# Backlog:
#   retain the ~186k unresolved rows for detailed age analysis.
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0

service_request_counts: Counter = Counter()

backlog_frames: list[pd.DataFrame] = []

for i, part in enumerate(parts, start=1):
    print(f"[{i:02d}/{len(parts):02d}] {part.name}")

    df = pd.read_parquet(
        part,
        columns=[
            STATUS_COL,
            AGE_COL,
            SERVICE_COL,
        ],
        engine="pyarrow",
    )

    total_rows += len(df)

    status = safe_label(df[STATUS_COL])
    service = safe_label(df[SERVICE_COL])

    # -------------------------------------------------------------------------
    # LOCKED BUSINESS RULE:
    #
    # Current request state comes from Status.
    # Backlog = current Status is NOT Closed.
    #
    # Closed Date is NOT used here.
    # -------------------------------------------------------------------------

    is_closed = status.str.casefold().eq("closed")

    part_closed = int(is_closed.sum())
    part_backlog = int((~is_closed).sum())

    closed_rows += part_closed
    backlog_rows += part_backlog

    # Total demand by service.
    service_request_counts.update(service.value_counts().to_dict())

    # Keep only backlog records for detailed analysis.
    backlog_part = pd.DataFrame(
        {
            "status": status.loc[~is_closed].values,
            "service_problem": service.loc[~is_closed].values,
            "backlog_age_days": pd.to_numeric(
                df.loc[~is_closed, AGE_COL],
                errors="coerce",
            ).values,
        }
    )

    backlog_frames.append(backlog_part)


# =============================================================================
# RECONCILIATION
# =============================================================================

print_section("1 — DAY 1 RECONCILIATION")

print(f"Total Silver rows:       {total_rows:,}")
print(f"Closed requests:         {closed_rows:,}")
print(f"Current backlog:         {backlog_rows:,}")
print(f"Backlog rate:            {backlog_rows / total_rows * 100:.2f}%")
print()

row_reconciliation = closed_rows + backlog_rows == total_rows

expected_total_match = total_rows == EXPECTED_TOTAL
expected_closed_match = closed_rows == EXPECTED_CLOSED
expected_backlog_match = backlog_rows == EXPECTED_BACKLOG

print(f"Closed + Backlog = Total: {'PASS' if row_reconciliation else 'FAIL'}")
print(f"Day 1 total match:        {'PASS' if expected_total_match else 'FAIL'}")
print(f"Day 1 closed match:       {'PASS' if expected_closed_match else 'FAIL'}")
print(f"Day 1 backlog match:      {'PASS' if expected_backlog_match else 'FAIL'}")

if not (
    row_reconciliation
    and expected_total_match
    and expected_closed_match
    and expected_backlog_match
):
    raise RuntimeError(
        "\nDAY 2 STOPPED.\n"
        "Backlog reconciliation does not match the locked Day 1 state.\n"
        "Do not continue analysis until the discrepancy is understood."
    )


# =============================================================================
# BUILD BACKLOG DATASET
# =============================================================================

backlog = pd.concat(backlog_frames, ignore_index=True)

valid_age_mask = (
    backlog["backlog_age_days"].notna()
    & backlog["backlog_age_days"].ge(0)
)

invalid_age_count = int((~valid_age_mask).sum())


# =============================================================================
# AGE COHORTS
# =============================================================================

cohort_labels = [
    "<1 day",
    "1-3 days",
    "3-7 days",
    "7-14 days",
    "14-30 days",
    "30-60 days",
    "60-90 days",
    "90-180 days",
    "180+ days",
]

cohort_bins = [
    0,
    1,
    3,
    7,
    14,
    30,
    60,
    90,
    180,
    np.inf,
]

backlog["age_cohort"] = "Invalid/Unknown"

backlog.loc[valid_age_mask, "age_cohort"] = pd.cut(
    backlog.loc[valid_age_mask, "backlog_age_days"],
    bins=cohort_bins,
    labels=cohort_labels,
    right=False,
    include_lowest=True,
).astype("string")


# =============================================================================
# CITY-WIDE AGE COHORT TABLE
# =============================================================================

cohort_order = cohort_labels + ["Invalid/Unknown"]

cohort_rows = []

for cohort in cohort_order:
    subset = backlog.loc[backlog["age_cohort"].eq(cohort)]

    count = len(subset)

    ages = subset.loc[
        subset["backlog_age_days"].notna()
        & subset["backlog_age_days"].ge(0),
        "backlog_age_days",
    ]

    cohort_rows.append(
        {
            "age_cohort": cohort,
            "backlog_requests": count,
            "share_of_backlog_pct": (
                count / backlog_rows * 100 if backlog_rows else np.nan
            ),
            "median_age_days": (
                ages.median() if not ages.empty else np.nan
            ),
            "p75_age_days": (
                ages.quantile(0.75) if not ages.empty else np.nan
            ),
            "p90_age_days": (
                ages.quantile(0.90) if not ages.empty else np.nan
            ),
        }
    )

backlog_age_cohorts = pd.DataFrame(cohort_rows)

backlog_age_cohorts["cumulative_share_pct"] = (
    backlog_age_cohorts["share_of_backlog_pct"].cumsum()
)


# =============================================================================
# STATUS COMPOSITION
# =============================================================================

status_rows = []

for status_name, group in backlog.groupby("status", dropna=False):
    ages = group["backlog_age_days"]
    valid_ages = ages[ages.notna() & ages.ge(0)]

    status_rows.append(
        {
            "status": status_name,
            "backlog_requests": len(group),
            "share_of_backlog_pct": len(group) / backlog_rows * 100,
            "median_backlog_age_days": (
                valid_ages.median() if not valid_ages.empty else np.nan
            ),
            "p75_backlog_age_days": percentile(valid_ages, 0.75),
            "p90_backlog_age_days": percentile(valid_ages, 0.90),
            "backlog_30d_plus": int((valid_ages >= 30).sum()),
            "backlog_60d_plus": int((valid_ages >= 60).sum()),
            "backlog_90d_plus": int((valid_ages >= 90).sum()),
            "backlog_180d_plus": int((valid_ages >= 180).sum()),
        }
    )

backlog_by_status = (
    pd.DataFrame(status_rows)
    .sort_values("backlog_requests", ascending=False)
    .reset_index(drop=True)
)


# =============================================================================
# SERVICE-LEVEL BACKLOG
# =============================================================================

total_by_service = pd.DataFrame(
    [
        {
            "service_problem": service,
            "request_count": count,
        }
        for service, count in service_request_counts.items()
    ]
)

service_rows = []

for service_name, group in backlog.groupby(
    "service_problem",
    dropna=False,
):
    ages = group["backlog_age_days"]
    valid_ages = ages[ages.notna() & ages.ge(0)]

    backlog_count = len(group)

    backlog_30d = int((valid_ages >= 30).sum())
    backlog_60d = int((valid_ages >= 60).sum())
    backlog_90d = int((valid_ages >= 90).sum())
    backlog_180d = int((valid_ages >= 180).sum())

    service_rows.append(
        {
            "service_problem": service_name,
            "backlog_count": backlog_count,
            "valid_backlog_age_count": len(valid_ages),
            "median_backlog_age_days": (
                valid_ages.median() if not valid_ages.empty else np.nan
            ),
            "p75_backlog_age_days": percentile(valid_ages, 0.75),
            "p90_backlog_age_days": percentile(valid_ages, 0.90),
            "backlog_30d_plus": backlog_30d,
            "backlog_60d_plus": backlog_60d,
            "backlog_90d_plus": backlog_90d,
            "backlog_180d_plus": backlog_180d,
            "old_backlog_share_60d_plus_pct": (
                backlog_60d / backlog_count * 100
                if backlog_count
                else np.nan
            ),
        }
    )

backlog_service = pd.DataFrame(service_rows)

backlog_by_service = total_by_service.merge(
    backlog_service,
    on="service_problem",
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
    backlog_by_service[col] = backlog_by_service[col].fillna(0).astype(int)

backlog_by_service["backlog_rate_pct"] = (
    backlog_by_service["backlog_count"]
    / backlog_by_service["request_count"]
    * 100
)

backlog_by_service["share_of_city_backlog_pct"] = (
    backlog_by_service["backlog_count"]
    / backlog_rows
    * 100
)

backlog_by_service = backlog_by_service[
    [
        "service_problem",
        "request_count",
        "backlog_count",
        "backlog_rate_pct",
        "share_of_city_backlog_pct",
        "valid_backlog_age_count",
        "median_backlog_age_days",
        "p75_backlog_age_days",
        "p90_backlog_age_days",
        "backlog_30d_plus",
        "backlog_60d_plus",
        "backlog_90d_plus",
        "backlog_180d_plus",
        "old_backlog_share_60d_plus_pct",
    ]
].sort_values(
    ["backlog_count", "request_count"],
    ascending=[False, False],
).reset_index(drop=True)


# =============================================================================
# CITY-WIDE AGE KPIs
# =============================================================================

valid_city_ages = backlog.loc[
    valid_age_mask,
    "backlog_age_days",
]

median_age = valid_city_ages.median()
p75_age = valid_city_ages.quantile(0.75)
p90_age = valid_city_ages.quantile(0.90)

city_30d = int((valid_city_ages >= 30).sum())
city_60d = int((valid_city_ages >= 60).sum())
city_90d = int((valid_city_ages >= 90).sum())
city_180d = int((valid_city_ages >= 180).sum())


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

backlog_age_cohorts.to_csv(
    OUTPUT_DIR / "backlog_age_cohorts.csv",
    index=False,
)

backlog_by_service.to_csv(
    OUTPUT_DIR / "backlog_by_service.csv",
    index=False,
)

backlog_by_status.to_csv(
    OUTPUT_DIR / "backlog_by_status.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

print_section("2 — CITY-WIDE BACKLOG AGE")

print(f"Backlog requests:              {backlog_rows:,}")
print(f"Valid backlog ages:            {len(valid_city_ages):,}")
print(f"Invalid/unknown ages:          {invalid_age_count:,}")
print()
print(f"Median backlog age:            {median_age:,.2f} days")
print(f"P75 backlog age:               {p75_age:,.2f} days")
print(f"P90 backlog age:               {p90_age:,.2f} days")
print()
print(f"Backlog 30+ days:              {city_30d:,} ({city_30d / backlog_rows * 100:.2f}%)")
print(f"Backlog 60+ days:              {city_60d:,} ({city_60d / backlog_rows * 100:.2f}%)")
print(f"Backlog 90+ days:              {city_90d:,} ({city_90d / backlog_rows * 100:.2f}%)")
print(f"Backlog 180+ days:             {city_180d:,} ({city_180d / backlog_rows * 100:.2f}%)")

print()
print(backlog_age_cohorts.to_string(index=False))


print_section("3 — BACKLOG BY CURRENT STATUS")

print(
    backlog_by_status[
        [
            "status",
            "backlog_requests",
            "share_of_backlog_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ].to_string(index=False)
)


print_section("4 — LARGEST SERVICE BACKLOGS")

print(
    backlog_by_service[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ]
    .head(20)
    .to_string(index=False)
)


print_section("5 — LARGEST 60+ DAY BACKLOGS")

old_backlog_rank = (
    backlog_by_service.loc[
        backlog_by_service["backlog_60d_plus"] > 0
    ]
    .sort_values(
        ["backlog_60d_plus", "backlog_count"],
        ascending=False,
    )
    .head(20)
)

print(
    old_backlog_rank[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ].to_string(index=False)
)


print_section("6 — HIGHEST BACKLOG RATE — MATERIAL SERVICES")

# This is only a diagnostic ranking.
# It prevents tiny categories from dominating a rate-only comparison.
material = backlog_by_service.loc[
    backlog_by_service["request_count"] >= 1_000
].copy()

material = material.sort_values(
    ["backlog_rate_pct", "backlog_count"],
    ascending=False,
).head(20)

print(
    material[
        [
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
        ]
    ].to_string(index=False)
)


# =============================================================================
# SUMMARY FILE
# =============================================================================

summary_lines = [
    "URBAN SERVICE RELIABILITY — DAY 2 BACKLOG ANALYSIS",
    "=" * 72,
    "",
    "Backlog age source: Silver request_age_days",
    "",
    "RECONCILIATION",
    f"Total Silver rows:       {total_rows:,}",
    f"Closed requests:         {closed_rows:,}",
    f"Current backlog:         {backlog_rows:,}",
    f"Backlog rate:            {backlog_rows / total_rows * 100:.2f}%",
    f"Reconciliation:          {'PASS' if row_reconciliation else 'FAIL'}",
    "",
    "CITY-WIDE BACKLOG AGE",
    f"Valid backlog ages:      {len(valid_city_ages):,}",
    f"Invalid/unknown ages:    {invalid_age_count:,}",
    f"Median age:              {median_age:.2f} days",
    f"P75 age:                 {p75_age:.2f} days",
    f"P90 age:                 {p90_age:.2f} days",
    "",
    f"30+ day backlog:         {city_30d:,} ({city_30d / backlog_rows * 100:.2f}%)",
    f"60+ day backlog:         {city_60d:,} ({city_60d / backlog_rows * 100:.2f}%)",
    f"90+ day backlog:         {city_90d:,} ({city_90d / backlog_rows * 100:.2f}%)",
    f"180+ day backlog:        {city_180d:,} ({city_180d / backlog_rows * 100:.2f}%)",
    "",
    "Locked business rule:",
    "Backlog = current Status is not Closed.",
    "Closed Date is not independently used to determine current closure state.",
    "",
]

summary_path = OUTPUT_DIR / "backlog_analysis_summary.txt"
summary_path.write_text(
    "\n".join(summary_lines),
    encoding="utf-8",
)


print_section("DAY 2 — STEP 1A COMPLETE")

print(f"Outputs written to:")
print(f"  {OUTPUT_DIR / 'backlog_age_cohorts.csv'}")
print(f"  {OUTPUT_DIR / 'backlog_by_service.csv'}")
print(f"  {OUTPUT_DIR / 'backlog_by_status.csv'}")
print(f"  {OUTPUT_DIR / 'backlog_analysis_summary.txt'}")
print()
print("BACKLOG ANALYSIS PASSED")