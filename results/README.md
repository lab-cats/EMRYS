# Generated results

`results/` is the ignored repository-level root for generated pipeline,
validation, evidence, analysis, and reporting artifacts. This README keeps the
root present in a fresh checkout; all other root children are ignored by
default and are created by their functional owners as needed.

Each owner controls its own subtree, output contract, locks, staging,
validation, rollback, and recovery. The root is a storage convention, not a
central publication implementation. Generated output is not automatically
validated, publishable, or evidence-promoting.

## Retention and cleanup

Generated does not mean disposable. Before deleting a subtree, identify its
owner and confirm that no active process, lock, recovery marker, validated
evidence, report, or retention requirement depends on it. Storage inventory
and retention contracts record operator decisions but never execute deletion;
see the [storage-inventory owner](../src/norad/evidence/storage_inventory/README.md).
