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

Expansion runs with the Makefile's declared `?=` defaults: the test removes
caller-supplied values for those variables and inherited recursive-Make state.
It also inventories the declared configurable variables, so adding a new one
requires explicit review of this fixture contract.

This fixture characterizes local command expansion. It does not execute
recipes, authorize dependency restoration or output publication, or establish
scheduler, runtime, cluster, scientific, or biological evidence. Update it
only as part of an explicitly reviewed Make-interface change.
