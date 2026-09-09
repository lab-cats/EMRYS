# Mechanical-orientation tests

These cases check Step 06 flag grouping, tool failures, count arithmetic, and
structural validation through the grouped command. Shared runner tests cover
publication, interruption, and recovery. Private `validator.py` is not a direct command. The
[stage contract](../../../src/emrys/stages/mechanical_orientation/CONTRACT.md)
defines the exact behavior.

`FWD_like` and `REV_like` fixture groups describe read flags; they do not
establish transcript strand or sense/antisense direction.
