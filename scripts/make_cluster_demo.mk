demo-step03-dry-run:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,SAMPLE_ID=$(DEMO_SAMPLE) \
		src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm

demo-step03:
	mkdir -p logs
	sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1,SAMPLE_ID=$(DEMO_SAMPLE) \
		src/norad/evidence/collect_RSeQC_paired_orientation_evidence/step_03_infer_strandedness_and_orientation.slurm
