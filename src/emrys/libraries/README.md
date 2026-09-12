# Internal libraries

Libraries provide shared parsing, validation, filesystem, runtime, and logging
mechanics. Their callers keep scientific policy, check lists, commands, and
interpretation of evidence. [SOURCE_TOPOLOGY](../contracts/SOURCE_TOPOLOGY.md)
defines each library's permitted consumers and import direction; a helper's
presence does not make it a general utility. New shared code must replace
proven-equivalent implementations across its callers.

## Shell workers

`argument_parsing.sh`, `file_checks.sh`, and `gatk_invocation.sh` support the
Bash scientific workers. They require the runner's absolute executable
paths and bound Python for hashing. Tool discovery belongs to runtime admission;
workers do not search PATH, environment overrides, or alternative hash tools. The
[Run task runner](../orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution)
owns those operations across all scientific owners.
