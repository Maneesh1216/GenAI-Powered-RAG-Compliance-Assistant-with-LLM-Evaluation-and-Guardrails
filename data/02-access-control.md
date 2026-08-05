# Access Control and RBAC Policy

## Principle of least privilege
Every principal receives the minimum access required to perform their role.
Access is granted to roles, never to individual users. Direct grants to a user
account are prohibited in production and are flagged by the nightly entitlement
scan.

## Role definitions
Four standard roles exist in the warehouse. DATA_READER may select from curated
schemas only. DATA_ANALYST may select from curated schemas and create objects in
personal sandbox schemas. DATA_ENGINEER may create and modify objects in curated
and staging schemas, and may execute pipeline service accounts. DATA_ADMIN may
grant and revoke roles and is restricted to named platform administrators.

## Privileged access
Access to raw landing zones containing unmasked sensitive data requires
DATA_ADMIN approval and is granted for a maximum of eight hours through the
just-in-time elevation workflow. All elevated sessions are recorded and reviewed
weekly.

## Access review
Entitlements are reviewed quarterly. Role owners must attest to every membership
in their roles. Any membership not attested within 14 days of the review opening
is automatically revoked.

## Service accounts
Pipeline service accounts must not be shared between environments. Credentials
rotate every 90 days through the secrets manager. A service account that has not
authenticated in 45 days is automatically disabled.
