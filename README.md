# SNIRP HPC FreeSurfer Pipeline

A production-grade Nextflow pipeline for automated structural neuroimaging analysis on HPC clusters. Developed by the SNIRP Lab for cortical reconstruction, longitudinal analysis, and multi-atlas parcellation using FastSurfer on CPU-only systems.

[![Nextflow](https://img.shields.io/badge/nextflow-%E2%89%A524.10-brightgreen.svg)](https://www.nextflow.io/)
[![FastSurfer](https://img.shields.io/badge/FastSurfer-2.4+-blue.svg)](https://github.com/Deep-MI/FastSurfer)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

- **Fully Automated** - From raw T1 images to publication-ready statistics
- **HPC-Optimized** - Massively parallel processing on Slurm clusters
- **Longitudinal Support** - Track cortical changes over time with slope estimation
- **Multi-Atlas Parcellation** - 6+ atlases including Schaefer, Glasser, Yeo
- **Containerized** - Reproducible with Apptainer/Singularity
- **Resume Capability** - Automatic recovery from failures
- **CPU-Only** - No GPU required

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/SNIRP-HPC-FreeSurfer-Pipeline.git
cd SNIRP-HPC-FreeSurfer-Pipeline

# 2. Set up directories
mkdir -p images fs_license nii

# 3. Download FastSurfer container
apptainer pull images/fastsurfer-cpu.sif docker://deepmi/fastsurfer:cpu-latest

# 4. Add your FreeSurfer license
cp /path/to/license.txt fs_license/license.txt

# 5. Add your T1 images (BIDS-named)
cp /path/to/data/*_T1w.nii.gz nii/

# 6. Submit to cluster
sbatch run_pipeline.sbatch
```

## Prerequisites

### Required
- **Nextflow** ≥24.10
- **Apptainer/Singularity** (available on HPC)
- **Slurm** workload manager
- **FreeSurfer license** ([free registration](https://surfer.nmr.mgh.harvard.edu/registration.html))

### Optional
- **Atlas files** for advanced parcellations (see [ATLASES.md](ATLASES.md))

## Installation

### 1. Install Nextflow

```bash
curl -s https://get.nextflow.io | bash
mv nextflow ~/bin/  # or another directory in $PATH
```

### 2. Set Up Java (if needed)

Nextflow requires Java 11+. On HPC systems:

```bash
# Check Java version
java -version

# If Java 8 or lower, install Java 17
cd ~
wget https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.13%2B11/OpenJDK17U-jdk_x64_linux_hotspot_17.0.13_11.tar.gz
tar -xzf OpenJDK17U-jdk_x64_linux_hotspot_17.0.13_11.tar.gz
echo 'export JAVA_HOME=~/jdk-17.0.13+11' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. Download FastSurfer Container

```bash
mkdir -p images
apptainer pull images/fastsurfer-cpu.sif docker://deepmi/fastsurfer:cpu-latest
```

### 4. Add FreeSurfer License

```bash
mkdir -p fs_license
# Copy your license file
cp /path/to/your/license.txt fs_license/license.txt
```

## Usage

### Basic Cross-Sectional Analysis

Process T1-weighted images:

```bash
# Place files in nii/ directory with BIDS naming
# Format: sub-{ID}_T1w.nii.gz or sub-{ID}_ses-{SESSION}_T1w.nii.gz

sbatch run_pipeline.sbatch
```

### Longitudinal Analysis

For subjects with multiple timepoints:

```bash
sbatch --export=ALL,RUN_LONGITUDINAL=true run_pipeline.sbatch
```

### Custom Configuration

```bash
# Adjust thread count
sbatch --export=ALL,THREADS=32 run_pipeline.sbatch

# Enable quality control
sbatch --export=ALL,RUN_MRIQC=true run_pipeline.sbatch

# Disable advanced atlases
sbatch --export=ALL,EXTRACT_SCHAEFER=false run_pipeline.sbatch
```

## Pipeline Stages

1. **Input Validation** - Check file formats and naming
2. **FastSurfer Cross-Sectional** - Cortical reconstruction (~8-12h per subject)
3. **Longitudinal Processing** (optional) - Within-subject template creation
4. **Atlas Extraction** - Multi-atlas parcellation statistics
5. **Statistics Aggregation** - Combine results into CSV tables
6. **Report Generation** - HTML execution reports

## Outputs

### Directory Structure

```
.
├── fs_outputs/              # FastSurfer cross-sectional results
│   └── sub-{ID}/
│       ├── mri/            # Volumetric data
│       ├── surf/           # Surface meshes
│       └── stats/          # Per-subject statistics
├── long_outputs/           # Longitudinal results
├── stats/                  # Aggregated statistics (CSV)
│   ├── cortical_thickness.csv
│   ├── subcortical_volumes.csv
│   ├── aparc_dkt.csv
│   ├── longitudinal_slope_estimates.csv
│   └── longitudinal_percent_change.csv
└── logs/                   # Execution logs and reports
    ├── report_*.html
    ├── timeline_*.html
    └── trace_*.txt
```

### Statistics Files

- **cortical_thickness.csv** - Thickness measurements per region
- **subcortical_volumes.csv** - Volumes of subcortical structures
- **aparc_dkt.csv** - Complete DKT atlas statistics
- **longitudinal_slope_estimates.csv** - Rate of change (mm/year or mm³/year)
- **longitudinal_percent_change.csv** - Percent change between timepoints

## Monitoring

```bash
# Check job status
squeue -u $USER

# Watch live progress
tail -f logs/nextflow_*.out

# Count completed subjects
ls fs_outputs/ | wc -l

# View execution report (after completion)
firefox logs/report_*.html
```

## Configuration

### Resource Allocation

Edit `conf/slurm.config` to adjust resources:

```groovy
withName: 'FASTSURFER_CROSS' {
    cpus = 16
    memory = '64 GB'
    time = '24h'
}
```

### Pipeline Parameters

Edit `nextflow.config` or pass via command line:

```groovy
params {
    threads = 16
    extract_schaefer = true
    extract_glasser = true
    schaefer_parcels = "100,200,400"
}
```

## Troubleshooting

### Container Not Found

```bash
# Verify container exists
ls -lh images/fastsurfer-cpu.sif

# Re-download if needed
apptainer pull images/fastsurfer-cpu.sif docker://deepmi/fastsurfer:cpu-latest
```

### Out of Memory

Increase memory allocation in `conf/slurm.config`:

```groovy
withName: 'FASTSURFER_CROSS' {
    memory = '128 GB'  // Increase from default 64 GB
}
```

### Job Timeout

Increase time limit:

```groovy
withName: 'FASTSURFER_CROSS' {
    time = '48h'  // Increase from default 24h
}
```

### Corrupted Input Files

If you encounter file corruption errors:

```bash
# Identify corrupted files
grep "OSError.*bytes" logs/nextflow_*.out

# Check file sizes
ls -lh nii/*.nii.gz | awk '$5 < 10000000 {print}'

# Re-download or exclude corrupted files
```

## Advanced Usage

See [USAGE.md](USAGE.md) for detailed examples including:
- DICOM to BIDS conversion
- BIDS validation workflows
- Quality control with MRIQC
- Custom atlas integration
- Batch processing strategies

## Atlas Documentation

See [ATLASES.md](ATLASES.md) for:
- Atlas download instructions
- Custom atlas integration
- Citation requirements
- Parcellation comparisons

## Performance

With optimized settings on a modern HPC cluster:

| Dataset Size | Parallelization | Estimated Time |
|--------------|----------------|----------------|
| 50 subjects | 50 concurrent | ~12-18 hours |
| 150 subjects | 100 concurrent | ~18-24 hours |
| 500 subjects | 150 concurrent | ~48-72 hours |

*Times include cross-sectional + longitudinal processing*

## Citation

If you use this pipeline, please cite:

**FastSurfer:**
> Henschel L, Conjeti S, Estrada S, Diers K, Fischl B, Reuter M. (2020). FastSurfer - A fast and accurate deep learning based neuroimaging pipeline. NeuroImage, 219:117012.

**Nextflow:**
> Di Tommaso P, Chatzou M, Floden EW, et al. (2017). Nextflow enables reproducible computational workflows. Nature Biotechnology, 35(4):316-319.

**FreeSurfer:**
> Fischl B. (2012). FreeSurfer. NeuroImage, 62(2):774-781.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SNIRP-HPC-FreeSurfer-Pipeline/issues)
- **Documentation**: See `docs/` directory
- **FastSurfer**: https://github.com/Deep-MI/FastSurfer
- **Nextflow**: https://www.nextflow.io/docs/

## Acknowledgments

- FastSurfer team at MIT/MGH
- Nextflow development team
- FreeSurfer community
