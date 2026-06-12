# Runbook

# Discovered info

## Confirmed bioinformatics modules

- `star/2.7.11b`
  - executable: `STAR`

- `samtools/1.19.2`
  - executable: `samtools`

- `picard/3.1.1`
  - loads `java/17.0.10`
  - sets `PICARD=/cm/shared/apps/picard/picard/build/libs/picard.jar`
  - invoke with: `java -jar "$PICARD" <PicardCommand>`

- `python39`
  - preferred current Python module unless changed later

## Still unresolved

- GATK module/location
- R/Rscript module/location
- reference genome / STAR index paths
- RNA-seq input data location
- SLURM memory/partition/account rules

## Available CSU modules discovered

Known available modules:

- `slurm/slurm/21.08.8`
- `star/2.7.11b`
- `samtools/1.19.2`
- `picard/3.1.1`
- `python3`
- `python39`
- `python314`

Still need to identify:

- GATK module
- R module
- preferred Python version
- reference genome / STAR index paths
- full RNA-seq data location

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


# Prep list

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
