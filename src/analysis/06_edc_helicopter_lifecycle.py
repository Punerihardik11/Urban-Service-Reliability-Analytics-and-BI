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
EXPECTED_TARGET = 6_974

TARGET_AGENCY = "EDC"
TARGET_SERVICE = "Noise - Helicopter"


# =============================================================================
# HELPERS
# =============================================================================

def resolve_required(columns, candidates, label):
    for col in candidates:
        if col in columns:
            return col

    raise KeyError(
        f"Could not resolve {label}. "
        f"Tried {candidates}.\n"
        f"Available columns:\n{columns}"
    )


def resolve_optional(columns, candidates):
    for col in candidates:
        if col in columns:
            return col

    return None


def safe_label(series, unknown="Unknown"):
    result = (
        series
        .astype("string")
        .str.strip()
        .fillna(unknown)
    )

    return result.mask(
        result.eq(""),
        unknown,
    )


def section(title):
    print()
    print("=" * 112)
    print(title)
    print("=" * 112)


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


AGENCY = resolve_required(
    columns,
    ["agency"],
    "agency",
)


SERVICE = resolve_required(
    columns,
    [
        "service_problem",
        "complaint_type",
    ],
    "service problem",
)


STATUS = resolve_required(
    columns,
    ["status"],
    "status",
)


CREATED = resolve_required(
    columns,
    [
        "created_at",
        "created_date",
    ],
    "created timestamp",
)


AGE = resolve_required(
    columns,
    ["request_age_days"],
    "request age",
)


# Optional diagnostic fields.
# The script will use them only if they actually exist in Silver.

optional = {

    "unique_key":
        resolve_optional(
            columns,
            ["unique_key"],
        ),

    "closed_at":
        resolve_optional(
            columns,
            [
                "closed_at",
                "closed_date",
            ],
        ),

    "descriptor":
        resolve_optional(
            columns,
            ["descriptor"],
        ),

    "resolution_description":
        resolve_optional(
            columns,
            ["resolution_description"],
        ),

    "agency_name":
        resolve_optional(
            columns,
            ["agency_name"],
        ),

    "borough":
        resolve_optional(
            columns,
            ["borough"],
        ),

    "incident_zip":
        resolve_optional(
            columns,
            [
                "incident_zip",
                "zip_code",
            ],
        ),

    "location_type":
        resolve_optional(
            columns,
            ["location_type"],
        ),

    "due_at":
        resolve_optional(
            columns,
            [
                "due_at",
                "due_date",
            ],
        ),
}


optional = {
    key: value
    for key, value
    in optional.items()
    if value is not None
}


read_cols = [
    AGENCY,
    SERVICE,
    STATUS,
    CREATED,
    AGE,
]


for col in optional.values():
    if col not in read_cols:
        read_cols.append(col)


section(
    "URBAN SERVICE RELIABILITY - DAY 2 "
    "EDC / NOISE - HELICOPTER INVESTIGATION"
)


print(
    f"Silver parts:            "
    f"{len(parts)}"
)

print()

print(
    f"Agency column:           "
    f"{AGENCY}"
)

print(
    f"Service column:          "
    f"{SERVICE}"
)

print(
    f"Status column:           "
    f"{STATUS}"
)

print(
    f"Created column:          "
    f"{CREATED}"
)

print(
    f"Request age column:      "
    f"{AGE}"
)


print()
print("Optional diagnostic fields found:")


if optional:

    for logical, actual in optional.items():

        print(
            f"  {logical:<24} "
            f"{actual}"
        )

else:

    print("  None")


# =============================================================================
# SCAN SILVER
# =============================================================================

total_rows = 0

edc_rows = 0
helicopter_rows = 0

target_parts = []


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
        columns=read_cols,
        engine="pyarrow",
    )


    total_rows += len(df)


    agency = safe_label(
        df[AGENCY]
    )


    service = safe_label(
        df[SERVICE]
    )


    is_edc = (
        agency
        .str
        .casefold()
        .eq(
            TARGET_AGENCY.casefold()
        )
    )


    is_helicopter = (
        service
        .str
        .casefold()
        .eq(
            TARGET_SERVICE.casefold()
        )
    )


    target_mask = (
        is_edc
        & is_helicopter
    )


    edc_rows += int(
        is_edc.sum()
    )


    helicopter_rows += int(
        is_helicopter.sum()
    )


    if target_mask.any():

        target_parts.append(
            df.loc[
                target_mask
            ].copy()
        )


# =============================================================================
# RECONCILIATION
# =============================================================================

target = pd.concat(
    target_parts,
    ignore_index=True,
)


section(
    "1 - RECONCILIATION"
)


checks = {

    "Day 1 total match":
        total_rows
        == EXPECTED_TOTAL,

    "EDC rows":
        edc_rows
        == EXPECTED_TARGET,

    "Noise - Helicopter rows":
        helicopter_rows
        == EXPECTED_TARGET,

    "EDC x Helicopter rows":
        len(target)
        == EXPECTED_TARGET,

    "No other EDC service":
        edc_rows
        == len(target),

    "No non-EDC helicopter rows":
        helicopter_rows
        == len(target),
}


print(
    f"Total Silver rows:              "
    f"{total_rows:,}"
)

print(
    f"EDC rows:                       "
    f"{edc_rows:,}"
)

print(
    f"Noise - Helicopter rows:        "
    f"{helicopter_rows:,}"
)

print(
    f"EDC x Noise - Helicopter rows:  "
    f"{len(target):,}"
)

print()


for label, passed in checks.items():

    print(
        f"{label:<32} "
        f"{'PASS' if passed else 'FAIL'}"
    )


if not all(
    checks.values()
):

    raise RuntimeError(
        "STEP 6 STOPPED: "
        "target population does not reconcile."
    )


# =============================================================================
# NORMALIZE TARGET
# =============================================================================

target[
    "status_clean"
] = safe_label(
    target[STATUS]
)


target[
    "created_ts"
] = pd.to_datetime(
    target[CREATED],
    errors="coerce",
)


target[
    "age_days"
] = pd.to_numeric(
    target[AGE],
    errors="coerce",
)


if target[
    "created_ts"
].isna().any():

    raise RuntimeError(
        "Target contains invalid Created timestamps."
    )


valid_age = (
    target[
        "age_days"
    ].notna()
    & target[
        "age_days"
    ].ge(0)
)


if not valid_age.all():

    raise RuntimeError(
        "Target contains invalid request ages."
    )


# =============================================================================
# STATUS PROFILE
# =============================================================================

status_profile = (
    target[
        "status_clean"
    ]
    .value_counts()
    .rename_axis(
        "status"
    )
    .reset_index(
        name="row_count"
    )
)


status_profile[
    "share_pct"
] = (
    status_profile[
        "row_count"
    ]
    / len(target)
    * 100
)


closed_status_rows = int(
    target[
        "status_clean"
    ]
    .str
    .casefold()
    .eq("closed")
    .sum()
)


# =============================================================================
# CLOSURE / RESOLUTION EVIDENCE
# =============================================================================

closure_rows = [

    {
        "metric":
            "Target rows",

        "row_count":
            len(target),
    },

    {
        "metric":
            "Status = Closed",

        "row_count":
            closed_status_rows,
    },
]


if "closed_at" in optional:

    closed_col = optional[
        "closed_at"
    ]

    parsed_closed = pd.to_datetime(
        target[
            closed_col
        ],
        errors="coerce",
    )

    closure_rows.append(
        {
            "metric":
                f"{closed_col} present",

            "row_count":
                int(
                    parsed_closed
                    .notna()
                    .sum()
                ),
        }
    )


if "resolution_description" in optional:

    resolution_col = optional[
        "resolution_description"
    ]

    resolution = (
        target[
            resolution_col
        ]
        .astype("string")
        .str
        .strip()
    )


    resolution_present = (
        resolution.notna()
        & resolution.ne("")
    )


    closure_rows.append(
        {
            "metric":
                f"{resolution_col} present",

            "row_count":
                int(
                    resolution_present.sum()
                ),
        }
    )


closure_evidence = pd.DataFrame(
    closure_rows
)


closure_evidence[
    "share_pct"
] = (
    closure_evidence[
        "row_count"
    ]
    / len(target)
    * 100
)


# =============================================================================
# AGE PROFILE
# =============================================================================

age_bins = [
    0,
    30,
    60,
    90,
    180,
    np.inf,
]


age_labels = [
    "<30 days",
    "30-60 days",
    "60-90 days",
    "90-180 days",
    "180+ days",
]


target[
    "age_cohort"
] = pd.cut(
    target[
        "age_days"
    ],
    bins=age_bins,
    labels=age_labels,
    right=False,
    include_lowest=True,
)


age_profile = (
    target[
        "age_cohort"
    ]
    .value_counts(
        sort=False
    )
    .rename_axis(
        "age_cohort"
    )
    .reset_index(
        name="row_count"
    )
)


age_profile[
    "share_pct"
] = (
    age_profile[
        "row_count"
    ]
    / len(target)
    * 100
)


# =============================================================================
# TEMPORAL PROFILE
# =============================================================================

target[
    "date"
] = (
    target[
        "created_ts"
    ]
    .dt
    .normalize()
)


target[
    "month"
] = (
    target[
        "created_ts"
    ]
    .dt
    .to_period("M")
    .astype(str)
)


monthly_profile = (
    target
    .groupby(
        "month"
    )
    .size()
    .reset_index(
        name="request_count"
    )
    .sort_values(
        "month"
    )
)


daily_profile = (
    target
    .groupby(
        "date"
    )
    .size()
    .reset_index(
        name="request_count"
    )
    .sort_values(
        "date"
    )
)


# =============================================================================
# OPTIONAL FIELD PROFILES
# =============================================================================

optional_profiles = {}


for logical in [

    "descriptor",
    "resolution_description",
    "agency_name",
    "borough",
    "incident_zip",
    "location_type",

]:

    if logical in optional:

        col = optional[
            logical
        ]


        profile = (
            safe_label(
                target[col]
            )
            .value_counts()
            .rename_axis(
                col
            )
            .reset_index(
                name="row_count"
            )
        )


        profile[
            "share_pct"
        ] = (
            profile[
                "row_count"
            ]
            / len(target)
            * 100
        )


        optional_profiles[
            logical
        ] = profile


        profile.to_csv(
            OUTPUT_DIR
            / (
                "edc_noise_helicopter_"
                f"{logical}_profile.csv"
            ),
            index=False,
        )


# =============================================================================
# WRITE OUTPUTS
# =============================================================================

status_profile.to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_status_profile.csv",
    index=False,
)


closure_evidence.to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_closure_evidence.csv",
    index=False,
)


age_profile.to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_age_cohorts.csv",
    index=False,
)


monthly_profile.to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_monthly_profile.csv",
    index=False,
)


daily_profile.to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_daily_profile.csv",
    index=False,
)


sample_cols = [
    AGENCY,
    SERVICE,
    STATUS,
    CREATED,
    AGE,
]


for col in optional.values():

    if col not in sample_cols:

        sample_cols.append(
            col
        )


target[
    sample_cols
].head(
    200
).to_csv(
    OUTPUT_DIR
    / "edc_noise_helicopter_inspection_sample.csv",
    index=False,
)


# =============================================================================
# PRINT RESULTS
# =============================================================================

section(
    "2 - STATUS PROFILE"
)


print(
    status_profile
    .to_string(
        index=False
    )
)


section(
    "3 - CLOSURE / RESOLUTION EVIDENCE"
)


print(
    closure_evidence
    .to_string(
        index=False
    )
)


section(
    "4 - AGE PROFILE"
)


print(
    f"Median age: "
    f"{target['age_days'].median():.2f} days"
)

print(
    f"P75 age:    "
    f"{target['age_days'].quantile(0.75):.2f} days"
)

print(
    f"P90 age:    "
    f"{target['age_days'].quantile(0.90):.2f} days"
)

print()


print(
    age_profile
    .to_string(
        index=False
    )
)


section(
    "5 - MONTHLY CREATION PROFILE"
)


print(
    monthly_profile
    .to_string(
        index=False
    )
)


section(
    "6 - HIGHEST-DEMAND DAYS"
)


print(
    daily_profile
    .sort_values(
        "request_count",
        ascending=False,
    )
    .head(20)
    .to_string(
        index=False
    )
)


for logical, profile in optional_profiles.items():

    section(
        f"7 - OPTIONAL PROFILE: "
        f"{logical.upper()}"
    )


    printable = (
        profile
        .head(20)
        .copy()
    )


    value_col = (
        printable
        .columns[0]
    )


    printable[
        value_col
    ] = (
        printable[
            value_col
        ]
        .astype(str)
        .str
        .slice(
            0,
            160,
        )
    )


    print(
        printable
        .to_string(
            index=False
        )
    )


# =============================================================================
# SUMMARY
# =============================================================================

summary_lines = [

    "URBAN SERVICE RELIABILITY - DAY 2 "
    "EDC / NOISE - HELICOPTER INVESTIGATION",

    "=" * 82,

    "",

    f"EDC rows:                       "
    f"{edc_rows:,}",

    f"Noise - Helicopter rows:        "
    f"{helicopter_rows:,}",

    f"Intersection rows:              "
    f"{len(target):,}",

    f"Status = Closed rows:           "
    f"{closed_status_rows:,}",

    f"Median request age:             "
    f"{target['age_days'].median():.2f} days",

    f"P90 request age:                "
    f"{target['age_days'].quantile(0.90):.2f} days",

    "",

    "INTERPRETATION RULES",

    "- This is a lifecycle diagnostic, not a performance score.",

    "- Absence of Closed status does not by itself establish service failure.",

    "- Closed-date and resolution-description evidence are inspected separately.",

    "- No rows are deleted or reclassified by this analysis.",
]


(
    OUTPUT_DIR
    / "edc_noise_helicopter_summary.txt"
).write_text(
    "\n".join(
        summary_lines
    ),
    encoding="utf-8",
)


# =============================================================================
# COMPLETE
# =============================================================================

section(
    "DAY 2 - STEP 6 ANALYSIS COMPLETE"
)


print(
    f"Outputs -> "
    f"{OUTPUT_DIR}"
)

print()

print(
    "EDC / NOISE - HELICOPTER INVESTIGATION PASSED"
)