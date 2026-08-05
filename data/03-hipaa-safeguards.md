# HIPAA Technical Safeguards Implementation

## Scope
This document describes how the data platform implements the technical
safeguards required under the HIPAA Security Rule for electronic protected
health information processed by clinical and laboratory pipelines.

## Access control
Unique user identification is enforced through federated identity; shared
accounts are prohibited. Automatic logoff terminates warehouse sessions after
30 minutes of inactivity. Emergency access procedures allow a break-glass
account to be activated by two authorised approvers, with all actions logged.

## Encryption
Electronic protected health information is encrypted at rest using AES-256 with
keys held in the managed key service and rotated annually. Data in transit is
encrypted using TLS 1.2 or above. Encryption keys are never stored alongside the
data they protect.

## De-identification and masking
Direct identifiers are masked at ingestion, before data lands in any queryable
schema. Masking is applied through dynamic masking policies bound to the column,
so an unmasked value is never materialised in a curated table. The eighteen
identifier categories under the Safe Harbor method are treated as direct
identifiers for this purpose.

## Audit controls
Every read of a table containing protected health information is logged with the
principal, timestamp, statement, and rows returned. Audit records are written to
append-only storage and cannot be modified by any platform role, including
DATA_ADMIN.

## Integrity and transmission
Checksums are computed at ingestion and verified at each transformation
boundary. A checksum mismatch fails the pipeline task rather than propagating
suspect data downstream.
