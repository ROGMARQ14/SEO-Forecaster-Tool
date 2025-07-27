#!/usr/bin/env python3
"""Debug script to check column names in sample data."""

import pandas as pd
import os

def check_columns():
    """Check actual column names in sample files."""
    
    # Check GSC data
    gsc_path = 'examples/sample_gsc_data.csv'
    if os.path.exists(gsc_path):
        df = pd.read_csv(gsc_path)
        print("=== GSC Data ===")
        print(f"Columns: {list(df.columns)}")
        print(f"First row: {df.iloc[0].to_dict()}")
        print()
    
    # Check SEMrush data
    semrush_path = 'examples/sample_semrush_data.csv'
    if os.path.exists(semrush_path):
        df = pd.read_csv(semrush_path)
        print("=== SEMrush Data ===")
        print(f"Columns: {list(df.columns)}")
        print(f"First row: {df.iloc[0].to_dict()}")
        print()

if __name__ == "__main__":
    check_columns()
