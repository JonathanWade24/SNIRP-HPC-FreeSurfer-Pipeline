# ADNI-DOD Dataset Analysis

## Dataset Overview

**Manifest File:** `ADNI-DOD_11_18_2025.csv`

### Summary Statistics
- **Total Scans:** 155 images
- **Unique Subjects:** 74 patients
- **Image Type:** MT1; N3m (Pre-processed) ✅ **Perfect for pipeline!**
- **Format:** NiFTI
- **Date Range:** 2013-2020

### Demographics
- **Sex:** 73 Male, 1 Female (subject 0068236)
- **Age Range:** 61-86 years at scan time

## Visit Types and Longitudinal Structure

Your dataset contains **longitudinal data** with multiple timepoints:

| Visit Code | Meaning | Count | Timeline |
|------------|---------|-------|----------|
| **SCMRI** | Screening/Baseline | ~74 | Baseline (Year 0) |
| **M12** | Month 12 Follow-up | ~40 | 1 year after baseline |
| **TAU** | Tau PET Visit | ~20 | 1-3 years after baseline |
| **TAU2** | Second Tau Visit | ~8 | 2-4 years after baseline |

### Longitudinal Subjects

**You have ~50+ subjects with multiple timepoints!** This is perfect for longitudinal analysis.

Examples from your data:
- **Subject 0421933:** SCMRI (2019) + TAU (2020) = 2 timepoints
- **Subject 0415433:** SCMRI (2019) + TAU (2020) = 2 timepoints
- **Subject 0410120:** SCMRI (2019) + TAU (2020) = 2 timepoints
- **Subject 0394956:** SCMRI (2018) + M12 (2019) + TAU (2020) = 3 timepoints
- **Subject 0398560:** SCMRI (2018) + M12 (2019) = 2 timepoints
- **Subject 0043523:** SCMRI (2014) + M12 (2015) + TAU (2017) + TAU2 (2018) = **4 timepoints!**

## Subjects with Multiple Scans

Some subjects have **duplicate scans on the same day**. These may be:
1. Different sequence parameters (quality check)
2. Repeat scans (motion/quality issues)
3. Different preprocessing versions

**Examples:**
- Subject 0400016: 3 scans on same day (7/18/2018)
- Subject 0394956: 2 TAU scans on same day (2/10/2020)
- Subject 0403123: 2 SCMRI scans on same day (1/16/2019)

**Recommendation:** The preprocessing script will automatically number these (e.g., `ses-bl_1`, `ses-bl_2`) so you can review them later and keep the best quality scan.

## Data Organization Strategy

### Session Mapping

The preprocessing script will map visits as follows:

```
ADNI Visit → Pipeline Session Name
----------------------------------
SCMRI      → ses-bl      (baseline)
M12        → ses-m12     (month 12)
TAU        → ses-tau     (tau visit)
TAU2       → ses-tau2    (tau visit 2)
```

### Final Naming Convention

Your files will be organized as:

```
nii/
├── sub-0421933_ses-bl_T1w.nii.gz       # Baseline
├── sub-0421933_ses-tau_T1w.nii.gz     # TAU visit
├── sub-0415433_ses-bl_T1w.nii.gz
├── sub-0415433_ses-tau_T1w.nii.gz
├── sub-0043523_ses-bl_T1w.nii.gz      # 4 timepoints
├── sub-0043523_ses-m12_T1w.nii.gz
├── sub-0043523_ses-tau_T1w.nii.gz
├── sub-0043523_ses-tau2_T1w.nii.gz
└── ...
```

## Processing Recommendations

### 1. For Cross-Sectional Analysis (Baseline Only)

If you only want baseline scans:

```bash
# After running prepare_adni_data.py
# Keep only ses-bl files
mkdir nii_baseline
cp nii/*_ses-bl_T1w.nii.gz nii_baseline/

# Run pipeline
sbatch run_pipeline.sbatch --nii_dir=nii_baseline
```

### 2. For Longitudinal Analysis (All Timepoints)

**Recommended!** Since you have excellent longitudinal data:

```bash
# Process all timepoints with longitudinal pipeline
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch
```

This will:
1. Process each timepoint cross-sectionally
2. Create base template for each subject
3. Reprocess each timepoint longitudinally
4. Calculate change rates (slopes)
5. Generate percent change statistics

### 3. Timeline Analysis

With your data spanning 2013-2020, you can analyze:
- **Short-term changes** (M12): 1-year progression
- **Medium-term changes** (TAU): 1-3 year progression  
- **Long-term changes** (TAU2): 2-4 year progression

## Expected Output Statistics

After processing, you'll have:

**Baseline Statistics:**
- Cortical thickness for all 74 subjects
- Subcortical volumes
- 6+ atlas parcellations

**Longitudinal Statistics:**
- Slope estimates (mm/year for thickness, mm³/year for volume)
- Percent change between timepoints
- Significance testing for each region
- ~50+ subjects with longitudinal trajectories

## Step-by-Step Workflow

### Step 1: Generate Subject Info

```bash
cd /path/to/fastsurfer_pipeline

# Generate subject information (no file processing)
python prepare_adni_data.py \
    --manifest ADNI-DOD_11_18_2025.csv \
    --info-only

# This creates: ADNI-DOD_11_18_2025_subject_info.csv
# Review this file to see subject counts, ages, visits
```

### Step 2: Organize Files

```bash
# Assuming your ADNI downloads are in /data/ADNI/
python prepare_adni_data.py \
    --manifest ADNI-DOD_11_18_2025.csv \
    --dicom-dir /data/ADNI/downloads \
    --output-dir nii

# This will:
# - Find all NIfTI files by Image ID
# - Rename to BIDS format
# - Compress if needed
# - Create file_list.txt
```

### Step 3: Quality Check

```bash
# Check organized files
ls -lh nii/*.nii.gz | head -20
cat nii/file_list.txt | head -20

# Count timepoints per subject
ls nii/ | cut -d_ -f1-2 | sort | uniq -c | sort -rn | head
```

### Step 4: Run Pipeline

```bash
# Option A: Longitudinal (RECOMMENDED for your data)
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch

# Option B: Cross-sectional only
sbatch run_pipeline.sbatch

# Option C: With quality control
sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true,RUN_MRIQC=true run_pipeline.sbatch
```

### Step 5: Monitor Progress

```bash
# Check job status
squeue -u $USER

# Watch progress
tail -f logs/nextflow_*.out

# Check processed subjects
ls fs_outputs/
```

## Handling Duplicate Scans

For subjects with multiple scans on same day:

1. **After preprocessing**, review quality:
   ```bash
   # Check both scans
   ls fs_outputs/sub-0400016*
   
   # Compare QC metrics if MRIQC was run
   grep "0400016" stats/qc_summary.csv
   ```

2. **Keep best quality scan:**
   - Check MRIQC metrics (SNR, CNR)
   - Visual inspection of segmentation
   - Delete or mark lower quality scan

3. **Or process both:**
   - Pipeline handles duplicates automatically
   - You can analyze consistency/reliability

## Special Considerations

### 1. Age at Scan

Each visit has different ages recorded. The pipeline will use:
- Baseline age for cross-sectional analysis
- Age progression for longitudinal analysis

### 2. Scanner Effects

Data from 2013-2020 may have:
- Different scanner upgrades
- Protocol changes
- The MT1; N3m preprocessing helps standardize across scanners

### 3. Missing Timepoints

Not all subjects have all visits. That's normal and expected:
- Cross-sectional: Process all available subjects
- Longitudinal: Only subjects with 2+ timepoints get slope estimates

## Estimated Processing Time

For your dataset:
- **Cross-sectional (155 scans):** ~24-36 hours
  - Parallel processing: 8 CPUs per scan
  - ~12-24 hours per scan
  - Many run in parallel

- **Longitudinal (~50 subjects, 2-4 timepoints each):** ~48-72 hours
  - Cross-sectional first
  - Base template creation
  - Longitudinal processing
  - Worth it for the trajectory data!

## Questions to Consider

Before running:

1. **Do you want ALL scans or just baseline?**
   - ALL → Run longitudinal pipeline
   - Baseline only → Filter to ses-bl scans

2. **Quality control?**
   - Add `RUN_MRIQC=true` for QC metrics
   - Recommended for publication-quality data

3. **Storage space?**
   - Cross-sectional: ~2-3 GB per subject = ~460 GB total
   - Longitudinal: Add ~50% more = ~700 GB total
   - Ensure adequate space in `fs_outputs/` and `long_outputs/`

## Next Steps

1. ✅ **You have perfect MT1; N3m images**
2. ✅ **You have longitudinal data** (rare and valuable!)
3. ⏳ Run `prepare_adni_data.py` to organize files
4. ⏳ Run longitudinal pipeline
5. ⏳ Analyze trajectory data

Your dataset is excellent for longitudinal neuroimaging analysis! The combination of MT1; N3m preprocessing and multiple timepoints will give you high-quality results.

## Support

Questions about:
- **File organization:** Check `nii/file_list.txt` and `_subject_info.csv`
- **Running script:** `python prepare_adni_data.py --help`
- **Pipeline:** See `README.md` and `USAGE.md`



