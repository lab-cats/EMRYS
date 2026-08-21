# Troubleshooting

Use this guide to preserve evidence, classify a failure, and route recovery.
Exact commands live in the adjacent owner README; exact interfaces and checks
live in its `CONTRACT.md`.

## Common recovery rules

Before retry, deletion, restoration, or adoption of uncertain output:

1. Stop new writers and downstream readers. Inspect scheduler/process state,
   the lock owner, and every declared output root.
2. Preserve stable outputs, run-token staging, temporary, backup, quarantine,
   recovery, and lock paths; logs and accounting; command and checkout; tools
   and environment; input identities and hashes; filesystem identity; and
   unrelated directory entries.
3. Treat an absent lock, backup, receipt, or marker as missing evidence—not a
   clean state. A visible receipt or summary is valid only when the complete
   transaction validates.
4. Never delete a foreign lock, combine attempts, manufacture a receipt, infer
   ownership from names or timestamps, or overwrite a late or identity-changed
   path.
5. Choose and record one recovery target: a validated predecessor, a validated
   new transaction, or a clean first-publication state. Remove only residue
   whose ownership is proved.
6. Use an isolated absolute output root for diagnostics that must not disturb
   the questioned state. Diagnostic success is not production evidence.

Git rollback changes tracked implementation only. It does not authenticate or
restore runtime artifacts. A validator or evidence command can exit `0` while
recording failed evidence rows; exit `2` means unsafe input, CLI, tool, or
publication failure.

## Public local-pilot diagnosis

Begin with the root [researcher journey](../../README.md). Keep the exact
request, runtime profile, run root, and clean source checkout selected for the
attempt; changing them is not recovery.

The table spells out command intent compactly. Invoke every `run`, `resume`,
and `inspect` route with the controlled checkout interpreter shown in the root
journey: `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad` followed by
the displayed subcommand and arguments. The doctor uses the same controlled
prefix: `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad doctor
local-pilot ...`.

| Observed state or symptom | Public route and safe response |
| --- | --- |
| Doctor prints `NOT READY` | Read every `BLOCKER` and `REMEDIATION` from `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad doctor local-pilot ...`. Correct the declared input, checkout, workspace, or runtime outside the doctor, then rerun it. Do not start `norad run`. |
| Doctor exits `2` | The request, runtime profile, or path boundary is malformed or unsafe. Correct the authored file or path; do not bypass admission or edit a result to manufacture `READY`. |
| Readiness passed, but execution has not started | Run `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad run ...` without `--execute` and review the complete no-write plan. Add `--execute` only to the identical admitted request after review. |
| An initial run fails or its state is uncertain | Run `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect local-pilot-run --run-root /absolute/run/root`. Do not submit another initial run against the existing run root. |
| Inspection prints `resume_available` and `Resume available: yes` | Run `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad resume --run-root ... --runtime-profile ...` without `--execute`; review reusable and pending jobs; then add `--execute` to that resume command. NORAD re-admits completed work before reuse. |
| Inspection prints `blocked` | Preserve the complete run root, attempt receipts, locks, task/reporting ledgers, logs, native artifacts, partials, backups, and recovery markers. No public command forces, unlocks, cleans, or automatically reconciles an owner that crossed producer entry without verified completion. Route the failing scope to its owner below. |
| Inspection prints `local_pipeline_complete` | Resume refusal is expected. Use the validated products and receipts under the inspected run root; a new analysis requires a separately admitted request and run identity. |
| `Run root already exists; inspect or resume it instead` | Use `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad inspect local-pilot-run --run-root ...` on that exact root. Never delete or rename it merely to make an initial run start. |
| Step `00c` cannot create or re-admit the reference FAI/dictionary | Stop before downstream work. Preserve the FASTA, `<reference-fasta>.fai`, `<reference-stem>.dict`, and every adjacent Step `00c` lock/staging path. Confirm that the declared external reference directory is the intended writable sidecar authority; do not copy, delete, or regenerate one member independently. |

Control-plane fixtures, real-tool demonstrations, and scheduled runs establish
different evidence. Consult [`HANDOFF.md`](HANDOFF.md) for the exact current
commit, commands, artifacts, and ceiling; do not infer a current execution
claim from this recovery guide.

## First-run admission blockers

| Symptom or message | What it means | Safe next action |
| --- | --- | --- |
| Shell prints `permission denied` or `is a directory` for a path | A directory or nonexecutable data file was entered as though it were a command. | Use `cd /absolute/path/to/norad` for the checkout and invoke NORAD through its selected `.venv/bin/python`; pass data paths only as command arguments. |
| `No module named norad` | The selected Python does not contain this checkout's installed package. | From the clean checkout, perform the explicit locked setup with `uv sync --locked --group workflow`, then use that checkout's `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad`. Do not add `PYTHONPATH`. |
| Selected interpreter imports another checkout | The Python/package authority differs from the current Git tree. | Stop, bind `NORAD_PY` to the intended checkout's `.venv/bin/python`, and rerun help. Do not copy package files between environments. |
| Doctor says the checkout is dirty | Runtime identity cannot bind an uncommitted implementation. | Inspect `git status --short`; preserve and resolve the changes through the approved development workflow. Do not stash or discard unrelated work merely to make doctor pass. |
| Request contains an unknown/duplicate field or YAML merge | The request schema is intentionally closed and merge expansion is disabled. | Start from the matched starter and author each literal supported field once. Do not use anchors, templates, or environment interpolation. |
| FASTQ, manifest, partition, FASTA, or GTF path is rejected | Paths resolve from the request directory and must name stable regular files using the explicit path vocabulary. | Correct the authored path. Remove `~`, `$VAR`, globs, redundant separators, and `.`/`..` components; do not create a symlink workaround. |
| Control/treatment pairing is rejected | `replicate` is the pairing authority and the two analysis conditions do not define identical paired strata. | For at least two replicate IDs, provide exactly one control row and one treatment row with the same replicate value. Do not rely on row order or sample-name patterns. |
| R1 and R2 are identical or compression differs | One paired library must have two distinct files with the same plain/gzip mode. | Correct the manifest or upstream staging; do not rename the same file twice. |
| Partition or contig later fails owner validation | The declared selector does not reconcile with the FASTA/FAI or partitions overlap. | Preserve the attempt. Correct reference/partition preparation for a new admitted request; do not hand-edit VCFs or receipts. |
| Workspace already exists | Initial publication is create-absent and refuses adoption. | Inspect it if it is a NORAD workspace. Otherwise choose a different absent child under an existing writable parent; do not delete an uncertain directory. |
| Workspace or reference sidecars are on unqualified storage | Locking, hard-link, rename, visibility, durability, or head/compute access is not admitted. | Run both phases of `norad inspect storage-qualification` for the exact workspace/reference pair. Stop if it fails; scheduler availability is not storage support. |

## Runtime and scheduler blockers

| Symptom or message | What it means | Safe next action |
| --- | --- | --- |
| Tool is visible on the login node but absent in a job | Login and batch module environments differ. | Submit a small batch probe to the intended compute node, load modules in that job, and author the resulting canonical executable paths. Do not treat the head-node result as runtime evidence. |
| `module avail` lists a tool but doctor cannot run it | A module name is not a selected executable identity. | Load the module in the execution context, resolve the actual command/jar, confirm its version, and put the absolute target in the runtime profile. |
| `module purge` emits unload errors | The site has default modules whose unload metadata is incomplete. | Preserve the output and use the site's supported module initialization/selection. Do not infer that requested scientific modules failed solely from purge warnings; inspect `module list` and actual probes. |
| Java module name and `java -version` disagree | The site module may expose the system launcher or only supporting variables. | Author the canonical executable that actually reports Java 17 or newer. Picard and GATK use that same selected launcher. |
| Picard sets `PICARD`, not `PICARD_JAR` | The site module's environment name differs from a generic probe. | Put the actual readable Picard 3.1.1 jar path in the `picard_jar` row and its coupled `-jar` argument. NORAD does not depend on either environment-variable name. |
| `srun` or `sbatch` reports an unsatisfied memory/node configuration | The requested launcher resources or placement do not match an eligible node, or the site rejects explicit memory. | Inspect `sinfo` and account policy. Set launcher `memory: site-default` only when the site supplies memory and rejects `--mem`; otherwise keep an explicit reviewed size. Recheck `exclusive` and `nodelist` together. |
| `invalid partition specified` | A literal placeholder or unavailable partition was submitted. | Use a partition authorized for the account, verified by `sinfo`/site policy. Do not submit `YOUR_PARTITION` or another documentation placeholder. |
| `tail` says the SLURM log does not exist | The job is pending or SLURM has not opened the declared stream; the parent may also have been absent at submission. | Ensure the log parent existed before `sbatch`, inspect `squeue`/`sacct`, wait until both exact `%j` paths exist, then use `tail -n +1 -F`. |
| `TMPDIR [/local/tmp] is not writeable` | The inherited temporary directory is unusable. | Set generated-wrapper `NORAD_SCRATCH_PARENT` to an existing writable compute path. Confirm the logged private `TMPDIR`, filesystem, and capacity; do not rely on fallback `/tmp`. |

## Result and report questions

| Observation | Interpretation |
| --- | --- |
| Standalone Steps `07`–`09` passed but no HTML reports exist | Expected: standalone wrappers publish native outputs and validation TSVs only. They are not adopted into orchestration state. Use `norad run` for automatic reporting; `norad build report` requires an existing canonical run summary. |
| Report labels results `not scientifically adjudicated` | Expected: NORAD reports computational candidates and provenance only. Keep external review, adjudication, or biological-interpretation records separate from the run. |
| Significant computational rows are present | They passed the declared Step `09` depth, background, FDR, odds-ratio, and allele-fraction-change rules. They remain review candidates, not validated editing sites. |
| Candidate table has rows but significant table is empty | Step `08` found candidate SNVs, but none passed every strict Step `09` call threshold. Inspect `test_status` and `call_status`; do not relax policy after seeing results without creating and justifying a new analysis request. |
| Step `08`/`09` tables are header-only | Zero candidates can be valid when upstream receipts and all zero counts reconcile. Confirm owner validation and the run summary rather than assuming a crash. |
| `Computational results` says its tables or figures are unavailable | Confirm the exact run/report identity and inspect the primary-analysis Step `09` all-sites, significant-sites, summary, mutation-spectrum, and owner-validation artifact records. The renderer requires that complete exact bundle plus an exact all-pass validation report and opens no candidate rows or scientific figures from an incomplete or nonpassing set. Preserve the renderer receipt and route a mismatch to the reporting owner. |
| Sequence, motif, or candidate-context figures are unavailable | Inspect the primary-analysis Step `10` context receipt, its four bound TSVs, and the one-check owner validation report. An absent complete bundle leaves only the dependent figures unavailable; a present but inconsistent bundle fails report preparation. Verify the exact FASTA/FAI, motif catalog, Step `09` trio, hashes, and policy recorded by the receipt rather than reconstructing context in reporting. |
| HTML shows fewer candidates than the source count | Each report candidate table is intentionally capped at 250 displayed rows. Read its explicit truncation note, exact source path/hash/size/full row count, then use the bound native TSV for the complete table. |
| `FWD_like` and `REV_like` disagree with expected library strand | They are mechanical SAM-flag groups and do not claim biological strand, sense, or antisense. Use the separate RSeQC evidence in the external interpretation process; do not relabel native artifacts. |

## Common environment and operation matrix

| Symptom | Response |
| --- | --- |
| `logs/...: No such file or directory` at submission | Create `logs/` before `sbatch`; SLURM opens streams before the job body. |
| Empty `.err` or `COMPLETED 0:0` | Inspect both streams, accounting, outputs, and owner validation; neither is proof alone. |
| Wrong log prefix | Locate the job's actual files; do not borrow a prefix from another owner. |
| `/local/tmp` is unwritable | Set the generated wrapper's explicit writable scratch parent and inspect its logged private `TMPDIR` capacity. |
| Tool/module appears on login but not in a job | Establish the exact executable in the approved batch context. Module names are not runtime proof. |
| Picard `UnsupportedClassVersionError` | Step `04` requires the effective Java major version to be at least 17. Validate the selected executable, not `JAVA_HOME` alone. |
| R or namespace unavailable | Restore only as a separate operator action into the declared library, then run strict non-mutating `r-check` in the compute context. The workflow and generated wrapper never install. |
| `uv` is unavailable | Use the [official user-level installer](https://docs.astral.sh/uv/getting-started/installation/) as an explicit setup action, run `uv --version`, then `uv sync --locked --group workflow`. NORAD commands never install it. |
| `uv sync --locked` reports a stale lock | Stop and review the `pyproject.toml`/`uv.lock` diff. Do not relock as an incidental setup side effect. |
| Validation reports that the selected Python environment does not match `uv.lock` | Run `uv sync --locked` as an explicit setup action, then rerun validation. Do not let the validation command repair or relock the environment. |
| Offline wheel installation cannot find a package | Prepare an approved local cache or wheelhouse for the complete locked runtime graph. Do not omit dependencies, add checkout paths, or enable network access inside the package test. |
| Quiet local gate appears silent | Wait for the lane result or inspect retained failure/interruption logs; use serial or verbose mode for diagnosis. |
| Coverage regression | Inspect the exact environment, subprocess data, module, and JSON diff. Never update the baseline merely to pass. |
| Schema fixture or synthetic report passes | Report local contract evidence only; it is not production, cluster, scientific-review, or biological proof. |

## Owner-specific defect matrix

These are current characterized boundaries, not approved behavior. Follow the
linked owner after applying the common rules.

| Owner | Characterized defect or evidence limit | Required disposition |
| --- | --- | --- |
| [`construct_STAR_index`](../../src/norad/stages/star_index/README.md) | Reference/index disagreement or ambiguous validation-report predecessor can survive around publication. | Preserve index, parameters, reference identities, report transaction, lock, and logs; rebuild only through the owner. |
| [`convert_GTF_to_BED12`](../../src/norad/stages/gtf_to_bed12/README.md) | Final/intermediate BED may disagree with deterministic GTF normalization. | Preserve both plus GTF and logs; never hand-edit BED12. |
| [`construct_FASTA_sidecars`](../../src/norad/stages/fasta_sidecars/README.md) | FAI may publish before DICT failure; malformed or mismatched sidecars are not repaired. | Preserve FASTA, both sidecars, stage/backup/lock state, and provenance; recover through the owner. |
| [`align_RNA_reads_with_STAR`](../../src/norad/stages/star_alignment/README.md) | Five direct final outputs may be partial or mixed after failure. | Preserve the entire attempt and scheduler evidence; diagnose in an isolated root. |
| [`construct_canonical_BAM`](../../src/norad/stages/canonical_bam/README.md) | A severe restoration failure can lose the prior BAM while leaving a prior BAI with no recovery marker. | Stop downstream readers; preserve the whole directory and reconstruct only after separate review. |
| [`collect_canonical_BAM_QC_evidence`](../../src/norad/evidence/canonical_bam_qc/README.md) | Direct-final quickcheck/flagstat writes can leave a partial, mixed, or stale pair accepted by existence checks. | Establish attempt identity for both files before retry or reuse. |
| [`collect_RSeQC_paired_orientation_evidence`](../../src/norad/evidence/rseqc_orientation/README.md) | Direct stdout redirection can leave partial, empty, or stale reports. | Preserve report, streams, BAM/BAI, BED12, tool, and job identity; retain mechanical labels. |
| [`mark_BAM_duplicates_with_Picard`](../../src/norad/stages/duplicate_marking/README.md) | BAM, BAI, and metrics are not an all-or-none transaction and may be mixed or stale. | Stop Step `05`; preserve the triplet, input, Java/Picard/samtools identities, streams, and directory metadata. |
| [`split_N_cigar_reads_with_GATK`](../../src/norad/stages/split_n_cigar/README.md) | Best-effort restoration may lose the prior BAM, restore only BAI, and erase recovery evidence. | Stop Step `06`; isolate diagnostics and preserve all final, staged, backup, temp, lock, reference, and scheduler state. |
| [`partition_BAM_by_mechanical_read_orientation`](../../src/norad/stages/mechanical_orientation/README.md) | Two output roots can collide on shared counts; severe rollback can lose one prior BAM and stale files may pass existence checks. | Stop every writer/reader to both roots; isolate both roots for diagnosis and preserve all five outputs and locks. |
| [`generate_partitioned_cohort_mpileup_VCFs`](../../src/norad/stages/partitioned_cohort_mpileup/README.md) | Receipt visibility precedes final validation; restoration can leave a prior final absent and wrapper checks can accept a stale set. | Preserve VCFs, receipt, manifests, input pairs, run-token paths, lock, selector, and tool identity. A header-only VCF is valid only when its zero count reconciles. |
| [`preprocess_and_annotate_cohort_candidates`](../../src/norad/stages/cohort_candidate_preprocessing/README.md) | Cross-root rollback lacks a durable marker; receipt visibility precedes final validation and stale triples may pass existence checks. | Stop Step `09`; preserve both roots, all transactions and manifests, R environment, locks, backups, and streams. |
| [`rank_cohort_candidates_with_paired_CMH`](../../src/norad/analyses/paired_cmh_candidate_ranking/README.md) | Scheduler success can accept stale six-file output; severe rollback and lock states remain. Production validation does not independently recompute CMH statistics. | Preserve all six outputs, upstream transaction, selected R program/runtime, streams, lock, backups, and scheduler identity; retain the separate test oracle evidence ceiling. |
| [Runtime availability](../../src/norad/evidence/runtime_availability/README.md) | Exit `0` may contain `fail`, `blocked`, or `not_checked`. Lock acquisition can strand a lock; failed restoration leaves only a `.previous` file without a lock or marker; suppressed lock-cleanup failure can report success while retaining the lock. | Inspect every row and asserted context. Preserve the report and all lock, temporary, and previous paths; absence of the lock is not publication proof. |
| [Reference provenance](../../src/norad/evidence/reference_provenance/README.md) | Hash/contig disagreement is observation only. | Correct declarations or regenerate through the upstream owner; never repair references in the evidence tool. |
| [Storage inventory](../../src/norad/evidence/storage_inventory/README.md) | Measurement or policy state grants no retention authority; its three-file publication can remain ambiguous. | Preserve the transaction and approval state; never mutate storage content through this tool. |
| [Artifact contracts and reporting](../../src/norad/reporting/README.md) | Schema, adapter, summary, and direct Jinja report transactions have distinct locks, identities, receipts, and rollback boundaries. A v1 or incomplete report directory is rejected rather than adopted. Completion markers do not promote evidence. | Recover within the exact owner transaction; use a fresh report output root for retired v1 state unless migration is explicitly approved. Never mix records, edit hashes/statuses, install from rendering, or call synthetic output production evidence. |

## Scientific and evidence ceiling

`FWD_like` and `REV_like` remain mechanical groupings. Step `09` produces
CMH-ranked candidates, not validated editing sites. A report, application log,
transaction receipt, or successful computation cannot establish a scientific
or biological conclusion. Candidate review, adjudication, and biological
interpretation remain external work-process records, not pipeline states.
