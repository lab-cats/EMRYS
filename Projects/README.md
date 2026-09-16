# EMRYS Projects

This directory is the home for Projects created from this EMRYS checkout.
Follow the Quickstart to enter this directory; EMRYS creates each new Project
as one absent child here. Do not create the Project child yourself.

Each Project contains its own `project.yaml`, `samples.tsv`, `partitions.tsv`,
runtime preparation, logs, Runs, and Results. FASTQs and references remain in
their declared durable locations and must remain available for the life of the
Runs that use them.

Project children are ignored by Git. Do not force-add Projects, scientific
inputs, runtime tools, logs, or Results. Preserve a partial Project after an
error and follow the printed diagnostic; do not delete it to retry.
