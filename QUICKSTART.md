# Quick Start Guide

Get your neuroimaging pipeline running in 5 minutes!

## Prerequisites

- [ ] HPC cluster with Slurm
- [ ] Apptainer available on compute nodes
- [ ] Nextflow installed
- [ ] FastSurfer container: `images/fastsurfer-cpu.sif`
- [ ] FreeSurfer license: `fs_license/license.txt`
- [ ] T1-weighted images

## 5-Minute Setup

### 1. Verify Prerequisites (1 min)

```bash
# Check Nextflow
nextflow -version

# Check Apptainer (on compute node)
srun --partition=hpcnirc apptainer --version

# Check required files
ls images/fastsurfer-cpu.sif
ls fs_license/license.txt
```

### 2. Prepare Input Data (1 min)

```bash
# Place your T1 images in nii/ directory
# Files MUST end with _T1w.nii.gz
cp /path/to/your/data/*_T1w.nii.gz nii/

# Verify
ls nii/
```

### 3. Submit Pipeline (1 min)

```bash
# Basic cross-sectional processing
sbatch run_pipeline.sbatch
```

### 4. Monitor Progress (2 min)

```bash
# Check job status
squeue -u $USER

# Watch progress
tail -f logs/nextflow_*.out

# Or check later
cat logs/nextflow_*.out
```

### 5. Check Results

```bash
# View summary
cat pipeline_summary.txt

# Check outputs
ls fs_outputs/     # FastSurfer outputs
ls stats/          # Statistics tables

# View execution report
firefox logs/report_*.html
```

## Expected Outputs

After successful completion, you'll have:

```
fs_outputs/
├── sub-001/
├── sub-002/
└── sub-003/

stats/
├── cortical_thickness.csv
├── subcortical_volumes.csv
└── aparc_dkt.csv

pipeline_summary.txt
pipeline_summary.html

logs/
├── report_*.html
├── timeline_*.html
└── trace_*.txt
```

## Common Scenarios

### Scenario A: BIDS Input

```bash
# If you have BIDS data
sbatch --export=ALL,INPUT_MODE=bids run_pipeline.sbatch
```

### Scenario B: With Quality Control

```bash
# Add MRIQC
sbatch --export=ALL,INPUT_MODE=bids,RUN_MRIQC=true run_pipeline.sbatch
```

### Scenario C: Longitudinal Data

```bash
# Multiple timepoints per subject
sbatch --export=ALL,INPUT_MODE=bids,RUN_LONGITUDINAL=true run_pipeline.sbatch
```

### Scenario D: From DICOM

```bash
# First, customize bin/heuristic.py for your DICOM naming
# Then run:
sbatch --export=ALL,INPUT_MODE=dicom,RUN_DICOM_CONVERSION=true run_pipeline.sbatch
```

## Troubleshooting

### Pipeline Fails Immediately

**Check:**
```bash
# View error log
cat logs/nextflow_*.err

# Verify container
ls -lh images/fastsurfer-cpu.sif

# Verify license
cat fs_license/license.txt

# Check input files
ls nii/*_T1w.nii.gz
```

### No Input Files Found

**Fix:**
```bash
# Files must end with _T1w.nii.gz
# Rename if needed:
for f in nii/*.nii.gz; do
    mv "$f" "${f%.nii.gz}_T1w.nii.gz"
done
```

### Job Stuck in Queue

**Check:**
```bash
# View queue
squeue -u $USER

# Check partition
sinfo -p hpcnirc

# If wrong partition, edit conf/slurm.config
```

### Out of Memory

**Fix:**
Edit `conf/slurm.config`:
```groovy
withName: 'FASTSURFER_CROSS' {
    memory = '64 GB'  // Increase from 32 GB
}
```

## Resume Failed Pipeline

Nextflow automatically resumes from the last successful step:

```bash
# Just resubmit
sbatch run_pipeline.sbatch
```

## Processing Time Estimates

| Subjects | Processing Time | Notes |
|----------|----------------|-------|
| 1 | 12-24 hours | Single subject |
| 10 | 12-24 hours | Parallel processing |
| 50 | 12-24 hours | Parallel processing |
| 100 | 24-48 hours | Depends on queue |

*Assumes 8 CPUs per subject, parallel execution*

## Quick Commands Reference

```bash
# Submit pipeline
sbatch run_pipeline.sbatch

# Check status
squeue -u $USER

# Monitor progress
tail -f logs/nextflow_*.out

# Cancel job
scancel <job_id>

# View summary
cat pipeline_summary.txt

# Check outputs
ls fs_outputs/
ls stats/

# View execution report
firefox logs/report_*.html
```

## What Gets Processed?

### Input
- T1-weighted MRI images
- Format: NIfTI, BIDS, or DICOM
- Naming: `*_T1w.nii.gz`

### Processing
1. FastSurfer reconstruction (12-24h per subject)
2. Atlas-based parcellation (6+ atlases)
3. Statistics extraction (thickness, volume, area)
4. Aggregation across subjects

### Output
- FreeSurfer-compatible outputs
- CSV tables with statistics
- Summary reports
- Execution logs

## Next Steps

Once the basic pipeline works:

1. **Add Quality Control:**
   ```bash
   sbatch --export=ALL,RUN_MRIQC=true run_pipeline.sbatch
   ```

2. **Enable Advanced Atlases:**
   - Download atlas files (see `bin/atlases/README.md`)
   - Atlases provide additional parcellation schemes

3. **Process Longitudinal Data:**
   - Organize data with sessions/timepoints
   - Enable longitudinal processing

4. **Customize Resources:**
   - Edit `conf/slurm.config` for your cluster
   - Adjust CPUs, memory, time limits

5. **Explore Documentation:**
   - `README.md` - Complete overview
   - `USAGE.md` - Detailed examples
   - `ATLASES.md` - Atlas setup
   - `INSTALLATION_GUIDE.md` - Full setup

## Getting Help

**Check these first:**
1. Error logs: `logs/nextflow_*.err`
2. Execution report: `logs/report_*.html`
3. Work directory: `work/` (contains process logs)

**Documentation:**
- Quick issues: This file
- Detailed usage: `USAGE.md`
- Setup problems: `INSTALLATION_GUIDE.md`
- Atlas questions: `ATLASES.md`

**Common Issues:**
- Container not found → Check `images/fastsurfer-cpu.sif`
- License error → Check `fs_license/license.txt`
- No input files → Check naming: `*_T1w.nii.gz`
- Job fails → Check `logs/` and `work/` directories

## Success Checklist

After your first run, verify:

- [ ] Pipeline completed successfully (check logs)
- [ ] Subject directories created in `fs_outputs/`
- [ ] Statistics tables generated in `stats/`
- [ ] Summary file created: `pipeline_summary.txt`
- [ ] No errors in execution report
- [ ] Output files look reasonable (check one subject)

## Tips for Success

1. **Start Small:** Test on 1-2 subjects first
2. **Check Outputs:** Verify one subject before processing all
3. **Use Resume:** Nextflow automatically resumes failed pipelines
4. **Monitor Resources:** Check execution reports to optimize
5. **Keep Logs:** Save logs for troubleshooting
6. **Backup Data:** Keep original data separate from pipeline

## Example Session

```bash
# 1. Navigate to pipeline directory
cd /path/to/fastsurfer_pipeline

# 2. Check setup
ls images/fastsurfer-cpu.sif
ls fs_license/license.txt
ls nii/*_T1w.nii.gz

# 3. Submit job
sbatch run_pipeline.sbatch
# Output: Submitted batch job 12345

# 4. Check status
squeue -u $USER
# Shows: 12345 running

# 5. Monitor (optional)
tail -f logs/nextflow_12345.out

# 6. Wait for completion (12-24 hours)

# 7. Check results
cat pipeline_summary.txt
ls fs_outputs/
ls stats/

# 8. View report
firefox logs/report_12345.html

# Success!
```

## Ready to Go!

You're all set! Submit your first job:

```bash
sbatch run_pipeline.sbatch
```

For more advanced usage, see:
- `USAGE.md` - Detailed examples and workflows
- `README.md` - Complete documentation
- `ATLASES.md` - Advanced atlas configuration

Good luck with your neuroimaging analysis! 🧠

