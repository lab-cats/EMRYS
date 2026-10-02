# Runtime-availability tests

These tests check runtime profiles and the Project/Run-read-only probes used by
[runtime availability](../../../src/emrys/evidence/runtime_availability/README.md).
They preserve tool and package checks, context handling, bounded execution,
path visibility, and the observations consumed by Doctor and the coordinator.
Snakemake cases also invoke the installed backend with an empty workflow in
disposable scratch, including restricted login-name lookup. Separate injected
runner cases exercise timeouts and launch failures. Actual local startup does
not establish cluster accessibility or successful study execution.

Whole-Run scheduler/runtime agreement is checked by the coordinator's synthetic
driver. Mocked probes cannot establish that CSU modules ran or dependencies work
in batch. Tests solely for the retired standalone report publisher are removed.

## Restored-cache symlink verification

`RUN-01` is verified by [managed golden job 110679892115](https://github.com/lab-cats/EMRYS/actions/runs/36956303545/job/110679892115)
for source `06f88dbca7161599d7445f8cb2bfedf58f377282`. The runner checked out
PR merge `48fb38d0a613669aa79c6906392895ed0a93daf7`; both commits have tree
`4a3f00f74a06a1eb178ee580d289b3bc0292f87b`. This is hosted real-runtime evidence,
not institutional, transitive-dependency-closure or scientific validation.

The retained [managed golden artifact 11205479927](https://github.com/lab-cats/EMRYS/actions/runs/36956303545/artifacts/11205479927)
contains the direct evidence, independently reconciled on 2026-10-02:

- `project/runtime/runtime.tsv` selects the restored library;
  `donor-before.namespace.tsv` records its `VariantAnnotation` member as a
  symlink to the managed renv cache's `VariantAnnotation/1.58.0/cb9d52ae112de741b34d7a888df76ae7/VariantAnnotation`.
- The Doctor JSONL records `r_variant_annotation` passing at `runtime_discovery`
  (sequence 33) and `project_readiness` (59), with that same resolved root,
  version `1.58.0`, and the digest of the retained runtime inventory.
- The successful Attempt and `project/runtime/shared.json` bind that same root
  and package-tree SHA-256
  `d83bed6ca876a3bbdff4931ef33ea9c8aa6702152aee0cd150cd77eb3eaecb07`.
  `05-inspect.log` records valid Run admission, a succeeded Attempt, complete
  computational Results and complete reporting.

The Run is `run-f5e03bf68c4296a2546c03c86b684f87c57ae3cff501406876a0b786fb2b1f47`;
the Attempt is `workflow-20261002T023915Z-50142f9c16c842dcbd1b5d52b28e515c`.
The downloaded artifact ZIP SHA-256 is
`ebce71c4006638b54080b64e0a78ecc4212bb3a65e66f3605e1f24156c5e6794`.
Raw evidence remains outside the repository. The existing retarget-after-hashing
refusal and managed-generation containment checks remain separate protections;
this positive observation neither replaces them nor expands the fixed package roster.
