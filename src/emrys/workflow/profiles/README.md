# Snakemake engine settings

These YAML files configure the engine, separately from the JSON
[workflow graphs](../contracts/README.md). The current [local profile](local/README.md)
runs on one host. It defines neither the scientific graph nor stage commands,
Run resource identity, Slurm submission, or recovery.

The lifecycle binds the profile from the admitted installed package; operators do
not select it directly. Adding another selectable profile changes supported
execution behavior and requires explicit approval. The [workflow overview](../README.md)
explains how these files enter execution.
