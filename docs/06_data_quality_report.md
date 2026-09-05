# Data Quality Report

## Analytical Snapshot

Rows acquired: 2,644,153
Rows in Silver: 2,644,153
Rows lost during transformation: 0

Unique Keys: 2,644,153
Duplicate Unique Keys: 0
Missing Unique Keys: 0

The validated analytical grain is one row per 311 Service Request.

## Lifecycle

Observed statuses:

Closed
Open
In Progress
Assigned
Pending
Started
Unspecified

Lifecycle anomalies:

Closed without Closed Date: 9
Non-Closed with Closed Date: 20,377
Total lifecycle mismatches: 20,386

Current lifecycle state is therefore determined using Status rather than
Closed Date.

## Resolution Timestamp Quality

Negative duration rows: 650

All observed negative durations occurred within DEP and DOT requests.

These requests are retained but excluded from valid resolution-duration
metrics.

Future Closed Date rows: 1

The future timestamp is retained as a source value but excluded from valid
resolution-duration calculations.

Valid resolution-duration rows:
2,457,340

## Zero-Duration Requests

Observed zero-duration closures:
56,511

Inspection showed legitimate operational explanations including:

duplicate reports,
referrals,
administrative closure,
inspection outcomes,
and agency workflow behaviour.

Zero-duration cases are therefore not automatically removed.

## Extreme Durations

Requests exceeding 180 days:
855

Inspection identified plausible long-running workflows across TLC, DOB, HPD,
DOT and other agencies.

Extreme duration is retained as an analytical flag rather than treated as an
automatic error.

## Geography

Missing coordinate pairs:
65,793

Partial latitude/longitude pairs:
0

Coordinates outside broad NYC bounding box:
0

Invalid ZIP formats:
2

Borough = Unspecified:
2,832

Missing geography does not cause removal from the core request dataset.

## Due Date

Due Date populated:
9,815 requests

Coverage:
approximately 0.37%

All populated Due Date records belong to DSNY.

Due Date is therefore unsuitable for city-wide SLA analysis.

## Potential Duplicate Requests

Repeated conservative request fingerprints:
25,706

Rows participating:
54,557

These are not considered confirmed duplicates because every request has a
distinct Unique Key.

Records are retained.

## Category Consistency

Only three Complaint Type case-normalization collisions were detected:

PLUMBING / Plumbing
SAFETY / Safety
ELEVATOR / Elevator

Three Descriptor collisions were detected:

DOOR / Door
LIGHTING / Lighting
SEWAGE / Sewage

Source taxonomy is retained because category meaning can depend on agency
context.

## Source Text

Some Resolution Description values contain encoding artifacts.

Raw values remain preserved.

Free text will not be used as a core KPI without dedicated cleaning.