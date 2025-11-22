#!/usr/bin/env python3
"""
ADNI Data Preparation Script
Converts ADNI-DOD manifest to pipeline-ready format with proper naming

Usage:
    python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv --dicom-dir /path/to/dicoms --output-dir nii
"""

import pandas as pd
import os
import sys
import shutil
import gzip
from pathlib import Path
import argparse
from datetime import datetime


def parse_manifest(manifest_file):
    """Parse ADNI manifest CSV"""
    print(f"Reading manifest: {manifest_file}")
    df = pd.read_csv(manifest_file)
    
    print(f"\nDataset Summary:")
    print(f"  Total scans: {len(df)}")
    print(f"  Unique subjects: {df['Subject'].nunique()}")
    print(f"  Visit types: {df['Visit'].unique()}")
    print(f"  Date range: {df['Acq Date'].min()} to {df['Acq Date'].max()}")
    
    return df


def map_visit_to_session(visit, acq_date, subject_visits):
    """
    Map ADNI visit codes to session numbers
    Handles multiple visits of same type by using acquisition date
    """
    # Visit type mapping
    visit_map = {
        'SCMRI': 'bl',      # Baseline screening
        'M12': 'm12',       # 12 months
        'M24': 'm24',       # 24 months (if exists)
        'TAU': 'tau',       # Tau imaging visit
        'TAU2': 'tau2'      # Second tau visit
    }
    
    # Get base session name
    base_session = visit_map.get(visit, visit.lower())
    
    # If subject has multiple scans on same visit type, add date suffix
    visit_count = subject_visits.get(visit, 0)
    subject_visits[visit] = visit_count + 1
    
    if visit_count > 0:
        # Multiple scans of same visit type - add date or counter
        return f"{base_session}_{visit_count + 1}"
    
    return base_session


def create_bids_filename(row, subject_visits_dict):
    """Create BIDS-compliant filename"""
    subject = row['Subject']
    visit = row['Visit']
    image_id = row['Image Data ID']
    acq_date = row['Acq Date']
    
    # Initialize subject visit tracker if needed
    if subject not in subject_visits_dict:
        subject_visits_dict[subject] = {}
    
    # Map visit to session
    session = map_visit_to_session(visit, acq_date, subject_visits_dict[subject])
    
    # Create BIDS filename
    # Format: sub-{subject}_ses-{session}_T1w.nii.gz
    filename = f"sub-{subject}_ses-{session}_T1w.nii.gz"
    
    return filename, session


def find_nifti_file(dicom_dir, image_id, subject):
    """
    Find the corresponding NIfTI file for an image ID
    ADNI typically names files with image ID or subject/date info
    """
    possible_patterns = [
        f"*{image_id}*.nii*",
        f"*{subject}*{image_id}*.nii*",
        f"{image_id}.nii*",
    ]
    
    dicom_path = Path(dicom_dir)
    
    for pattern in possible_patterns:
        matches = list(dicom_path.rglob(pattern))
        if matches:
            return matches[0]
    
    return None


def organize_dataset(manifest_file, dicom_dir, output_dir, create_links=False):
    """
    Organize ADNI dataset into pipeline-ready format
    
    Args:
        manifest_file: Path to ADNI manifest CSV
        dicom_dir: Directory containing downloaded ADNI NIfTI files
        output_dir: Output directory for organized files
        create_links: If True, create symlinks instead of copying
    """
    # Parse manifest
    df = parse_manifest(manifest_file)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Track visits per subject for naming
    subject_visits_dict = {}
    
    # Track statistics
    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'subjects': set(),
        'sessions_per_subject': {}
    }
    
    print(f"\n{'='*60}")
    print("Processing Files")
    print('='*60)
    
    # Process each scan
    for idx, row in df.iterrows():
        image_id = row['Image Data ID']
        subject = row['Subject']
        visit = row['Visit']
        
        try:
            # Create BIDS filename
            bids_filename, session = create_bids_filename(row, subject_visits_dict)
            output_file = output_path / bids_filename
            
            # Find source NIfTI file
            source_file = find_nifti_file(dicom_dir, image_id, subject)
            
            if source_file is None:
                print(f"  ⚠ SKIP: {image_id} - File not found")
                stats['skipped'] += 1
                continue
            
            # Check if output already exists
            if output_file.exists():
                print(f"  ⚠ EXISTS: {bids_filename}")
                stats['skipped'] += 1
                continue
            
            # Copy or link file
            if create_links:
                output_file.symlink_to(source_file.absolute())
                action = "linked"
            else:
                # Handle compression
                if str(source_file).endswith('.gz'):
                    shutil.copy2(source_file, output_file)
                else:
                    # Compress uncompressed NIfTI
                    with open(source_file, 'rb') as f_in:
                        with gzip.open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                action = "copied"
            
            print(f"  ✓ {action.upper()}: {bids_filename}")
            
            stats['processed'] += 1
            stats['subjects'].add(subject)
            
            # Track sessions per subject
            if subject not in stats['sessions_per_subject']:
                stats['sessions_per_subject'][subject] = []
            stats['sessions_per_subject'][subject].append(session)
            
        except Exception as e:
            print(f"  ✗ ERROR: {image_id} - {e}")
            stats['errors'] += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("Processing Summary")
    print('='*60)
    print(f"Successfully processed: {stats['processed']}")
    print(f"Skipped (not found/exists): {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Unique subjects: {len(stats['subjects'])}")
    
    # Show subjects with multiple sessions (longitudinal)
    longitudinal_subjects = [s for s, sessions in stats['sessions_per_subject'].items() 
                            if len(sessions) > 1]
    print(f"Longitudinal subjects: {len(longitudinal_subjects)}")
    
    if longitudinal_subjects:
        print(f"\nExample longitudinal subjects:")
        for subj in list(longitudinal_subjects)[:5]:
            sessions = stats['sessions_per_subject'][subj]
            print(f"  sub-{subj}: {len(sessions)} sessions ({', '.join(sessions)})")
    
    # Generate file list
    list_file = output_path / "file_list.txt"
    with open(list_file, 'w') as f:
        for file in sorted(output_path.glob("*.nii.gz")):
            f.write(f"{file.name}\n")
    print(f"\nFile list saved to: {list_file}")
    
    return stats


def generate_subject_info(manifest_file, output_file):
    """Generate subject information CSV for reference"""
    df = pd.read_csv(manifest_file)
    
    # Create subject-level summary
    subject_info = df.groupby('Subject').agg({
        'Sex': 'first',
        'Age': 'min',  # Age at first scan
        'Visit': lambda x: list(x),
        'Acq Date': lambda x: list(x),
        'Image Data ID': 'count'
    }).reset_index()
    
    subject_info.columns = ['Subject', 'Sex', 'Baseline_Age', 'Visits', 'Acq_Dates', 'N_Scans']
    
    # Add longitudinal flag
    subject_info['Longitudinal'] = subject_info['N_Scans'] > 1
    
    subject_info.to_csv(output_file, index=False)
    print(f"\nSubject information saved to: {output_file}")
    
    return subject_info


def main():
    parser = argparse.ArgumentParser(
        description='Prepare ADNI data for neuroimaging pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Copy files to pipeline directory
  python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv \\
      --dicom-dir /data/ADNI/downloads \\
      --output-dir nii

  # Create symlinks instead of copying (saves space)
  python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv \\
      --dicom-dir /data/ADNI/downloads \\
      --output-dir nii \\
      --symlinks

  # Generate subject info only
  python prepare_adni_data.py --manifest ADNI-DOD_11_18_2025.csv \\
      --info-only
        """
    )
    
    parser.add_argument('--manifest', required=True,
                       help='Path to ADNI manifest CSV file')
    parser.add_argument('--dicom-dir', 
                       help='Directory containing ADNI NIfTI files')
    parser.add_argument('--output-dir', default='nii',
                       help='Output directory for organized files (default: nii)')
    parser.add_argument('--symlinks', action='store_true',
                       help='Create symlinks instead of copying files')
    parser.add_argument('--info-only', action='store_true',
                       help='Only generate subject info CSV, do not process files')
    
    args = parser.parse_args()
    
    # Check manifest exists
    if not os.path.exists(args.manifest):
        print(f"Error: Manifest file not found: {args.manifest}")
        sys.exit(1)
    
    # Generate subject info
    subject_info_file = args.manifest.replace('.csv', '_subject_info.csv')
    generate_subject_info(args.manifest, subject_info_file)
    
    # If info-only, stop here
    if args.info_only:
        print("\nInfo-only mode: Subject information generated successfully!")
        return
    
    # Check dicom directory
    if not args.dicom_dir:
        print("Error: --dicom-dir is required (unless using --info-only)")
        sys.exit(1)
    
    if not os.path.exists(args.dicom_dir):
        print(f"Error: DICOM directory not found: {args.dicom_dir}")
        sys.exit(1)
    
    # Organize dataset
    stats = organize_dataset(
        manifest_file=args.manifest,
        dicom_dir=args.dicom_dir,
        output_dir=args.output_dir,
        create_links=args.symlinks
    )
    
    print(f"\n{'='*60}")
    print("Next Steps")
    print('='*60)
    print(f"1. Verify files: ls -lh {args.output_dir}/*.nii.gz | head")
    print(f"2. Check naming: cat {args.output_dir}/file_list.txt | head")
    print(f"3. Run pipeline:")
    if stats['sessions_per_subject'] and any(len(s) > 1 for s in stats['sessions_per_subject'].values()):
        print(f"   # Longitudinal processing (you have multi-session subjects)")
        print(f"   sbatch --export=ALL,INPUT_MODE=nii,RUN_LONGITUDINAL=true run_pipeline.sbatch")
    else:
        print(f"   # Cross-sectional processing")
        print(f"   sbatch run_pipeline.sbatch")
    
    print(f"\n✓ Dataset preparation complete!")


if __name__ == '__main__':
    main()



