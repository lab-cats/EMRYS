# Public CLI contract fixtures

`make_target_expansions.json` is the literal stdout contract for no-write
expansion of every public Make target. Tests normalize only the absolute
checkout path and recursive-Make executable identity. They accept the complete
GNU Make 3.81/4.3 rendering difference of one leading recipe tab, but reject
mixed indentation or changes to commands, arguments, order, quoting, versions,
or line boundaries.

Expansion uses declared Make defaults in a bounded environment, excludes
ambient Make state, and fixes `LC_ALL=C`. The test also inventories configurable
variables. Update this fixture only with an explicitly reviewed Make-interface
change; it characterizes command expansion and executes no recipe.
