#!/usr/bin/env python3
"""
QC Metrics Aggregator

Aggregates MRIQC quality control metrics across subjects:
- Parses MRIQC JSON outputs
- Creates summary CSV with key metrics
- Flags outliers based on thresholds

Author: HPC Neuroimaging Team
Version: 2.0.0
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import argparse


# QC metric thresholds (based on MRIQC recommendations)
QC_THRESHOLDS = {
    'cnr': 2.0,                    # Contrast-to-noise ratio (min)
    'snr_total': 10.0,             # Signal-to-noise ratio (min)
    'fber': 1000.0,                # Foreground-background energy ratio (min)
    'efc': 0.7,                    # Entropy focus criterion (max)
    'qi_2': 0.0,                   # Quality index 2 (max)
    'cjv': 0.5,                    # Coefficient of joint variation (max)
    'wm2max': 0.5,                 # White matter to max intensity ratio (max)
}


def load_mriqc_json(json_file: Path) -> Dict:
    """Load MRIQC JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def extract_key_metrics(data: Dict) -> Dict:
    """
    Extract key QC metrics from MRIQC data
    
    Args:
        data: MRIQC JSON data
        
    Returns:
        Dictionary of key metrics
    """
    metrics = {
        'subject_id': data.get('bids_meta', {}).get('subject', 'unknown'),
        'session': data.get('bids_meta', {}).get('session', None),
    }
    
    # Image quality metrics
    metrics['cnr'] = data.get('cnr', None)
    metrics['snr_total'] = data.get('snr_total', None)
    metrics['snr_gm'] = data.get('snr_gm', None)
    metrics['snr_wm'] = data.get('snr_wm', None)
    metrics['snr_csf'] = data.get('snr_csf', None)
    
    # Noise and artifact metrics
    metrics['fber'] = data.get('fber', None)
    metrics['efc'] = data.get('efc', None)
    metrics['qi_1'] = data.get('qi_1', None)
    metrics['qi_2'] = data.get('qi_2', None)
    
    # Tissue contrast metrics
    metrics['cjv'] = data.get('cjv', None)
    metrics['wm2max'] = data.get('wm2max', None)
    
    # Image homogeneity
    metrics['inu_range'] = data.get('inu_range', None)
    metrics['inu_med'] = data.get('inu_med', None)
    
    # Summary statistics
    metrics['summary_mean'] = data.get('summary', {}).get('mean', None)
    metrics['summary_std'] = data.get('summary', {}).get('std', None)
    
    # Image dimensions
    spacing = data.get('spacing', {})
    if isinstance(spacing, dict):
        metrics['voxel_size_x'] = spacing.get('x', None)
        metrics['voxel_size_y'] = spacing.get('y', None)
        metrics['voxel_size_z'] = spacing.get('z', None)
    
    # Provenance
    metrics['mriqc_version'] = data.get('provenance', {}).get('version', None)
    
    return metrics


def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag outliers based on QC thresholds
    
    Args:
        df: DataFrame with QC metrics
        
    Returns:
        DataFrame with outlier flags
    """
    print("Flagging outliers...")
    
    # Initialize outlier columns
    df['outlier_cnr'] = False
    df['outlier_snr'] = False
    df['outlier_fber'] = False
    df['outlier_efc'] = False
    df['outlier_qi2'] = False
    df['outlier_cjv'] = False
    df['outlier_wm2max'] = False
    
    # Flag based on thresholds
    if 'cnr' in df.columns:
        df['outlier_cnr'] = df['cnr'] < QC_THRESHOLDS['cnr']
    
    if 'snr_total' in df.columns:
        df['outlier_snr'] = df['snr_total'] < QC_THRESHOLDS['snr_total']
    
    if 'fber' in df.columns:
        df['outlier_fber'] = df['fber'] < QC_THRESHOLDS['fber']
    
    if 'efc' in df.columns:
        df['outlier_efc'] = df['efc'] > QC_THRESHOLDS['efc']
    
    if 'qi_2' in df.columns:
        df['outlier_qi2'] = df['qi_2'] > QC_THRESHOLDS['qi_2']
    
    if 'cjv' in df.columns:
        df['outlier_cjv'] = df['cjv'] > QC_THRESHOLDS['cjv']
    
    if 'wm2max' in df.columns:
        df['outlier_wm2max'] = df['wm2max'] > QC_THRESHOLDS['wm2max']
    
    # Overall outlier flag (any metric flagged)
    outlier_cols = [col for col in df.columns if col.startswith('outlier_')]
    df['outlier_any'] = df[outlier_cols].any(axis=1)
    
    # Count number of outlier flags
    df['outlier_count'] = df[outlier_cols[:-1]].sum(axis=1)  # Exclude 'outlier_any'
    
    n_outliers = df['outlier_any'].sum()
    print(f"  Flagged {n_outliers} subjects with outlier metrics")
    
    return df


def calculate_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate z-scores for key metrics
    
    Args:
        df: DataFrame with QC metrics
        
    Returns:
        DataFrame with z-scores
    """
    print("Calculating z-scores...")
    
    # Metrics to calculate z-scores for
    metrics_to_zscore = ['cnr', 'snr_total', 'fber', 'efc', 'qi_2', 'cjv', 'wm2max']
    
    for metric in metrics_to_zscore:
        if metric in df.columns:
            mean = df[metric].mean()
            std = df[metric].std()
            
            if std > 0:
                df[f'{metric}_zscore'] = (df[metric] - mean) / std
            else:
                df[f'{metric}_zscore'] = 0
    
    return df


def aggregate_qc_metrics(qc_json_dir: str, output_csv: str, output_outliers: str):
    """
    Aggregate QC metrics from MRIQC outputs
    
    Args:
        qc_json_dir: Directory containing MRIQC JSON files
        output_csv: Output CSV file path
        output_outliers: Output file for outlier list
    """
    print("\n" + "="*60)
    print("QC Metrics Aggregation")
    print("="*60 + "\n")
    
    # Find all MRIQC JSON files
    qc_path = Path(qc_json_dir)
    json_files = sorted(qc_path.glob('sub-*.json'))
    
    if not json_files:
        print(f"Warning: No MRIQC JSON files found in {qc_json_dir}")
        # Create empty files
        pd.DataFrame().to_csv(output_csv, index=False)
        with open(output_outliers, 'w') as f:
            f.write("No MRIQC data available\n")
        return
    
    print(f"Found {len(json_files)} MRIQC JSON files\n")
    
    # Extract metrics from each file
    rows = []
    for json_file in json_files:
        try:
            data = load_mriqc_json(json_file)
            metrics = extract_key_metrics(data)
            rows.append(metrics)
        except Exception as e:
            print(f"  Warning: Failed to parse {json_file.name}: {e}")
            continue
    
    if not rows:
        print("Error: No valid MRIQC data found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    print(f"Extracted metrics from {len(df)} subjects\n")
    
    # Flag outliers
    df = flag_outliers(df)
    
    # Calculate z-scores
    df = calculate_z_scores(df)
    
    # Save summary CSV
    df.to_csv(output_csv, index=False)
    print(f"\nSaved QC summary to: {output_csv}")
    
    # Save outlier list
    outliers = df[df['outlier_any'] == True]
    with open(output_outliers, 'w') as f:
        f.write("QC Outliers Report\n")
        f.write("="*60 + "\n\n")
        
        if len(outliers) > 0:
            f.write(f"Total outliers: {len(outliers)} / {len(df)} subjects\n\n")
            
            for _, row in outliers.iterrows():
                f.write(f"Subject: {row['subject_id']}\n")
                if pd.notna(row.get('session')):
                    f.write(f"  Session: {row['session']}\n")
                f.write(f"  Outlier flags: {int(row['outlier_count'])}\n")
                
                # List specific outlier metrics
                outlier_cols = [col for col in df.columns if col.startswith('outlier_') and col != 'outlier_any' and col != 'outlier_count']
                flagged = [col.replace('outlier_', '') for col in outlier_cols if row[col]]
                if flagged:
                    f.write(f"  Flagged metrics: {', '.join(flagged)}\n")
                
                f.write("\n")
        else:
            f.write("No outliers detected!\n")
    
    print(f"Saved outlier report to: {output_outliers}")
    
    # Print summary statistics
    print("\n" + "-"*60)
    print("Summary Statistics")
    print("-"*60)
    print(f"Total subjects: {len(df)}")
    print(f"Subjects with outliers: {len(outliers)}")
    
    if 'cnr' in df.columns:
        print(f"Mean CNR: {df['cnr'].mean():.2f} ± {df['cnr'].std():.2f}")
    if 'snr_total' in df.columns:
        print(f"Mean SNR: {df['snr_total'].mean():.2f} ± {df['snr_total'].std():.2f}")
    
    print("\n" + "="*60)
    print("QC metrics aggregation completed")
    print("="*60 + "\n")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Aggregate MRIQC quality control metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate QC metrics from MRIQC outputs
  python qc_aggregator.py --qc-json-dir qc/mriqc \\
      --output-csv qc_summary.csv \\
      --output-outliers qc_outliers.txt
        """
    )
    
    parser.add_argument('--qc-json-dir', required=True,
                       help='Directory containing MRIQC JSON files')
    parser.add_argument('--output-csv', required=True,
                       help='Output CSV file for QC summary')
    parser.add_argument('--output-outliers', required=True,
                       help='Output file for outlier report')
    
    args = parser.parse_args()
    
    aggregate_qc_metrics(
        qc_json_dir=args.qc_json_dir,
        output_csv=args.output_csv,
        output_outliers=args.output_outliers
    )


if __name__ == '__main__':
    main()

