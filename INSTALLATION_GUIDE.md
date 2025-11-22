# Installation and Setup Guide

This guide walks you through setting up the complete neuroimaging pipeline from scratch.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Access to an HPC cluster with Slurm
- [ ] Apptainer/Singularity installed on compute nodes
- [ ] Nextflow installed (or ability to install it)
- [ ] FreeSurfer license file
- [ ] Input data (DICOM, BIDS, or NIfTI)

## Step-by-Step Installation

### Step 1: Install Nextflow

```bash
# Download and install Nextflow
cd ~
curl -s https://get.nextflow.io | bash

# Move to a directory in your PATH
mkdir -p ~/bin
mv nextflow ~/bin/

# Add to PATH if not already there
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Verify installation
nextflow -version
```

Expected output:
```
nextflow version 23.10.0.5889
```

### Step 2: Verify Apptainer/Singularity

```bash
# Check if Apptainer is available
module avail apptainer
# or
module avail singularity

# Load the module
module load apptainer  # or singularity

# Verify it works
apptainer --version
```

### Step 3: Set Up Pipeline Directory

```bash
# Navigate to your project location
cd /path/to/your/projects

# If you already have the pipeline files, skip to Step 4
# Otherwise, create the directory structure
mkdir -p fastsurfer_pipeline
cd fastsurfer_pipeline

# Create all necessary directories
mkdir -p images fs_license dicom bids nii fs_outputs long_outputs qc stats logs work bin/atlases conf
```

### Step 4: Download FastSurfer Container

```bash
cd images

# Pull the FastSurfer CPU container
# This may take 10-20 minutes depending on your connection
apptainer pull fastsurfer-cpu.sif docker://deepmi/fastsurfer:cpu-latest

# Verify the container
ls -lh fastsurfer-cpu.sif

cd ..
```

Expected: A file around 2-3 GB named `fastsurfer-cpu.sif`

### Step 5: Add FreeSurfer License

```bash
# Option 1: If you already have a license
cp /path/to/your/license.txt fs_license/license.txt

# Option 2: If you need to obtain a license
# Visit: https://surfer.nmr.mgh.harvard.edu/registration.html
# Fill out the form and download license.txt
# Then copy it to fs_license/license.txt

# Verify the license file
cat fs_license/license.txt
```

The license file should contain your email and license key.

### Step 6: Download Atlas Files (Optional but Recommended)

```bash
cd bin/atlases

# Create download script
cat > download_atlases.sh <<'EOF'
#!/bin/bash
set -e

echo "Downloading Schaefer atlases..."
BASE_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/fsaverage/label"

for parcels in 100 200 400; do
    for networks in 7 17; do
        for hemi in lh rh; do
            file="${hemi}.Schaefer2018_${parcels}Parcels_${networks}Networks_order.annot"
            echo "  Downloading $file..."
            wget -q "${BASE_URL}/${file}" || echo "Failed to download $file"
        done
    done
done

echo "Downloading Yeo networks..."
YEO_URL="https://github.com/ThomasYeoLab/CBIG/raw/master/stable_projects/brain_parcellation/Yeo2011_fcMRI_clustering/1000subjects_reference/Yeo_JNeurophysiol11_SplitLabels/fsaverage5/label"

for networks in 7 17; do
    for hemi in lh rh; do
        file="${hemi}.Yeo2011_${networks}Networks_N1000.annot"
        echo "  Downloading $file..."
        wget -q "${YEO_URL}/${file}" || echo "Failed to download $file"
    done
done

echo "Done! Downloaded files:"
ls -lh *.annot 2>/dev/null || echo "No files downloaded"
EOF

# Make executable and run
chmod +x download_atlases.sh
./download_atlases.sh

cd ../..
```

### Step 7: Prepare Your Input Data

Choose one of the following based on your data format:

#### Option A: NIfTI Files (Simplest)

```bash
# Copy your T1-weighted NIfTI files to nii/
# Files MUST end with _T1w.nii.gz
cp /path/to/data/subject001_T1w.nii.gz nii/sub-001_T1w.nii.gz
cp /path/to/data/subject002_T1w.nii.gz nii/sub-002_T1w.nii.gz

# Verify naming
ls nii/
```

#### Option B: BIDS Format

```bash
# If you already have BIDS data
cp -r /path/to/bids/sub-* bids/

# Create dataset_description.json
cat > bids/dataset_description.json <<EOF
{
  "Name": "My Neuroimaging Study",
  "BIDSVersion": "1.8.0",
  "Authors": ["Your Name"]
}
EOF

# Verify structure
tree bids/ -L 3
```

#### Option C: DICOM Files

```bash
# Organize DICOM files by subject
mkdir -p dicom/sub-001
cp -r /path/to/dicom/patient001/* dicom/sub-001/

# You'll need to customize bin/heuristic.py
# See USAGE.md for detailed instructions
```

### Step 8: Verify Installation

```bash
# Check all required files
echo "Checking installation..."

# Check Nextflow
command -v nextflow && echo "✓ Nextflow installed" || echo "✗ Nextflow missing"

# Check container
[ -f images/fastsurfer-cpu.sif ] && echo "✓ FastSurfer container present" || echo "✗ Container missing"

# Check license
[ -f fs_license/license.txt ] && echo "✓ FreeSurfer license present" || echo "✗ License missing"

# Check pipeline files
[ -f main.nf ] && echo "✓ main.nf present" || echo "✗ main.nf missing"
[ -f nextflow.config ] && echo "✓ nextflow.config present" || echo "✗ Config missing"
[ -f run_pipeline.sbatch ] && echo "✓ run_pipeline.sbatch present" || echo "✗ Launcher missing"

# Check input data
INPUT_COUNT=$(find nii -name "*_T1w.nii.gz" 2>/dev/null | wc -l)
echo "Found $INPUT_COUNT T1 images in nii/"

echo ""
echo "Installation check complete!"
```

### Step 9: Test Run (Recommended)

Test the pipeline on a single subject before processing your full dataset:

```bash
# Create a test directory with one subject
mkdir -p nii_test
cp nii/sub-001_T1w.nii.gz nii_test/

# Run a quick test
nextflow run main.nf -profile slurm --nii_dir nii_test --threads 4

# If successful, you should see:
# - Process execution logs
# - Output in fs_outputs/sub-001/
# - Summary in pipeline_summary.txt
```

### Step 10: Run Full Pipeline

Once the test succeeds, run on your full dataset:

```bash
# Submit to Slurm
sbatch run_pipeline.sbatch

# Monitor progress
tail -f logs/nextflow_*.out

# Check job status
squeue -u $USER
```

## Configuration for Your HPC Environment

### Customize Slurm Settings

Edit `conf/slurm.config` to match your cluster:

```groovy
process {
    // Change partition name if different
    clusterOptions = '--partition=YOUR_PARTITION_NAME'
    
    // Adjust resources based on your cluster limits
    withName: 'FASTSURFER_CROSS' {
        cpus = 8
        memory = '32 GB'
        time = '24h'
    }
}
```

### Load Required Modules

Edit `run_pipeline.sbatch` to load your cluster's modules:

```bash
# Add your cluster-specific modules
module load nextflow/23.10.0
module load apptainer/1.2.0
module load java/17
```

## Common Setup Issues

### Issue: Nextflow not found

```bash
# Solution: Add to PATH
export PATH=$HOME/bin:$PATH
echo 'export PATH=$HOME/bin:$PATH' >> ~/.bashrc
```

### Issue: Container pull fails

```bash
# Solution: Pull on compute node with internet access
srun --partition=hpcnirc apptainer pull images/fastsurfer-cpu.sif docker://deepmi/fastsurfer:cpu-latest
```

### Issue: Permission denied on scripts

```bash
# Solution: Make scripts executable
chmod +x run_pipeline.sbatch
chmod +x bin/*.py
```

### Issue: Module not found

```bash
# Solution: Check available modules
module avail

# Load correct module name
module load apptainer  # or singularity, or apptainer/1.2.0
```

## Directory Structure After Setup

Your directory should look like this:

```
fastsurfer_pipeline/
├── main.nf                          ✓ Pipeline file
├── nextflow.config                  ✓ Configuration
├── run_pipeline.sbatch              ✓ Launcher script
├── README.md                        ✓ Documentation
├── USAGE.md                         ✓ Usage guide
├── ATLASES.md                       ✓ Atlas guide
├── INSTALLATION_GUIDE.md            ✓ This file
│
├── conf/
│   └── slurm.config                ✓ Slurm config
│
├── bin/
│   ├── extract_atlases.py          ✓ Helper scripts
│   ├── aggregate_stats.py          ✓
│   ├── longitudinal_stats.py       ✓
│   ├── qc_aggregator.py            ✓
│   ├── heuristic.py                ✓
│   └── atlases/
│       ├── README.md               ✓
│       └── *.annot                 ✓ (optional)
│
├── images/
│   └── fastsurfer-cpu.sif         ✓ Container (you add)
│
├── fs_license/
│   └── license.txt                 ✓ License (you add)
│
├── nii/                             ✓ Your input data
│   ├── sub-001_T1w.nii.gz
│   └── sub-002_T1w.nii.gz
│
└── [other directories created during pipeline run]
```

## Next Steps

1. **Review Documentation:**
   - Read `README.md` for overview
   - Check `USAGE.md` for detailed examples
   - See `ATLASES.md` for atlas setup

2. **Customize for Your Data:**
   - Adjust `nextflow.config` parameters
   - Modify `conf/slurm.config` resources
   - Update `run_pipeline.sbatch` modules

3. **Test Pipeline:**
   - Run on 1-2 subjects first
   - Verify outputs look correct
   - Check execution reports

4. **Process Full Dataset:**
   - Submit full batch
   - Monitor progress
   - Analyze results

## Getting Help

- **Pipeline issues:** Check `README.md` and `USAGE.md`
- **Atlas setup:** See `ATLASES.md`
- **Nextflow help:** https://www.nextflow.io/docs/latest/
- **FastSurfer:** https://github.com/Deep-MI/FastSurfer
- **FreeSurfer:** https://surfer.nmr.mgh.harvard.edu/

## Quick Reference Commands

```bash
# Submit pipeline
sbatch run_pipeline.sbatch

# Check job status
squeue -u $USER

# Monitor progress
tail -f logs/nextflow_*.out

# Cancel job
scancel <job_id>

# Resume failed pipeline
sbatch run_pipeline.sbatch  # Nextflow auto-resumes

# View execution report
firefox logs/report_*.html

# Check outputs
ls fs_outputs/
ls stats/
```

## Support

If you encounter issues:
1. Check the error logs in `logs/`
2. Review the Nextflow trace file
3. Inspect the work directory for failed processes
4. Consult the documentation files
5. Check FastSurfer and FreeSurfer documentation

Good luck with your neuroimaging analysis!

