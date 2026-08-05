# Metadata, Lineage and Cataloguing Policy

## Catalogue registration
No dataset may be published to a curated schema without a catalogue entry. The
entry records the data owner, steward, classification, retention class, source
systems, and refresh schedule. Publication of an uncatalogued dataset is blocked
at the deployment gate.

## Lineage capture
Column-level lineage is captured automatically from pipeline execution metadata.
Lineage must resolve from every curated column back to its originating source
system column. A dataset whose lineage cannot be resolved is marked untrusted in
the catalogue and excluded from regulatory reporting.

## Classification
Datasets are classified as Public, Internal, Confidential, or Restricted.
Protected health information and payment card data are always Restricted.
Classification determines the applicable masking policy and the approval path
for access requests.

## Change management
A breaking schema change to a curated dataset requires 10 business days notice
to registered consumers. Additive changes require no notice. The catalogue
records a deprecation date for every column marked for removal.

## Ownership
Every dataset has a named data owner accountable for its quality and access
decisions, and a named steward responsible for day-to-day curation. Ownership
cannot be assigned to a team alias without a named individual as backup.
