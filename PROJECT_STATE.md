# Finally: `PROJECT_STATE.md`

This is the handover file that lets us start Day 2 without reconstructing today's reasoning.

```
```

```
# PROJECT STATE

## Project

Urban Service Reliability Analytics and BI

Implementation:
NYC 311 Service Operations Intelligence

## Current Phase

DAY 1 COMPLETE

UNDERSTAND → VERIFY → PROFILE → VALIDATE → STRUCTURE → DISCOVER

## Source

NYC Open Data
311 Service Requests from 2020 to Present
Dataset ID: erm2-nwe9

## Analytical Scope

NYC-wide

Created Date:
2026-01-01 inclusive
through
2026-08-30 exclusive

Human-readable:
January 1 through August 29, 2026

August 30 was excluded because source profiling showed an incomplete
publication day.

## Data Volume

Bronze:
2,644,153 requests

Silver:
2,644,153 requests

Row reconciliation:
PASS

Unique request keys:
2,644,153

Duplicate Unique Keys:
0

## Architecture Completed

NYC Open Data API
→ Bronze compressed JSON
→ Python profiling
→ Python validation
→ Silver Parquet

Future:

Silver
→ MySQL
→ SQL Gold/business layer
→ Power BI semantic model

## Core Business Rules

Current request state is determined from Status.

Closed Date does not independently determine closure.

Backlog means current Status is not Closed.

Resolution duration is valid only when:

- Status = Closed
- Created Date valid
- Closed Date valid
- Closed Date >= Created Date
- Closed Date <= analytical snapshot

Due Date is not used for city-wide SLA analysis.

Unknown/null geography is preserved.

Potential duplicate fingerprints are not automatically deleted.

## Quality Results

Lifecycle mismatch rows:
20,386

Negative resolution durations:
650

Future Closed Dates:
1

Zero-duration closures:
56,511

Requests >180-day raw duration:
855

Missing coordinate pairs:
65,793

Invalid ZIP formats:
2

Due Date coverage:
0.37%, DSNY only

## Initial KPIs

Total Requests:
2,644,153

Closed Requests:
2,457,717

Current Backlog:
186,436

Backlog Rate:
7.05%

Requests / Day:
10,971.6

Median Resolution:
6.94 hours

P75 Resolution:
73.79 hours

P90 Resolution:
325.21 hours

Median Backlog Age:
50.81 days

P75 Backlog Age:
125.76 days

P90 Backlog Age:
193.04 days

Top 5 Service Share:
42.46%

Top 10 Service Share:
56.07%

## Strongest Day 1 Insight

High service-request volume does not necessarily imply high operational
backlog.

Several of the largest request categories have extremely low unresolved rates,
while smaller operational workflows contain high and persistent backlog.

Therefore project prioritization should combine:

demand
+
backlog volume
+
backlog rate
+
backlog age
+
service/workflow context

rather than ranking services by complaint volume alone.

## Day 2 Priority

1. Backlog composition and age cohorts
2. Agency × Service performance rather than raw agency rankings
3. Geographic service hotspots
4. Temporal/service decomposition
5. Recurring local service demand
6. Investigate structural lifecycle patterns such as EDC / Noise - Helicopter
7. Investigate approximately-60-day closure patterns in selected services

## Explicit Non-Claims

No universal SLA has been established.

High backlog does not automatically mean poor agency performance.

High resolution duration does not automatically mean service failure.

Raw ZIP request counts are not population-adjusted service burden.

January/February demand spikes have not yet been causally explained.

Full annual seasonality cannot be claimed from the selected partial-year scope.

## Day 1 Status

API accessibility                     COMPLETE
Raw sample                            COMPLETE
Schema understanding                  COMPLETE
Scope selection                       COMPLETE
Lifecycle investigation               COMPLETE
Data dictionary                       COMPLETE
Quality audit                         COMPLETE
Business rules                        COMPLETE
Bronze                                COMPLETE
Silver                                COMPLETE
Initial KPIs                          COMPLETE
Initial operational findings          COMPLETE
Day 2 analytical questions            COMPLETE

DAY 1 COMPLETE.
```

## Day 1 is done

We accomplished everything we originally required before touching BI:

**API proven → 2.64M real requests acquired → grain validated → lifecycle semantics challenged → quality anomalies preserved → business rules established → Bronze built → Silver built → legitimate KPIs calculated → first operational discoveries found → next questions established.**

And importantly, the main insight isn't “Brooklyn has the most complaints.”

It's already becoming:

> **Urban service demand, operational backlog, and service reliability are different phenomena — and prioritizing city operations requires separating them.**

That's a much stronger foundation for what we build on **Day 2**.


# PROJECT STATE

## Project

Urban Service Reliability Analytics and BI

Implementation:
NYC 311 Service Operations Intelligence

## Current Phase

DAY 2 COMPLETE

UNDERSTAND
→ VERIFY
→ PROFILE
→ VALIDATE
→ STRUCTURE
→ DISCOVER
→ DECOMPOSE
→ SYNTHESIZE
→ GOLD
→ MYSQL

---

## Source

NYC Open Data

311 Service Requests from 2020 to Present

Dataset ID:
erm2-nwe9

---

## Analytical Scope

NYC-wide

Created Date:

2026-01-01 inclusive
through
2026-08-30 exclusive

Human-readable:

January 1 through August 29, 2026

August 30 remains excluded because source profiling showed an incomplete publication day.

Observed calendar days:

241

---

## Core Data Volume

Bronze:
2,644,153 requests

Silver:
2,644,153 requests

Total Requests:
2,644,153

Closed Requests:
2,457,717

Current Backlog:
186,436

Valid Resolution Rows:
2,457,340

Unique request keys:
2,644,153

Duplicate Unique Keys:
0

Bronze → Silver reconciliation:
PASS

Silver → Gold reconciliation:
PASS

Gold → MySQL reconciliation:
PASS

---

## Architecture Completed

NYC Open Data API
→ Bronze compressed JSON
→ Python profiling
→ Python validation
→ Silver Parquet
→ Python analytical investigations
→ Gold Parquet / CSV
→ MySQL Gold business layer

Future:

MySQL Gold
→ Power BI semantic model
→ Dashboard
→ Insight narrative
→ QA / portfolio packaging

---

## MySQL

Database:

urban_service_reliability

Gold schema:

sql/10_create_gold_schema.sql

MySQL load:

PASS

Business metric reconciliation:

PASS

---

## Gold Tables

### gold_city_snapshot

Grain:
One analytical scope snapshot

Rows:
1

Purpose:
City-wide KPI and distribution summary.

### gold_service_snapshot

Grain:
Agency × Service

Rows:
205

Purpose:
Primary operational workflow comparison layer.

### gold_service_daily

Grain:
Created Date × Agency × Service

Rows:
31,918

Purpose:
Temporal service-demand decomposition.

### gold_zip_snapshot

Grain:
Incident ZIP

Rows:
335

Purpose:
Geographic request/backlog concentration.

Raw ZIP counts are NOT population-adjusted service burden.

### gold_service_zip_snapshot

Grain:
Agency × Service × Incident ZIP

Rows:
23,391

Purpose:
Workflow-level geographic hotspot analysis.

### gold_service_zip_recurrence

Grain:
Agency × Service × Incident ZIP

Rows:
23,391

Purpose:
Sustained versus burst-driven local demand.

### gold_lifecycle_flags

Grain:
Agency × Service

Rows:
205

Purpose:
Lifecycle interpretation and systematic closure-pattern flags.

---

## Locked Core Business Rules

1. Current request state is determined from Status.

2. Closed Date does not independently determine current closure state.

3. Backlog means:

Status != Closed

4. Backlog age uses Silver:

request_age_days

Do not recompute using an arbitrary new snapshot.

5. Valid resolution duration uses Silver:

resolution_duration_valid

6. Resolution timing uses Silver:

resolution_hours

7. Due Date is not used as a universal city-wide SLA field.

8. Unknown/null geography is preserved.

9. Potential duplicate fingerprints are not automatically deleted.

10. Raw ZIP counts measure request concentration, not population-adjusted burden.

---

## Day 1 Data Quality Findings

Lifecycle mismatch rows:
20,386

Negative resolution durations:
650

Future Closed Dates:
1

Zero-duration closures:
56,511

Requests >180-day raw duration:
855

Missing coordinate pairs:
65,793

Invalid ZIP formats:
2

Due Date coverage:
0.37%

Due Date concentrated in DSNY workflows.

---

## City-Wide Operational KPIs

Total Requests:
2,644,153

Closed Requests:
2,457,717

Current Backlog:
186,436

Backlog Rate:
7.05%

Requests / Day:
10,971.6

Median Resolution:
6.94 hours

P75 Resolution:
73.79 hours

P90 Resolution:
325.21 hours

Median Backlog Age:
50.81 days

P75 Backlog Age:
125.76 days

P90 Backlog Age:
193.04 days

30+ Day Backlog:
63.46%

60+ Day Backlog:
45.34%

90+ Day Backlog:
34.80%

180+ Day Backlog:
12.84%

---

# LOCKED DAY 2 FINDINGS

## D2-F01 — Persistent Backlog

Current unresolved inventory contains substantial aged backlog.

63.46% is 30+ days old.

45.34% is 60+ days old.

34.80% is 90+ days old.

12.84% is 180+ days old.

Operational prioritization must distinguish fresh unresolved work from persistent aged inventory.

---

## D2-F02 — Agency × Service Is the Correct Operational Grain

Agency-level metrics conceal fundamentally different workflow behavior.

Example:

HPD — UNSANITARY CONDITION

Backlog:
12,967

Median backlog age:
20.84 days

versus

HPD — HEAT/HOT WATER

Backlog:
11,972

Median backlog age:
189.71 days

Therefore agency totals should be descriptive rather than standalone performance grades.

---

## D2-F03 — Agency Backlog Can Be Highly Concentrated

For Hire Vehicle Complaint and Taxi Complaint together explain approximately 93.13% of TLC backlog.

A high agency backlog rate may therefore be driven by a small number of workflows rather than an agency-wide condition.

---

## D2-F04 — Geographic Volume != Persistent Geographic Backlog

High request volume and persistent backlog are different geographic phenomena.

Example:

ZIP 10023

Backlog rate:
24.24%

Median backlog age:
142.48 days

versus

ZIP 11226

High request volume but backlog rate:
6.09%

Median backlog age:
24.78 days

Service × Geography must be inspected before interpreting hotspots.

---

## D2-F05 — Demand Spikes Are Service-Composition Events

February had the highest normalized monthly demand.

2026-02-24:

Snow or Ice:
11,370 requests

Share of that day's demand:
49.86%

January/February peaks were strongly influenced by HEAT/HOT WATER and Snow or Ice.

July peaks had different compositions including Water System and July 4 fireworks/noise activity.

Do not interpret demand spikes without service decomposition.

---

## D2-F06 — Recurring and Burst Demand Are Different

Illegal Parking and several residential-noise Service × ZIP combinations were active across essentially every observed day.

Example:

Illegal Parking × ZIP 11101

Active days:
241 / 241

Requests per active day:
52.71

Snow or Ice showed much stronger top-day concentration and represents a more burst/event-driven pattern.

HEAT/HOT WATER behaves as a hybrid recurring + surge workflow.

---

## D2-F07 — EDC / Noise - Helicopter Is a Structural Lifecycle Exception

EDC rows:
6,974

Noise - Helicopter rows:
6,974

All:
In Progress

Closed:
0

Closed Date present:
0

Resolution description present:
0

Median age:
148.69 days

This workflow remains included under the locked Status-based backlog definition but must not be compared naïvely with conventional closure workflows.

Gold flag:

is_structural_lifecycle_exception = TRUE

---

## D2-F08 — Systematic ~60-Day Recorded Closure Patterns Exist

Food Establishment:

84.05% of valid resolutions occur within 59.9–60.1 days.

Smoking or Vaping:

45.66% occur within 59.9–60.1 days.

These are highly concentrated recorded lifecycle patterns.

They are NOT proof of a 60-day SLA or field-service completion timing.

---

## D2-F09 — Other ~60-Day Workflow Patterns

Mobile Food Vendor:

100% of valid resolutions fall within 59.5–60.5 days.

Non-Residential Heat:

76.26% fall within 59.5–60.5 days.

Gold flag:

has_systematic_60d_closure_pattern

currently identifies:

- Mobile Food Vendor
- Food Establishment
- Non-Residential Heat
- Smoking or Vaping

---

## D2-F10 — Interpretation Guardrails

No universal SLA established.

High backlog does not automatically imply poor agency performance.

High resolution duration does not automatically mean service failure.

Recorded closure timing does not necessarily equal actual field-service completion.

Raw ZIP request counts are not population-adjusted burden.

Partial-year data cannot establish full annual seasonality.

EDC / Noise - Helicopter remains included but explicitly flagged.

---

# Strongest Overall Analytical Insight

NYC 311 operational reliability cannot be understood using complaint volume or agency backlog rate alone.

Operational behavior differs materially across:

demand volume
+ backlog volume
+ backlog rate
+ backlog age
+ service workflow
+ geographic concentration
+ recurrence
+ temporal context
+ lifecycle semantics

The primary operational analytical grain is:

Agency × Service

with Service × Geography and Service × Time providing the supporting decomposition.

---

# Day 2 Files

Analysis:

src/analysis/01_backlog_analysis.py
src/analysis/02_agency_service_analysis.py
src/analysis/03_geographic_hotspots.py
src/analysis/04_temporal_service_analysis.py
src/analysis/05_recurring_local_demand.py
src/analysis/06_edc_helicopter_lifecycle.py
src/analysis/07_closure_pattern_analysis.py
src/analysis/08_synthesize_day2.py

Gold:

src/gold/09_build_gold_layer.py
src/gold/10_load_gold_to_mysql.py

SQL:

sql/10_create_gold_schema.sql

Gold data:

data/gold/nyc_311_2026_ytd/

---

# Day 2 Status

Backlog analysis:
COMPLETE

Agency × Service decomposition:
COMPLETE

Geographic hotspot analysis:
COMPLETE

Temporal decomposition:
COMPLETE

Recurring local demand:
COMPLETE

Lifecycle anomaly investigation:
COMPLETE

~60-day closure investigation:
COMPLETE

Analytical synthesis:
COMPLETE

Gold business layer:
COMPLETE

MySQL Gold load:
COMPLETE

Cross-layer reconciliation:
PASS

DAY 2 COMPLETE.

---

# Day 3 Priority

1. Design Power BI semantic/star model from MySQL Gold.
2. Define dimensions and relationships.
3. Define KPI/measure layer.
4. Design dashboard information architecture.
5. Build executive overview.
6. Build workflow/backlog intelligence page.
7. Build geography/recurrence page.
8. Build service drill-through / lifecycle-context page.
9. Validate every Power BI KPI against MySQL Gold.
10. Document final business insights and dashboard interpretation.

Do not rebuild Bronze, Silver or Gold unless new evidence requires a change.

Do not reopen locked Day 1 / Day 2 business rules without evidence.

DAY 3 STARTING POINT:

MySQL Gold business layer.