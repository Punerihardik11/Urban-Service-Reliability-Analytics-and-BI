# Business Rules

## BR-001 — Request Grain

One row represents one submitted 311 service request.

`unique_key` is used as the request-level primary key.

Validation result:

- 2,644,153 rows
- 2,644,153 distinct Unique Keys
- 0 missing keys
- 0 duplicate keys

---

## BR-002 — Current Request State

The source `status` field represents the current observed lifecycle state.

Observed statuses:

- Closed
- Open
- In Progress
- Assigned
- Pending
- Started
- Unspecified

Current operational backlog is therefore determined from current status,
not from the presence or absence of `closed_date`.

---

## BR-003 — Current Backlog

A request is treated as currently unresolved when its current status is:

- Open
- In Progress
- Assigned
- Pending
- Started
- Unspecified

A request is treated as currently closed only when:

`status = 'Closed'`

---

## BR-004 — Closed Date Semantics

`closed_date IS NOT NULL` must NOT be used as the definition of a currently
closed request.

20,377 requests in the selected dataset had a populated Closed Date while
their current status remained non-Closed.

These cases were strongly concentrated in specific DOB, DOT and DEP
workflows rather than appearing randomly.

Therefore Closed Date is retained as a source lifecycle timestamp but does
not independently determine current request state.

---

## BR-005 — Resolution Duration Eligibility

Resolution duration is considered analytically valid only when:

1. current status = Closed
2. created_date is populated and valid
3. closed_date is populated and valid
4. closed_date >= created_date

Requests that do not satisfy all four conditions remain in the analytical
dataset but receive no valid resolution-duration metric.

---

## BR-006 — Closed Requests Missing Closed Date

Requests with:

`status = 'Closed' AND closed_date IS NULL`

remain classified as currently Closed.

However, resolution duration is unavailable for these requests.

Observed count: 9.

---

## BR-007 — Negative Resolution Durations

A negative value of:

`closed_date - created_date`

is treated as a timestamp-quality anomaly.

The underlying request is retained.

The invalid duration is excluded from resolution-time KPIs.

Observed count: 650.

---

## BR-008 — Due Date

Due Date will not be used for city-wide SLA or target-date compliance.

Only 9,815 requests contained Due Date and all belonged to DSNY.

Any future Due Date analysis must therefore be explicitly DSNY-specific.

---

## BR-009 — Geography

Missing geographic fields do not cause request removal.

Coordinate-based analysis requires both latitude and longitude.

`borough = 'Unspecified'` remains an explicit unknown geography category.

Invalid ZIP values are preserved in the raw field and converted to null only
in a separate cleaned ZIP field.

---

## BR-010 — Duplicate-Looking Requests

Repeated service-request fingerprints are not treated as confirmed
duplicates.

Distinct Unique Keys represent distinct submitted service requests unless
stronger source semantics prove otherwise.

Observed:

- 25,706 repeated fingerprints
- 54,557 rows involved

These records remain in the analytical dataset.

---

## BR-011 — Duration Distribution

Resolution duration is heavily right-skewed.

Operational reporting will therefore prioritize:

- Median
- P75
- P90

rather than relying primarily on mean resolution time.
## BR-012 — Zero-Duration Closures

A zero-duration closure is not automatically treated as a data-quality error.

Observed examples include duplicate requests, referrals, administrative
closures and agency workflow events.

Zero-duration requests remain eligible for resolution-duration calculations
when all other duration-validity conditions are satisfied.

A separate zero-duration flag is retained for sensitivity analysis.

---

## BR-013 — Extreme Resolution Durations

Long resolution durations are not automatically classified as invalid.

Cases exceeding 180 days were observed in operationally plausible workflows
including TLC investigations, DOB inspection processes, HPD complaints and
Parks work.

Extreme durations remain visible and receive an explicit analytical flag.

---

## BR-014 — Future Closure Timestamps

A Closed Date later than the extraction/snapshot timestamp is considered a
timestamp-quality anomaly.

The request remains in the dataset.

The Closed Date remains preserved as a raw source value.

However, the record is excluded from valid resolution-duration metrics.

---

## BR-015 — Category Labels

Complaint Type and Descriptor values are preserved using their source
taxonomy.

Case variants such as:

PLUMBING / Plumbing
ELEVATOR / Elevator
SAFETY / Safety

are not automatically merged because service categories can be
agency-specific.

Agency context must be retained when comparing service categories.

---

## BR-016 — Text Encoding

Resolution Description contains occasional source text-encoding artifacts.

The raw source value is preserved.

Resolution Description will not be used as a primary quantitative KPI field
without explicit text cleaning.