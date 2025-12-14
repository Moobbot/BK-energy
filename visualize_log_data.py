
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import argparse
import numpy as np

def process_file(filepath, output_base_dir):
    try:
        # Attempt to read CSV
        df = pd.read_csv(filepath, on_bad_lines='skip', low_memory=False)
        
        # Clean up column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Identify timestamp column
        time_cols = [c for c in df.columns if c.lower() in ['timestamp', 'times', 'datetime', 'time', 'date']]
        
        if not time_cols:
            print(f"Skipping {filepath}: No timestamp column found.")
            return

        time_col = time_cols[0]
        
        # Parse datetime
        try:
            df[time_col] = pd.to_datetime(df[time_col], dayfirst=True, errors='coerce')
        except Exception as e:
            print(f"Error parsing time for {filepath}: {e}")
            return
            
        # Drop rows with invalid time
        df = df.dropna(subset=[time_col])
        
        if df.empty:
            print(f"Skipping {filepath}: Empty after time parsing.")
            return

        # Sort by time
        df = df.sort_values(by=time_col)
        
        # Identify numeric columns for plotting
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            print(f"Skipping {filepath}: No numeric data found.")
            return
            
        valid_cols = []
        for col in numeric_df.columns:
            if col == time_col: continue
            if numeric_df[col].isna().all(): continue
            valid_cols.append(col)
            
        if not valid_cols:
             print(f"Skipping {filepath}: No valid numeric columns to plot.")
             return

        # Create output directory
        # Determine relative path from 'datasets/log' to maintain structure
        try:
            rel_path = os.path.relpath(filepath, start='datasets/log')
        except ValueError:
             # Fallback if paths are incompatible or outside expected layout
            rel_path = os.path.basename(filepath)

        output_dir = os.path.join(output_base_dir, os.path.dirname(rel_path))
        os.makedirs(output_dir, exist_ok=True)
        
        base_filename = os.path.splitext(os.path.basename(filepath))[0]

        # 1. Generate Individual Plots
        for col in valid_cols:
            plt.figure(figsize=(12, 6))
            plt.plot(df[time_col], numeric_df[col], label=col)
            plt.title(f'{base_filename} - {col}')
            plt.xlabel('Time')
            plt.ylabel(col)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            
            safe_col_name = "".join([c if c.isalnum() else "_" for c in col])
            save_path = os.path.join(output_dir, f'{base_filename}_{safe_col_name}.png')
            plt.savefig(save_path)
            plt.close()

        # 2. Generate Combined Plot
        num_plots = len(valid_cols)
        if num_plots > 0:
            fig, axes = plt.subplots(nrows=num_plots, ncols=1, figsize=(15, 3 * num_plots), sharex=True)
            
            if num_plots == 1:
                axes = [axes]
            
            for i, col in enumerate(valid_cols):
                axes[i].plot(df[time_col], numeric_df[col], label=col)
                axes[i].set_ylabel(col)
                axes[i].legend(loc='upper right')
                axes[i].grid(True)
                
            axes[-1].set_xlabel('Time')
            fig.suptitle(f'{base_filename} - All Signals', fontsize=16)
            plt.tight_layout(rect=[0, 0.03, 1, 0.97]) # adjust for suptitle
            
            save_path_combined = os.path.join(output_dir, f'{base_filename}_combined.png')
            plt.savefig(save_path_combined)
            plt.close()
            
        print(f"Processed {filepath} -> {output_dir}")

    except Exception as e:
        print(f"Failed to process {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Visualize Log Data')
    parser.add_argument('--folder', type=str, default='datasets/log', help='Path to the bucket/folder to process')
    args = parser.parse_args()

    input_root = args.folder
    output_root = 'visualizations/log'
    
    if not os.path.exists(input_root):
        print(f"Input path does not exist: {input_root}")
        return

    # If it's single file
    if os.path.isfile(input_root) and input_root.endswith('.csv'):
         process_file(input_root, output_root)
         return

    # Find all CSV files recursively in the specified folder
    csv_files = glob.glob(os.path.join(input_root, '**', '*.csv'), recursive=True)
    
    if not csv_files:
        print(f"No CSV files found in {input_root}")
        return

    print(f"Found {len(csv_files)} CSV files in {input_root}. Starting processing...")
    
    for csv_file in csv_files:
        process_file(csv_file, output_root)

if __name__ == "__main__":
    main()
