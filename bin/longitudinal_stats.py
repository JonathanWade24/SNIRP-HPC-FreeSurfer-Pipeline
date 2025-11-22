#!/usr/bin/env python3
"""
Longitudinal Statistics Calculator

Calculates longitudinal changes in cortical thickness and subcortical volumes:
- Slope estimates (rate of change per year)
- Percent change between timepoints
- Statistical significance testing

Author: HPC Neuroimaging Team
Version: 2.0.0
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import argparse
from scipy import stats


def parse_timepoint_info(subject_id: str) -> Tuple[str, Optional[str], Optional[int]]:
    """
    Parse subject ID to extract base subject, session, and timepoint
    
    Args:
        subject_id: Subject identifier (e.g., 'sub-001_ses-01' or 'sub-001_tp1')
        
    Returns:
        Tuple of (base_id, session_id, timepoint_number)
    """
    # Handle session-based naming (sub-XXX_ses-YYY)
    if '_ses-' in subject_id:
        parts = subject_id.split('_ses-')
        base_id = parts[0]
        session_id = f"ses-{parts[1]}"
        # Try to extract numeric timepoint
        try:
            tp_num = int(''.join(filter(str.isdigit, parts[1])))
        except ValueError:
            tp_num = None
        return base_id, session_id, tp_num
    
    # Handle timepoint-based naming (sub-XXX_tpN)
    elif '_tp' in subject_id:
        parts = subject_id.split('_tp')
        base_id = parts[0]
        try:
            tp_num = int(parts[1])
            session_id = f"tp{tp_num}"
        except ValueError:
            tp_num = None
            session_id = f"tp{parts[1]}"
        return base_id, session_id, tp_num
    
    # No timepoint information
    else:
        return subject_id, None, None


def load_longitudinal_stats(long_dirs: str) -> pd.DataFrame:
    """
    Load statistics from longitudinal FreeSurfer outputs
    
    Args:
        long_dirs: Directory containing longitudinal outputs
        
    Returns:
        DataFrame with longitudinal statistics
    """
    print("Loading longitudinal statistics...")
    
    long_path = Path(long_dirs)
    rows = []
    
    # Find all longitudinal output directories
    # Format: subject.long.base_subject
    for subject_dir in long_path.iterdir():
        if not subject_dir.is_dir():
            continue
        
        # Parse directory name
        dir_name = subject_dir.name
        if '.long.' not in dir_name:
            continue
        
        parts = dir_name.split('.long.')
        timepoint_id = parts[0]
        base_id = parts[1]
        
        # Parse timepoint information
        _, session_id, tp_num = parse_timepoint_info(timepoint_id)
        
        # Load statistics from aseg.stats
        aseg_file = subject_dir / 'stats' / 'aseg.stats'
        if aseg_file.exists():
            subcortical = parse_aseg_stats(aseg_file)
            
            for structure, volume in subcortical.items():
                rows.append({
                    'base_subject': base_id,
                    'timepoint_id': timepoint_id,
                    'session': session_id,
                    'timepoint_num': tp_num,
                    'measure_type': 'volume',
                    'structure': structure,
                    'value': volume
                })
        
        # Load cortical thickness from aparc.stats
        for hemi in ['lh', 'rh']:
            aparc_file = subject_dir / 'stats' / f'{hemi}.aparc.stats'
            if aparc_file.exists():
                thickness = parse_aparc_stats(aparc_file)
                
                for region, metrics in thickness.items():
                    rows.append({
                        'base_subject': base_id,
                        'timepoint_id': timepoint_id,
                        'session': session_id,
                        'timepoint_num': tp_num,
                        'measure_type': 'thickness',
                        'structure': f'{hemi}_{region}',
                        'value': metrics.get('thickness_avg_mm', None)
                    })
    
    df = pd.DataFrame(rows)
    print(f"  Loaded {len(df)} measurements from {df['base_subject'].nunique()} subjects")
    
    return df


def parse_aseg_stats(aseg_file: Path) -> Dict[str, float]:
    """Parse subcortical volumes from aseg.stats"""
    volumes = {}
    
    with open(aseg_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            parts = line.split()
            if len(parts) >= 5:
                try:
                    structure = parts[4]
                    volume = float(parts[3])
                    volumes[structure] = volume
                except (ValueError, IndexError):
                    continue
    
    return volumes


def parse_aparc_stats(aparc_file: Path) -> Dict[str, Dict]:
    """Parse cortical statistics from aparc.stats"""
    stats = {}
    
    with open(aparc_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            parts = line.split()
            if len(parts) >= 5:
                try:
                    region = parts[0]
                    surf_area = float(parts[2])
                    gray_vol = float(parts[3])
                    thick_avg = float(parts[4])
                    
                    stats[region] = {
                        'surface_area_mm2': surf_area,
                        'gray_volume_mm3': gray_vol,
                        'thickness_avg_mm': thick_avg
                    }
                except (ValueError, IndexError):
                    continue
    
    return stats


def calculate_slopes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate slope estimates (rate of change) for each subject and structure
    
    Args:
        df: DataFrame with longitudinal measurements
        
    Returns:
        DataFrame with slope estimates
    """
    print("Calculating slope estimates...")
    
    slope_rows = []
    
    # Group by base subject, measure type, and structure
    for (base_subj, measure_type, structure), group in df.groupby(['base_subject', 'measure_type', 'structure']):
        # Need at least 2 timepoints
        if len(group) < 2:
            continue
        
        # Sort by timepoint number
        group = group.sort_values('timepoint_num')
        
        # Get timepoints and values
        timepoints = group['timepoint_num'].values
        values = group['value'].values
        
        # Remove any NaN values
        mask = ~np.isnan(values)
        timepoints = timepoints[mask]
        values = values[mask]
        
        if len(timepoints) < 2:
            continue
        
        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(timepoints, values)
        
        # Calculate percent change
        baseline_value = values[0]
        final_value = values[-1]
        percent_change = ((final_value - baseline_value) / baseline_value) * 100 if baseline_value != 0 else None
        
        # Calculate absolute change
        absolute_change = final_value - baseline_value
        
        slope_rows.append({
            'base_subject': base_subj,
            'measure_type': measure_type,
            'structure': structure,
            'n_timepoints': len(timepoints),
            'baseline_value': baseline_value,
            'final_value': final_value,
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'std_error': std_err,
            'absolute_change': absolute_change,
            'percent_change': percent_change,
            'timepoint_span': timepoints[-1] - timepoints[0]
        })
    
    slope_df = pd.DataFrame(slope_rows)
    print(f"  Calculated slopes for {len(slope_df)} structure-subject combinations")
    
    return slope_df


def calculate_percent_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate percent change between consecutive timepoints
    
    Args:
        df: DataFrame with longitudinal measurements
        
    Returns:
        DataFrame with percent changes
    """
    print("Calculating percent changes...")
    
    change_rows = []
    
    # Group by base subject, measure type, and structure
    for (base_subj, measure_type, structure), group in df.groupby(['base_subject', 'measure_type', 'structure']):
        # Sort by timepoint number
        group = group.sort_values('timepoint_num')
        
        # Calculate changes between consecutive timepoints
        for i in range(len(group) - 1):
            row1 = group.iloc[i]
            row2 = group.iloc[i + 1]
            
            value1 = row1['value']
            value2 = row2['value']
            
            if pd.notna(value1) and pd.notna(value2) and value1 != 0:
                percent_change = ((value2 - value1) / value1) * 100
                absolute_change = value2 - value1
                
                change_rows.append({
                    'base_subject': base_subj,
                    'measure_type': measure_type,
                    'structure': structure,
                    'timepoint_from': row1['timepoint_id'],
                    'timepoint_to': row2['timepoint_id'],
                    'tp_num_from': row1['timepoint_num'],
                    'tp_num_to': row2['timepoint_num'],
                    'value_from': value1,
                    'value_to': value2,
                    'absolute_change': absolute_change,
                    'percent_change': percent_change
                })
    
    change_df = pd.DataFrame(change_rows)
    print(f"  Calculated {len(change_df)} timepoint-to-timepoint changes")
    
    return change_df


def calculate_longitudinal_stats(long_dirs: str, output_slopes: str, output_percent: str):
    """
    Calculate all longitudinal statistics
    
    Args:
        long_dirs: Directory containing longitudinal outputs
        output_slopes: Output file for slope estimates
        output_percent: Output file for percent changes
    """
    print("\n" + "="*60)
    print("Longitudinal Statistics Calculation")
    print("="*60 + "\n")
    
    # Load longitudinal data
    df = load_longitudinal_stats(long_dirs)
    
    if df.empty:
        print("Warning: No longitudinal data found")
        return
    
    # Calculate slopes
    slopes_df = calculate_slopes(df)
    if not slopes_df.empty:
        slopes_df.to_csv(output_slopes, index=False)
        print(f"\nSaved slope estimates to: {output_slopes}")
    
    # Calculate percent changes
    percent_df = calculate_percent_change(df)
    if not percent_df.empty:
        percent_df.to_csv(output_percent, index=False)
        print(f"Saved percent changes to: {output_percent}")
    
    # Print summary statistics
    if not slopes_df.empty:
        print("\n" + "-"*60)
        print("Summary Statistics")
        print("-"*60)
        print(f"Subjects with longitudinal data: {slopes_df['base_subject'].nunique()}")
        print(f"Structures analyzed: {slopes_df['structure'].nunique()}")
        print(f"Significant changes (p < 0.05): {(slopes_df['p_value'] < 0.05).sum()}")
        print(f"Mean absolute R²: {slopes_df['r_squared'].mean():.3f}")
    
    print("\n" + "="*60)
    print("Longitudinal statistics calculation completed")
    print("="*60 + "\n")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Calculate longitudinal statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate longitudinal statistics
  python longitudinal_stats.py --long-dirs long_outputs \\
      --output-slopes longitudinal_slope_estimates.csv \\
      --output-percent longitudinal_percent_change.csv
        """
    )
    
    parser.add_argument('--long-dirs', required=True,
                       help='Directory containing longitudinal outputs')
    parser.add_argument('--output-slopes', required=True,
                       help='Output file for slope estimates')
    parser.add_argument('--output-percent', required=True,
                       help='Output file for percent changes')
    
    args = parser.parse_args()
    
    calculate_longitudinal_stats(
        long_dirs=args.long_dirs,
        output_slopes=args.output_slopes,
        output_percent=args.output_percent
    )


if __name__ == '__main__':
    main()

