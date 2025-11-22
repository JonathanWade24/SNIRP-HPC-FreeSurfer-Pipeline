#!/bin/bash
#SBATCH --job-name=neuroimaging_pipeline
#SBATCH --partition=hpcnirc
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=72:00:00
#SBATCH --output=logs/nextflow_%j.out
#SBATCH --error=logs/nextflow_%j.err

################################################################################
# Neuroimaging Pipeline Launcher
# 
# This script launches the comprehensive Nextflow neuroimaging pipeline on
# an HPC cluster using Slurm and Apptainer.
#
# Usage:
#   sbatch run_pipeline.sbatch
#
# Or with custom parameters:
#   sbatch --export=ALL,INPUT_MODE=bids,RUN_MRIQC=true run_pipeline.sbatch
#
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

################################################################################
# CONFIGURATION
################################################################################

# Pipeline mode (can be overridden by environment variables)
INPUT_MODE=${INPUT_MODE:-"nii"}           # Options: 'dicom', 'bids', 'nii'
RUN_DICOM_CONVERSION=${RUN_DICOM_CONVERSION:-"false"}
RUN_BIDS_VALIDATION=${RUN_BIDS_VALIDATION:-"true"}
RUN_MRIQC=${RUN_MRIQC:-"false"}
RUN_LONGITUDINAL=${RUN_LONGITUDINAL:-"false"}

# Advanced atlas options
EXTRACT_SCHAEFER=${EXTRACT_SCHAEFER:-"true"}
EXTRACT_GLASSER=${EXTRACT_GLASSER:-"true"}
EXTRACT_YEO=${EXTRACT_YEO:-"true"}

# Resource parameters
THREADS=${THREADS:-16}

################################################################################
# ENVIRONMENT SETUP
################################################################################

# Load Anaconda module
module load anaconda3

# Set Java 17 path (use full path, not ~)
export JAVA_HOME=/scratch/jonathanwade/slurm_pipeline/jdk-17.0.13+11
export PATH=$JAVA_HOME/bin:$PATH

# Clear any cached paths
hash -r

# Verify versions
echo "Environment setup:"
echo "  Java location: $(which java)"
echo "  Java version: $(java -version 2>&1 | head -1)"
echo "  Python version: $(python --version)"
echo "  Nextflow version: $(nextflow -version 2>&1 | grep version | head -1)"
echo ""

################################################################################
# HEADER
################################################################################

echo "=============================================="
echo "Neuroimaging Pipeline Launcher"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Started at: $(date)"
echo "Running on: $(hostname)"
echo "=============================================="
echo ""
echo "Pipeline Configuration:"
echo "  Input mode: $INPUT_MODE"
echo "  DICOM conversion: $RUN_DICOM_CONVERSION"
echo "  BIDS validation: $RUN_BIDS_VALIDATION"
echo "  MRIQC: $RUN_MRIQC"
echo "  Longitudinal: $RUN_LONGITUDINAL"
echo "  Extract Schaefer: $EXTRACT_SCHAEFER"
echo "  Extract Glasser: $EXTRACT_GLASSER"
echo "  Extract Yeo: $EXTRACT_YEO"
echo "  Threads per job: $THREADS"
echo "=============================================="
echo ""

################################################################################
# ENVIRONMENT SETUP
################################################################################

# Load required modules (uncomment and adjust based on your HPC environment)
# module load nextflow/23.10.0
# module load apptainer/1.2.0
# module load java/17

# Verify Nextflow is available
if ! command -v nextflow &> /dev/null; then
    echo "ERROR: Nextflow is not available"
    echo "Please install Nextflow or load the appropriate module"
    echo ""
    echo "Installation instructions:"
    echo "  curl -s https://get.nextflow.io | bash"
    echo "  mv nextflow ~/bin/ (or another directory in your PATH)"
    exit 1
fi

# Display Nextflow version
echo "Nextflow version:"
nextflow -version
echo ""

################################################################################
# PRE-FLIGHT CHECKS
################################################################################

echo "Running pre-flight checks..."
echo ""

# Check for required files and directories
CHECKS_PASSED=true

# Check for FastSurfer container
if [ ! -f "images/fastsurfer-cpu.sif" ]; then
    echo "ERROR: FastSurfer container not found at images/fastsurfer-cpu.sif"
    CHECKS_PASSED=false
fi

# Check for FreeSurfer license
if [ ! -f "fs_license/license.txt" ]; then
    echo "ERROR: FreeSurfer license not found at fs_license/license.txt"
    echo "Please obtain a FreeSurfer license from: https://surfer.nmr.mgh.harvard.edu/registration.html"
    CHECKS_PASSED=false
fi

# Check for input data based on mode
if [ "$INPUT_MODE" = "dicom" ]; then
    if [ ! -d "dicom" ] || [ -z "$(ls -A dicom 2>/dev/null)" ]; then
        echo "ERROR: No DICOM data found in dicom/ directory"
        CHECKS_PASSED=false
    else
        DICOM_COUNT=$(find dicom -type d -mindepth 1 -maxdepth 1 | wc -l)
        echo "  Found $DICOM_COUNT subject directories in dicom/"
    fi
elif [ "$INPUT_MODE" = "bids" ]; then
    if [ ! -d "bids" ] || [ -z "$(ls -A bids 2>/dev/null)" ]; then
        echo "ERROR: No BIDS data found in bids/ directory"
        CHECKS_PASSED=false
    else
        T1_COUNT=$(find bids -name "*_T1w.nii.gz" -type f 2>/dev/null | wc -l)
        echo "  Found $T1_COUNT T1 images in bids/"
    fi
elif [ "$INPUT_MODE" = "nii" ]; then
    if [ ! -d "nii" ] || [ -z "$(ls -A nii 2>/dev/null)" ]; then
        echo "ERROR: No NIfTI data found in nii/ directory"
        CHECKS_PASSED=false
    else
        T1_COUNT=$(find nii -name "*_T1w.nii.gz" -type f 2>/dev/null | wc -l)
        echo "  Found $T1_COUNT T1 images in nii/"
    fi
else
    echo "ERROR: Invalid INPUT_MODE: $INPUT_MODE"
    echo "Valid options: dicom, bids, nii"
    CHECKS_PASSED=false
fi

# Check for main pipeline file
if [ ! -f "main.nf" ]; then
    echo "ERROR: main.nf not found"
    CHECKS_PASSED=false
fi

# Check for configuration files
if [ ! -f "nextflow.config" ]; then
    echo "ERROR: nextflow.config not found"
    CHECKS_PASSED=false
fi

if [ ! -f "conf/slurm.config" ]; then
    echo "ERROR: conf/slurm.config not found"
    CHECKS_PASSED=false
fi

# Check for helper scripts
if [ ! -f "bin/extract_atlases.py" ]; then
    echo "WARNING: bin/extract_atlases.py not found - atlas extraction may fail"
fi

if [ ! -f "bin/aggregate_stats.py" ]; then
    echo "WARNING: bin/aggregate_stats.py not found - stats aggregation may fail"
fi

# Check for HeuDiConv heuristic if DICOM conversion is enabled
if [ "$RUN_DICOM_CONVERSION" = "true" ] && [ ! -f "bin/heuristic.py" ]; then
    echo "ERROR: bin/heuristic.py not found (required for DICOM conversion)"
    CHECKS_PASSED=false
fi

echo ""

if [ "$CHECKS_PASSED" = false ]; then
    echo "=============================================="
    echo "Pre-flight checks FAILED"
    echo "Please fix the errors above and try again"
    echo "=============================================="
    exit 1
fi

echo "Pre-flight checks PASSED"
echo ""

################################################################################
# CREATE DIRECTORIES
################################################################################

echo "Creating output directories..."
mkdir -p logs work fs_outputs long_outputs qc stats
echo "  Directories created"
echo ""

################################################################################
# BUILD NEXTFLOW COMMAND
################################################################################

# Base command
NF_CMD="nextflow run main.nf -profile slurm -resume"

# Add parameters
NF_CMD="$NF_CMD --input_mode $INPUT_MODE"
NF_CMD="$NF_CMD --run_dicom_conversion $RUN_DICOM_CONVERSION"
NF_CMD="$NF_CMD --run_bids_validation $RUN_BIDS_VALIDATION"
NF_CMD="$NF_CMD --run_mriqc $RUN_MRIQC"
NF_CMD="$NF_CMD --run_longitudinal $RUN_LONGITUDINAL"
NF_CMD="$NF_CMD --extract_schaefer $EXTRACT_SCHAEFER"
NF_CMD="$NF_CMD --extract_glasser $EXTRACT_GLASSER"
NF_CMD="$NF_CMD --extract_yeo $EXTRACT_YEO"
NF_CMD="$NF_CMD --threads $THREADS"

# Add reporting options
NF_CMD="$NF_CMD -with-report logs/report_${SLURM_JOB_ID}.html"
NF_CMD="$NF_CMD -with-timeline logs/timeline_${SLURM_JOB_ID}.html"
NF_CMD="$NF_CMD -with-trace logs/trace_${SLURM_JOB_ID}.txt"
NF_CMD="$NF_CMD -with-dag logs/dag_${SLURM_JOB_ID}.html"

################################################################################
# RUN PIPELINE
################################################################################

echo "=============================================="
echo "Starting Nextflow pipeline..."
echo "=============================================="
echo ""
echo "Command:"
echo "$NF_CMD"
echo ""
echo "=============================================="
echo ""

# Ensure Java 17 is in PATH for all Nextflow processes (double-check)
export JAVA_HOME=/scratch/jonathanwade/slurm_pipeline/jdk-17.0.13+11
export PATH=$JAVA_HOME/bin:$PATH
hash -r

# Verify Java before running
echo "Final Java check before pipeline:"
echo "  Using Java: $(which java)"
echo "  Java version: $(java -version 2>&1 | head -1)"
echo ""

# Run the pipeline
eval $NF_CMD

EXIT_CODE=$?

################################################################################
# COMPLETION
################################################################################

echo ""
echo "=============================================="
echo "Pipeline finished at: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=============================================="
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Pipeline completed successfully!"
    echo ""
    echo "Output locations:"
    echo "  - FastSurfer outputs: fs_outputs/"
    echo "  - Statistics: stats/"
    echo "  - QC reports: qc/"
    echo "  - Logs: logs/"
    echo ""
    echo "Summary files:"
    echo "  - Pipeline summary: pipeline_summary.txt"
    echo "  - HTML summary: pipeline_summary.html"
    echo "  - Execution report: logs/report_${SLURM_JOB_ID}.html"
    echo "  - Timeline: logs/timeline_${SLURM_JOB_ID}.html"
    echo ""
    echo "Generated statistics:"
    if [ -f "stats/cortical_thickness.csv" ]; then
        echo "  - Cortical thickness: stats/cortical_thickness.csv"
    fi
    if [ -f "stats/subcortical_volumes.csv" ]; then
        echo "  - Subcortical volumes: stats/subcortical_volumes.csv"
    fi
    if [ -f "stats/aparc_dkt.csv" ]; then
        echo "  - DKT atlas: stats/aparc_dkt.csv"
    fi
    if [ "$RUN_LONGITUDINAL" = "true" ] && [ -f "stats/longitudinal_slope_estimates.csv" ]; then
        echo "  - Longitudinal slopes: stats/longitudinal_slope_estimates.csv"
        echo "  - Percent changes: stats/longitudinal_percent_change.csv"
    fi
    if [ "$RUN_MRIQC" = "true" ] && [ -f "stats/qc_summary.csv" ]; then
        echo "  - QC summary: stats/qc_summary.csv"
    fi
    echo ""
else
    echo "ERROR: Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check the error logs:"
    echo "     - Nextflow log: logs/nextflow_${SLURM_JOB_ID}.err"
    echo "     - Trace file: logs/trace_${SLURM_JOB_ID}.txt"
    echo "  2. Check individual process logs in work/ directory"
    echo "  3. Review the execution report: logs/report_${SLURM_JOB_ID}.html"
    echo "  4. Try resuming the pipeline with: nextflow run main.nf -resume"
    echo ""
    echo "Common issues:"
    echo "  - Out of memory: Increase memory in conf/slurm.config"
    echo "  - Timeout: Increase time limits in conf/slurm.config"
    echo "  - Container issues: Check Apptainer availability on compute nodes"
    echo "  - Input data: Verify file naming and directory structure"
    echo ""
fi

echo "=============================================="
echo "Job completed"
echo "=============================================="

exit $EXIT_CODE

################################################################################
# USAGE EXAMPLES
################################################################################

: <<'EXAMPLES'

# Example 1: Basic cross-sectional processing from NIfTI files
sbatch run_pipeline.sbatch

# Example 2: Full pipeline from DICOM with MRIQC
sbatch --export=ALL,INPUT_MODE=dicom,RUN_DICOM_CONVERSION=true,RUN_MRIQC=true run_pipeline.sbatch

# Example 3: BIDS input with longitudinal processing
sbatch --export=ALL,INPUT_MODE=bids,RUN_LONGITUDINAL=true run_pipeline.sbatch

# Example 4: BIDS input without advanced atlases
sbatch --export=ALL,INPUT_MODE=bids,EXTRACT_SCHAEFER=false,EXTRACT_GLASSER=false,EXTRACT_YEO=false run_pipeline.sbatch

# Example 5: Custom resource allocation
sbatch --cpus-per-task=4 --mem=16G --export=ALL,THREADS=16 run_pipeline.sbatch

# Example 6: Resume a failed pipeline
# (Nextflow will automatically resume from the last successful step)
sbatch run_pipeline.sbatch

EXAMPLES
