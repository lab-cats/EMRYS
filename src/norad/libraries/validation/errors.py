"""Shared validation failure types and helpers."""

from __future__ import annotations


class ValidationError(RuntimeError):
    """Raised when validation or publication cannot proceed safely."""


def fail(message: str) -> None:
    """Raise a validation failure with a stable public diagnostic."""

    raise ValidationError(message)
