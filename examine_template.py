#!/usr/bin/env python3
"""
Script to examine the Excel template structure
"""
import pandas as pd
from pathlib import Path

def examine_template():
    template_path = Path("tablecensus/templates/dictionary_template.xlsx")
    
    if not template_path.exists():
        print(f"Template not found at {template_path}")
        return
    
    # Read all sheets
    excel_file = pd.ExcelFile(template_path)
    print(f"Excel file has {len(excel_file.sheet_names)} sheets:")
    print(f"Sheet names: {excel_file.sheet_names}")
    print()
    
    for sheet_name in excel_file.sheet_names:
        print(f"=== Sheet: {sheet_name} ===")
        try:
            df = pd.read_excel(template_path, sheet_name=sheet_name)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First few rows:")
            print(df.head())
            print()
            
            # Show data types
            print("Data types:")
            print(df.dtypes)
            print()
            
            # Check for any non-null data that might be examples
            print("Non-null values per column:")
            print(df.count())
            print()
            
            # Show unique values for columns with few unique values
            for col in df.columns:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 10 and len(unique_vals) > 0:
                    print(f"Unique values in '{col}': {unique_vals}")
            print()
            
        except Exception as e:
            print(f"Error reading sheet {sheet_name}: {e}")
        
        print("-" * 50)
        print()

if __name__ == "__main__":
    examine_template()