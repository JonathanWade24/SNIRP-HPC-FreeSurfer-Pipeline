# Atlas Setup and Configuration Guide

This guide provides detailed information about brain atlases supported by the pipeline, how to set them up, and how to customize atlas extraction.

## Table of Contents

- [Overview](#overview)
- [Standard Atlases](#standard-atlases)
- [Advanced Atlases](#advanced-atlases)
- [Setup Instructions](#setup-instructions)
- [Adding Custom Atlases](#adding-custom-atlases)
- [Atlas Comparison](#atlas-comparison)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Overview

The pipeline extracts statistics from multiple brain parcellation schemes:

### Standard Atlases (Always Available)
These are included with FreeSurfer/FastSurfer and require no additional setup:
- **Desikan-Killiany** (aparc)
- **Destrieux** (aparc.a2009s)
- **DKT** (aparc.DKTatlas)

### Advanced Atlases (Require Setup)
These require downloading annotation files:
- **Schaefer Parcellation** (multi-resolution)
- **Glasser HCP-MMP1.0** (multimodal)
- **Yeo Functional Networks** (7 or 17 networks)

## Standard Atlases

### Desikan-Killiany (aparc)

**Description:**
The most widely used FreeSurfer parcellation, dividing each hemisphere into 34 cortical regions based on gyral and sulcal structure.

**Regions:** 68 cortical (34 per hemisphere)

**Use Cases:**
- General-purpose cortical parcellation
- Clinical studies
- Cross-study comparisons (most common atlas)

**Output Files:**
- `lh.aparc.stats`, `rh.aparc.stats`

**Extracted Metrics:**
- Cortical thickness (mean, std)
- Surface area
- Gray matter volume
- Number of vertices

**Citation:**
> Desikan RS, Ségonne F, Fischl B, et al. (2006). An automated labeling system for subdividing the human cerebral cortex on MRI scans into gyral based regions of interest. NeuroImage, 31(3):968-980.

---

### Destrieux (aparc.a2009s)

**Description:**
A higher-resolution parcellation with 148 cortical regions, providing finer anatomical detail based on gyri and sulci.

**Regions:** 148 cortical (74 per hemisphere)

**Use Cases:**
- Detailed anatomical studies
- Fine-grained regional analysis
- Studies requiring sulcal/gyral specificity

**Output Files:**
- `lh.aparc.a2009s.stats`, `rh.aparc.a2009s.stats`

**Extracted Metrics:**
- Cortical thickness (mean, std)
- Surface area
- Gray matter volume
- Number of vertices

**Citation:**
> Destrieux C, Fischl B, Dale A, Halgren E. (2010). Automatic parcellation of human cortical gyri and sulci using standard anatomical nomenclature. NeuroImage, 53(1):1-15.

---

### DKT (Desikan-Killiany-Tourville)

**Description:**
A refined version of the Desikan-Killiany atlas with improved anatomical definitions and labeling protocol.

**Regions:** 62 cortical (31 per hemisphere)

**Use Cases:**
- Standardized cortical labeling
- Multi-site studies
- Reproducibility-focused research

**Output Files:**
- `lh.aparc.DKTatlas.stats`, `rh.aparc.DKTatlas.stats`

**Extracted Metrics:**
- Cortical thickness (mean, std)
- Surface area
- Gray matter volume
- Number of vertices

**Citation:**
> Klein A, Tourville J. (2012). 101 labeled brain images and a consistent human cortical labeling protocol. Frontiers in Neuroscience, 6:171.

---

## Advanced Atlases

### Schaefer Parcellation

**Description:**
Multi-resolution functional parcellation based on resting-state fMRI, available at multiple scales (100, 200, 400, 600, 800, 1000 parcels) and organized into 7 or 17 functional networks.

**Resolutions:** 100, 200, 400, 600, 800, 1000 parcels
**Networks:** 7 or 17 networks (Yeo networks)

**Use Cases:**
- Functional connectivity analysis
- Network-based studies
- Multi-scale analysis
- Resting-state fMRI

**Networks (7-network version):**
1. Visual
2. Somatomotor
3. Dorsal Attention
4. Ventral Attention
5. Limbic
6. Frontoparietal
7. Default Mode

**Networks (17-network version):**
Subdivisions of the 7 networks for finer functional specificity.

**Setup:**
```bash
cd bin/atlases

# Download specific resolution (example: 400 parcels, 7 networks)
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label/lh.Schaefer2018_400Parcels_7Networks_order.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label/rh.Schaefer2018_400Parcels_7Networks_order.annot
```

**Configuration:**
```groovy
// In nextflow.config
params {
    extract_schaefer = true
    schaefer_parcels = "100,200,400"  // Comma-separated
    schaefer_networks = "7,17"
}
```

**Citation:**
> Schaefer A, Kong R, Gordon EM, et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex from Intrinsic Functional Connectivity MRI. Cerebral Cortex, 29:3095-3114.

---

### Glasser HCP-MMP1.0

**Description:**
High-resolution multimodal parcellation from the Human Connectome Project, defining 360 cortical areas based on architecture, function, connectivity, and topography.

**Regions:** 360 cortical (180 per hemisphere)

**Use Cases:**
- High-resolution cortical mapping
- Multimodal studies
- Human Connectome Project analyses
- Detailed functional-anatomical studies

**Modalities Used:**
- Cortical architecture (myelin maps)
- Function (task fMRI)
- Connectivity (resting-state fMRI, diffusion MRI)
- Topography (retinotopy, somatotopy)

**Setup:**
```bash
cd bin/atlases

# Option 1: From FreeSurfer (if installed)
cp $FREESURFER_HOME/subjects/fsaverage/label/lh.HCP-MMP1.annot .
cp $FREESURFER_HOME/subjects/fsaverage/label/rh.HCP-MMP1.annot .

# Option 2: Download from figshare
wget https://figshare.com/ndownloader/files/5528816 -O lh.HCP-MMP1.annot
wget https://figshare.com/ndownloader/files/5528819 -O rh.HCP-MMP1.annot
```

**Configuration:**
```groovy
// In nextflow.config
params {
    extract_glasser = true
}
```

**Citation:**
> Glasser MF, Coalson TS, Robinson EC, et al. (2016). A multi-modal parcellation of human cerebral cortex. Nature, 536(7615):171-178.

---

### Yeo Functional Networks

**Description:**
Functional network parcellation based on clustering of resting-state fMRI data from 1000 subjects, available as 7 or 17 networks.

**Networks:** 7 or 17 functional networks

**Use Cases:**
- Functional network analysis
- Resting-state connectivity
- Network-level statistics
- Large-scale brain organization

**7 Networks:**
1. Visual
2. Somatomotor
3. Dorsal Attention
4. Ventral Attention
5. Limbic
6. Frontoparietal Control
7. Default Mode

**17 Networks:**
Finer subdivisions of the 7 networks.

**Setup:**
```bash
cd bin/atlases

# 7 Networks
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/lh.Yeo2011_7Networks_N1000.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/rh.Yeo2011_7Networks_N1000.annot

# 17 Networks
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/lh.Yeo2011_17Networks_N1000.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/rh.Yeo2011_17Networks_N1000.annot
```

**Configuration:**
```groovy
// In nextflow.config
params {
    extract_yeo = true
}
```

**Citation:**
> Yeo BT, Krienen FM, Sepulcre J, et al. (2011). The organization of the human cerebral cortex estimated by intrinsic functional connectivity. Journal of Neurophysiology, 106(3):1125-1165.

---

## Setup Instructions

### Quick Setup (All Atlases)

Create a download script:

```bash
#!/bin/bash
# download_all_atlases.sh

set -e
cd bin/atlases

echo "Downloading Schaefer atlases..."
BASE_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label"

for parcels in 100 200 400; do
    for networks in 7 17; do
        for hemi in lh rh; do
            file="${hemi}.Schaefer2018_${parcels}Parcels_${networks}Networks_order.annot"
            echo "  Downloading $file..."
            wget -q "${BASE_URL}/${file}"
        done
    done
done

echo "Downloading Yeo networks..."
YEO_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label"

for networks in 7 17; do
    for hemi in lh rh; do
        file="${hemi}.Yeo2011_${networks}Networks_N1000.annot"
        echo "  Downloading $file..."
        wget -q "${YEO_URL}/${file}"
    done
done

echo "Note: Glasser atlas requires manual download or FreeSurfer installation"
echo "See ATLASES.md for instructions"

echo "Done!"
ls -lh *.annot
```

Run the script:
```bash
chmod +x bin/atlases/download_all_atlases.sh
cd bin/atlases
./download_all_atlases.sh
```

### Verification

```bash
# Check downloaded files
ls -lh bin/atlases/*.annot

# Expected files (example for 100, 200, 400 parcels):
# lh.Schaefer2018_100Parcels_7Networks_order.annot
# rh.Schaefer2018_100Parcels_7Networks_order.annot
# lh.Schaefer2018_100Parcels_17Networks_order.annot
# rh.Schaefer2018_100Parcels_17Networks_order.annot
# ... (and so on for 200, 400 parcels)
# lh.Yeo2011_7Networks_N1000.annot
# rh.Yeo2011_7Networks_N1000.annot
# lh.Yeo2011_17Networks_N1000.annot
# rh.Yeo2011_17Networks_N1000.annot
```

---

## Adding Custom Atlases

### Step 1: Prepare Annotation Files

Annotation files (`.annot`) contain:
- Vertex labels
- Color table
- Region names

Create or obtain `.annot` files for your custom atlas.

### Step 2: Place Files in Atlas Directory

```bash
cp /path/to/lh.custom_atlas.annot bin/atlases/
cp /path/to/rh.custom_atlas.annot bin/atlases/
```

### Step 3: Modify Extraction Script

Edit `bin/extract_atlases.py`:

```python
def extract_custom_atlas(self) -> Dict:
    """Extract custom atlas statistics"""
    print(f"  Extracting custom atlas...")
    
    stats = {}
    
    if not self.atlas_dir or not self.atlas_dir.exists():
        print(f"    Warning: Atlas directory not found")
        self.data['custom_atlas'] = {'note': 'Atlas files not available'}
        return stats
    
    # Check for annotation files
    for hemi in ['lh', 'rh']:
        annot_file = self.atlas_dir / f'{hemi}.custom_atlas.annot'
        
        if annot_file.exists():
            # Use FreeSurfer tools to extract statistics
            # Example: mris_anatomical_stats with custom annotation
            stats[f'{hemi}_custom'] = {
                'status': 'annotation_available',
                'file': str(annot_file)
            }
        else:
            stats[f'{hemi}_custom'] = {'status': 'annotation_not_found'}
    
    self.data['custom_atlas'] = stats
    return stats
```

### Step 4: Call in Main Extraction

In `extract_all_atlases()` function:

```python
# Extract custom atlas
if extract_custom:
    extractor.extract_custom_atlas()
```

### Step 5: Update Configuration

In `nextflow.config`:

```groovy
params {
    extract_custom = true
}
```

---

## Atlas Comparison

| Atlas | Regions | Type | Resolution | Best For |
|-------|---------|------|------------|----------|
| Desikan-Killiany | 68 | Anatomical | Standard | General use, clinical |
| Destrieux | 148 | Anatomical | High | Detailed anatomy |
| DKT | 62 | Anatomical | Standard | Standardized labeling |
| Schaefer-100 | 100 | Functional | Low | Network overview |
| Schaefer-400 | 400 | Functional | Medium | Balanced detail |
| Schaefer-1000 | 1000 | Functional | High | Fine-grained networks |
| Glasser | 360 | Multimodal | High | HCP studies |
| Yeo-7 | 7 | Functional | Network | Large-scale networks |
| Yeo-17 | 17 | Functional | Network | Network subdivisions |

### Choosing an Atlas

**For clinical studies:**
- Use Desikan-Killiany (most widely used, good for comparisons)

**For detailed anatomical analysis:**
- Use Destrieux (finer anatomical detail)

**For functional connectivity:**
- Use Schaefer (multiple resolutions available)
- Use Yeo for network-level analysis

**For multimodal studies:**
- Use Glasser (combines multiple modalities)

**For longitudinal studies:**
- Use consistent atlas across timepoints
- Desikan-Killiany or DKT recommended

---

## Troubleshooting

### Issue: Atlas files not found

**Symptoms:**
```
Warning: Atlas directory not found, skipping Schaefer extraction
```

**Solution:**
```bash
# Verify files exist
ls -la bin/atlases/*.annot

# Check permissions
chmod 644 bin/atlases/*.annot

# Verify path in configuration
grep atlas_dir nextflow.config
```

### Issue: Extraction fails for specific atlas

**Symptoms:**
```
Error in atlas extraction for subject sub-001
```

**Solution:**
```bash
# Check subject's FreeSurfer output
ls -la fs_outputs/sub-001/stats/

# Verify required files exist
ls fs_outputs/sub-001/stats/lh.aparc.stats
ls fs_outputs/sub-001/label/lh.aparc.annot

# Check extraction log
cat work/*/extract_atlases_sub-001/.command.log
```

### Issue: Wrong atlas version

**Symptoms:**
Atlas statistics don't match expected regions.

**Solution:**
Ensure annotation files match FreeSurfer version:
- FreeSurfer 5.3: Use fsaverage
- FreeSurfer 6.0+: Use fsaverage or fsaverage6
- FastSurfer: Compatible with FreeSurfer 7.x

### Issue: Missing statistics for some regions

**Symptoms:**
Some regions have NA or missing values.

**Solution:**
This can be normal if:
- Region is very small
- Poor image quality in that area
- Segmentation failed for that region

Check QC reports and visual inspection.

---

## Advanced Usage

### Extracting Statistics Manually

For custom analysis outside the pipeline:

```bash
# Using FreeSurfer tools
mris_anatomical_stats \
    -a bin/atlases/lh.Schaefer2018_400Parcels_7Networks_order.annot \
    -f fs_outputs/sub-001/stats/lh.schaefer400.stats \
    sub-001 lh

# Using Python script
python bin/extract_atlases.py \
    --subject-dir fs_outputs/sub-001 \
    --subject-id sub-001 \
    --extract-schaefer \
    --schaefer-parcels 400 \
    --atlas-dir bin/atlases
```

### Batch Atlas Extraction

```bash
# Extract for all subjects
for subject in fs_outputs/sub-*; do
    subj_id=$(basename $subject)
    python bin/extract_atlases.py \
        --subject-dir $subject \
        --subject-id $subj_id \
        --extract-schaefer \
        --atlas-dir bin/atlases
done
```

---

## References

### Primary Citations

1. **Desikan-Killiany:**
   Desikan RS, et al. (2006). NeuroImage, 31(3):968-980.
   DOI: 10.1016/j.neuroimage.2006.01.021

2. **Destrieux:**
   Destrieux C, et al. (2010). NeuroImage, 53(1):1-15.
   DOI: 10.1016/j.neuroimage.2010.06.010

3. **DKT:**
   Klein A, Tourville J. (2012). Frontiers in Neuroscience, 6:171.
   DOI: 10.3389/fnins.2012.00171

4. **Schaefer:**
   Schaefer A, et al. (2018). Cerebral Cortex, 29:3095-3114.
   DOI: 10.1093/cercor/bhx179

5. **Glasser:**
   Glasser MF, et al. (2016). Nature, 536(7615):171-178.
   DOI: 10.1038/nature18933

6. **Yeo:**
   Yeo BT, et al. (2011). Journal of Neurophysiology, 106(3):1125-1165.
   DOI: 10.1152/jn.00338.2011

### Additional Resources

- **FreeSurfer Wiki:** https://surfer.nmr.mgh.harvard.edu/
- **CBIG GitHub:** https://github.com/ThomasYeoLab/CBIG
- **HCP:** https://www.humanconnectome.org/
- **BIDS:** https://bids.neuroimaging.io/

---

## Support

For atlas-specific questions:
- Check `bin/atlases/README.md` for download instructions
- See `USAGE.md` for pipeline usage
- Review `README.md` for general information

