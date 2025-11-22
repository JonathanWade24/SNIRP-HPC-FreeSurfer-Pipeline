#!/usr/bin/env python3
"""
Statistics Aggregation Script

Aggregates statistics across all subjects to create summary tables:
- cortical_thickness.csv
- subcortical_volumes.csv
- aparc_dkt.csv

Author: HPC Neuroimaging Team
Version: 2.0.0
"""

import os
import sys
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import argparse


def load_atlas_json(json_file: Path) -> Dict:
    """Load atlas statistics from JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def aggregate_cortical_thickness(atlas_jsons: List[Path], output_file: str):
    """
    Aggregate cortical thickness measurements across subjects
    
    Args:
        atlas_jsons: List of paths to atlas JSON files
        output_file: Output CSV file path
    """
    print("Aggregating cortical thickness...")
    
    rows = []
    
    for json_file in atlas_jsons:
        data = load_atlas_json(json_file)
        subject_id = data.get('subject_id', 'unknown')
        
        # Extract thickness from Desikan-Killiany atlas
        for region, metrics in data.get('desikan_killiany', {}).items():
            if isinstance(metrics, dict) and 'thickness_avg_mm' in metrics:
                rows.append({
                    'subject_id': subject_id,
                    'atlas': 'desikan_killiany',
                    'region': region,
                    'thickness_mm': metrics['thickness_avg_mm'],
                    'thickness_std_mm': metrics.get('thickness_std_mm', None),
                    'surface_area_mm2': metrics.get('surface_area_mm2', None),
                    'gray_volume_mm3': metrics.get('gray_volume_mm3', None)
                })
        
        # Extract thickness from Destrieux atlas
        for region, metrics in data.get('destrieux', {}).items():
            if isinstance(metrics, dict) and 'thickness_avg_mm' in metrics:
                rows.append({
                    'subject_id': subject_id,
                    'atlas': 'destrieux',
                    'region': region,
                    'thickness_mm': metrics['thickness_avg_mm'],
                    'thickness_std_mm': metrics.get('thickness_std_mm', None),
                    'surface_area_mm2': metrics.get('surface_area_mm2', None),
                    'gray_volume_mm3': metrics.get('gray_volume_mm3', None)
                })
        
        # Extract thickness from DKT atlas
        for region, metrics in data.get('dkt', {}).items():
            if isinstance(metrics, dict) and 'thickness_avg_mm' in metrics:
                rows.append({
                    'subject_id': subject_id,
                    'atlas': 'dkt',
                    'region': region,
                    'thickness_mm': metrics['thickness_avg_mm'],
                    'thickness_std_mm': metrics.get('thickness_std_mm', None),
                    'surface_area_mm2': metrics.get('surface_area_mm2', None),
                    'gray_volume_mm3': metrics.get('gray_volume_mm3', None)
                })
    
    # Create DataFrame and save
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"  Saved cortical thickness to: {output_file}")
        print(f"  Total measurements: {len(df)}")
    else:
        print("  Warning: No cortical thickness data found")


def aggregate_subcortical_volumes(atlas_jsons: List[Path], output_file: str):
    """
    Aggregate subcortical volume measurements across subjects
    
    Args:
        atlas_jsons: List of paths to atlas JSON files
        output_file: Output CSV file path
    """
    print("Aggregating subcortical volumes...")
    
    rows = []
    
    for json_file in atlas_jsons:
        data = load_atlas_json(json_file)
        subject_id = data.get('subject_id', 'unknown')
        
        # Extract subcortical volumes
        for structure, metrics in data.get('subcortical', {}).items():
            if isinstance(metrics, dict) and 'volume_mm3' in metrics:
                rows.append({
                    'subject_id': subject_id,
                    'structure': structure,
                    'volume_mm3': metrics['volume_mm3']
                })
    
    # Create DataFrame and save
    if rows:
        df = pd.DataFrame(rows)
        
        # Pivot to wide format (subjects as rows, structures as columns)
        df_wide = df.pivot(index='subject_id', columns='structure', values='volume_mm3')
        df_wide.reset_index(inplace=True)
        
        df_wide.to_csv(output_file, index=False)
        print(f"  Saved subcortical volumes to: {output_file}")
        print(f"  Subjects: {len(df_wide)}, Structures: {len(df_wide.columns) - 1}")
    else:
        print("  Warning: No subcortical volume data found")


def aggregate_aparc_dkt(atlas_jsons: List[Path], output_file: str):
    """
    Aggregate DKT atlas statistics across subjects
    
    Args:
        atlas_jsons: List of paths to atlas JSON files
        output_file: Output CSV file path
    """
    print("Aggregating DKT atlas statistics...")
    
    rows = []
    
    for json_file in atlas_jsons:
        data = load_atlas_json(json_file)
        subject_id = data.get('subject_id', 'unknown')
        
        # Extract DKT statistics
        for region, metrics in data.get('dkt', {}).items():
            if isinstance(metrics, dict):
                row = {
                    'subject_id': subject_id,
                    'region': region
                }
                row.update(metrics)
                rows.append(row)
    
    # Create DataFrame and save
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"  Saved DKT atlas statistics to: {output_file}")
        print(f"  Total regions: {len(df)}")
    else:
        print("  Warning: No DKT atlas data found")


def aggregate_summary_stats(atlas_jsons: List[Path], output_file: str):
    """
    Aggregate summary statistics across subjects
    
    Args:
        atlas_jsons: List of paths to atlas JSON files
        output_file: Output CSV file path
    """
    print("Aggregating summary statistics...")
    
    rows = []
    
    for json_file in atlas_jsons:
        data = load_atlas_json(json_file)
        subject_id = data.get('subject_id', 'unknown')
        
        # Extract summary statistics
        summary = data.get('summary', {})
        if summary:
            row = {'subject_id': subject_id}
            row.update(summary)
            rows.append(row)
    
    # Create DataFrame and save
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"  Saved summary statistics to: {output_file}")
        print(f"  Subjects: {len(df)}")
    else:
        print("  Warning: No summary statistics found")


def aggregate_all_stats(atlas_json_dir: str, subject_dirs: str, 
                       output_dir: str, qc_dir: Optional[str] = None):
    """
    Aggregate all statistics across subjects
    
    Args:
        atlas_json_dir: Directory containing atlas JSON files
        subject_dirs: Directory containing subject FreeSurfer outputs
        output_dir: Output directory for aggregated statistics
        qc_dir: Optional QC directory for quality metrics
    """
    print("\n" + "="*60)
    print("Statistics Aggregation")
    print("="*60 + "\n")
    
    # Find all atlas JSON files
    atlas_json_path = Path(atlas_json_dir)
    atlas_jsons = sorted(atlas_json_path.glob('*_atlases.json'))
    
    if not atlas_jsons:
        print(f"Error: No atlas JSON files found in {atlas_json_dir}")
        sys.exit(1)
    
    print(f"Found {len(atlas_jsons)} subjects to aggregate\n")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Aggregate different statistics
    aggregate_cortical_thickness(atlas_jsons, str(output_path / 'cortical_thickness.csv'))
    aggregate_subcortical_volumes(atlas_jsons, str(output_path / 'subcortical_volumes.csv'))
    aggregate_aparc_dkt(atlas_jsons, str(output_path / 'aparc_dkt.csv'))
    aggregate_summary_stats(atlas_jsons, str(output_path / 'summary_stats.csv'))
    
    print("\n" + "="*60)
    print("Statistics aggregation completed")
    print("="*60 + "\n")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Aggregate statistics across subjects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate statistics from atlas JSON files
  python aggregate_stats.py --atlas-json-dir stats/atlases --output-dir stats
  
  # Include subject directories for additional processing
  python aggregate_stats.py --atlas-json-dir stats/atlases \\
      --subject-dirs fs_outputs --output-dir stats
        """
    )
    
    parser.add_argument('--atlas-json-dir', required=True,
                       help='Directory containing atlas JSON files')
    parser.add_argument('--subject-dirs', default='.',
                       help='Directory containing subject FreeSurfer outputs')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for aggregated statistics')
    parser.add_argument('--qc-dir', default=None,
                       help='Optional QC directory for quality metrics')
    
    args = parser.parse_args()
    
    aggregate_all_stats(
        atlas_json_dir=args.atlas_json_dir,
        subject_dirs=args.subject_dirs,
        output_dir=args.output_dir,
        qc_dir=args.qc_dir
    )


if __name__ == '__main__':
    main()

