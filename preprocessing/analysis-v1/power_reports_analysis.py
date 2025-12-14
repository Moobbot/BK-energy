"""
Power Reports Analysis

Phân tích báo cáo công suất từ file Excel "Power reports (1-15)102025.xls"
Bao gồm phân tích công suất AC/DC theo thời gian, theo block/inverter, 
bức xạ mặt trời, và các thống kê.
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


class PowerReportsAnalyzer:
    """Phân tích báo cáo công suất"""
    
    def __init__(self, excel_path):
        """Khởi tạo với đường dẫn file Excel"""
        self.excel_path = excel_path
        self.raw_data = None
        self.processed_data = None
        self.summary_stats = None
        
    def load_data(self):
        """Đọc và parse file Excel"""
        print("Loading Excel file...")
        
        # Đọc file Excel không có header để xử lý thủ công
        df = pd.read_excel(self.excel_path, sheet_name=0, header=None)
        
        print(f"File size: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Tìm hàng chứa "Date Time" (thường là hàng 3, index 3)
        date_time_row = None
        for idx in range(min(10, len(df))):
            if pd.notna(df.iloc[idx, 1]) and 'Date Time' in str(df.iloc[idx, 1]):
                date_time_row = idx
                break
        
        if date_time_row is None:
            print("Cannot find 'Date Time' row, trying row 3...")
            date_time_row = 3
        
        print(f"Header row: {date_time_row}")
        
        # Lấy header từ hàng date_time_row và hàng tiếp theo
        header_row1 = df.iloc[date_time_row].values  # Hàng chứa "Date Time", "RADIATION", "BLOCK X"
        header_row2 = df.iloc[date_time_row + 1].values  # Hàng chứa "(W/m2)", "INV#X AC/DC"
        
        # Tạo tên cột hợp lý
        column_names = []
        for i in range(len(header_row1)):
            col1 = str(header_row1[i]) if pd.notna(header_row1[i]) else ''
            col2 = str(header_row2[i]) if pd.notna(header_row2[i]) else ''
            
            if col1 == 'Date Time' or 'Date Time' in col1:
                column_names.append('DateTime')
            elif col1 == 'RADIATION' or 'RADIATION' in col1:
                # Bức xạ mặt trời
                if col2 and col2 != 'nan':
                    column_names.append(f"Radiation_{col2.replace('(', '').replace(')', '').replace('/', '_')}")
                else:
                    column_names.append('Radiation_W_m2')
            elif 'BLOCK' in col1.upper():
                # Có Block name
                if col2 and col2 != 'nan':
                    # Kết hợp Block và Inverter
                    inv_name = col2.replace('#', '').replace(' ', '_')
                    column_names.append(f"{col1.replace(' ', '_')}_{inv_name}")
                else:
                    column_names.append(col1.replace(' ', '_'))
            elif col2 and col2 != 'nan' and col2 not in ['(W/m2)', '']:
                # Chỉ có Inverter name (thuộc Block trước đó)
                inv_name = col2.replace('#', '').replace(' ', '_')
                # Tìm Block gần nhất
                block_name = 'BLOCK_UNKNOWN'
                for j in range(i-1, max(0, i-10), -1):
                    if j < len(header_row1) and pd.notna(header_row1[j]):
                        if 'BLOCK' in str(header_row1[j]).upper():
                            block_name = str(header_row1[j]).replace(' ', '_')
                            break
                column_names.append(f"{block_name}_{inv_name}")
            else:
                column_names.append(f"Column_{i}")
        
        # Lấy dữ liệu từ hàng sau header
        data_start_row = date_time_row + 2
        data_df = df.iloc[data_start_row:].copy()
        data_df.columns = column_names[:len(data_df.columns)]
        
        # Đặt lại index
        data_df = data_df.reset_index(drop=True)
        
        # Parse DateTime
        if 'DateTime' in data_df.columns:
            data_df['DateTime'] = pd.to_datetime(
                data_df['DateTime'], 
                format='%d/%m/%Y %H:%M', 
                errors='coerce'
            )
            # Loại bỏ hàng không có DateTime hợp lệ
            data_df = data_df[data_df['DateTime'].notna()].copy()
        
        # Chuyển đổi các cột số thành numeric
        for col in data_df.columns:
            if col != 'DateTime' and col in data_df.columns:
                try:
                    data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
                except (TypeError, ValueError):
                    # Skip if conversion fails
                    pass
        
        self.raw_data = df
        self.processed_data = data_df
        
        print(f"Loaded {len(data_df)} records")
        print(f"Number of columns: {len(data_df.columns)}")
        if 'DateTime' in data_df.columns:
            print(f"Time range: {data_df['DateTime'].min()} to {data_df['DateTime'].max()}")
        
        return data_df
    
    def analyze_structure(self):
        """Phân tích cấu trúc dữ liệu"""
        print("\n=== Analyzing Data Structure ===")
        
        if self.processed_data is None:
            print("No data available! Please run load_data() first.")
            return
        
        # Phân loại cột
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Tìm cột bức xạ
        radiation_cols = [col for col in numeric_cols if 'Radiation' in str(col) or 'RADIATION' in str(col)]
        
        # Tìm cột AC/DC
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        
        # Tìm cột Block
        block_cols = [col for col in numeric_cols if 'BLOCK' in str(col).upper()]
        
        # Tìm cột Inverter
        inv_cols = [col for col in numeric_cols if 'INV' in str(col).upper()]
        
        other_cols = [col for col in numeric_cols 
                     if col not in radiation_cols and col not in ac_cols 
                     and col not in dc_cols and col not in block_cols and col not in inv_cols]
        
        print(f"\nData columns:")
        print(f"  - Radiation columns: {len(radiation_cols)}")
        print(f"  - AC Power columns: {len(ac_cols)}")
        print(f"  - DC Power columns: {len(dc_cols)}")
        print(f"  - Block columns: {len(block_cols)}")
        print(f"  - Inverter columns: {len(inv_cols)}")
        print(f"  - Other columns: {len(other_cols)}")
        
        if radiation_cols:
            print(f"\nRadiation: {radiation_cols[:3]}{'...' if len(radiation_cols) > 3 else ''}")
        if ac_cols:
            print(f"\nAC Power: {ac_cols[:5]}{'...' if len(ac_cols) > 5 else ''}")
        if dc_cols:
            print(f"\nDC Power: {dc_cols[:5]}{'...' if len(dc_cols) > 5 else ''}")
        
        return {
            'radiation_cols': radiation_cols,
            'ac_cols': ac_cols,
            'dc_cols': dc_cols,
            'block_cols': block_cols,
            'inv_cols': inv_cols,
            'other_cols': other_cols
        }
    
    def calculate_statistics(self):
        """Tính toán thống kê"""
        print("\n=== Calculating Statistics ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        
        stats = {}
        for col in numeric_cols:
            data = self.processed_data[col].dropna()
            if len(data) > 0:
                stats[col] = {
                    'mean': data.mean(),
                    'median': data.median(),
                    'std': data.std(),
                    'min': data.min(),
                    'max': data.max(),
                    'sum': data.sum(),
                    'count': len(data)
                }
        
        self.summary_stats = stats
        
        print(f"Calculated statistics for {len(stats)} columns")
        
        return stats
    
    def calculate_efficiency(self):
        """Tính toán hiệu suất AC/DC (efficiency ratio)"""
        print("\n=== Calculating Efficiency (AC/DC Ratio) ===")
        
        if self.processed_data is None:
            print("No data available!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        
        efficiency_data = {}
        
        # Tính hiệu suất cho từng cặp AC/DC
        for ac_col in ac_cols:
            # Tìm cột DC tương ứng
            base_name = ac_col.replace('_AC', '').replace('AC', '')
            matching_dc = [dc for dc in dc_cols if base_name in dc or dc.replace('_DC', '').replace('DC', '') in base_name]
            
            if matching_dc:
                dc_col = matching_dc[0]
                ac_data = self.processed_data[ac_col]
                dc_data = self.processed_data[dc_col]
                
                # Tính hiệu suất (AC/DC * 100%)
                efficiency = (ac_data / dc_data.replace(0, np.nan)) * 100
                efficiency = efficiency.replace([np.inf, -np.inf], np.nan)
                
                efficiency_data[f"{ac_col}_efficiency"] = efficiency
                
                # Thêm vào processed_data
                self.processed_data[f"{ac_col}_efficiency"] = efficiency
        
        # Tính hiệu suất tổng
        if ac_cols and dc_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            total_dc = self.processed_data[dc_cols].sum(axis=1)
            total_efficiency = (total_ac / total_dc.replace(0, np.nan)) * 100
            total_efficiency = total_efficiency.replace([np.inf, -np.inf], np.nan)
            self.processed_data['Total_Efficiency'] = total_efficiency
            
            efficiency_data['Total_Efficiency'] = total_efficiency
            
            print(f"  - Calculated efficiency for {len(efficiency_data)} inverter pairs")
            if total_efficiency.notna().sum() > 0:
                print(f"  - Average total efficiency: {total_efficiency.mean():.2f}%")
                print(f"  - Efficiency range: {total_efficiency.min():.2f}% - {total_efficiency.max():.2f}%")
        
        return efficiency_data
    
    def analyze_by_block(self):
        """Phân tích công suất theo Block"""
        print("\n=== Analyzing by Block ===")
        
        if self.processed_data is None:
            print("No data available!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        
        # Nhóm các cột theo Block
        block_data = {}
        
        for col in ac_cols + dc_cols:
            # Tìm Block name từ tên cột
            parts = str(col).split('_')
            block_name = None
            for part in parts:
                if 'BLOCK' in part.upper():
                    block_name = part
                    break
            
            if block_name is None:
                continue
            
            if block_name not in block_data:
                block_data[block_name] = {'AC': [], 'DC': []}
            
            if 'AC' in col and 'DC' not in col:
                block_data[block_name]['AC'].append(col)
            elif 'DC' in col:
                block_data[block_name]['DC'].append(col)
        
        # Tính thống kê cho mỗi Block
        block_stats = {}
        for block_name, cols in block_data.items():
            ac_cols_block = cols['AC']
            dc_cols_block = cols['DC']
            
            if ac_cols_block:
                block_ac = self.processed_data[ac_cols_block].sum(axis=1)
                block_stats[block_name] = {
                    'avg_ac_power': block_ac.mean(),
                    'max_ac_power': block_ac.max(),
                    'min_ac_power': block_ac.min(),
                    'total_ac_power': block_ac.sum(),
                    'num_inverters': len(ac_cols_block)
                }
            
            if dc_cols_block:
                block_dc = self.processed_data[dc_cols_block].sum(axis=1)
                if block_name in block_stats:
                    block_stats[block_name]['avg_dc_power'] = block_dc.mean()
                    block_stats[block_name]['max_dc_power'] = block_dc.max()
                    block_stats[block_name]['total_dc_power'] = block_dc.sum()
                    
                    # Tính hiệu suất Block
                    block_efficiency = (block_ac / block_dc.replace(0, np.nan)) * 100
                    block_efficiency = block_efficiency.replace([np.inf, -np.inf], np.nan)
                    block_stats[block_name]['avg_efficiency'] = block_efficiency.mean()
        
        print(f"  - Analyzed {len(block_stats)} blocks")
        
        return block_stats
    
    def calculate_correlations(self):
        """Tính toán tương quan giữa các biến"""
        print("\n=== Calculating Correlations ===")
        
        if self.processed_data is None:
            print("No data available!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        radiation_cols = [col for col in numeric_cols if 'Radiation' in str(col)]
        
        correlations = {}
        
        # Tương quan giữa radiation và power
        if radiation_cols and ac_cols:
            radiation = self.processed_data[radiation_cols[0]].dropna()
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            
            # Lấy chỉ số chung
            common_idx = radiation.index.intersection(total_ac.index)
            if len(common_idx) > 1:
                corr = radiation.loc[common_idx].corr(total_ac.loc[common_idx])
                correlations['radiation_vs_total_ac'] = corr
                print(f"  - Radiation vs Total AC Power: {corr:.4f}")
        
        # Tương quan giữa AC và DC
        if ac_cols and dc_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            total_dc = self.processed_data[dc_cols].sum(axis=1)
            
            common_idx = total_ac.index.intersection(total_dc.index)
            if len(common_idx) > 1:
                corr = total_ac.loc[common_idx].corr(total_dc.loc[common_idx])
                correlations['total_ac_vs_total_dc'] = corr
                print(f"  - Total AC vs Total DC Power: {corr:.4f}")
        
        return correlations
    
    def detect_anomalies(self, threshold_std=3):
        """Phát hiện các giá trị bất thường"""
        print(f"\n=== Detecting Anomalies (threshold: {threshold_std} std) ===")
        
        if self.processed_data is None:
            print("No data available!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        
        anomalies = {
            'negative_power': [],
            'outliers': [],
            'zero_power': []
        }
        
        # Phát hiện công suất âm
        if ac_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            negative_idx = total_ac[total_ac < 0].index
            if len(negative_idx) > 0:
                anomalies['negative_power'] = negative_idx.tolist()
                print(f"  - Found {len(negative_idx)} records with negative AC power")
        
        # Phát hiện outliers (sử dụng Z-score)
        if ac_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            mean = total_ac.mean()
            std = total_ac.std()
            
            z_scores = np.abs((total_ac - mean) / std)
            outlier_idx = total_ac[z_scores > threshold_std].index
            if len(outlier_idx) > 0:
                anomalies['outliers'] = outlier_idx.tolist()
                print(f"  - Found {len(outlier_idx)} outlier records (>{threshold_std} std)")
        
        # Phát hiện công suất bằng 0 trong giờ cao điểm (giả định: 9-15h)
        if 'DateTime' in self.processed_data.columns and ac_cols:
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            peak_hours = self.processed_data[(self.processed_data['Hour'] >= 9) & 
                                             (self.processed_data['Hour'] <= 15)]
            total_ac_peak = peak_hours[ac_cols].sum(axis=1)
            zero_power_idx = peak_hours[total_ac_peak == 0].index
            if len(zero_power_idx) > 0:
                anomalies['zero_power'] = zero_power_idx.tolist()
                print(f"  - Found {len(zero_power_idx)} records with zero power during peak hours")
        
        return anomalies
    
    def analyze_daily(self):
        """Phân tích công suất theo ngày"""
        print("\n=== Analyzing Daily Performance ===")
        
        if self.processed_data is None or 'DateTime' not in self.processed_data.columns:
            print("No data available or no DateTime column!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        radiation_cols = [col for col in numeric_cols if 'Radiation' in str(col)]
        
        self.processed_data['Date'] = self.processed_data['DateTime'].dt.date
        
        daily_stats = {}
        
        for date in self.processed_data['Date'].unique():
            day_data = self.processed_data[self.processed_data['Date'] == date]
            
            stats = {
                'date': date,
                'num_records': len(day_data)
            }
            
            if ac_cols:
                total_ac = day_data[ac_cols].sum(axis=1)
                stats['avg_ac_power'] = total_ac.mean()
                stats['max_ac_power'] = total_ac.max()
                stats['min_ac_power'] = total_ac.min()
                stats['total_ac_energy'] = total_ac.sum()  # Tích phân công suất (xấp xỉ)
            
            if dc_cols:
                total_dc = day_data[dc_cols].sum(axis=1)
                stats['avg_dc_power'] = total_dc.mean()
                stats['max_dc_power'] = total_dc.max()
                stats['total_dc_energy'] = total_dc.sum()
            
            if radiation_cols:
                radiation = day_data[radiation_cols[0]].dropna()
                if len(radiation) > 0:
                    stats['avg_radiation'] = radiation.mean()
                    stats['max_radiation'] = radiation.max()
            
            daily_stats[date] = stats
        
        print(f"  - Analyzed {len(daily_stats)} days")
        
        return daily_stats
    
    def calculate_detailed_stats(self):
        """Tính toán thống kê chi tiết (percentiles, CV, variance)"""
        print("\n=== Calculating Detailed Statistics ===")
        
        if self.processed_data is None:
            print("No data available!")
            return None
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        
        detailed_stats = {}
        
        # Tính cho tổng công suất AC
        if ac_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            data = total_ac.dropna()
            
            if len(data) > 0:
                detailed_stats['total_ac'] = {
                    'mean': data.mean(),
                    'median': data.median(),
                    'std': data.std(),
                    'variance': data.var(),
                    'cv': (data.std() / data.mean() * 100) if data.mean() != 0 else np.nan,  # Coefficient of Variation
                    'min': data.min(),
                    'max': data.max(),
                    'q25': data.quantile(0.25),
                    'q75': data.quantile(0.75),
                    'q90': data.quantile(0.90),
                    'q95': data.quantile(0.95),
                    'q99': data.quantile(0.99),
                    'skewness': data.skew(),
                    'kurtosis': data.kurtosis()
                }
        
        # Tính cho tổng công suất DC
        if dc_cols:
            total_dc = self.processed_data[dc_cols].sum(axis=1)
            data = total_dc.dropna()
            
            if len(data) > 0:
                detailed_stats['total_dc'] = {
                    'mean': data.mean(),
                    'median': data.median(),
                    'std': data.std(),
                    'variance': data.var(),
                    'cv': (data.std() / data.mean() * 100) if data.mean() != 0 else np.nan,
                    'min': data.min(),
                    'max': data.max(),
                    'q25': data.quantile(0.25),
                    'q75': data.quantile(0.75),
                    'q90': data.quantile(0.90),
                    'q95': data.quantile(0.95),
                    'q99': data.quantile(0.99),
                    'skewness': data.skew(),
                    'kurtosis': data.kurtosis()
                }
        
        print(f"  - Calculated detailed statistics")
        
        return detailed_stats
    
    def create_visualizations(self, output_dir='output'):
        """Tạo các biểu đồ trực quan"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n=== Creating Visualizations ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        radiation_cols = [col for col in numeric_cols if 'Radiation' in str(col)]
        
        # 1. Biểu đồ công suất tổng theo thời gian
        if 'DateTime' in self.processed_data.columns:
            plt.figure(figsize=(16, 8))
            
            # Tính tổng công suất AC và DC
            if ac_cols:
                total_ac = self.processed_data[ac_cols].sum(axis=1)
                plt.plot(self.processed_data['DateTime'], total_ac, 
                        label='Total AC Power', linewidth=1.5, alpha=0.8)
            
            if dc_cols:
                total_dc = self.processed_data[dc_cols].sum(axis=1)
                plt.plot(self.processed_data['DateTime'], total_dc, 
                        label='Total DC Power', linewidth=1.5, alpha=0.8)
            
            plt.title('Total Power (AC/DC) Over Time', fontsize=16, fontweight='bold')
            plt.xlabel('Time', fontsize=12)
            plt.ylabel('Power (kW)', fontsize=12)
            plt.legend()
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/power_over_time.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: power_over_time.png")
        
        # 2. Biểu đồ bức xạ mặt trời và công suất
        if radiation_cols and 'DateTime' in self.processed_data.columns:
            fig, axes = plt.subplots(2, 1, figsize=(16, 10))
            
            # Bức xạ mặt trời
            if len(radiation_cols) > 0:
                radiation_data = self.processed_data[radiation_cols[0]].dropna()
                if len(radiation_data) > 0:
                    axes[0].plot(self.processed_data['DateTime'], 
                               self.processed_data[radiation_cols[0]], 
                               color='orange', linewidth=1.5, alpha=0.8)
                    axes[0].set_title('Solar Radiation Over Time', fontsize=14, fontweight='bold')
                    axes[0].set_ylabel('Radiation (W/m²)', fontsize=12)
                    axes[0].grid(True, alpha=0.3)
            
            # Công suất AC
            if ac_cols:
                total_ac = self.processed_data[ac_cols].sum(axis=1)
                axes[1].plot(self.processed_data['DateTime'], total_ac, 
                            color='blue', linewidth=1.5, alpha=0.8)
                axes[1].set_title('Total AC Power Over Time', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Time', fontsize=12)
                axes[1].set_ylabel('AC Power (kW)', fontsize=12)
                axes[1].grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/radiation_vs_power.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: radiation_vs_power.png")
        
        # 3. Biểu đồ top 10 Inverter theo công suất trung bình
        if ac_cols:
            inv_avg_power = {}
            for col in ac_cols:
                data = self.processed_data[col].dropna()
                if len(data) > 0:
                    inv_avg_power[col] = data.mean()
            
            if inv_avg_power:
                sorted_inv = sorted(inv_avg_power.items(), key=lambda x: x[1], reverse=True)[:10]
                
                plt.figure(figsize=(14, 8))
                inv_names = [str(k).replace('_', ' ')[:40] for k, v in sorted_inv]
                inv_values = [v for k, v in sorted_inv]
                
                plt.barh(inv_names, inv_values, color='steelblue', alpha=0.8)
                plt.title('Top 10 Inverters - Average AC Power', fontsize=16, fontweight='bold')
                plt.xlabel('Average Power (kW)', fontsize=12)
                plt.ylabel('Inverter', fontsize=12)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/top_inverters_power.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: top_inverters_power.png")
        
        # 4. Biểu đồ phân bố công suất theo giờ trong ngày
        if 'DateTime' in self.processed_data.columns and ac_cols:
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            hourly_power = self.processed_data.groupby('Hour')[ac_cols].mean().mean(axis=1)
            
            plt.figure(figsize=(12, 6))
            plt.bar(hourly_power.index, hourly_power.values, color='coral', alpha=0.8)
            plt.title('Average AC Power Distribution by Hour of Day', fontsize=16, fontweight='bold')
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Average Power (kW)', fontsize=12)
            plt.xticks(range(24))
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/hourly_power_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: hourly_power_distribution.png")
        
        # 5. Heatmap công suất theo ngày và giờ
        if 'DateTime' in self.processed_data.columns and ac_cols:
            self.processed_data['Date'] = self.processed_data['DateTime'].dt.date
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            
            # Tính công suất trung bình theo ngày và giờ
            daily_hourly = self.processed_data.groupby(['Date', 'Hour'])[ac_cols].mean().mean(axis=1).reset_index()
            daily_hourly.columns = ['Date', 'Hour', 'Power']
            
            # Tạo pivot table
            pivot_table = daily_hourly.pivot(index='Date', columns='Hour', values='Power')
            
            plt.figure(figsize=(16, max(8, len(pivot_table) * 0.3)))
            sns.heatmap(pivot_table, annot=False, fmt='.1f', cmap='YlOrRd', 
                       cbar_kws={'label': 'Average Power (kW)'})
            plt.title('Heatmap: Average AC Power by Date and Hour', fontsize=16, fontweight='bold')
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Date', fontsize=12)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/daily_hourly_power_heatmap.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: daily_hourly_power_heatmap.png")
        
        # 6. So sánh AC vs DC Power
        if ac_cols and dc_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            total_dc = self.processed_data[dc_cols].sum(axis=1)
            
            plt.figure(figsize=(14, 6))
            plt.scatter(total_dc, total_ac, alpha=0.5, s=10)
            plt.xlabel('Total DC Power (kW)', fontsize=12)
            plt.ylabel('Total AC Power (kW)', fontsize=12)
            plt.title('AC Power vs DC Power', fontsize=16, fontweight='bold')
            
            # Thêm đường trend
            if len(total_dc.dropna()) > 1 and len(total_ac.dropna()) > 1:
                try:
                    z = np.polyfit(total_dc.dropna(), total_ac.dropna(), 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(total_dc.min(), total_dc.max(), 100)
                    plt.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Trend')
                    plt.legend()
                except:
                    pass
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/ac_vs_dc_power.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: ac_vs_dc_power.png")
        
        # 7. Biểu đồ hiệu suất theo thời gian
        if 'Total_Efficiency' in self.processed_data.columns and 'DateTime' in self.processed_data.columns:
            efficiency = self.processed_data['Total_Efficiency'].dropna()
            if len(efficiency) > 0:
                plt.figure(figsize=(16, 6))
                plt.plot(self.processed_data['DateTime'], self.processed_data['Total_Efficiency'], 
                        color='green', linewidth=1.5, alpha=0.8)
                plt.axhline(y=efficiency.mean(), color='r', linestyle='--', 
                           label=f'Average: {efficiency.mean():.2f}%', linewidth=2)
                plt.title('Total System Efficiency (AC/DC) Over Time', fontsize=16, fontweight='bold')
                plt.xlabel('Time', fontsize=12)
                plt.ylabel('Efficiency (%)', fontsize=12)
                plt.legend()
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/efficiency_over_time.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: efficiency_over_time.png")
        
        # 8. Biểu đồ so sánh Block
        block_stats = self.analyze_by_block()
        if block_stats:
            # Top 10 Blocks theo công suất trung bình
            sorted_blocks = sorted(block_stats.items(), 
                                  key=lambda x: x[1].get('avg_ac_power', 0), 
                                  reverse=True)[:15]
            
            if sorted_blocks:
                plt.figure(figsize=(14, 8))
                block_names = [str(k).replace('_', ' ')[:30] for k, v in sorted_blocks]
                block_powers = [v.get('avg_ac_power', 0) for k, v in sorted_blocks]
                
                plt.barh(block_names, block_powers, color='teal', alpha=0.8)
                plt.title('Top 15 Blocks - Average AC Power', fontsize=16, fontweight='bold')
                plt.xlabel('Average AC Power (kW)', fontsize=12)
                plt.ylabel('Block', fontsize=12)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/top_blocks_power.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: top_blocks_power.png")
        
        # 9. Biểu đồ tương quan giữa Radiation và Power
        if radiation_cols and ac_cols:
            radiation = self.processed_data[radiation_cols[0]].dropna()
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            
            common_idx = radiation.index.intersection(total_ac.index)
            if len(common_idx) > 10:
                plt.figure(figsize=(12, 8))
                plt.scatter(radiation.loc[common_idx], total_ac.loc[common_idx], 
                           alpha=0.5, s=10, color='purple')
                
                # Thêm đường trend
                try:
                    z = np.polyfit(radiation.loc[common_idx], total_ac.loc[common_idx], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(radiation.loc[common_idx].min(), 
                                        radiation.loc[common_idx].max(), 100)
                    plt.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Trend')
                    
                    corr = radiation.loc[common_idx].corr(total_ac.loc[common_idx])
                    plt.title(f'Radiation vs Total AC Power (Correlation: {corr:.4f})', 
                             fontsize=16, fontweight='bold')
                    plt.legend()
                except:
                    plt.title('Radiation vs Total AC Power', fontsize=16, fontweight='bold')
                
                plt.xlabel('Solar Radiation (W/m²)', fontsize=12)
                plt.ylabel('Total AC Power (kW)', fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/radiation_correlation.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: radiation_correlation.png")
        
        # 10. Biểu đồ phân tích theo ngày
        if 'DateTime' in self.processed_data.columns and ac_cols:
            self.processed_data['Date'] = self.processed_data['DateTime'].dt.date
            daily_power = self.processed_data.groupby('Date')[ac_cols].sum().sum(axis=1)
            
            if len(daily_power) > 0:
                plt.figure(figsize=(14, 6))
                dates = [str(d) for d in daily_power.index]
                plt.bar(range(len(daily_power)), daily_power.values, color='crimson', alpha=0.8)
                plt.title('Daily Total AC Power', fontsize=16, fontweight='bold')
                plt.xlabel('Date', fontsize=12)
                plt.ylabel('Total AC Power (kW)', fontsize=12)
                plt.xticks(range(len(daily_power)), dates, rotation=45, ha='right')
                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
                plt.savefig(f'{output_dir}/daily_power_comparison.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: daily_power_comparison.png")
        
        # 11. Box plot công suất theo giờ
        if 'DateTime' in self.processed_data.columns and ac_cols:
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            
            # Tạo DataFrame cho box plot
            hourly_data = []
            for hour in range(24):
                hour_power = total_ac[self.processed_data['Hour'] == hour]
                if len(hour_power) > 0:
                    hourly_data.append(hour_power.values)
            
            if hourly_data:
                plt.figure(figsize=(14, 6))
                plt.boxplot(hourly_data, labels=range(24))
                plt.title('AC Power Distribution by Hour of Day (Box Plot)', 
                         fontsize=16, fontweight='bold')
                plt.xlabel('Hour of Day', fontsize=12)
                plt.ylabel('AC Power (kW)', fontsize=12)
                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
                plt.savefig(f'{output_dir}/hourly_power_boxplot.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: hourly_power_boxplot.png")
        
        # 12. Biểu đồ phân bố hiệu suất
        if 'Total_Efficiency' in self.processed_data.columns:
            efficiency = self.processed_data['Total_Efficiency'].dropna()
            if len(efficiency) > 0:
                plt.figure(figsize=(12, 6))
                plt.hist(efficiency, bins=50, color='skyblue', alpha=0.8, edgecolor='black')
                plt.axvline(efficiency.mean(), color='r', linestyle='--', 
                           linewidth=2, label=f'Mean: {efficiency.mean():.2f}%')
                plt.axvline(efficiency.median(), color='g', linestyle='--', 
                           linewidth=2, label=f'Median: {efficiency.median():.2f}%')
                plt.title('Distribution of System Efficiency', fontsize=16, fontweight='bold')
                plt.xlabel('Efficiency (%)', fontsize=12)
                plt.ylabel('Frequency', fontsize=12)
                plt.legend()
                plt.grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
                plt.savefig(f'{output_dir}/efficiency_distribution.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: efficiency_distribution.png")
        
        print(f"\nAll visualizations saved to '{output_dir}' directory")
    
    def generate_markdown_report(self, output_file='power_reports_analysis.md'):
        """Tạo báo cáo markdown"""
        print(f"\n=== Generating Markdown Report ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        md_content = []
        md_content.append("# Power Reports Analysis")
        md_content.append("")
        md_content.append("## Phân tích báo cáo công suất")
        md_content.append("")
        md_content.append(f"**Ngày tạo:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        md_content.append(f"**Nguồn dữ liệu:** `{self.excel_path}`  ")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        
        # Tổng quan
        md_content.append("## 1. Tổng quan dữ liệu")
        md_content.append("")
        md_content.append(f"- **Tổng số bản ghi:** {len(self.processed_data):,}")
        if 'DateTime' in self.processed_data.columns:
            md_content.append(f"- **Khoảng thời gian:** {self.processed_data['DateTime'].min()} đến {self.processed_data['DateTime'].max()}")
        md_content.append(f"- **Số cột dữ liệu:** {len(self.processed_data.columns)}")
        md_content.append("")
        
        # Phân tích cấu trúc
        structure = self.analyze_structure()
        md_content.append("## 2. Cấu trúc dữ liệu")
        md_content.append("")
        md_content.append(f"- **Số cột Bức xạ mặt trời:** {len(structure['radiation_cols'])}")
        md_content.append(f"- **Số cột Công suất AC:** {len(structure['ac_cols'])}")
        md_content.append(f"- **Số cột Công suất DC:** {len(structure['dc_cols'])}")
        md_content.append(f"- **Số cột Block:** {len(structure['block_cols'])}")
        md_content.append(f"- **Số cột Inverter:** {len(structure['inv_cols'])}")
        md_content.append("")
        
        # Thống kê
        if self.summary_stats is None:
            self.calculate_statistics()
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        ac_cols = [col for col in numeric_cols if 'AC' in str(col) and 'DC' not in str(col)]
        dc_cols = [col for col in numeric_cols if 'DC' in str(col)]
        radiation_cols = [col for col in numeric_cols if 'Radiation' in str(col)]
        
        # Thống kê tổng hợp
        md_content.append("## 3. Thống kê tổng hợp")
        md_content.append("")
        
        if ac_cols:
            total_ac = self.processed_data[ac_cols].sum(axis=1)
            md_content.append(f"- **Công suất AC trung bình:** {total_ac.mean():.2f} kW")
            md_content.append(f"- **Công suất AC tối đa:** {total_ac.max():.2f} kW")
            md_content.append(f"- **Công suất AC tối thiểu:** {total_ac.min():.2f} kW")
            md_content.append("")
        
        if dc_cols:
            total_dc = self.processed_data[dc_cols].sum(axis=1)
            md_content.append(f"- **Công suất DC trung bình:** {total_dc.mean():.2f} kW")
            md_content.append(f"- **Công suất DC tối đa:** {total_dc.max():.2f} kW")
            md_content.append(f"- **Công suất DC tối thiểu:** {total_dc.min():.2f} kW")
            md_content.append("")
        
        if radiation_cols:
            radiation_data = self.processed_data[radiation_cols[0]].dropna()
            if len(radiation_data) > 0:
                md_content.append(f"- **Bức xạ mặt trời trung bình:** {radiation_data.mean():.2f} W/m²")
                md_content.append(f"- **Bức xạ mặt trời tối đa:** {radiation_data.max():.2f} W/m²")
                md_content.append("")
        
        # Top inverters
        if ac_cols:
            inv_avg_power = {}
            for col in ac_cols:
                data = self.processed_data[col].dropna()
                if len(data) > 0:
                    inv_avg_power[col] = data.mean()
            
            if inv_avg_power:
                sorted_inv = sorted(inv_avg_power.items(), key=lambda x: x[1], reverse=True)[:10]
                
                md_content.append("### Top 10 Inverter - Công suất AC trung bình")
                md_content.append("")
                md_content.append("| Inverter | Công suất trung bình (kW) |")
                md_content.append("|----------|---------------------------|")
                for inv, power in sorted_inv:
                    inv_name = str(inv).replace('_', ' ')[:40]
                    md_content.append(f"| {inv_name} | {power:,.2f} |")
                md_content.append("")
        
        # Biểu đồ
        md_content.append("## 4. Biểu đồ trực quan")
        md_content.append("")
        md_content.append("### 4.1. Công suất theo thời gian")
        md_content.append("")
        md_content.append("![Power Over Time](output/power_over_time.png)")
        md_content.append("")
        
        md_content.append("### 4.2. Bức xạ mặt trời và công suất")
        md_content.append("")
        md_content.append("![Radiation vs Power](output/radiation_vs_power.png)")
        md_content.append("")
        
        md_content.append("### 4.3. Top 10 Inverter")
        md_content.append("")
        md_content.append("![Top Inverters Power](output/top_inverters_power.png)")
        md_content.append("")
        
        md_content.append("### 4.4. Phân bố theo giờ trong ngày")
        md_content.append("")
        md_content.append("![Hourly Power Distribution](output/hourly_power_distribution.png)")
        md_content.append("")
        
        md_content.append("### 4.5. Heatmap: Công suất theo ngày và giờ")
        md_content.append("")
        md_content.append("![Daily Hourly Power Heatmap](output/daily_hourly_power_heatmap.png)")
        md_content.append("")
        
        md_content.append("### 4.6. So sánh AC vs DC Power")
        md_content.append("")
        md_content.append("![AC vs DC Power](output/ac_vs_dc_power.png)")
        md_content.append("")
        
        md_content.append("### 4.7. Hiệu suất hệ thống theo thời gian")
        md_content.append("")
        md_content.append("![Efficiency Over Time](output/efficiency_over_time.png)")
        md_content.append("")
        
        md_content.append("### 4.8. Top 15 Blocks - Công suất AC")
        md_content.append("")
        md_content.append("![Top Blocks Power](output/top_blocks_power.png)")
        md_content.append("")
        
        md_content.append("### 4.9. Tương quan giữa Bức xạ và Công suất")
        md_content.append("")
        md_content.append("![Radiation Correlation](output/radiation_correlation.png)")
        md_content.append("")
        
        md_content.append("### 4.10. So sánh công suất theo ngày")
        md_content.append("")
        md_content.append("![Daily Power Comparison](output/daily_power_comparison.png)")
        md_content.append("")
        
        md_content.append("### 4.11. Phân bố công suất theo giờ (Box Plot)")
        md_content.append("")
        md_content.append("![Hourly Power Boxplot](output/hourly_power_boxplot.png)")
        md_content.append("")
        
        md_content.append("### 4.12. Phân bố hiệu suất hệ thống")
        md_content.append("")
        md_content.append("![Efficiency Distribution](output/efficiency_distribution.png)")
        md_content.append("")
        
        # Phân tích hiệu suất
        if 'Total_Efficiency' in self.processed_data.columns:
            efficiency = self.processed_data['Total_Efficiency'].dropna()
            if len(efficiency) > 0:
                md_content.append("## 5. Phân tích Hiệu suất (Efficiency)")
                md_content.append("")
                md_content.append(f"- **Hiệu suất trung bình:** {efficiency.mean():.2f}%")
                md_content.append(f"- **Hiệu suất trung vị:** {efficiency.median():.2f}%")
                md_content.append(f"- **Hiệu suất tối đa:** {efficiency.max():.2f}%")
                md_content.append(f"- **Hiệu suất tối thiểu:** {efficiency.min():.2f}%")
                md_content.append(f"- **Độ lệch chuẩn:** {efficiency.std():.2f}%")
                md_content.append("")
        
        # Phân tích theo Block
        block_stats = self.analyze_by_block()
        if block_stats:
            md_content.append("## 6. Phân tích theo Block")
            md_content.append("")
            sorted_blocks = sorted(block_stats.items(), 
                                  key=lambda x: x[1].get('avg_ac_power', 0), 
                                  reverse=True)[:10]
            
            md_content.append("### Top 10 Blocks - Công suất AC trung bình")
            md_content.append("")
            md_content.append("| Block | Công suất AC TB (kW) | Công suất DC TB (kW) | Hiệu suất TB (%) | Số Inverter |")
            md_content.append("|-------|----------------------|----------------------|------------------|-------------|")
            for block_name, stats in sorted_blocks:
                block_display = str(block_name).replace('_', ' ')[:20]
                avg_ac = stats.get('avg_ac_power', 0)
                avg_dc = stats.get('avg_dc_power', 0)
                avg_eff = stats.get('avg_efficiency', 0)
                num_inv = stats.get('num_inverters', 0)
                md_content.append(f"| {block_display} | {avg_ac:,.2f} | {avg_dc:,.2f} | {avg_eff:.2f} | {num_inv} |")
            md_content.append("")
        
        # Tương quan
        correlations = self.calculate_correlations()
        if correlations:
            md_content.append("## 7. Phân tích Tương quan")
            md_content.append("")
            if 'radiation_vs_total_ac' in correlations:
                corr = correlations['radiation_vs_total_ac']
                md_content.append(f"- **Tương quan giữa Bức xạ và Công suất AC:** {corr:.4f}")
                if abs(corr) > 0.7:
                    md_content.append("  - Mối tương quan mạnh: Bức xạ mặt trời ảnh hưởng lớn đến công suất")
                elif abs(corr) > 0.4:
                    md_content.append("  - Mối tương quan trung bình")
                else:
                    md_content.append("  - Mối tương quan yếu")
            if 'total_ac_vs_total_dc' in correlations:
                corr = correlations['total_ac_vs_total_dc']
                md_content.append(f"- **Tương quan giữa Công suất AC và DC:** {corr:.4f}")
            md_content.append("")
        
        # Phát hiện bất thường
        anomalies = self.detect_anomalies()
        if anomalies:
            md_content.append("## 8. Phát hiện Bất thường")
            md_content.append("")
            if anomalies.get('negative_power'):
                md_content.append(f"- **Số bản ghi có công suất âm:** {len(anomalies['negative_power'])}")
            if anomalies.get('outliers'):
                md_content.append(f"- **Số bản ghi bất thường (outliers):** {len(anomalies['outliers'])}")
            if anomalies.get('zero_power'):
                md_content.append(f"- **Số bản ghi có công suất = 0 trong giờ cao điểm:** {len(anomalies['zero_power'])}")
            md_content.append("")
        
        # Phân tích theo ngày
        daily_stats = self.analyze_daily()
        if daily_stats:
            md_content.append("## 9. Phân tích theo Ngày")
            md_content.append("")
            sorted_days = sorted(daily_stats.items(), 
                                key=lambda x: x[1].get('avg_ac_power', 0), 
                                reverse=True)
            
            md_content.append("### Top 5 ngày có công suất cao nhất")
            md_content.append("")
            md_content.append("| Ngày | Công suất AC TB (kW) | Công suất AC Max (kW) | Bức xạ TB (W/m²) |")
            md_content.append("|------|---------------------|----------------------|------------------|")
            for date, stats in sorted_days[:5]:
                avg_ac = stats.get('avg_ac_power', 0)
                max_ac = stats.get('max_ac_power', 0)
                avg_rad = stats.get('avg_radiation', 0)
                md_content.append(f"| {date} | {avg_ac:,.2f} | {max_ac:,.2f} | {avg_rad:.2f} |")
            md_content.append("")
        
        # Thống kê chi tiết
        detailed_stats = self.calculate_detailed_stats()
        if detailed_stats:
            md_content.append("## 10. Thống kê Chi tiết")
            md_content.append("")
            if 'total_ac' in detailed_stats:
                stats = detailed_stats['total_ac']
                md_content.append("### Công suất AC")
                md_content.append("")
                md_content.append(f"- **Hệ số biến thiên (CV):** {stats.get('cv', 0):.2f}%")
                md_content.append(f"- **Phân vị 25% (Q25):** {stats.get('q25', 0):,.2f} kW")
                md_content.append(f"- **Phân vị 75% (Q75):** {stats.get('q75', 0):,.2f} kW")
                md_content.append(f"- **Phân vị 90% (Q90):** {stats.get('q90', 0):,.2f} kW")
                md_content.append(f"- **Phân vị 95% (Q95):** {stats.get('q95', 0):,.2f} kW")
                md_content.append(f"- **Phân vị 99% (Q99):** {stats.get('q99', 0):,.2f} kW")
                md_content.append(f"- **Độ lệch (Skewness):** {stats.get('skewness', 0):.2f}")
                md_content.append(f"- **Độ nhọn (Kurtosis):** {stats.get('kurtosis', 0):.2f}")
                md_content.append("")
        
        # Kết luận
        md_content.append("## 11. Kết luận")
        md_content.append("")
        md_content.append("Báo cáo này phân tích công suất AC/DC từ hệ thống điện mặt trời.")
        md_content.append("Các yếu tố quan trọng:")
        md_content.append("")
        md_content.append("- **Theo dõi công suất theo thời gian** để đánh giá hiệu suất")
        md_content.append("- **Phân tích mối quan hệ giữa bức xạ mặt trời và công suất** để tối ưu hóa")
        md_content.append("- **So sánh công suất AC và DC** để đánh giá hiệu suất bộ nghịch lưu")
        md_content.append("- **Phân tích theo giờ trong ngày** để xác định giờ cao điểm")
        md_content.append("- **So sánh hiệu suất giữa các inverter** để phát hiện vấn đề")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        md_content.append(f"*Báo cáo được tạo tự động bởi Power Reports Analyzer*")
        md_content.append("")
        
        # Ghi file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        print(f"  - Report saved to: {output_file}")
    
    def run_full_analysis(self):
        """Chạy phân tích đầy đủ"""
        print("=" * 70)
        print("POWER REPORTS ANALYSIS")
        print("=" * 70)
        
        # Load data
        self.load_data()
        
        # Analyze structure
        structure = self.analyze_structure()
        
        # Calculate statistics
        stats = self.calculate_statistics()
        
        # Calculate efficiency
        efficiency_data = self.calculate_efficiency()
        
        # Analyze by block
        block_stats = self.analyze_by_block()
        
        # Calculate correlations
        correlations = self.calculate_correlations()
        
        # Detect anomalies
        anomalies = self.detect_anomalies()
        
        # Analyze daily performance
        daily_stats = self.analyze_daily()
        
        # Calculate detailed statistics
        detailed_stats = self.calculate_detailed_stats()
        
        # Create visualizations
        self.create_visualizations()
        
        # Generate report
        self.generate_markdown_report()
        
        print("\n" + "=" * 70)
        print("Analysis Complete!")
        print("=" * 70)
        
        return {
            'processed_data': self.processed_data,
            'structure': structure,
            'statistics': stats,
            'efficiency': efficiency_data,
            'block_stats': block_stats,
            'correlations': correlations,
            'anomalies': anomalies,
            'daily_stats': daily_stats,
            'detailed_stats': detailed_stats
        }


def main():
    """Hàm chính"""
    excel_path = 'dataset/Power reports (1-15)102025.xls'
    
    analyzer = PowerReportsAnalyzer(excel_path)
    results = analyzer.run_full_analysis()
    
    return results


if __name__ == "__main__":
    results = main()

