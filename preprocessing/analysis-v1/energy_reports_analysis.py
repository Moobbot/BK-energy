"""
Energy Reports Analysis

Phân tích báo cáo năng lượng từ file Excel "Energy reports 01102025 - 27102025.xls"
Bao gồm phân tích năng lượng theo thời gian, theo block/inverter, và các thống kê.
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

class EnergyReportsAnalyzer:
    """Phân tích báo cáo năng lượng"""
    
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
            if df.iloc[idx, 1] == 'Date Time' or 'Date Time' in str(df.iloc[idx, 1]):
                date_time_row = idx
                break
        
        if date_time_row is None:
            print("Cannot find 'Date Time' row, trying row 3...")
            date_time_row = 3
        
        print(f"Header row: {date_time_row}")
        
        # Lấy header từ hàng date_time_row và hàng tiếp theo
        header_row1 = df.iloc[date_time_row].values  # Hàng chứa "Date Time" và block names
        header_row2 = df.iloc[date_time_row + 1].values  # Hàng chứa inverter names
        
        # Tạo tên cột hợp lý
        column_names = []
        for i in range(len(header_row1)):
            col1 = str(header_row1[i]) if pd.notna(header_row1[i]) else ''
            col2 = str(header_row2[i]) if pd.notna(header_row2[i]) else ''
            
            if col1 == 'Date Time' or 'Date Time' in col1:
                column_names.append('DateTime')
            elif col1 and col1 != 'nan':
                # Có block name
                if col2 and col2 != 'nan':
                    column_names.append(f"{col1}_{col2}")
                else:
                    column_names.append(col1)
            elif col2 and col2 != 'nan':
                column_names.append(col2)
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
            data_df['DateTime'] = pd.to_datetime(data_df['DateTime'], format='%d/%m/%Y %H:%M', errors='coerce')
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
        inv_cols = [col for col in numeric_cols if 'INV' in str(col).upper() or 'INV' in str(col)]
        block_cols = [col for col in numeric_cols if 'BLOCK' in str(col).upper()]
        other_cols = [col for col in numeric_cols if col not in inv_cols and col not in block_cols]
        
        print(f"\nData columns:")
        print(f"  - Inverter columns: {len(inv_cols)}")
        print(f"  - Block columns: {len(block_cols)}")
        print(f"  - Other columns: {len(other_cols)}")
        
        if inv_cols:
            print(f"\nInverters: {inv_cols[:10]}{'...' if len(inv_cols) > 10 else ''}")
        
        return {
            'inverter_cols': inv_cols,
            'block_cols': block_cols,
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
    
    def calculate_energy_differences(self):
        """Tính toán sự thay đổi năng lượng (năng lượng sản xuất)"""
        print("\n=== Calculating Energy Production ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        
        # Tính sự thay đổi năng lượng (diff) cho mỗi cột
        energy_production = self.processed_data.copy()
        
        for col in numeric_cols:
            # Tính diff (năng lượng sản xuất trong khoảng thời gian)
            energy_production[f'{col}_diff'] = self.processed_data[col].diff()
            # Tính tổng tích lũy
            energy_production[f'{col}_cumsum'] = energy_production[f'{col}_diff'].fillna(0).cumsum()
        
        return energy_production
    
    def create_visualizations(self, output_dir='output'):
        """Tạo các biểu đồ trực quan"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n=== Creating Visualizations ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        inv_cols = [col for col in numeric_cols if 'INV' in str(col).upper()]
        
        # 1. Biểu đồ năng lượng theo thời gian (tổng hợp)
        if 'DateTime' in self.processed_data.columns and len(numeric_cols) > 0:
            plt.figure(figsize=(16, 8))
            
            # Tính tổng năng lượng cho mỗi thời điểm
            total_energy = self.processed_data[numeric_cols].sum(axis=1)
            
            plt.plot(self.processed_data['DateTime'], total_energy, linewidth=1.5, alpha=0.8)
            plt.title('Total Energy Over Time', fontsize=16, fontweight='bold')
            plt.xlabel('Time', fontsize=12)
            plt.ylabel('Energy (MWh)', fontsize=12)
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/energy_over_time.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: energy_over_time.png")
        
        # 2. Biểu đồ năng lượng theo từng inverter (top 10)
        if inv_cols:
            # Tính tổng năng lượng cho mỗi inverter
            inv_totals = {}
            for col in inv_cols[:20]:  # Giới hạn 20 inverter đầu
                data = self.processed_data[col].dropna()
                if len(data) > 0:
                    # Tính diff và tổng
                    diff = data.diff().fillna(0)
                    inv_totals[col] = diff.sum()
            
            if inv_totals:
                # Sắp xếp và lấy top 10
                sorted_inv = sorted(inv_totals.items(), key=lambda x: x[1], reverse=True)[:10]
                
                plt.figure(figsize=(14, 8))
                inv_names = [str(k).replace('_', ' ')[:30] for k, v in sorted_inv]
                inv_values = [v for k, v in sorted_inv]
                
                plt.barh(inv_names, inv_values, color='steelblue', alpha=0.8)
                plt.title('Top 10 Inverters - Total Energy Production', fontsize=16, fontweight='bold')
                plt.xlabel('Energy (MWh)', fontsize=12)
                plt.ylabel('Inverter', fontsize=12)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/top_inverters.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  - Saved: top_inverters.png")
        
        # 3. Biểu đồ phân bố năng lượng theo giờ trong ngày
        if 'DateTime' in self.processed_data.columns and len(numeric_cols) > 0:
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            hourly_energy = self.processed_data.groupby('Hour')[numeric_cols].sum().sum(axis=1)
            
            plt.figure(figsize=(12, 6))
            plt.bar(hourly_energy.index, hourly_energy.values, color='coral', alpha=0.8)
            plt.title('Energy Distribution by Hour of Day', fontsize=16, fontweight='bold')
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Energy (MWh)', fontsize=12)
            plt.xticks(range(24))
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/hourly_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: hourly_distribution.png")
        
        # 4. Heatmap năng lượng theo ngày và giờ
        if 'DateTime' in self.processed_data.columns and len(numeric_cols) > 0:
            self.processed_data['Date'] = self.processed_data['DateTime'].dt.date
            self.processed_data['Hour'] = self.processed_data['DateTime'].dt.hour
            
            # Tính tổng năng lượng theo ngày và giờ
            daily_hourly = self.processed_data.groupby(['Date', 'Hour'])[numeric_cols].sum().sum(axis=1).reset_index()
            daily_hourly.columns = ['Date', 'Hour', 'Energy']
            
            # Tạo pivot table
            pivot_table = daily_hourly.pivot(index='Date', columns='Hour', values='Energy')
            
            plt.figure(figsize=(16, max(8, len(pivot_table) * 0.3)))
            sns.heatmap(pivot_table, annot=False, fmt='.0f', cmap='YlOrRd', cbar_kws={'label': 'Energy (MWh)'})
            plt.title('Heatmap: Energy by Date and Hour', fontsize=16, fontweight='bold')
            plt.xlabel('Hour of Day', fontsize=12)
            plt.ylabel('Date', fontsize=12)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/daily_hourly_heatmap.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  - Saved: daily_hourly_heatmap.png")
        
        print(f"\nAll visualizations saved to '{output_dir}' directory")
    
    def generate_markdown_report(self, output_file='energy_reports_analysis.md'):
        """Tạo báo cáo markdown"""
        print(f"\n=== Generating Markdown Report ===")
        
        if self.processed_data is None:
            print("No data available!")
            return
        
        md_content = []
        md_content.append("# Energy Reports Analysis")
        md_content.append("")
        md_content.append("## Phân tích báo cáo năng lượng")
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
        md_content.append(f"- **Khoảng thời gian:** {self.processed_data['DateTime'].min()} đến {self.processed_data['DateTime'].max()}")
        md_content.append(f"- **Số cột dữ liệu:** {len(self.processed_data.columns)}")
        md_content.append("")
        
        # Phân tích cấu trúc
        structure = self.analyze_structure()
        md_content.append("## 2. Cấu trúc dữ liệu")
        md_content.append("")
        md_content.append(f"- **Số cột Inverter:** {len(structure['inverter_cols'])}")
        md_content.append(f"- **Số cột Block:** {len(structure['block_cols'])}")
        md_content.append(f"- **Số cột khác:** {len(structure['other_cols'])}")
        md_content.append("")
        
        # Thống kê
        if self.summary_stats is None:
            self.calculate_statistics()
        
        numeric_cols = self.processed_data.select_dtypes(include=[np.number]).columns.tolist()
        inv_cols = [col for col in numeric_cols if 'INV' in str(col).upper()]
        
        # Tính tổng năng lượng sản xuất
        total_production = 0
        for col in numeric_cols:
            data = self.processed_data[col].dropna()
            if len(data) > 1:
                diff = data.diff().fillna(0)
                total_production += diff.sum()
        
        md_content.append("## 3. Thống kê tổng hợp")
        md_content.append("")
        md_content.append(f"- **Tổng năng lượng sản xuất:** {total_production:,.2f} MWh")
        md_content.append("")
        
        # Top inverters
        if inv_cols:
            inv_totals = {}
            for col in inv_cols:
                data = self.processed_data[col].dropna()
                if len(data) > 1:
                    diff = data.diff().fillna(0)
                    inv_totals[col] = diff.sum()
            
            if inv_totals:
                sorted_inv = sorted(inv_totals.items(), key=lambda x: x[1], reverse=True)[:10]
                
                md_content.append("### Top 10 Inverter - Năng lượng sản xuất")
                md_content.append("")
                md_content.append("| Inverter | Năng lượng (MWh) |")
                md_content.append("|----------|------------------|")
                for inv, energy in sorted_inv:
                    inv_name = str(inv).replace('_', ' ')[:40]
                    md_content.append(f"| {inv_name} | {energy:,.2f} |")
                md_content.append("")
        
        # Biểu đồ
        md_content.append("## 4. Biểu đồ trực quan")
        md_content.append("")
        md_content.append("### 4.1. Năng lượng theo thời gian")
        md_content.append("")
        md_content.append("![Energy Over Time](output/energy_over_time.png)")
        md_content.append("")
        
        md_content.append("### 4.2. Top 10 Inverter")
        md_content.append("")
        md_content.append("![Top Inverters](output/top_inverters.png)")
        md_content.append("")
        
        md_content.append("### 4.3. Phân bố theo giờ trong ngày")
        md_content.append("")
        md_content.append("![Hourly Distribution](output/hourly_distribution.png)")
        md_content.append("")
        
        md_content.append("### 4.4. Heatmap: Năng lượng theo ngày và giờ")
        md_content.append("")
        md_content.append("![Daily Hourly Heatmap](output/daily_hourly_heatmap.png)")
        md_content.append("")
        
        # Kết luận
        md_content.append("## 5. Kết luận")
        md_content.append("")
        md_content.append("Báo cáo này phân tích năng lượng sản xuất từ hệ thống điện mặt trời.")
        md_content.append("Các yếu tố quan trọng:")
        md_content.append("")
        md_content.append("- **Theo dõi năng lượng theo thời gian** để đánh giá hiệu suất")
        md_content.append("- **So sánh hiệu suất giữa các inverter** để phát hiện vấn đề")
        md_content.append("- **Phân tích theo giờ trong ngày** để tối ưu hóa sản xuất")
        md_content.append("- **Theo dõi xu hướng theo ngày** để dự đoán và lập kế hoạch")
        md_content.append("")
        md_content.append("---")
        md_content.append("")
        md_content.append(f"*Báo cáo được tạo tự động bởi Energy Reports Analyzer*")
        md_content.append("")
        
        # Ghi file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))
        
        print(f"  - Report saved to: {output_file}")
    
    def run_full_analysis(self):
        """Chạy phân tích đầy đủ"""
        print("=" * 70)
        print("ENERGY REPORTS ANALYSIS")
        print("=" * 70)
        
        # Load data
        self.load_data()
        
        # Analyze structure
        structure = self.analyze_structure()
        
        # Calculate statistics
        stats = self.calculate_statistics()
        
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
            'statistics': stats
        }


def main():
    """Hàm chính"""
    excel_path = 'dataset/Energy reports 01102025 - 27102025.xls'
    
    analyzer = EnergyReportsAnalyzer(excel_path)
    results = analyzer.run_full_analysis()
    
    return results


if __name__ == "__main__":
    results = main()

