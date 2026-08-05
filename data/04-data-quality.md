# Data Quality and Pipeline Reliability Standard

## Quality dimensions
Every curated dataset declares expectations across six dimensions: completeness,
uniqueness, validity, consistency, timeliness, and accuracy. Expectations live
alongside the pipeline definition and are version controlled.

## Validation gates
Validation runs at three gates. The ingestion gate checks schema conformance and
rejects records that fail type or nullability constraints into a quarantine
table. The transformation gate checks referential integrity and business rules.
The publication gate checks row count variance against the trailing 30-day
median; a variance beyond 25 percent blocks publication and raises an incident.

## Reconciliation
Financial and clinical datasets are reconciled against the source system of
record daily. Reconciliation compares record counts and control totals. An
unreconciled variance must be cleared within one business day or escalated to
the data owner.

## Incident handling
A pipeline failure that affects a published dataset is a Severity 2 incident. A
failure that affects a dataset used for regulatory reporting is Severity 1 and
requires notification to the data owner within one hour. Root cause analysis is
required for every Severity 1 and Severity 2 incident, documented within five
business days.

## Freshness
Curated datasets publish a freshness SLA. Batch datasets must land within four
hours of the source cutoff. Streaming datasets must maintain end-to-end lag
below fifteen minutes measured at the ninety-fifth percentile.
