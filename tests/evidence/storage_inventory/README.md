# Storage inventory and qualification tests

This directory protects both optional storage inventory and required
two-phase storage qualification for the
[storage-inventory owner](../../../src/emrys/evidence/storage_inventory/README.md)
and its grouped routes. Inventory records caller-declared roots, measurements,
and retention-policy state for operator diagnosis. Qualification performs the
compute/finalize site checks whose final receipt is consumed by local-pilot
doctor.

The suite covers admission, deterministic outputs, publication, rollback, and
CLI failures for both roles. Synthetic filesystem cases do not authorize
retention action, verify a production inventory, qualify a production storage
path, or establish an approved production retention policy.
