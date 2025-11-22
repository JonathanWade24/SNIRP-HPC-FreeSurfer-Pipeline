# Detailed Usage Guide

This guide provides step-by-step instructions and examples for running the neuroimaging pipeline in various configurations.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Example Workflows](#example-workflows)
- [Input Data Preparation](#input-data-preparation)
- [Advanced Configuration](#advanced-configuration)
- [Longitudinal Processing](#longitudinal-processing)
- [Quality Control](#quality-control)
- [Statistics Extraction](#statistics-extraction)
- [Batch Processing](#batch-processing)

## Basic Usage

### Command Structure

```bash
# Using sbatch (recommended for HPC)
sbatch [sbatch-options] --export=ALL,[VARIABLES] run_pipeline.sbatch

# Direct Nextflow execution (for testing)
nextflow run main.nf -profile slurm [--parameter value]
```

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| INPUT_MODE | nii | dicom, bids, nii | Input data format |
| RUN_DICOM_CONVERSION | false | true, false | Convert DICOM to BIDS |
| RUN_BIDS_VALIDATION | true | true, false | Validate BIDS structure |
| RUN_MRIQC | false | true, false | Run quality control |
| RUN_LONGITUDINAL | false | true, false | Longitudinal processing |
| EXTRACT_SCHAEFER | true | true, false | Extract Schaefer atlas |
| EXTRACT_GLASSER | true | true, false | Extract Glasser atlas |
| EXTRACT_YEO | true | true, false | Extract Yeo networks |
| THREADS | 8 | 1-32 | CPU threads per job |

## Example Workflows

### Example 1: Basic Cross-Sectional from NIfTI

**Scenario:** You have pre-processed T1-weighted NIfTI files.

**Setup:**
```bash
# 1. Place your T1 images in nii/ directory
mkdir -p nii
cp /path/to/data/sub-001_T1w.nii.gz nii/
cp /path/to/data/sub-002_T1w.nii.gz nii/
cp /path/to/data/sub-003_T1w.nii.gz nii/

# 2. Verify file naming (must end with _T1w.nii.gz)
ls nii/
```

**Run:**
```bash
sbatch run_pipeline.sbatch
```

**Expected Output:**
- `fs_outputs/sub-001/`, `fs_outputs/sub-002/`, `fs_outputs/sub-003/`
- `stats/cortical_thickness.csv`
- `stats/subcortical_volumes.csv`
- `stats/aparc_dkt.csv`
- `pipeline_summary.txt`

---

### Example 2: Full Pipeline from DICOM

**Scenario:** Starting from raw DICOM files.

**Setup:**
```bash
# 1. Organize DICOM files by subject
mkdir -p dicom/sub-001 dicom/sub-002
cp -r /path/to/dicom/patient001/* dicom/sub-001/
cp -r /path/to/dicom/patient002/* dicom/sub-002/

# 2. Customize HeuDiConv heuristic
# Edit bin/heuristic.py to match your DICOM series descriptions
# See heuristic.py for detailed instructions

# 3. Test on one subject first
heudiconv -d 'dicom/sub-001/*/*.dcm' -s sub-001 -c none -f convertall -o /tmp/test
# Check /tmp/test/.heudiconv/sub-001/info/dicominfo.tsv
# Update bin/heuristic.py based on series descriptions
```

**Run:**
```bash
sbatch --export=ALL,INPUT_MODE=dicom,RUN_DICOM_CONVERSION=true,RUN_MRIQC=true run_pipeline.sbatch
```

**Expected Output:**
- `bids/` - BIDS-formatted dataset
- `bids/bids_validation_report.txt`
- `qc/mriqc/` - Quality control reports
- `fs_outputs/` - FastSurfer outputs
- `stats/` - All statistics tables
- `stats/qc_summary.csv` - QC metrics

---

### Example 3: BIDS Input with Validation

**Scenario:** You have a BIDS-formatted dataset.

**Setup:**
```bash
# 1. Verify BIDS structure
tree bids/
# Should show:
# bids/
# ├── sub-001/
# │   └── anat/
# │       └── sub-001_T1w.nii.gz
# ├── sub-002/
# │   └── anat/
# │       └── sub-002_T1w.nii.gz
# └── dataset_description.json

# 2. Create dataset_description.json if missing
cat > bids/dataset_description.json <<EOF
{
  "Name": "My Neuroimaging Study",
  "BIDSVersion": "1.8.0"
}
EOF
```

**Run:**
```bash
sbatch --export=ALL,INPUT_MODE=bids run_pipeline.sbatch
```

---

### Example 4: Longitudinal Processing

**Scenario:** Multiple timepoints per subject.

**Setup Option A - Session-based (BIDS standard):**
```bash
# BIDS structure with sessions
bids/
├── sub-001/
│   ├── ses-01/
│   │   └── anat/
│   │       └── sub-001_ses-01_T1w.nii.gz
│   └── ses-02/
│       └── anat/
│           └── sub-001_ses-02_T1w.nii.gz
└── sub-002/
    ├── ses-01/
    │   └── anat/
    │       └── sub-002_ses-01_T1w.nii.gz
    └── ses-02/
        └── anat/
            └── sub-002_ses-02_T1w.nii.gz
```

**Setup Option B - Timepoint suffix:**
```bash
# NIfTI with timepoint suffix
nii/
├── sub-001_tp1_T1w.nii.gz
├── sub-001_tp2_T1w.nii.gz
├── sub-001_tp3_T1w.nii.gz
├── sub-002_tp1_T1w.nii.gz
└── sub-002_tp2_T1w.nii.gz
```

**Run:**
```bash
# For BIDS with sessions
sbatch --export=ALL,INPUT_MODE=bids,RUN_LONGITUDINAL=true run_pipeline.sbatch

# For NIfTI with timepoint suffix
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch
```

**Expected Output:**
- `fs_outputs/` - Cross-sectional outputs for each timepoint
- `long_outputs/` - Longitudinal outputs
  - `sub-001/` - Base template
  - `sub-001_ses-01.long.sub-001/` - Longitudinal timepoint 1
  - `sub-001_ses-02.long.sub-001/` - Longitudinal timepoint 2
- `stats/longitudinal_slope_estimates.csv` - Rate of change
- `stats/longitudinal_percent_change.csv` - Percent changes

---

### Example 5: MRIQC Only

**Scenario:** Run quality control on existing BIDS data.

**Run:**
```bash
sbatch --export=ALL,INPUT_MODE=bids,RUN_MRIQC=true run_pipeline.sbatch
```

**Expected Output:**
- `qc/mriqc/` - Individual QC reports (HTML + JSON)
- `qc/mriqc/group_*.html` - Group-level reports
- `stats/qc_summary.csv` - Aggregated metrics
- `stats/qc_outliers.txt` - Flagged subjects

---

### Example 6: Subset Processing

**Scenario:** Process only specific subjects.

**Method 1 - Prepare subset directory:**
```bash
# Create temporary directory with subset
mkdir -p nii_subset
cp nii/sub-001_T1w.nii.gz nii_subset/
cp nii/sub-005_T1w.nii.gz nii_subset/
cp nii/sub-010_T1w.nii.gz nii_subset/

# Run on subset
nextflow run main.nf -profile slurm --nii_dir nii_subset
```

**Method 2 - Modify input pattern:**
```bash
# Process only subjects matching pattern
nextflow run main.nf -profile slurm --pattern "sub-00[1-5]_T1w.nii.gz"
```

---

## Input Data Preparation

### NIfTI Files

**Requirements:**
- Files must end with `_T1w.nii.gz`
- Place in `nii/` directory
- Subject ID extracted from filename (everything before `_T1w.nii.gz`)

**Naming Examples:**
```
✓ sub-001_T1w.nii.gz          → Subject: sub-001
✓ participant_123_T1w.nii.gz  → Subject: participant_123
✓ sub-001_tp1_T1w.nii.gz      → Subject: sub-001_tp1 (for longitudinal)
✗ sub-001.nii.gz               → Missing _T1w suffix
✗ sub-001_T1.nii.gz            → Missing 'w' in T1w
```

### BIDS Format

**Minimal Structure:**
```
bids/
├── dataset_description.json
└── sub-<label>/
    └── anat/
        └── sub-<label>_T1w.nii.gz
```

**With Sessions:**
```
bids/
├── dataset_description.json
└── sub-<label>/
    └── ses-<label>/
        └── anat/
            └── sub-<label>_ses-<label>_T1w.nii.gz
```

**dataset_description.json:**
```json
{
  "Name": "Study Name",
  "BIDSVersion": "1.8.0",
  "Authors": ["Author Name"],
  "License": "CC0"
}
```

### DICOM Files

**Organization:**
```
dicom/
├── sub-001/
│   ├── series_001/
│   │   ├── IM-0001-0001.dcm
│   │   ├── IM-0001-0002.dcm
│   │   └── ...
│   └── series_002/
│       └── ...
└── sub-002/
    └── ...
```

**Heuristic Customization:**
1. Run test conversion to see series descriptions:
   ```bash
   heudiconv -d 'dicom/sub-001/*/*.dcm' -s sub-001 -c none -f convertall -o /tmp/test
   cat /tmp/test/.heudiconv/sub-001/info/dicominfo.tsv
   ```

2. Edit `bin/heuristic.py` to match your series descriptions

3. Test conversion:
   ```bash
   heudiconv -d 'dicom/sub-001/*/*.dcm' -s sub-001 -c dcm2niix -f bin/heuristic.py -o test_bids -b
   ```

4. Validate output:
   ```bash
   bids-validator test_bids/
   ```

---

## Advanced Configuration

### Custom Resource Allocation

**Edit conf/slurm.config:**
```groovy
process {
    withName: 'FASTSURFER_CROSS' {
        cpus = 16          // Increase CPUs
        memory = '64 GB'   // Increase memory
        time = '48h'       // Increase time limit
    }
}
```

**Or override via command line:**
```bash
nextflow run main.nf -profile slurm \
    --threads 16 \
    -c custom.config
```

### Custom Container Images

**Edit nextflow.config:**
```groovy
params {
    heudiconv_container = "docker://nipy/heudiconv:1.1.6"
    mriqc_container = "docker://nipreps/mriqc:24.0.0"
    bids_validator_container = "docker://bids/validator:1.14.0"
}
```

### Custom Atlas Configuration

**Edit nextflow.config:**
```groovy
params {
    extract_schaefer = true
    schaefer_parcels = "100,200,400,600,800,1000"  // More resolutions
    schaefer_networks = "7,17"
}
```

---

## Longitudinal Processing

### Understanding Longitudinal Pipeline

The longitudinal pipeline consists of three stages:

1. **Cross-sectional processing** of each timepoint
2. **Base template creation** from all timepoints
3. **Longitudinal processing** of each timepoint relative to template

### Timepoint Naming

**Automatic Detection:**
- Session format: `sub-001_ses-01`, `sub-001_ses-02`
- Timepoint format: `sub-001_tp1`, `sub-001_tp2`
- Pipeline automatically groups by base subject ID

**Manual Grouping:**
If your naming doesn't follow these patterns, you may need to modify the grouping logic in `main.nf`.

### Interpreting Longitudinal Results

**Slope Estimates (longitudinal_slope_estimates.csv):**
- `slope`: Rate of change per timepoint unit
- `p_value`: Statistical significance
- `r_squared`: Model fit quality
- `percent_change`: Total percent change from baseline

**Use Cases:**
- Aging studies: Track cortical thinning
- Disease progression: Monitor atrophy rates
- Treatment effects: Assess intervention impact

---

## Quality Control

### MRIQC Metrics

**Key Metrics:**
- `cnr`: Contrast-to-noise ratio (higher is better)
- `snr_total`: Signal-to-noise ratio (higher is better)
- `fber`: Foreground-background energy ratio (higher is better)
- `efc`: Entropy focus criterion (lower is better)
- `qi_2`: Quality index 2 (lower is better)

**Outlier Detection:**
Subjects flagged in `stats/qc_outliers.txt` should be visually inspected.

**Visual Inspection:**
Open individual HTML reports in `qc/mriqc/` for detailed QC.

---

## Statistics Extraction

### Output Tables

**cortical_thickness.csv:**
```csv
subject_id,atlas,region,thickness_mm,thickness_std_mm,surface_area_mm2,gray_volume_mm3
sub-001,desikan_killiany,lh_superiorfrontal,2.543,0.234,11234.5,28456.7
```

**subcortical_volumes.csv:**
```csv
subject_id,Left-Hippocampus,Right-Hippocampus,Left-Amygdala,...
sub-001,3456.7,3512.3,1234.5,...
```

**aparc_dkt.csv:**
```csv
subject_id,region,num_vertices,surface_area_mm2,gray_volume_mm3,thickness_avg_mm
sub-001,lh_superiorfrontal,5678,11234.5,28456.7,2.543
```

### Analyzing Results

**Load in R:**
```r
library(tidyverse)

# Load data
thickness <- read_csv("stats/cortical_thickness.csv")
volumes <- read_csv("stats/subcortical_volumes.csv")

# Example analysis
thickness %>%
  filter(atlas == "desikan_killiany") %>%
  group_by(region) %>%
  summarize(mean_thickness = mean(thickness_mm, na.rm = TRUE))
```

**Load in Python:**
```python
import pandas as pd

# Load data
thickness = pd.read_csv("stats/cortical_thickness.csv")
volumes = pd.read_csv("stats/subcortical_volumes.csv")

# Example analysis
thickness[thickness['atlas'] == 'desikan_killiany'].groupby('region')['thickness_mm'].mean()
```

---

## Batch Processing

### Processing Multiple Cohorts

**Scenario:** Process multiple independent datasets.

```bash
#!/bin/bash
# process_cohorts.sh

COHORTS=("cohort1" "cohort2" "cohort3")

for cohort in "${COHORTS[@]}"; do
    echo "Processing $cohort"
    
    # Create cohort-specific directory
    mkdir -p results_${cohort}
    
    # Run pipeline
    sbatch --export=ALL,INPUT_MODE=bids \
           --job-name=${cohort}_pipeline \
           run_pipeline.sbatch
    
    # Wait between submissions
    sleep 10
done
```

### Monitoring Multiple Jobs

```bash
# Check all your jobs
squeue -u $USER

# Check specific pipeline jobs
squeue -u $USER -n neuroimaging_pipeline

# Cancel all jobs
scancel -u $USER

# Cancel specific job
scancel <job_id>
```

---

## Tips and Best Practices

1. **Start Small:** Test on 1-2 subjects before full cohort
2. **Use Resume:** Always use `-resume` to avoid reprocessing
3. **Monitor Resources:** Check execution reports to optimize resources
4. **Validate Early:** Run BIDS validation before full processing
5. **QC First:** Run MRIQC to identify problematic scans
6. **Backup:** Keep original data separate from pipeline directory
7. **Document:** Keep notes on processing parameters and decisions

---

## Getting Help

- Check `README.md` for general information
- See `ATLASES.md` for atlas setup
- Review execution reports in `logs/`
- Inspect failed process logs in `work/` directory
- Check Nextflow documentation: https://www.nextflow.io/docs/latest/

