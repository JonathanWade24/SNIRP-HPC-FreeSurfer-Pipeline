#!/bin/bash
# Cleanup script for preparing repository for GitHub

echo "Cleaning up repository for GitHub..."

# Remove ADNI-specific files
rm -f ADNI-DOD_11_18_2025.csv
rm -f ADNI_DATASET_ANALYSIS.md
rm -f ADNI_QUICK_START.md
rm -f RUN_ADNI_PIPELINE.sh
rm -f prepare_adni_data.py

# Remove redundant documentation
rm -f IMPLEMENTATION_SUMMARY.md
rm -f QUICKSTART.md  
rm -f INSTALLATION_GUIDE.md

# Remove temporary files
rm -f nextflow_*.out
rm -f report_*.html
rm -f *subject_info.csv

# Remove downloaded images directory
rm -rf downloaded_images/

echo "✓ Removed ADNI-specific and temporary files"
echo "✓ Repository is ready for GitHub"
echo ""
echo "Next steps:"
echo "1. git init"
echo "2. git add ."
echo "3. git commit -m 'Initial commit'"
echo "4. Create GitHub repository"
echo "5. git remote add origin <your-repo-url>"
echo "6. git push -u origin main"
