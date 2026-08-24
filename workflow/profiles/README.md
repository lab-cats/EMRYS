# Snakemake execution profiles

This directory contains checkout-bound Snakemake engine settings selected by
EMRYS's lifecycle. These YAML files are execution profiles; they are distinct
from the JSON workflow-projection contracts under
[`../contracts/`](../contracts/README.md).

The current [`local/`](local/README.md) family executes the supported graph on
one host. That host may be a workstation or a single allocated Slurm node.

Execution profiles do not define the scientific graph, public owner commands,
scientific resource identity, standalone-stage scheduling, Slurm submission,
or recovery admission. Requests own capacity, functional owners own their work,
and local-pilot lifecycle owns invocation and recovery.

Operators select no profile directly: `emrys run` and `emrys resume` bind the
supported file from the exact source checkout. Adding a family or selectable
profile is new execution surface and requires explicit approval.

