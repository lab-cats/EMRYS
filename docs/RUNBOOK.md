```md
# Runbook

## 1. Prepare environment

```bash
module load ...
```

## 2. Check input files

```bash
ls ...
```

## 3. Run step1

```bash
sbatch jobs/step_01_align.slurm
```

## 4. Check logs

```bash
squeue -u <username>
tail -f logs/...
```

## 5. Verify outputs

```bash
ls results/...
```

## 6. Continue to next step