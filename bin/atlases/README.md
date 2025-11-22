# Atlas Files for Neuroimaging Pipeline

This directory contains annotation files for advanced brain parcellation schemes. These atlases extend the standard FreeSurfer/FastSurfer parcellations (Desikan-Killiany, Destrieux, DKT) with additional functional and anatomical parcellations.

## Overview

The pipeline automatically extracts statistics from:
- **Standard atlases** (always available): Desikan-Killiany, Destrieux, DKT
- **Advanced atlases** (require setup): Schaefer, Glasser, Yeo

## Required Atlas Files

### 1. Schaefer Parcellation

The Schaefer atlas provides multi-resolution cortical parcellations based on resting-state fMRI data.

**Files needed:**
```
lh.Schaefer2018_100Parcels_7Networks_order.annot
rh.Schaefer2018_100Parcels_7Networks_order.annot
lh.Schaefer2018_100Parcels_17Networks_order.annot
rh.Schaefer2018_100Parcels_17Networks_order.annot
lh.Schaefer2018_200Parcels_7Networks_order.annot
rh.Schaefer2018_200Parcels_7Networks_order.annot
lh.Schaefer2018_200Parcels_17Networks_order.annot
rh.Schaefer2018_200Parcels_17Networks_order.annot
lh.Schaefer2018_400Parcels_7Networks_order.annot
rh.Schaefer2018_400Parcels_7Networks_order.annot
lh.Schaefer2018_400Parcels_17Networks_order.annot
rh.Schaefer2018_400Parcels_17Networks_order.annot
```

**Download:**
```bash
# Download from GitHub
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label/lh.Schaefer2018_100Parcels_7Networks_order.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label/rh.Schaefer2018_100Parcels_7Networks_order.annot

# Repeat for other resolutions (200, 400 parcels) and networks (7, 17)
```

**Alternative - Download all at once:**
```bash
cd bin/atlases
bash download_schaefer.sh  # See script below
```

**Citation:**
> Schaefer A, Kong R, Gordon EM, Laumann TO, Zuo XN, Holmes AJ, Eickhoff SB, Yeo BTT. (2018). Local-Global Parcellation of the Human Cerebral Cortex from Intrinsic Functional Connectivity MRI. Cerebral Cortex, 29:3095-3114.

### 2. Glasser Multimodal Parcellation (HCP-MMP1.0)

The Glasser atlas is a high-resolution parcellation of human cortex based on multimodal neuroimaging data from the Human Connectome Project.

**Files needed:**
```
lh.HCP-MMP1.annot
rh.HCP-MMP1.annot
```

**Download:**
```bash
# Download from FreeSurfer
cd bin/atlases

# Option 1: If you have FreeSurfer installed
cp $FREESURFER_HOME/subjects/fsaverage/label/lh.HCP-MMP1.annot .
cp $FREESURFER_HOME/subjects/fsaverage/label/rh.HCP-MMP1.annot .

# Option 2: Download directly
wget https://figshare.com/ndownloader/files/5528816 -O lh.HCP-MMP1.annot
wget https://figshare.com/ndownloader/files/5528819 -O rh.HCP-MMP1.annot
```

**Citation:**
> Glasser MF, Coalson TS, Robinson EC, et al. (2016). A multi-modal parcellation of human cerebral cortex. Nature, 536(7615):171-178.

### 3. Yeo Functional Networks

The Yeo atlas provides functional network parcellations based on resting-state fMRI.

**Files needed:**
```
lh.Yeo2011_7Networks_N1000.annot
rh.Yeo2011_7Networks_N1000.annot
lh.Yeo2011_17Networks_N1000.annot
rh.Yeo2011_17Networks_N1000.annot
```

**Download:**
```bash
# Download from GitHub
cd bin/atlases
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/lh.Yeo2011_7Networks_N1000.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/rh.Yeo2011_7Networks_N1000.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/lh.Yeo2011_17Networks_N1000.annot
wget https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label/rh.Yeo2011_17Networks_N1000.annot
```

**Citation:**
> Yeo BT, Krienen FM, Sepulcre J, et al. (2011). The organization of the human cerebral cortex estimated by intrinsic functional connectivity. Journal of Neurophysiology, 106(3):1125-1165.

## Quick Setup Script

Create a script to download all atlases at once:

```bash
#!/bin/bash
# download_atlases.sh - Download all atlas files

set -e

ATLAS_DIR="$(dirname "$0")"
cd "$ATLAS_DIR"

echo "Downloading atlas files..."
echo "This may take a few minutes..."

# Create temporary directory
mkdir -p temp
cd temp

# ============================================================================
# Schaefer Atlases
# ============================================================================
echo ""
echo "Downloading Schaefer atlases..."

BASE_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label"

for parcels in 100 200 400; do
    for networks in 7 17; do
        for hemi in lh rh; do
            file="${hemi}.Schaefer2018_${parcels}Parcels_${networks}Networks_order.annot"
            echo "  Downloading $file..."
            wget -q "${BASE_URL}/${file}" -O "../${file}"
        done
    done
done

# ============================================================================
# Yeo Networks
# ============================================================================
echo ""
echo "Downloading Yeo networks..."

YEO_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label"

for networks in 7 17; do
    for hemi in lh rh; do
        file="${hemi}.Yeo2011_${networks}Networks_N1000.annot"
        echo "  Downloading $file..."
        wget -q "${YEO_URL}/${file}" -O "../${file}"
    done
done

# ============================================================================
# Glasser Atlas
# ============================================================================
echo ""
echo "Downloading Glasser atlas..."
echo "  Note: Glasser atlas requires manual download or FreeSurfer installation"
echo "  Please download from: https://figshare.com/articles/HCP-MMP1_0_projected_on_fsaverage/3498446"
echo "  Or copy from: \$FREESURFER_HOME/subjects/fsaverage/label/"

# Clean up
cd ..
rm -rf temp

echo ""
echo "============================================"
echo "Atlas download complete!"
echo "============================================"
echo ""
echo "Downloaded files:"
ls -lh *.annot 2>/dev/null || echo "  (No .annot files found)"
echo ""
echo "Note: You may need to manually download the Glasser atlas"
echo "See README.md for instructions"
```

Save this as `download_atlases.sh` and run:
```bash
chmod +x bin/atlases/download_atlases.sh
cd bin/atlases
./download_atlases.sh
```

## Verifying Atlas Files

After downloading, verify the files are present:

```bash
cd bin/atlases
ls -lh *.annot
```

You should see annotation files (`.annot`) for each atlas.

## Using Custom Atlases

To add your own custom atlas:

1. Place the `.annot` files in this directory
2. Modify `bin/extract_atlases.py` to include your atlas
3. Update the pipeline parameters in `nextflow.config`

Example for a custom atlas:
```python
# In extract_atlases.py, add a new method:
def extract_custom_atlas(self) -> Dict:
    """Extract custom atlas statistics"""
    stats = {}
    for hemi in ['lh', 'rh']:
        annot_file = self.atlas_dir / f'{hemi}.custom_atlas.annot'
        if annot_file.exists():
            # Process annotation file
            stats[f'{hemi}_custom'] = {'status': 'available'}
    return stats
```

## Atlas Information Summary

| Atlas | Regions | Resolution | Data Modality | Use Case |
|-------|---------|------------|---------------|----------|
| Desikan-Killiany | 68 | Standard | Anatomical | General parcellation |
| Destrieux | 148 | High | Anatomical | Detailed gyral/sulcal |
| DKT | 62 | Standard | Anatomical | Cortical labeling |
| Schaefer | 100-1000 | Multi-scale | rs-fMRI | Functional networks |
| Glasser | 360 | High | Multimodal | Detailed cortical areas |
| Yeo | 7 or 17 | Network | rs-fMRI | Functional networks |

## Troubleshooting

### Issue: Files not found during pipeline execution

**Solution:** Ensure files are in the correct location:
```bash
ls -la bin/atlases/*.annot
```

### Issue: Permission denied

**Solution:** Make sure files are readable:
```bash
chmod 644 bin/atlases/*.annot
```

### Issue: Atlas extraction fails

**Solution:** Check that the atlas files match the expected naming convention. The pipeline looks for specific filenames.

## References

1. **Desikan-Killiany:** Desikan RS, et al. (2006). An automated labeling system for subdividing the human cerebral cortex on MRI scans into gyral based regions of interest. NeuroImage, 31(3):968-980.

2. **Destrieux:** Destrieux C, et al. (2010). Automatic parcellation of human cortical gyri and sulci using standard anatomical nomenclature. NeuroImage, 53(1):1-15.

3. **DKT:** Klein A, Tourville J. (2012). 101 labeled brain images and a consistent human cortical labeling protocol. Frontiers in Neuroscience, 6:171.

4. **Schaefer:** Schaefer A, et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex from Intrinsic Functional Connectivity MRI. Cerebral Cortex, 29:3095-3114.

5. **Glasser:** Glasser MF, et al. (2016). A multi-modal parcellation of human cerebral cortex. Nature, 536(7615):171-178.

6. **Yeo:** Yeo BT, et al. (2011). The organization of the human cerebral cortex estimated by intrinsic functional connectivity. Journal of Neurophysiology, 106(3):1125-1165.

## Support

For issues with atlas files or extraction, please check:
- FreeSurfer documentation: https://surfer.nmr.mgh.harvard.edu/
- CBIG GitHub: https://github.com/ThomasYeoLab/CBIG
- Pipeline documentation: See main README.md

