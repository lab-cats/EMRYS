# Public CLI contract fixtures

`make_target_expansions.json` is the reviewed literal stdout contract for
side-effect-free dry expansion of every public Make target:

```text
make -n --no-print-directory -C <repository> <target>
```

Only the absolute checkout path and recursive-Make executable identity are
normalized, to `<REPO_ROOT>` and `<MAKE>` respectively. The latter has literal
tests for bare and absolute `make` and `gmake` forms. Commands, arguments,
ordering, quoting, versions, and nested target expansion remain literal. The
test reads this committed fixture; it does not derive expected commands from
the Makefile under test.

Expansion runs with the Makefile's declared `?=` defaults in a bounded process
environment. It preserves only executable lookup, temporary-directory, and
platform process-launch variables, fixes `LC_ALL=C`, and excludes ambient Make
state such as `MAKEFILES`, `MAKEFLAGS`, `GNUMAKEFLAGS`, and `MAKEOVERRIDES`.
A direct contamination regression protects that isolation. The test also
inventories declared configurable variables, so adding one requires explicit
review of this fixture contract.

This fixture characterizes local command expansion. It does not execute
recipes, authorize dependency restoration or output publication, or establish
scheduler, runtime, cluster, scientific, or biological evidence. Update it
only as part of an explicitly reviewed Make-interface change.
