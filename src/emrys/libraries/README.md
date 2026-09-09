# Internal libraries

Libraries provide shared parsing, validation, filesystem, runtime, and logging
mechanics. Their callers keep scientific policy, check lists, commands, and
interpretation of evidence. [SOURCE_TOPOLOGY](../contracts/SOURCE_TOPOLOGY.md)
defines each library's permitted consumers and import direction; a helper's
presence does not make it a general utility. New shared code must replace
proven-equivalent implementations across its callers.

## Shell workers

`argument_parsing.sh`, `file_checks.sh`, `executable_resolution.sh`, and
`gatk_invocation.sh` support the native scientific workers. Their former
locking, signal, and publication helpers have retired; the
[Run task runner](../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution)
owns those operations across all scientific owners.
