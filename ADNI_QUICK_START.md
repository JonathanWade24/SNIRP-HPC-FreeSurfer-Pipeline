# ADNI-DOD Quick Start Guide

## Your Dataset at a Glance

✅ **155 MT1; N3m scans** (perfect preprocessing!)  
✅ **74 unique subjects**  
✅ **~50+ longitudinal subjects** (2-4 timepoints each)  
✅ **Date range:** 2013-2020  

## 3-Step Quickstart

### 1️⃣ Set Your ADNI Download Path

```bash
# Edit this in RUN_ADNI_PIPELINE.sh (line 12)
ADNI_DOWNLOADS="/path/to/your/adni/downloads"
```

### 2️⃣ Run the Setup Script

```bash
./RUN_ADNI_PIPELINE.sh
```

This will:
- Check prerequisites
- Analyze your manifest
- Organize files with proper BIDS naming
- Submit the pipeline to Slurm

### 3️⃣ Monitor Progress

```bash
# Check job status
squeue -u $USER

# Watch real-time progress
tail -f logs/nextflow_*.out

# Check results (after completion)
ls fs_outputs/
ls stats/
cat pipeline_summary.txt
```

## Alternative: Manual Steps

If you prefer manual control:

### Step 1: Analyze Dataset

```bash
python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv --info-only
```

**Output:** `ADNI-DOD_11_18_2025_subject_info.csv`  
Review this to see subject counts, ages, visits

### Step 2: Organize Files

```bash
python prepare_adni_data.py \
    --manifest ADNI-DOD_11_18_2025.csv \
    --dicom-dir /path/to/adni/downloads \
    --output-dir nii
```

**Output:** Organized files in `nii/` directory  
- Format: `sub-XXXXXXX_ses-XX_T1w.nii.gz`
- File list: `nii/file_list.txt`

### Step 3: Submit Pipeline

```bash
# Longitudinal (RECOMMENDED for your data)
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch

# Or with quality control
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true,RUN_MRIQC=true run_pipeline.sbatch
```

## What You'll Get

### Cross-Sectional Outputs (All 155 scans)

```
fs_outputs/
├── sub-0421933_ses-bl/          # FreeSurfer structure
├── sub-0421933_ses-tau/
├── sub-0415433_ses-bl/
└── ...

stats/
├── cortical_thickness.csv       # Thickness per region
├── subcortical_volumes.csv      # Subcortical volumes
└── aparc_dkt.csv                # DKT atlas stats
```

### Longitudinal Outputs (~50 subjects)

```
long_outputs/
├── sub-0043523/                 # Base template
├── sub-0043523_ses-bl.long.sub-0043523/
├── sub-0043523_ses-m12.long.sub-0043523/
├── sub-0043523_ses-tau.long.sub-0043523/
└── sub-0043523_ses-tau2.long.sub-0043523/

stats/
├── longitudinal_slope_estimates.csv    # Rate of change
└── longitudinal_percent_change.csv     # Percent change
```

## Key Points About Your Data

### Visit Codes → Sessions

| ADNI Visit | Pipeline Name | Description |
|-----------|---------------|-------------|
| SCMRI | ses-bl | Baseline screening |
| M12 | ses-m12 | 12-month follow-up |
| TAU | ses-tau | Tau imaging visit |
| TAU2 | ses-tau2 | Second tau visit |

### Example Subjects

**Subject 0043523** (Best example - 4 timepoints!):
```
sub-0043523_ses-bl_T1w.nii.gz    (2014, age 71)
sub-0043523_ses-m12_T1w.nii.gz   (2015, age 72)
sub-0043523_ses-tau_T1w.nii.gz   (2017, age 73)
sub-0043523_ses-tau2_T1w.nii.gz  (2018, age 75)
```

**Subject 0394956** (3 timepoints):
```
sub-0394956_ses-bl_T1w.nii.gz
sub-0394956_ses-m12_T1w.nii.gz
sub-0394956_ses-tau_T1w.nii.gz
```

### Duplicate Scans

Some subjects have multiple scans same day (e.g., subject 0400016 has 3 scans on 7/18/2018).

**Handled automatically:**
- Named as: `ses-bl_1`, `ses-bl_2`, `ses-bl_3`
- Review after processing and keep best quality

## Processing Time Estimates

| Mode | Time | Why |
|------|------|-----|
| **Cross-sectional** | 24-36 hours | 155 scans, parallel processing |
| **Longitudinal** | 48-72 hours | + base templates + long processing |
| **+ MRIQC** | +6-12 hours | Quality control per subject |

## Storage Requirements

| Data | Size | Location |
|------|------|----------|
| Input NIfTI | ~30-40 GB | `nii/` |
| Cross-sectional | ~460 GB | `fs_outputs/` |
| Longitudinal | ~230 GB | `long_outputs/` |
| **Total** | **~730 GB** | Ensure adequate space! |

## Troubleshooting

### Issue: Files not found

```bash
# Check your ADNI download directory structure
ls -R /path/to/adni/downloads | grep "I129" | head

# ADNI files typically named with Image ID
# Example: I1293003.nii or similar
```

### Issue: Permission denied

```bash
chmod +x RUN_ADNI_PIPELINE.sh
chmod +x prepare_adni_data.py
```

### Issue: Container not found

```bash
cd images
apptainer pull fastsurfer-cpu.sif docker://deepmi/fastsurfer:latest
```

### Issue: Python dependencies

```bash
# If prepare_adni_data.py fails
pip install pandas

# Or use conda
conda install pandas
```

## Next Steps After Processing

### 1. Check Completion

```bash
# View summary
cat pipeline_summary.txt

# Check execution report
firefox logs/report_*.html
```

### 2. Verify Outputs

```bash
# Count processed subjects
ls fs_outputs/ | wc -l

# Check statistics tables
head stats/cortical_thickness.csv
head stats/longitudinal_slope_estimates.csv
```

### 3. Quality Control

```bash
# If you ran MRIQC
cat stats/qc_outliers.txt
head stats/qc_summary.csv

# Visual inspection (pick random subjects)
freeview -v fs_outputs/sub-0043523/mri/brain.mgz
```

### 4. Analysis

Load data in R or Python:

**Python:**
```python
import pandas as pd

# Load cross-sectional data
thick = pd.read_csv('stats/cortical_thickness.csv')
volumes = pd.read_csv('stats/subcortical_volumes.csv')

# Load longitudinal data
slopes = pd.read_csv('stats/longitudinal_slope_estimates.csv')

# Example: Find regions with significant change
sig_regions = slopes[slopes['p_value'] < 0.05]
print(f"Regions with significant change: {len(sig_regions)}")
```

**R:**
```r
library(tidyverse)

# Load data
thick <- read_csv('stats/cortical_thickness.csv')
slopes <- read_csv('stats/longitudinal_slope_estimates.csv')

# Example: Plot thickness distribution
ggplot(thick, aes(x=thickness_mm)) +
  geom_histogram() +
  facet_wrap(~atlas)
```

## Important Notes

1. **MT1; N3m is perfect** ✅ No additional preprocessing needed
2. **Longitudinal data is valuable** - Use it! Run longitudinal pipeline
3. **Multiple timepoints** allow trajectory analysis (rare in neuroimaging!)
4. **Allow 2-3 days** for full longitudinal processing
5. **Save logs** for troubleshooting and documentation

## Support Files Created

- ✅ `prepare_adni_data.py` - File organization script
- ✅ `RUN_ADNI_PIPELINE.sh` - Automated setup script  
- ✅ `ADNI_DATASET_ANALYSIS.md` - Detailed analysis
- ✅ `ADNI_QUICK_START.md` - This file

## Questions?

1. **File organization:** Check generated `_subject_info.csv`
2. **Pipeline usage:** See `README.md` and `USAGE.md`
3. **Longitudinal processing:** See `USAGE.md` section on longitudinal
4. **Atlas setup:** See `ATLASES.md`

## Ready to Start?

```bash
# Make sure you're in the pipeline directory
cd /path/to/fastsurfer_pipeline

# Run the setup script
./RUN_ADNI_PIPELINE.sh

# Or manual approach
python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv --info-only
```

Good luck with your analysis! 🧠📊



