#!/bin/bash
################################################################################
# ADNI-DOD Pipeline Launcher
# Quick script to process your ADNI dataset
################################################################################

set -e

echo "=============================================="
echo "ADNI-DOD Neuroimaging Pipeline Setup"
echo "=============================================="
echo ""

# Configuration
MANIFEST="ADNI-DOD_11_18_2025.csv"
ADNI_DOWNLOADS="/path/to/your/adni/downloads"  # ← CHANGE THIS
OUTPUT_DIR="nii"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

################################################################################
# Step 1: Check Prerequisites
################################################################################

echo "Step 1: Checking prerequisites..."
echo ""

# Check manifest
if [ ! -f "$MANIFEST" ]; then
    echo -e "${RED}✗ Error: Manifest file not found: $MANIFEST${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Manifest found${NC}"

# Check container
if [ ! -f "images/fastsurfer-cpu.sif" ]; then
    echo -e "${RED}✗ Error: FastSurfer container not found${NC}"
    echo "  Download with: apptainer pull fastsurfer-cpu.sif docker://deepmi/fastsurfer:latest"
    exit 1
fi
echo -e "${GREEN}✓ FastSurfer container found${NC}"

# Check license
if [ ! -f "fs_license/license.txt" ]; then
    echo -e "${RED}✗ Error: FreeSurfer license not found${NC}"
    echo "  Place your license at: fs_license/license.txt"
    exit 1
fi
echo -e "${GREEN}✓ FreeSurfer license found${NC}"

# Check ADNI directory
if [ ! -d "$ADNI_DOWNLOADS" ]; then
    echo -e "${YELLOW}⚠ Warning: ADNI download directory not set${NC}"
    echo "  Please edit this script and set ADNI_DOWNLOADS path"
    echo "  Current value: $ADNI_DOWNLOADS"
    read -p "Press Enter to continue with file organization only, or Ctrl+C to exit..."
fi

echo ""

################################################################################
# Step 2: Generate Subject Information
################################################################################

echo "Step 2: Analyzing dataset..."
echo ""

python prepare_adni_data.py --manifest $MANIFEST --info-only

echo ""
echo -e "${GREEN}✓ Subject information generated${NC}"
echo "  Review: ${MANIFEST%.csv}_subject_info.csv"
echo ""
read -p "Press Enter to continue with file organization..."

################################################################################
# Step 3: Organize Files
################################################################################

echo ""
echo "Step 3: Organizing ADNI files..."
echo ""

if [ -d "$ADNI_DOWNLOADS" ]; then
    # Count existing files
    EXISTING_COUNT=$(find $OUTPUT_DIR -name "*.nii.gz" 2>/dev/null | wc -l)
    
    if [ $EXISTING_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $EXISTING_COUNT existing files in $OUTPUT_DIR${NC}"
        read -p "Continue? This will skip existing files (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
    
    # Run organization
    python prepare_adni_data.py \
        --manifest $MANIFEST \
        --dicom-dir $ADNI_DOWNLOADS \
        --output-dir $OUTPUT_DIR
    
    echo ""
    echo -e "${GREEN}✓ Files organized${NC}"
    echo ""
    
    # Show summary
    FILE_COUNT=$(find $OUTPUT_DIR -name "*.nii.gz" 2>/dev/null | wc -l)
    SUBJECT_COUNT=$(find $OUTPUT_DIR -name "*.nii.gz" 2>/dev/null | xargs basename -a | cut -d_ -f1-2 | sort -u | wc -l)
    
    echo "Summary:"
    echo "  Total files: $FILE_COUNT"
    echo "  Unique subjects: $SUBJECT_COUNT"
    echo ""
    
    # Check for longitudinal data
    MULTI_SESSION=$(find $OUTPUT_DIR -name "*.nii.gz" | xargs basename -a | cut -d_ -f1-2 | sort | uniq -c | awk '$1 > 1' | wc -l)
    
    if [ $MULTI_SESSION -gt 0 ]; then
        echo -e "${GREEN}✓ Detected $MULTI_SESSION subjects with multiple timepoints${NC}"
        echo "  → Longitudinal processing recommended"
        LONGITUDINAL="true"
    else
        echo "  Single timepoint per subject detected"
        echo "  → Cross-sectional processing only"
        LONGITUDINAL="false"
    fi
    
else
    echo -e "${YELLOW}⚠ ADNI directory not accessible, skipping file organization${NC}"
    echo "  Please organize files manually or update ADNI_DOWNLOADS path"
    exit 0
fi

echo ""
read -p "Press Enter to continue with pipeline submission..."

################################################################################
# Step 4: Submit Pipeline
################################################################################

echo ""
echo "Step 4: Submitting pipeline to Slurm..."
echo ""

# Ask user for processing mode
echo "Processing options:"
echo "  1) Longitudinal (RECOMMENDED - you have multi-timepoint data)"
echo "  2) Cross-sectional only"
echo "  3) Longitudinal + MRIQC quality control"
echo "  4) Exit without submitting"
echo ""
read -p "Select option (1-4): " -n 1 -r
echo ""

case $REPLY in
    1)
        echo "Submitting LONGITUDINAL pipeline..."
        sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch
        ;;
    2)
        echo "Submitting CROSS-SECTIONAL pipeline..."
        sbatch run_pipeline.sbatch
        ;;
    3)
        echo "Submitting LONGITUDINAL + MRIQC pipeline..."
        sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true,RUN_MRIQC=true run_pipeline.sbatch
        ;;
    4)
        echo "Pipeline not submitted. You can submit manually with:"
        echo "  sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch"
        exit 0
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

# Get job ID
sleep 2
JOB_ID=$(squeue -u $USER --format="%.18i %.20j" | grep "neuroimaging" | awk '{print $1}' | head -1)

echo ""
echo "=============================================="
echo "Pipeline Submitted!"
echo "=============================================="
echo ""
echo "Monitor progress:"
echo "  squeue -u $USER"
echo "  tail -f logs/nextflow_*.out"
echo ""

if [ -n "$JOB_ID" ]; then
    echo "Job ID: $JOB_ID"
    echo "Check status: squeue -j $JOB_ID"
fi

echo ""
echo "Expected completion time:"
if [ "$LONGITUDINAL" = "true" ]; then
    echo "  Longitudinal processing: 48-72 hours"
    echo "  (Includes cross-sectional + base + longitudinal stages)"
else
    echo "  Cross-sectional processing: 24-36 hours"
fi

echo ""
echo "Output locations:"
echo "  - FastSurfer outputs: fs_outputs/"
echo "  - Longitudinal outputs: long_outputs/"
echo "  - Statistics: stats/"
echo "  - Logs: logs/"
echo ""
echo "✓ Pipeline setup complete!"
echo "=============================================="



