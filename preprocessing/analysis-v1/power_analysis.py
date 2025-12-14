"""
Power Output Analysis: Environmental vs Subjective Factors

This script analyzes the influence of:
1. Environmental factors (objective): Irradiance, Temperature, Humidity
2. Subjective factors: PV panel condition (insulation resistance, leakage) 
   and DC-AC inverter performance (switching cycles, errors, warnings)

on power output from the photovoltaic system.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class PowerDataAnalyzer:
    """Main class for analyzing power output and its influencing factors"""
    
    def __init__(self, csv_path):
        """Initialize with CSV file path"""
        self.csv_path = csv_path
        self.data = {}
        self.processed_data = None
        
    def load_data(self):
        """Load and parse the CSV file with multiple log types"""
        print("Loading data from CSV file...")
        
        # Read the CSV file without header
        df = pd.read_csv(self.csv_path, header=None, low_memory=False)
        
        # First row is the general header
        # Subsequent rows have: Log Type, System, TimeStamp, then column names
        
        # Identify different log types
        log_types = df[df[0].notna()][0].unique()
        # Remove the first header row
        log_types = [lt for lt in log_types if str(lt) != 'Log Type']
        print(f"Found {len(log_types)} log types: {log_types}")
        
        # Parse each log type into separate dataframes
        for log_type in log_types:
            if pd.notna(log_type):
                # Get all rows for this log type
                log_rows = df[df[0] == log_type].copy()
                
                if len(log_rows) > 0:
                    # First row contains column headers starting from column 3
                    header_row = log_rows.iloc[0]
                    
                    # Extract column names from row (columns 3 onwards)
                    col_names = ['Log Type', 'System', 'TimeStamp']
                    for i in range(3, len(header_row)):
                        col_name = header_row.iloc[i]
                        if pd.notna(col_name) and str(col_name).strip():
                            col_names.append(str(col_name).strip())
                        else:
                            break
                    
                    # Get data rows (skip the header row)
                    data_rows = log_rows.iloc[1:].copy()
                    
                    # Create dataframe with proper column names
                    if len(data_rows) > 0 and len(col_names) > 3:
                        # Use only available columns
                        num_cols = min(len(col_names), len(data_rows.columns))
                        log_data = data_rows.iloc[:, :num_cols].copy()
                        log_data.columns = col_names[:num_cols]
                        
                        # Parse timestamp
                        if 'TimeStamp' in log_data.columns:
                            log_data['TimeStamp'] = pd.to_datetime(
                                log_data['TimeStamp'], 
                                format='%d/%m/%Y %H:%M', 
                                errors='coerce'
                            )
                        
                        # Remove rows with invalid timestamps
                        log_data = log_data[log_data['TimeStamp'].notna()].copy()
                        
                        # Convert numeric columns
                        for col in log_data.columns:
                            if col not in ['Log Type', 'System', 'TimeStamp']:
                                log_data[col] = pd.to_numeric(log_data[col], errors='coerce')
                        
                        if len(log_data) > 0:
                            self.data[log_type] = log_data
                            print(f"  - {log_type}: {len(log_data)} records, {len(col_names)-3} data columns")
        
        print(f"\nData loaded successfully!")
        return self.data
    
    def extract_environmental_factors(self):
        """Extract environmental (objective) factors"""
        print("\n=== Extracting Environmental Factors ===")
        
        env_data = {}
        
        # 1. Irradiance from APS Stat 10s
        if 'APS Stat 10s' in self.data:
            aps_stat = self.data['APS Stat 10s'].copy()
            # Find irradiance column (may have different encoding)
            irr_cols = [col for col in aps_stat.columns if 'Irr' in str(col) or 'irr' in str(col).lower()]
            if irr_cols:
                irr_col = irr_cols[0]
                env_data['irradiance'] = aps_stat[['TimeStamp', irr_col]].copy()
                env_data['irradiance'].rename(columns={irr_col: 'Irradiance_W_m2'}, inplace=True)
                env_data['irradiance'] = env_data['irradiance'].dropna()
                print(f"  - Irradiance: {len(env_data['irradiance'])} records")
        
        # 2. Temperature from APS Stat 60s
        if 'APS Stat 60s' in self.data:
            aps_stat_60 = self.data['APS Stat 60s'].copy()
            # Find temperature columns
            temp_cols = [col for col in aps_stat_60.columns if 'Tamb' in str(col) or 'Tpan' in str(col) or 'Ttrans' in str(col)]
            
            if temp_cols:
                temp_data = aps_stat_60[['TimeStamp'] + temp_cols].copy()
                # Clean column names
                new_cols = ['TimeStamp']
                for col in temp_cols:
                    new_name = str(col).replace('°C', 'C').replace('/', '_').replace('(', '').replace(')', '')
                    new_cols.append(new_name)
                temp_data.columns = new_cols
                env_data['temperature'] = temp_data.dropna()
                print(f"  - Temperature: {len(env_data['temperature'])} records")
        
        # 3. Humidity from APU Stat 60s
        if 'APU Stat 60s' in self.data:
            apu_stat_60 = self.data['APU Stat 60s'].copy()
            # Find humidity column
            hum_cols = [col for col in apu_stat_60.columns if 'Hum' in str(col) or 'hum' in str(col).lower()]
            if hum_cols:
                hum_col = hum_cols[0]
                env_data['humidity'] = apu_stat_60[['TimeStamp', hum_col]].copy()
                env_data['humidity'].rename(columns={hum_col: 'Humidity_RH'}, inplace=True)
                env_data['humidity'] = env_data['humidity'].dropna()
                print(f"  - Humidity: {len(env_data['humidity'])} records")
        
        return env_data
    
    def extract_subjective_factors(self):
        """Extract subjective factors (PV panels and inverters)"""
        print("\n=== Extracting Subjective Factors ===")
        
        subj_data = {}
        
        # 1. PV Panel Condition from APS Stat 60s
        if 'APS Stat 60s' in self.data:
            aps_stat_60 = self.data['APS Stat 60s'].copy()
            
            # Insulation resistance (indicates panel condition)
            iso_cols = [col for col in aps_stat_60.columns if 'Riso' in str(col)]
            # Leakage capacitance (indicates panel condition)
            leak_cols = [col for col in aps_stat_60.columns if 'Cleak' in str(col)]
            
            pv_data = aps_stat_60[['TimeStamp']].copy()
            if iso_cols:
                for col in iso_cols:
                    pv_data[col] = aps_stat_60[col]
            if leak_cols:
                for col in leak_cols:
                    pv_data[col] = aps_stat_60[col]
            
            if len(pv_data.columns) > 1:
                subj_data['pv_panel_condition'] = pv_data.dropna()
                print(f"  - PV Panel Condition: {len(subj_data['pv_panel_condition'])} records")
        
        # 2. Inverter Performance from APS Switching Cycles
        if 'APS Switching Cycles' in self.data:
            switching = self.data['APS Switching Cycles'].copy()
            # Get AC and DC switching cycles for each APU
            cycle_cols = [col for col in switching.columns if 'AC' in str(col) or 'DC' in str(col)]
            if cycle_cols:
                inv_data = switching[['TimeStamp'] + cycle_cols].copy()
                subj_data['inverter_switching'] = inv_data.dropna()
                print(f"  - Inverter Switching Cycles: {len(subj_data['inverter_switching'])} records")
        
        # 3. Inverter Errors and Warnings from APS Stat Trig
        if 'APS Stat Trig' in self.data:
            aps_trig = self.data['APS Stat Trig'].copy()
            error_cols = [col for col in aps_trig.columns if 'Error' in str(col)]
            warning_cols = [col for col in aps_trig.columns if 'Warning' in str(col)]
            
            if error_cols or warning_cols:
                error_data = aps_trig[['TimeStamp']].copy()
                if error_cols:
                    error_data['Total_Errors'] = aps_trig[error_cols].sum(axis=1)
                if warning_cols:
                    error_data['Total_Warnings'] = aps_trig[warning_cols].sum(axis=1)
                if 'OpState' in aps_trig.columns:
                    error_data['OpState'] = aps_trig['OpState']
                
                subj_data['inverter_errors'] = error_data.dropna()
                print(f"  - Inverter Errors/Warnings: {len(subj_data['inverter_errors'])} records")
        
        return subj_data
    
    def extract_power_output(self):
        """Extract power output data"""
        print("\n=== Extracting Power Output ===")
        
        power_data = {}
        
        # 1. Power output from APS Energy
        if 'APS Energy' in self.data:
            aps_energy = self.data['APS Energy'].copy()
            # Get output power columns
            out_cols = [col for col in aps_energy.columns if 'W_out' in str(col)]
            if out_cols:
                power_out = aps_energy[['TimeStamp'] + out_cols].copy()
                # Calculate total output
                numeric_cols = power_out.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    power_out['Total_Output_kWh'] = power_out[numeric_cols].sum(axis=1)
                power_data['aps_energy'] = power_out.dropna()
                print(f"  - APS Energy Output: {len(power_data['aps_energy'])} records")
        
        # 2. Real-time power from APU Stat 10s
        if 'APU Stat 10s' in self.data:
            apu_stat = self.data['APU Stat 10s'].copy()
            # Get power columns (PL1, PL2, PL3, Pdc)
            power_cols = [col for col in apu_stat.columns if 'PL' in str(col) or 'Pdc' in str(col)]
            if power_cols:
                realtime_power = apu_stat[['TimeStamp', 'System'] + power_cols].copy()
                # Calculate total power per system
                numeric_cols = realtime_power.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    realtime_power['Total_Power_kW'] = realtime_power[numeric_cols].sum(axis=1)
                power_data['realtime_power'] = realtime_power.dropna()
                print(f"  - Real-time Power: {len(power_data['realtime_power'])} records")
        
        return power_data
    
    def merge_data(self, env_data, subj_data, power_data):
        """Merge all data sources on timestamp"""
        print("\n=== Merging Data Sources ===")
        
        # Start with power output as base
        if 'realtime_power' in power_data:
            merged = power_data['realtime_power'].copy()
        elif 'aps_energy' in power_data:
            merged = power_data['aps_energy'].copy()
        else:
            print("Warning: No power data found!")
            return None
        
        # Merge environmental factors
        if 'irradiance' in env_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                env_data['irradiance'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        if 'temperature' in env_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                env_data['temperature'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        if 'humidity' in env_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                env_data['humidity'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        # Merge subjective factors
        if 'pv_panel_condition' in subj_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                subj_data['pv_panel_condition'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        if 'inverter_switching' in subj_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                subj_data['inverter_switching'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        if 'inverter_errors' in subj_data:
            merged = pd.merge_asof(
                merged.sort_values('TimeStamp'),
                subj_data['inverter_errors'].sort_values('TimeStamp'),
                on='TimeStamp',
                direction='nearest',
                tolerance=pd.Timedelta(minutes=1)
            )
        
        self.processed_data = merged
        print(f"  - Merged dataset: {len(merged)} records, {len(merged.columns)} columns")
        return merged
    
    def analyze_correlations(self):
        """Analyze correlations between factors and power output"""
        print("\n=== Correlation Analysis ===")
        
        if self.processed_data is None:
            print("Error: No processed data available!")
            return None
        
        # Select numeric columns for correlation
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Identify power output column
        power_col = None
        for col in ['Total_Power_kW', 'Total_Output_kWh', 'Pdc/kW']:
            if col in numeric_cols:
                power_col = col
                break
        
        if power_col is None:
            print("Warning: Power output column not found!")
            return None
        
        # Calculate correlations
        correlations = self.processed_data[numeric_cols].corr()[power_col].sort_values(ascending=False)
        
        print(f"\nCorrelations with {power_col}:")
        print("-" * 50)
        for var, corr in correlations.items():
            if var != power_col and not np.isnan(corr):
                try:
                    print(f"  {var:30s}: {corr:7.4f}")
                except UnicodeEncodeError:
                    # Handle encoding issues
                    var_safe = var.encode('ascii', 'ignore').decode('ascii')
                    print(f"  {var_safe:30s}: {corr:7.4f}")
        
        return correlations
    
    def create_visualizations(self, output_dir='output'):
        """Create visualization plots"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n=== Creating Visualizations ===")
        
        if self.processed_data is None:
            print("Error: No processed data available!")
            return
        
        # Find power output column
        power_col = None
        for col in ['Total_Power_kW', 'Total_Output_kWh', 'Pdc/kW']:
            if col in self.processed_data.columns:
                power_col = col
                break
        
        if power_col is None:
            print("Warning: Power output column not found!")
            return
        
        # 1. Power Output Over Time
        plt.figure(figsize=(14, 6))
        if 'TimeStamp' in self.processed_data.columns:
            time_data = self.processed_data.dropna(subset=['TimeStamp', power_col])
            plt.plot(time_data['TimeStamp'], time_data[power_col], linewidth=1, alpha=0.7)
            plt.title('Power Output Over Time', fontsize=14, fontweight='bold')
            plt.xlabel('Time')
            plt.ylabel('Power Output (kW)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/power_over_time.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: power_over_time.png")
        
        # 2. Environmental Factors vs Power Output
        env_factors = [col for col in self.processed_data.columns if 'Irradiance' in str(col) or 'Tamb' in str(col) or 'Tpan' in str(col) or 'Ttrans' in str(col) or 'Humidity' in str(col)]
        available_env = [f for f in env_factors if f in self.processed_data.columns]
        
        if available_env:
            fig, axes = plt.subplots(len(available_env), 1, figsize=(12, 4*len(available_env)))
            if len(available_env) == 1:
                axes = [axes]
            
            for idx, factor in enumerate(available_env):
                data = self.processed_data[[factor, power_col]].dropna()
                if len(data) > 0:
                    axes[idx].scatter(data[factor], data[power_col], alpha=0.5, s=10)
                    axes[idx].set_xlabel(factor)
                    axes[idx].set_ylabel('Power Output (kW)')
                    axes[idx].set_title(f'{factor} vs Power Output')
                    # Add trend line (with error handling)
                    try:
                        # Check for valid data
                        if len(data) > 1 and data[factor].std() > 0:
                            z = np.polyfit(data[factor], data[power_col], 1)
                            p = np.poly1d(z)
                            x_sorted = np.sort(data[factor])
                            axes[idx].plot(x_sorted, p(x_sorted), "r--", alpha=0.8, linewidth=2)
                    except (np.linalg.LinAlgError, ValueError):
                        # Skip trend line if calculation fails
                        pass
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/environmental_factors.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: environmental_factors.png")
        
        # 3. Subjective Factors Analysis
        # PV Panel Condition
        iso_cols = [col for col in self.processed_data.columns if 'Riso' in str(col)]
        if iso_cols and power_col:
            fig, axes = plt.subplots(1, len(iso_cols), figsize=(5*len(iso_cols), 5))
            if len(iso_cols) == 1:
                axes = [axes]
            
            for idx, col in enumerate(iso_cols):
                data = self.processed_data[[col, power_col]].dropna()
                if len(data) > 0:
                    axes[idx].scatter(data[col], data[power_col], alpha=0.5, s=10)
                    axes[idx].set_xlabel('Insulation Resistance')
                    axes[idx].set_ylabel('Power Output (kW)')
                    axes[idx].set_title(f'PV Panel Condition: {col}')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/pv_panel_condition.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: pv_panel_condition.png")
        
        # Inverter Performance
        if 'Total_Errors' in self.processed_data.columns or 'Total_Warnings' in self.processed_data.columns:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            if 'Total_Errors' in self.processed_data.columns:
                data = self.processed_data[['Total_Errors', power_col]].dropna()
                if len(data) > 0:
                    axes[0].scatter(data['Total_Errors'], data[power_col], alpha=0.5, s=10)
                    axes[0].set_xlabel('Total Errors')
                    axes[0].set_ylabel('Power Output (kW)')
                    axes[0].set_title('Inverter Errors vs Power Output')
            
            if 'Total_Warnings' in self.processed_data.columns:
                data = self.processed_data[['Total_Warnings', power_col]].dropna()
                if len(data) > 0:
                    axes[1].scatter(data['Total_Warnings'], data[power_col], alpha=0.5, s=10)
                    axes[1].set_xlabel('Total Warnings')
                    axes[1].set_ylabel('Power Output (kW)')
                    axes[1].set_title('Inverter Warnings vs Power Output')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/inverter_performance.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: inverter_performance.png")
        
        # 4. Correlation Heatmap
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 1:
            corr_matrix = self.processed_data[numeric_cols].corr()
            plt.figure(figsize=(12, 10))
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                       square=True, linewidths=1, cbar_kws={"shrink": 0.8})
            plt.title('Correlation Matrix: All Factors', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/correlation_heatmap.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: correlation_heatmap.png")
        
        print(f"\nAll visualizations saved to '{output_dir}' directory")
    
    def generate_markdown_report(self, output_file='analysis_report.md', correlations=None):
        """Generate a markdown report with key findings and visualizations"""
        print(f"\n=== Generating Markdown Report ===")
        
        if self.processed_data is None:
            print("Error: No processed data available!")
            return
        
        md_content = []
        md_content.append("# Power Output Analysis Report")
        md_content.append("")
        md_content.append("## Phân tích ảnh hưởng của các yếu tố lên công suất đầu ra")
        md_content.append("")
        md_content.append(f"**Ngày tạo:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        md_content.append(f"**Nguồn dữ liệu:** `{self.csv_path}`  ")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        
        # Dataset Overview
        md_content.append("## 1. Tổng quan dữ liệu")
        md_content.append("")
        md_content.append(f"- **Tổng số bản ghi:** {len(self.processed_data):,}")
        md_content.append(f"- **Khoảng thời gian:** {self.processed_data['TimeStamp'].min()} đến {self.processed_data['TimeStamp'].max()}")
        md_content.append(f"- **Số cột dữ liệu:** {len(self.processed_data.columns)}")
        md_content.append("")
        
        # Power Output Statistics
        power_col = None
        for col in ['Total_Power_kW', 'Total_Output_kWh', 'Pdc/kW']:
            if col in self.processed_data.columns:
                power_col = col
                break
        
        if power_col:
            md_content.append("## 2. Thống kê công suất đầu ra")
            md_content.append("")
            power_stats = self.processed_data[power_col].describe()
            md_content.append("| Thống kê | Giá trị |")
            md_content.append("|----------|---------|")
            md_content.append(f"| Trung bình | {power_stats['mean']:.2f} kW |")
            md_content.append(f"| Trung vị | {power_stats['50%']:.2f} kW |")
            md_content.append(f"| Tối đa | {power_stats['max']:.2f} kW |")
            md_content.append(f"| Tối thiểu | {power_stats['min']:.2f} kW |")
            md_content.append(f"| Độ lệch chuẩn | {power_stats['std']:.2f} kW |")
            md_content.append("")
            md_content.append(f"![Power Output Over Time](output/power_over_time.png)")
            md_content.append("")
        
        # Environmental Factors
        md_content.append("## 3. Yếu tố môi trường (Khách quan)")
        md_content.append("")
        md_content.append("Các yếu tố môi trường không thể kiểm soát được, bao gồm:")
        md_content.append("")
        
        env_factors = [col for col in self.processed_data.columns if 'Irradiance' in str(col) or 'Tamb' in str(col) or 'Tpan' in str(col) or 'Ttrans' in str(col) or 'Humidity' in str(col)]
        if env_factors:
            md_content.append("| Yếu tố | Trung bình | Phạm vi | Tương quan với công suất |")
            md_content.append("|--------|------------|---------|---------------------------|")
            
            for factor in env_factors:
                if factor in self.processed_data.columns:
                    data = self.processed_data[factor].dropna()
                    if len(data) > 0:
                        mean_val = data.mean()
                        min_val = data.min()
                        max_val = data.max()
                        corr_val = ""
                        if power_col:
                            corr = self.processed_data[[factor, power_col]].corr().iloc[0, 1]
                            if not np.isnan(corr):
                                corr_val = f"{corr:.4f}"
                        
                        # Clean factor name for display
                        factor_display = str(factor).replace('_', ' ').replace('/', ' ')
                        md_content.append(f"| {factor_display} | {mean_val:.2f} | {min_val:.2f} - {max_val:.2f} | {corr_val} |")
            
            md_content.append("")
            md_content.append(f"![Environmental Factors](output/environmental_factors.png)")
            md_content.append("")
        
        # Subjective Factors
        md_content.append("## 4. Yếu tố chủ quan")
        md_content.append("")
        md_content.append("Các yếu tố chủ quan có thể quản lý được thông qua bảo trì và vệ sinh:")
        md_content.append("")
        
        # PV Panel Condition
        iso_cols = [col for col in self.processed_data.columns if 'Riso' in str(col)]
        if iso_cols:
            md_content.append("### 4.1. Tình trạng tấm pin PV (Điện trở cách điện)")
            md_content.append("")
            md_content.append("| Chỉ số | Trung bình | Phạm vi | Tương quan với công suất |")
            md_content.append("|--------|------------|---------|---------------------------|")
            
            for col in iso_cols:
                data = self.processed_data[col].dropna()
                if len(data) > 0:
                    mean_val = data.mean()
                    min_val = data.min()
                    max_val = data.max()
                    corr_val = ""
                    if power_col:
                        corr = self.processed_data[[col, power_col]].corr().iloc[0, 1]
                        if not np.isnan(corr):
                            corr_val = f"{corr:.4f}"
                    
                    col_display = str(col).replace('_', ' ').replace('/', ' ')
                    md_content.append(f"| {col_display} | {mean_val:.2f} | {min_val:.2f} - {max_val:.2f} | {corr_val} |")
            
            md_content.append("")
            md_content.append(f"![PV Panel Condition](output/pv_panel_condition.png)")
            md_content.append("")
        
        # Inverter Performance
        md_content.append("### 4.2. Hiệu suất bộ nghịch lưu DC-AC")
        md_content.append("")
        
        if 'Total_Errors' in self.processed_data.columns:
            errors = self.processed_data['Total_Errors'].dropna()
            corr_err = ""
            if power_col:
                corr = self.processed_data[['Total_Errors', power_col]].corr().iloc[0, 1]
                if not np.isnan(corr):
                    corr_err = f"{corr:.4f}"
            
            md_content.append(f"- **Lỗi bộ nghịch lưu:** Trung bình = {errors.mean():.2f}, Tối đa = {errors.max()}")
            if corr_err:
                md_content.append(f"  - Tương quan với công suất: {corr_err}")
            md_content.append("")
        
        if 'Total_Warnings' in self.processed_data.columns:
            warnings = self.processed_data['Total_Warnings'].dropna()
            corr_warn = ""
            if power_col:
                corr = self.processed_data[['Total_Warnings', power_col]].corr().iloc[0, 1]
                if not np.isnan(corr):
                    corr_warn = f"{corr:.4f}"
            
            md_content.append(f"- **Cảnh báo bộ nghịch lưu:** Trung bình = {warnings.mean():.2f}, Tối đa = {warnings.max()}")
            if corr_warn:
                md_content.append(f"  - Tương quan với công suất: {corr_warn}")
            md_content.append("")
        
        md_content.append(f"![Inverter Performance](output/inverter_performance.png)")
        md_content.append("")
        
        # Correlation Analysis
        if correlations is not None:
            md_content.append("## 5. Phân tích tương quan")
            md_content.append("")
            md_content.append("### Top 10 yếu tố có tương quan mạnh nhất với công suất:")
            md_content.append("")
            md_content.append("| Yếu tố | Hệ số tương quan |")
            md_content.append("|--------|------------------|")
            
            # Get top correlations (excluding power column itself)
            top_corrs = correlations.drop(power_col).abs().sort_values(ascending=False).head(10)
            for var, corr_abs in top_corrs.items():
                corr_val = correlations[var]
                var_display = str(var).replace('_', ' ').replace('/', ' ')
                try:
                    md_content.append(f"| {var_display} | {corr_val:.4f} |")
                except:
                    var_safe = var.encode('ascii', 'ignore').decode('ascii')
                    md_content.append(f"| {var_safe} | {corr_val:.4f} |")
            
            md_content.append("")
            md_content.append(f"![Correlation Heatmap](output/correlation_heatmap.png)")
            md_content.append("")
        
        # Key Findings
        md_content.append("## 6. Kết luận và khuyến nghị")
        md_content.append("")
        md_content.append("### Kết luận:")
        md_content.append("")
        md_content.append("1. **Yếu tố môi trường (khách quan):**")
        md_content.append("   - Bức xạ mặt trời, nhiệt độ, độ ẩm là các yếu tố không thể kiểm soát")
        md_content.append("   - Chúng ảnh hưởng trực tiếp đến công suất đầu ra")
        md_content.append("   - Cần theo dõi để dự đoán và tối ưu hóa hiệu suất")
        md_content.append("")
        md_content.append("2. **Yếu tố chủ quan:**")
        md_content.append("   - Tình trạng tấm pin PV (điện trở cách điện, điện dung rò)")
        md_content.append("   - Hiệu suất bộ nghịch lưu DC-AC (số lần chuyển mạch, lỗi, cảnh báo)")
        md_content.append("   - Có thể quản lý thông qua bảo trì định kỳ")
        md_content.append("")
        md_content.append("### Khuyến nghị:")
        md_content.append("")
        md_content.append("- **Vệ sinh tấm pin PV định kỳ** để duy trì hiệu suất tối ưu")
        md_content.append("- **Bảo trì bộ nghịch lưu** để giảm lỗi và cảnh báo")
        md_content.append("- **Theo dõi các chỉ số chủ quan** để phát hiện sớm vấn đề")
        md_content.append("- **Phân tích tương quan** giúp xác định yếu tố nào có ảnh hưởng lớn nhất")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        md_content.append(f"*Báo cáo được tạo tự động bởi Power Data Analyzer*")
        md_content.append("")
        
        # Write markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        print(f"  - Markdown report saved to: {output_file}")
    
    def run_full_analysis(self):
        """Run the complete analysis pipeline"""
        print("=" * 70)
        print("POWER OUTPUT ANALYSIS: Environmental vs Subjective Factors")
        print("=" * 70)
        
        # Load data
        self.load_data()
        
        # Extract factors
        env_data = self.extract_environmental_factors()
        subj_data = self.extract_subjective_factors()
        power_data = self.extract_power_output()
        
        # Merge data
        merged = self.merge_data(env_data, subj_data, power_data)
        
        if merged is None:
            print("\nError: Could not merge data. Analysis stopped.")
            return
        
        # Analyze correlations
        correlations = self.analyze_correlations()
        
        # Create visualizations
        self.create_visualizations()
        
        # Generate markdown report
        self.generate_markdown_report(correlations=correlations)
        
        print("\n" + "=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
        
        return {
            'processed_data': self.processed_data,
            'correlations': correlations,
            'environmental': env_data,
            'subjective': subj_data,
            'power': power_data
        }


def main():
    """Main function to run the analysis"""
    # Path to the CSV file
    csv_path = 'dataset/APS-000258_20251001_000000.csv'
    
    # Create analyzer instance
    analyzer = PowerDataAnalyzer(csv_path)
    
    # Run full analysis
    results = analyzer.run_full_analysis()
    
    return results


if __name__ == "__main__":
    results = main()

