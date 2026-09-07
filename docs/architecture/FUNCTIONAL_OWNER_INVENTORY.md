# Current functional-owner inventory

This is a stable routing map, not a hand-maintained copy of every file, command,
test, or schema. `emrys --help` owns the installed command roster;
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md) owns semantic workflow
identities and edges; [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md)
owns permitted dependencies and shared seams. Each implementation's adjacent
`README.md`, `CONTRACT.md`, and mirrored tests own its exact behavior.

## Product owners

| Responsibility | Owner |
| --- | --- |
| Project creation, admission, Doctor, immutable Run planning, direct/Slurm placement, resume, inspection, and report invocation | [`orchestration/run_coordinator/`](../../src/emrys/orchestration/run_coordinator/README.md) |
| Reference and per-sample processing plus cohort candidate preparation | [`stages/`](../../src/emrys/stages/) and [`evidence/`](../../src/emrys/evidence/) owners listed by the [stage map](../../src/emrys/contracts/STAGE_MAP.md) |
| Built-in paired-CMH ranking and scientific-context projection | [`analyses/paired_cmh_candidate_ranking/`](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md) |
| Collaborator analysis-module admission | [`analyses/`](../../src/emrys/analyses/README.md) and the installed `emrys.analysis_modules` entry point selected by the Project |
| Artifact indexing, canonical summaries, and module-aware static reports | [`reporting/`](../../src/emrys/reporting/README.md) and the selected `emrys.analysis_reporters` provider |
| Artifact, orchestration, and scientific-evidence contracts | [`contracts/`](../../src/emrys/contracts/) |
| Narrow cross-owner parsing, validation, identity, publication, and logging mechanics | [`libraries/`](../../src/emrys/libraries/) seams admitted by [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) |

## Command audiences

| Audience | Surfaces |
| --- | --- |
| Scientist | `init`, `validate`, `doctor`, `run`, `resume`, `inspect`, and `report` |
| Operator | `runtime discover`, specialist `validate`, `reconcile`, `debug`, `convert`, and documented direct owner tools |
| Workflow | `validate all-pass` and the private Run task boundary |
| Maintainer | Make targets and repository scripts documented by their own `--help`, adjacent README, or engineering convention |

Importability, an executable bit, or a module-local harness does not create a
supported public surface. A command's owner and compatibility boundary remain
defined by its parser, adjacent contract, and direct tests.

## Repository development

The root [`Makefile`](../../Makefile) routes developer gates to focused includes
under [`scripts/`](../../scripts/). Documentation structure inspection belongs
to [`validate_structure.py`](../../scripts/documentation/validate_structure.py);
tests mirror their production owner under [`tests/`](../../tests/). Live Git
and checks bound to an exact commit own current validation status.
