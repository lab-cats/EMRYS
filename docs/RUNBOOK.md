# Runbook

# Cluster first login checklist

## 1. Confirm identity and location

```bash
hostname
whoami
pwd
```

## 2. Check SLURM

```bash
which sbatch
which squeue
which sinfo
squeue -u "$USER"
sinfo
```

## 3. Check modules

```bash
module avail
module list
```

## 4. Create project directory

```bash
mkdir -p ~/norad
cd ~/norad
```

## 5. Get code onto cluster

```bash
git clone https://github.com/Glen-Cocoa/norad.git .
```

## 6. Run smoke test

```bash
mkdir -p logs
sbatch jobs/hello.slurm
squeue -u "$USER"
cat logs/norad-hello-*.out
cat logs/norad-hello-*.err
```

## 7. record cluster-specific info

7. Record cluster-specific facts

Update docs/QUESTIONS.md / docs/RUNBOOK.md with:

login node
storage paths
module names/versions
SLURM partition/account
reference genome paths
data locations

## 1. Prepare environment

```bash
module load ...
```

## 2. Check input files

```bash
ls ...
```

## 3. Validate the sample manifest

Run this as a lightweight preflight check before submitting workflow jobs:

```bash
python3 scripts/validate_manifest.py \
  --manifest samples.example.tsv \
  --base-dir . \
  --check-files
```

Use the cluster manifest and cluster project/data path when running full-scale jobs.

## 4. Run step1

```bash
sbatch jobs/step_01_align.slurm
```

## 5. Check logs

```bash
squeue -u <username>
tail -f logs/...
```

## 6. Verify outputs

```bash
ls results/...
```

## 7. Continue to next step
