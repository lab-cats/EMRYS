# Stable task cards

Create new actionable cards in this directory and keep their path stable for
their lifetime. The explicit `State:` field in each card owns lifecycle state;
selection and ordinary execution do not move or rewrite the card.

The canonical schema, state semantics, legacy compatibility rules, and status
view command are defined by the parent [task-registry contract](../README.md).
Do not store generated status projections in this directory.
