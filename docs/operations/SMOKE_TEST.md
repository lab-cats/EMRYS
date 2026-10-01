# Optional Viking smoke test

This small example checks installation, tool preparation and execution with
made-up reads and a supplied reference. It adds Doctor setup, queue and Run
time. Success does not establish that the real study fits the resources or that
its scientific choices are correct.

Complete [Quickstart installation and setup](../../quickstart.md#1-install-emrys)
first. Use the Viking head node and the default Projects home from that guide.
To return in another terminal, use the
[shared reconnect instructions](../../quickstart.md#returning-to-the-project-in-a-new-terminal).

## Create and validate the example

From the EMRYS checkout:

```bash
cd "$EMRYS_SOURCE_ROOT"
```

Create the supplied example once:

```bash
emrys init synthetic --output-dir "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke" --execute
```

Continue after `Synthetic Project: ready` and the printed Project path:

```bash
cd "$EMRYS_SOURCE_ROOT/Projects/emrys-smoke"
```

Check the supplied inputs:

```bash
emrys validate
```

Continue only after `Project validation: PASS`. At any error, keep the output
and log path and follow [Troubleshooting](TROUBLESHOOTING.md); do not delete the
partial Project to retry.

## Prepare, run and inspect

Prepare the tools and storage:

```bash
emrys doctor --repair
```

Review the plan and answer `y`. First setup can take 5–25 minutes, plus
Slurm queue time. Continue only after `EMRYS is ready.`.

Preview and submit one Run:

```bash
emrys run
```

Review its resource request and answer `y` once. Keep its job and log paths;
a queued submission may not have a Run yet. Watch it:

```bash
emrys watch
```

When it announces `Run complete`, leave with `q` and verify:

```bash
emrys inspect
```

Require valid Run admission, a succeeded Attempt, complete Scientific Results
and complete Reporting. The example should produce three candidate rows, one
passing its thresholds. Open and copy reports using
[Quickstart step 7](../../quickstart.md#7-copy-and-open-the-reports); record any
visual or link problems separately from computational completion.

## Continue with the real study

Return to the checkout:

```bash
cd "$EMRYS_SOURCE_ROOT"
```

Continue at [Quickstart step 2](../../quickstart.md#2-gather-the-study-inputs-and-scientific-choices).
After creating the real Project, [step 5](../../quickstart.md#5-prepare-the-scientific-tools-and-storage)
reuses these prepared tools **before Doctor**. Keep the smoke Project and its
runtime; the real Project may depend on them.
