# Enterprise Data Retention Standard

## Purpose and scope
This standard governs retention and disposal of all data held in the enterprise
data platform, including raw landing zones, curated warehouse schemas, and
downstream extracts. It applies to every dataset regardless of storage tier.

## Retention periods by data class
Transaction records must be retained for seven years from the date of the
transaction to satisfy financial recordkeeping obligations. Audit logs covering
access to production data must be retained for a minimum of six years. Protected
health information must be retained for six years from the date of creation or
the date it was last in effect, whichever is later. Application debug logs
containing no customer or patient identifiers may be purged after 90 days.

## Disposal
Disposal of records past their retention period must be performed through the
automated purge job, which records a disposal certificate to the audit ledger.
Manual deletion of production records is prohibited. Any dataset placed under
legal hold is exempt from automated purge until the hold is formally released
by the Legal team.

## Backups and replicas
Retention obligations extend to backups, snapshots, and cross-region replicas.
A record is not considered disposed until it has been removed from all replicas.
Backup retention is capped at 35 days for operational restore purposes; backups
are not an acceptable substitute for the retention obligations above.
