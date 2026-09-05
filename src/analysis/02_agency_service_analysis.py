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


# =============================================================================
# HELPERS
# =============================================================================

def resolve_column(
    available_columns: list[str],
    candidates: list[str],
    logical_name: str,
) -> str:
    for candidate in candidates:
        if candidate in available_columns:
            return candidate

    raise KeyError(
        f"Could not resolve '{logical_name}'. "
        f"Tried: {candidates}\n"
        f"Available columns:\n{available_columns}"
    )


def safe_label(
    series: pd.Series,
    unknown_label: str = "Unknown",
) -> pd.Series:
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
    print("=" * 110)
    print(title)
    print("=" * 110)


# =============================================================================
# DISCOVER SILVER
# =============================================================================

parts = sorted(SILVER_DIR.glob("part_*.parquet"))

if not parts:
    raise FileNotFoundError(
        f"No Silver parquet parts found in:\n{SILVER_DIR}"
    )

available_columns = pq.ParquetFile(parts[0]).schema_arrow.names

AGENCY_COL = resolve_column(
    available_columns,
    ["agency"],
    "agency",
)

SERVICE_COL = resolve_column(
    available_columns,
    ["service_problem", "complaint_type"],
    "service problem",
)

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


print_section(
    "URBAN SERVICE RELIABILITY - DAY 2 AGENCY x SERVICE ANALYSIS"
)

print(f"Silver directory:        {SILVER_DIR}")
print(f"Silver parts:            {len(parts)}")
print()
print("Resolved columns:")
print(f"  Agency:                {AGENCY_COL}")
print(f"  Service problem:       {SERVICE_COL}")
print(f"  Status:                {STATUS_COL}")
print(f"  Request age:           {AGE_COL}")


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0
closed_rows = 0
backlog_rows = 0

agency_request_counts: Counter = Counter()
agency_service_request_counts: Counter = Counter()

backlog_frames: list[pd.DataFrame] = []


for i, part in enumerate(parts, start=1):
    print(f"[{i:02d}/{len(parts):02d}] {part.name}")

    df = pd.read_parquet(
        part,
        columns=[
            AGENCY_COL,
            SERVICE_COL,
            STATUS_COL,
            AGE_COL,
        ],
        engine="pyarrow",
    )

    total_rows += len(df)

    agency = safe_label(df[AGENCY_COL])
    service = safe_label(df[SERVICE_COL])
    status = safe_label(df[STATUS_COL])

    # Locked Day 1 rule:
    # Current state comes from Status.
    # Backlog = Status is not Closed.
    is_closed = status.str.casefold().eq("closed")
    is_backlog = ~is_closed

    closed_rows += int(is_closed.sum())
    backlog_rows += int(is_backlog.sum())

    # Agency demand
    agency_request_counts.update(
        agency.value_counts().to_dict()
    )

    # Agency x Service demand
    request_pairs = pd.DataFrame(
        {
            "agency": agency,
            "service_problem": service,
        }
    )

    pair_counts = request_pairs.value_counts().to_dict()
    agency_service_request_counts.update(pair_counts)

    # Keep only backlog rows for age analysis
    backlog_part = pd.DataFrame(
        {
            "agency": agency.loc[is_backlog].values,
            "service_problem": service.loc[is_backlog].values,
            "status": status.loc[is_backlog].values,
            "backlog_age_days": pd.to_numeric(
                df.loc[is_backlog, AGE_COL],
                errors="coerce",
            ).values,
        }
    )

    backlog_frames.append(backlog_part)


# =============================================================================
# RECONCILIATION
# =============================================================================

print_section("1 - RECONCILIATION")

print(f"Total Silver rows:       {total_rows:,}")
print(f"Closed requests:         {closed_rows:,}")
print(f"Current backlog:         {backlog_rows:,}")
print(f"Backlog rate:            {backlog_rows / total_rows * 100:.2f}%")
print()

row_match = total_rows == EXPECTED_TOTAL
closed_match = closed_rows == EXPECTED_CLOSED
backlog_match = backlog_rows == EXPECTED_BACKLOG
reconciliation = closed_rows + backlog_rows == total_rows

print(f"Closed + Backlog = Total: {'PASS' if reconciliation else 'FAIL'}")
print(f"Day 1 total match:        {'PASS' if row_match else 'FAIL'}")
print(f"Day 1 closed match:       {'PASS' if closed_match else 'FAIL'}")
print(f"Day 1 backlog match:      {'PASS' if backlog_match else 'FAIL'}")

if not (
    reconciliation
    and row_match
    and closed_match
    and backlog_match
):
    raise RuntimeError(
        "\nDAY 2 STEP 2 STOPPED.\n"
        "Agency x Service analysis does not reconcile "
        "with the locked Day 1 state."
    )


# =============================================================================
# BUILD BACKLOG DATASET
# =============================================================================

backlog = pd.concat(
    backlog_frames,
    ignore_index=True,
)

valid_age_mask = (
    backlog["backlog_age_days"].notna()
    & backlog["backlog_age_days"].ge(0)
)

invalid_age_count = int((~valid_age_mask).sum())

print()
print(f"Valid backlog ages:      {valid_age_mask.sum():,}")
print(f"Invalid backlog ages:    {invalid_age_count:,}")


# =============================================================================
# AGENCY SUMMARY
# =============================================================================

agency_rows = []

for agency_name, request_count in agency_request_counts.items():

    agency_backlog = backlog.loc[
        backlog["agency"].eq(agency_name)
    ]

    backlog_count = len(agency_backlog)

    ages = agency_backlog.loc[
        agency_backlog["backlog_age_days"].notna()
        & agency_backlog["backlog_age_days"].ge(0),
        "backlog_age_days",
    ]

    backlog_30d = int((ages >= 30).sum())
    backlog_60d = int((ages >= 60).sum())
    backlog_90d = int((ages >= 90).sum())
    backlog_180d = int((ages >= 180).sum())

    agency_rows.append(
        {
            "agency": agency_name,
            "request_count": request_count,
            "backlog_count": backlog_count,
            "backlog_rate_pct": (
                backlog_count / request_count * 100
                if request_count
                else np.nan
            ),
            "share_of_city_requests_pct": (
                request_count / total_rows * 100
            ),
            "share_of_city_backlog_pct": (
                backlog_count / backlog_rows * 100
            ),
            "median_backlog_age_days": (
                ages.median()
                if not ages.empty
                else np.nan
            ),
            "p75_backlog_age_days": percentile(
                ages,
                0.75,
            ),
            "p90_backlog_age_days": percentile(
                ages,
                0.90,
            ),
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

agency_summary = (
    pd.DataFrame(agency_rows)
    .sort_values(
        "backlog_count",
        ascending=False,
    )
    .reset_index(drop=True)
)


# =============================================================================
# AGENCY x SERVICE REQUEST COUNTS
# =============================================================================

request_rows = []

for (
    agency_name,
    service_name,
), request_count in agency_service_request_counts.items():

    request_rows.append(
        {
            "agency": agency_name,
            "service_problem": service_name,
            "request_count": request_count,
        }
    )

agency_service_requests = pd.DataFrame(request_rows)


# =============================================================================
# AGENCY x SERVICE BACKLOG METRICS
# =============================================================================

agency_service_rows = []

for (
    agency_name,
    service_name,
), group in backlog.groupby(
    ["agency", "service_problem"],
    dropna=False,
):

    backlog_count = len(group)

    ages = group.loc[
        group["backlog_age_days"].notna()
        & group["backlog_age_days"].ge(0),
        "backlog_age_days",
    ]

    backlog_30d = int((ages >= 30).sum())
    backlog_60d = int((ages >= 60).sum())
    backlog_90d = int((ages >= 90).sum())
    backlog_180d = int((ages >= 180).sum())

    agency_service_rows.append(
        {
            "agency": agency_name,
            "service_problem": service_name,
            "backlog_count": backlog_count,
            "valid_backlog_age_count": len(ages),
            "median_backlog_age_days": (
                ages.median()
                if not ages.empty
                else np.nan
            ),
            "p75_backlog_age_days": percentile(
                ages,
                0.75,
            ),
            "p90_backlog_age_days": percentile(
                ages,
                0.90,
            ),
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

agency_service_backlog = pd.DataFrame(
    agency_service_rows
)


# =============================================================================
# MERGE DEMAND + BACKLOG
# =============================================================================

agency_service_profile = (
    agency_service_requests
    .merge(
        agency_service_backlog,
        on=[
            "agency",
            "service_problem",
        ],
        how="left",
    )
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
    agency_service_profile[col] = (
        agency_service_profile[col]
        .fillna(0)
        .astype(int)
    )


# =============================================================================
# ADD AGENCY CONTEXT
# =============================================================================

agency_context = agency_summary[
    [
        "agency",
        "request_count",
        "backlog_count",
    ]
].rename(
    columns={
        "request_count": "agency_request_count",
        "backlog_count": "agency_backlog_count",
    }
)

agency_service_profile = (
    agency_service_profile
    .merge(
        agency_context,
        on="agency",
        how="left",
    )
)

agency_service_profile["backlog_rate_pct"] = (
    agency_service_profile["backlog_count"]
    / agency_service_profile["request_count"]
    * 100
)

agency_service_profile["share_of_agency_demand_pct"] = (
    agency_service_profile["request_count"]
    / agency_service_profile["agency_request_count"]
    * 100
)

agency_service_profile["share_of_agency_backlog_pct"] = np.where(
    agency_service_profile["agency_backlog_count"] > 0,
    (
        agency_service_profile["backlog_count"]
        / agency_service_profile["agency_backlog_count"]
        * 100
    ),
    np.nan,
)

agency_service_profile["share_of_city_backlog_pct"] = (
    agency_service_profile["backlog_count"]
    / backlog_rows
    * 100
)

agency_service_profile = agency_service_profile[
    [
        "agency",
        "service_problem",
        "request_count",
        "backlog_count",
        "backlog_rate_pct",
        "share_of_agency_demand_pct",
        "share_of_agency_backlog_pct",
        "share_of_city_backlog_pct",
        "median_backlog_age_days",
        "p75_backlog_age_days",
        "p90_backlog_age_days",
        "backlog_30d_plus",
        "backlog_60d_plus",
        "backlog_90d_plus",
        "backlog_180d_plus",
        "old_backlog_share_60d_plus_pct",
    ]
]

agency_service_profile = (
    agency_service_profile
    .sort_values(
        [
            "agency",
            "backlog_count",
            "request_count",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    )
    .reset_index(drop=True)
)


# =============================================================================
# STATUS MIX
# =============================================================================

status_mix = (
    backlog
    .groupby(
        [
            "agency",
            "service_problem",
            "status",
        ],
        dropna=False,
    )
    .size()
    .reset_index(name="status_backlog_count")
)

pair_totals = (
    status_mix
    .groupby(
        [
            "agency",
            "service_problem",
        ]
    )["status_backlog_count"]
    .transform("sum")
)

status_mix["share_of_workflow_backlog_pct"] = (
    status_mix["status_backlog_count"]
    / pair_totals
    * 100
)


# =============================================================================
# MATERIAL WORKFLOWS
# =============================================================================

material_workflows = (
    agency_service_profile.loc[
        agency_service_profile["request_count"] >= 1_000
    ]
    .copy()
)


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

agency_summary.to_csv(
    OUTPUT_DIR / "agency_summary.csv",
    index=False,
)

agency_service_profile.to_csv(
    OUTPUT_DIR / "agency_service_profile.csv",
    index=False,
)

material_workflows.to_csv(
    OUTPUT_DIR / "agency_service_material_workflows.csv",
    index=False,
)

status_mix.to_csv(
    OUTPUT_DIR / "agency_service_backlog_status_mix.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

print_section("2 - AGENCY BACKLOG SUMMARY")

print(
    agency_summary[
        [
            "agency",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "old_backlog_share_60d_plus_pct",
        ]
    ].to_string(index=False)
)


print_section(
    "3 - LARGEST AGENCY x SERVICE BACKLOGS"
)

largest_workflows = (
    agency_service_profile
    .loc[
        agency_service_profile["backlog_count"] > 0
    ]
    .sort_values(
        "backlog_count",
        ascending=False,
    )
    .head(30)
)

print(
    largest_workflows[
        [
            "agency",
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "share_of_agency_backlog_pct",
            "median_backlog_age_days",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
        ]
    ].to_string(index=False)
)


print_section(
    "4 - HIGHEST BACKLOG RATE - MATERIAL WORKFLOWS"
)

high_rate = (
    material_workflows
    .loc[
        material_workflows["backlog_count"] > 0
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
    high_rate[
        [
            "agency",
            "service_problem",
            "request_count",
            "backlog_count",
            "backlog_rate_pct",
            "median_backlog_age_days",
            "old_backlog_share_60d_plus_pct",
        ]
    ].to_string(index=False)
)


print_section(
    "5 - LARGEST 60+ DAY WORKFLOW BACKLOGS"
)

old_backlog = (
    agency_service_profile
    .loc[
        agency_service_profile["backlog_60d_plus"] > 0
    ]
    .sort_values(
        [
            "backlog_60d_plus",
            "backlog_count",
        ],
        ascending=False,
    )
    .head(30)
)

print(
    old_backlog[
        [
            "agency",
            "service_problem",
            "backlog_count",
            "backlog_60d_plus",
            "old_backlog_share_60d_plus_pct",
            "median_backlog_age_days",
            "p90_backlog_age_days",
        ]
    ].to_string(index=False)
)


print_section(
    "6 - WORKFLOW SHARE OF AGENCY BACKLOG"
)

concentrated = (
    agency_service_profile
    .loc[
        agency_service_profile["backlog_count"] >= 100
    ]
    .sort_values(
        [
            "share_of_agency_backlog_pct",
            "backlog_count",
        ],
        ascending=False,
    )
    .head(30)
)

print(
    concentrated[
        [
            "agency",
            "service_problem",
            "backlog_count",
            "share_of_agency_backlog_pct",
            "share_of_agency_demand_pct",
            "backlog_rate_pct",
            "median_backlog_age_days",
        ]
    ].to_string(index=False)
)


# =============================================================================
# SUMMARY
# =============================================================================

summary_lines = [
    "URBAN SERVICE RELIABILITY - DAY 2 AGENCY x SERVICE ANALYSIS",
    "=" * 78,
    "",
    "RECONCILIATION",
    f"Total Silver rows:       {total_rows:,}",
    f"Closed requests:         {closed_rows:,}",
    f"Current backlog:         {backlog_rows:,}",
    f"Backlog rate:            {backlog_rows / total_rows * 100:.2f}%",
    "",
    f"Valid backlog ages:      {valid_age_mask.sum():,}",
    f"Invalid backlog ages:    {invalid_age_count:,}",
    "",
    "INTERPRETATION RULES",
    "- Agency totals are descriptive, not standalone performance grades.",
    "- Agency x Service is the operational comparison grain.",
    "- Backlog volume, rate and age remain separate metrics.",
    "- No universal SLA is assumed.",
    "- High backlog does not automatically imply poor agency performance.",
]

summary_path = (
    OUTPUT_DIR
    / "agency_service_analysis_summary.txt"
)

summary_path.write_text(
    "\n".join(summary_lines),
    encoding="utf-8",
)


print_section(
    "DAY 2 - STEP 2 ANALYSIS COMPLETE"
)

print("Outputs written:")
print(OUTPUT_DIR / "agency_summary.csv")
print(OUTPUT_DIR / "agency_service_profile.csv")
print(OUTPUT_DIR / "agency_service_material_workflows.csv")
print(OUTPUT_DIR / "agency_service_backlog_status_mix.csv")
print(OUTPUT_DIR / "agency_service_analysis_summary.txt")

print()
print("AGENCY x SERVICE ANALYSIS PASSED")