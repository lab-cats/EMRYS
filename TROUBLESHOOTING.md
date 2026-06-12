# Troubleshooting

## `TMPDIR [/local/tmp] is not writeable`

Use:

```bash
#SBATCH --export=ALL,TMPDIR=/tmp
```
picard: command not found

Use:

```bash
module load picard/3.1.1
java -jar "$PICARD" MarkDuplicates ...
```

#SBATCH --mem=1G fails

Observed error:

`Memory specification can not be satisfied`

Avoid explicit --mem until CSU partition/memory rules are confirmed.