"""
Parse APS/APU Log CSV File

Script này đọc file CSV log từ hệ thống APS/APU (Auxiliary Power System / Auxiliary Power Unit),
parse header nhiều dòng, tách dữ liệu theo từng nhóm log và lưu ra các file CSV riêng.

Cấu trúc file:
- Hàng 1: Log Type (APS Ctrl Trig, APS Energy, ...)
- Hàng 2: System (APS, APU, ...)
- Hàng 3: Column Headers (TimeStamp, Error1, W_in_APU1/kWh, ...)
- Từ hàng 4: Dữ liệu thực tế

Cấu trúc dữ liệu APS/APU:
- APS Ctrl Trig: Trạng thái điều khiển hệ thống APS (event-based)
- APS Energy: Năng lượng vào/ra của hệ thống APS (tích lũy)
- APS Stat 10s: Thông số tức thời mỗi 10 giây (bức xạ mặt trời)
- APS Stat 60s: Thông số môi trường mỗi phút (nhiệt độ, điện trở cách điện)
- APS Stat Trig: Trạng thái vận hành, lỗi và cảnh báo (event-based)
- APS Switching Cycles: Số chu kỳ đóng cắt AC/DC của các APU
- APU Ctrl Trig: Lệnh điều khiển đầu ra từng APU (event-based)
- APU Stat 10s: Thông số điện áp, dòng, công suất (10 giây)
- APU Stat 60s: Thông số nhiệt độ & độ ẩm (60 giây)
- APU Stat Trig: Trạng thái, giới hạn và lỗi (event-based)
- APU Energy: Dữ liệu năng lượng tích lũy từng kênh (tích lũy)
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class APSLogParser:
    """Parser cho file log APS/APU"""
    
    def __init__(self, csv_path):
        """Khởi tạo với đường dẫn file CSV"""
        self.csv_path = csv_path
        self.raw_df = None
        self.parsed_groups = {}
        self.output_dir = 'parsed_logs'
        
    def read_raw_data(self):
        """Đọc file CSV không có header để xử lý thủ công"""
        print(f"Reading CSV file: {self.csv_path}")
        
        # Đọc file không có header
        self.raw_df = pd.read_csv(self.csv_path, header=None, low_memory=False)
        
        print(f"File size: {self.raw_df.shape[0]} rows x {self.raw_df.shape[1]} columns")
        
        return self.raw_df
    
    def parse_headers(self):
        """Parse header và tách dữ liệu theo nhóm log"""
        print("\n=== Parsing Headers and Grouping Data ===")
        
        if self.raw_df is None:
            self.read_raw_data()
        
        # Tìm các hàng header (hàng 2-12 chứa định nghĩa log type và cột)
        log_type_headers = {}
        
        # Quét các hàng header (thường từ hàng 1-12)
        for idx in range(1, min(15, len(self.raw_df))):
            log_type = str(self.raw_df.iloc[idx, 0]).strip() if pd.notna(self.raw_df.iloc[idx, 0]) else ''
            
            # Bỏ qua hàng header chung
            if log_type in ['Log Type', 'nan', '']:
                continue
            
            # Kiểm tra xem có phải log type hợp lệ không
            valid_log_types = ['APS Ctrl Trig', 'APS Energy', 'APS Stat 10s', 'APS Stat 60s', 
                             'APS Stat Trig', 'APS Switching Cycles', 'APU Ctrl Trig', 
                             'APU Stat 10s', 'APU Stat 60s', 'APU Stat Trig', 'APU Energy']
            
            if any(valid_type in log_type for valid_type in valid_log_types):
                system = str(self.raw_df.iloc[idx, 1]).strip() if pd.notna(self.raw_df.iloc[idx, 1]) else ''
                
                # Hàng này chứa tên cột (bắt đầu từ cột 3)
                columns = []
                for col_idx in range(3, self.raw_df.shape[1]):
                    col_name = str(self.raw_df.iloc[idx, col_idx]).strip()
                    if col_name and col_name != 'nan' and col_name not in ['', 'Column Header...']:
                        columns.append({
                            'index': col_idx,
                            'name': col_name
                        })
                
                if columns:
                    # Tạo key duy nhất cho mỗi log type
                    base_key = f"{log_type}_{system}".replace(' ', '_').replace('/', '_')
                    group_key = base_key
                    counter = 1
                    while group_key in log_type_headers:
                        group_key = f"{base_key}_{counter}"
                        counter += 1
                    
                    log_type_headers[group_key] = {
                        'log_type': log_type,
                        'system': system,
                        'header_row': idx,
                        'columns': columns
                    }
        
        print(f"Found {len(log_type_headers)} log type headers:")
        for key, info in log_type_headers.items():
            print(f"  - {key}: {len(info['columns'])} columns")
        
        return log_type_headers
    
    def extract_group_data(self, log_type_headers):
        """Trích xuất dữ liệu cho từng nhóm log"""
        print("\n=== Extracting Group Data ===")
        
        # Tìm tất cả các hàng dữ liệu (bắt đầu từ hàng 13, sau các header)
        data_start_row = 13  # Dữ liệu thực tế bắt đầu từ hàng 13
        
        # Nhóm dữ liệu theo log type
        grouped_data = {}
        
        for idx in range(data_start_row, len(self.raw_df)):
            row_log_type = str(self.raw_df.iloc[idx, 0]).strip() if pd.notna(self.raw_df.iloc[idx, 0]) else ''
            row_system = str(self.raw_df.iloc[idx, 1]).strip() if pd.notna(self.raw_df.iloc[idx, 1]) else ''
            
            # Tìm header tương ứng
            matching_header = None
            for header_key, header_info in log_type_headers.items():
                if header_info['log_type'] == row_log_type and header_info['system'] == row_system:
                    matching_header = header_key
                    break
            
            if matching_header:
                if matching_header not in grouped_data:
                    grouped_data[matching_header] = []
                
                # Trích xuất dữ liệu từ hàng này
                row_data = {}
                for col_info in log_type_headers[matching_header]['columns']:
                    col_idx = col_info['index']
                    col_name = col_info['name']
                    row_data[col_name] = self.raw_df.iloc[idx, col_idx]
                
                grouped_data[matching_header].append(row_data)
        
        # Chuyển đổi thành DataFrame cho mỗi nhóm
        for group_key, rows in grouped_data.items():
            print(f"\nProcessing: {group_key}")
            
            if not rows:
                print(f"  Warning: No data found for {group_key}")
                continue
            
            # Tạo DataFrame
            group_data = pd.DataFrame(rows)
            
            # Xử lý TimeStamp
            timestamp_col = None
            for col in group_data.columns:
                if 'TimeStamp' in str(col) or 'Date Time' in str(col) or 'Time' in str(col):
                    timestamp_col = col
                    break
            
            if timestamp_col:
                # Parse timestamp
                group_data[timestamp_col] = pd.to_datetime(
                    group_data[timestamp_col],
                    format='%d/%m/%Y %H:%M',
                    errors='coerce'
                )
                # Loại bỏ hàng không có timestamp hợp lệ
                group_data = group_data[group_data[timestamp_col].notna()].copy()
                # Sắp xếp theo thời gian
                if len(group_data) > 0:
                    group_data = group_data.sort_values(by=timestamp_col).reset_index(drop=True)
            
            # Chuyển đổi các cột số thành numeric
            for col in group_data.columns:
                if col != timestamp_col:
                    try:
                        group_data[col] = pd.to_numeric(group_data[col], errors='coerce')
                    except:
                        pass
            
            # Lưu vào dictionary
            if len(group_data) > 0:
                self.parsed_groups[group_key] = group_data
                print(f"  Extracted {len(group_data)} records")
                if timestamp_col:
                    print(f"  Time range: {group_data[timestamp_col].min()} to {group_data[timestamp_col].max()}")
            else:
                print(f"  Warning: No valid data extracted for {group_key}")
        
        return self.parsed_groups
    
    def save_parsed_logs(self):
        """Lưu các nhóm log đã parse ra file CSV riêng"""
        print(f"\n=== Saving Parsed Logs ===")
        
        # Tạo thư mục output
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Output directory: {self.output_dir}")
        
        # Mapping tên file thân thiện với mô tả
        file_name_mapping = {
            'APS_Ctrl_Trig_APS': 'APS_CtrlTrig',  # Trạng thái điều khiển hệ thống APS
            'APS_Energy_APS': 'APS_Energy',  # Năng lượng vào/ra của hệ thống APS
            'APS_Stat_10s_APS': 'APS_Stat10s',  # Thông số tức thời mỗi 10 giây
            'APS_Stat_60s_APS': 'APS_Stat60s',  # Thông số môi trường mỗi phút
            'APS_Stat_Trig_APS': 'APS_StatTrig',  # Trạng thái vận hành, lỗi và cảnh báo
            'APS_Switching_Cycles_APS': 'APS_SwitchingCycles',  # Số chu kỳ đóng cắt AC/DC
            'APU_Ctrl_Trig_APU': 'APU_CtrlTrig',  # Lệnh điều khiển đầu ra từng APU
            'APU_Stat_10s_APU': 'APU_Stat10s',  # Thông số điện áp, dòng, công suất (10s)
            'APU_Stat_60s_APU': 'APU_Stat60s',  # Thông số nhiệt độ & độ ẩm (60s)
            'APU_Stat_Trig_APU': 'APU_StatTrig',  # Trạng thái, giới hạn và lỗi
            'APU_Energy_APU': 'APU_Energy',  # Dữ liệu năng lượng tích lũy từng kênh
        }
        
        saved_files = []
        
        for group_key, group_data in self.parsed_groups.items():
            # Tạo tên file (loại bỏ ký tự đặc biệt)
            # Tìm mapping tốt nhất (có thể có suffix _1, _2 cho cùng log type)
            file_name = file_name_mapping.get(group_key, None)
            if not file_name:
                # Thử tìm base key (bỏ suffix số)
                base_key = '_'.join(group_key.split('_')[:-1]) if group_key.split('_')[-1].isdigit() else group_key
                file_name = file_name_mapping.get(base_key, group_key)
            
            # Làm sạch tên file
            file_name = file_name.replace('/', '_').replace('\\', '_').replace(':', '_')
            file_path = os.path.join(self.output_dir, f"{file_name}.csv")
            
            # Lưu file
            group_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            saved_files.append(file_path)
            
            print(f"  Saved: {file_path} ({len(group_data)} records, {len(group_data.columns)} columns)")
        
        print(f"\nTotal files saved: {len(saved_files)}")
        return saved_files
    
    def generate_summary_report(self):
        """Tạo báo cáo tóm tắt với mô tả chi tiết"""
        print(f"\n=== Generating Summary Report ===")
        
        # Mapping tên file (giống như trong save_parsed_logs)
        file_name_mapping = {
            'APS_Ctrl_Trig_APS': 'APS_CtrlTrig',
            'APS_Energy_APS': 'APS_Energy',
            'APS_Stat_10s_APS': 'APS_Stat10s',
            'APS_Stat_60s_APS': 'APS_Stat60s',
            'APS_Stat_Trig_APS': 'APS_StatTrig',
            'APS_Switching_Cycles_APS': 'APS_SwitchingCycles',
            'APU_Ctrl_Trig_APU': 'APU_CtrlTrig',
            'APU_Stat_10s_APU': 'APU_Stat10s',
            'APU_Stat_60s_APU': 'APU_Stat60s',
            'APU_Stat_Trig_APU': 'APU_StatTrig',
            'APU_Energy_APU': 'APU_Energy',
        }
        
        # Mô tả các nhóm dữ liệu
        group_descriptions = {
            'APS_CtrlTrig': {
                'name': 'APS Ctrl Trig',
                'description': 'Trạng thái điều khiển hệ thống APS (event-based)',
                'key_fields': ['Milliseconds/ms', 'AirAir1State', 'ApuCtrl1On', 'EnableOn', 'HeatingOn']
            },
            'APS_Energy': {
                'name': 'APS Energy',
                'description': 'Năng lượng vào/ra của hệ thống APS (tích lũy)',
                'key_fields': ['W_in_APU1/kWh', 'W_out_APU1/kWh', 'W_in_APS/kWh', 'W_out_APS/kWh']
            },
            'APS_Stat10s': {
                'name': 'APS Stat 10s',
                'description': 'Thông số tức thời mỗi 10 giây (bức xạ mặt trời)',
                'key_fields': ['Irr/(W/m^2)']
            },
            'APS_Stat60s': {
                'name': 'APS Stat 60s',
                'description': 'Thông số môi trường mỗi phút (nhiệt độ, điện trở cách điện)',
                'key_fields': ['Tamb/°C', 'Tpan/°C', 'Ttrans/°C', 'Riso12/k', 'Riso34/kO']
            },
            'APS_StatTrig': {
                'name': 'APS Stat Trig',
                'description': 'Trạng thái vận hành, lỗi và cảnh báo (event-based)',
                'key_fields': ['OpState', 'Error1', 'Error2', 'Warning1', 'Warning2']
            },
            'APS_SwitchingCycles': {
                'name': 'APS Switching Cycles',
                'description': 'Số chu kỳ đóng cắt AC/DC của các APU',
                'key_fields': ['APU1_AC', 'APU1_DC', 'APU2_AC', 'APU2_DC']
            },
            'APU_CtrlTrig': {
                'name': 'APU Ctrl Trig',
                'description': 'Lệnh điều khiển đầu ra từng APU (event-based)',
                'key_fields': ['PSetL1/kW', 'QSetL1/kvar', 'VislSet/V', 'fislSet/Hz', 'OpMode']
            },
            'APU_Stat10s': {
                'name': 'APU Stat 10s',
                'description': 'Thông số điện áp, dòng, công suất (10 giây)',
                'key_fields': ['VL1N/V', 'IL1/A', 'PL1/kW', 'Vdc/V', 'Pdc/kW']
            },
            'APU_Stat60s': {
                'name': 'APU Stat 60s',
                'description': 'Thông số nhiệt độ & độ ẩm (60 giây)',
                'key_fields': ['TInd/°C', 'TL1/°C', 'TPCB/°C', 'Hum/%RH']
            },
            'APU_StatTrig': {
                'name': 'APU Stat Trig',
                'description': 'Trạng thái, giới hạn và lỗi (event-based)',
                'key_fields': ['OpState', 'PL1Lim/kW', 'Error1', 'Error2']
            },
            'APU_Energy': {
                'name': 'APU Energy',
                'description': 'Dữ liệu năng lượng tích lũy từng kênh (tích lũy)',
                'key_fields': ['CH 1 pos/Ah', 'CH 1 neg/Ah', 'CH 2 pos/Ah', 'CH 2 neg/Ah']
            }
        }
        
        summary = []
        summary.append("# APS/APU Log Parsing Summary")
        summary.append("")
        summary.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"**Source File:** `{self.csv_path}`")
        summary.append("")
        summary.append("---")
        summary.append("")
        summary.append("## Parsed Log Groups")
        summary.append("")
        
        for group_key, group_data in self.parsed_groups.items():
            # Tìm tên file tương ứng
            file_name = None
            for key, name in file_name_mapping.items():
                if key.startswith(group_key.split('_')[0] + '_'):
                    file_name = name
                    break
            
            if not file_name:
                # Tạo tên từ group_key
                file_name = group_key.replace('_APS', '').replace('_APU', '').replace('_', '')
            
            # Lấy mô tả (tìm base name nếu có suffix)
            base_file_name = file_name.split('_')[0] + '_' + file_name.split('_')[1] if '_' in file_name else file_name
            desc = group_descriptions.get(file_name, group_descriptions.get(base_file_name, {
                'name': group_key,
                'description': 'Log data group',
                'key_fields': []
            }))
            
            summary.append(f"### {desc['name']}")
            summary.append("")
            summary.append(f"**Mô tả:** {desc['description']}")
            summary.append("")
            summary.append(f"- **Records:** {len(group_data):,}")
            summary.append(f"- **Columns:** {len(group_data.columns)}")
            
            # Tìm timestamp column
            timestamp_col = None
            for col in group_data.columns:
                if 'TimeStamp' in str(col) or 'Date Time' in str(col):
                    timestamp_col = col
                    break
            
            if timestamp_col:
                summary.append(f"- **Time Range:** {group_data[timestamp_col].min()} to {group_data[timestamp_col].max()}")
            
            # Liệt kê các cột quan trọng
            if desc['key_fields']:
                available_fields = [f for f in desc['key_fields'] if f in group_data.columns]
                if available_fields:
                    summary.append(f"- **Key Fields:** {', '.join(available_fields[:5])}{'...' if len(available_fields) > 5 else ''}")
            
            # Thống kê lỗi nếu có
            error_cols = [col for col in group_data.columns if 'Error' in str(col)]
            warning_cols = [col for col in group_data.columns if 'Warning' in str(col)]
            
            if error_cols:
                total_errors = group_data[error_cols].sum().sum()
                summary.append(f"- **Total Errors:** {int(total_errors)}")
            
            if warning_cols:
                total_warnings = group_data[warning_cols].sum().sum()
                summary.append(f"- **Total Warnings:** {int(total_warnings)}")
            
            summary.append("")
        
        summary.append("---")
        summary.append("")
        summary.append("## Data Structure Overview")
        summary.append("")
        summary.append("### Log Types by Sampling Rate:")
        summary.append("")
        summary.append("| Type | Sampling Rate | Purpose |")
        summary.append("|------|---------------|---------|")
        summary.append("| Ctrl Trig | Event-based | Lệnh điều khiển, trạng thái thiết bị |")
        summary.append("| Stat 10s | 10 seconds | Thông số điện, vật lý |")
        summary.append("| Stat 60s | 60 seconds | Nhiệt độ, môi trường |")
        summary.append("| Energy | Cumulative | Năng lượng tiêu thụ / sản sinh |")
        summary.append("| Switching | Event count | Chu kỳ đóng cắt |")
        summary.append("| Stat Trig | Event-based | Lỗi, cảnh báo, giới hạn |")
        summary.append("")
        
        summary.append("---")
        summary.append("")
        summary.append("## Usage")
        summary.append("")
        summary.append("Các file CSV đã được lưu trong thư mục `parsed_logs/`.")
        summary.append("Bạn có thể sử dụng chúng để:")
        summary.append("")
        summary.append("- **Vẽ biểu đồ công suất, nhiệt độ, dòng, áp** từ APU Stat 10s")
        summary.append("- **Phát hiện lỗi theo thời gian** (Error1–8, Warning1–8) từ APS/APU Stat Trig")
        summary.append("- **Tính hiệu suất nạp/xả APU** từ APU Energy (CH x pos/Ah, CH x neg/Ah)")
        summary.append("- **Đồng bộ dữ liệu thời gian** giữa APS và APU để phân tích tương quan")
        summary.append("- **Phân tích môi trường** (nhiệt độ, độ ẩm, bức xạ) từ APS Stat 60s")
        summary.append("- **Theo dõi chu kỳ đóng cắt** từ APS Switching Cycles để đánh giá tuổi thọ thiết bị")
        summary.append("")
        
        # Ghi file summary
        summary_path = os.path.join(self.output_dir, 'SUMMARY.md')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary))
        
        print(f"  Summary report saved: {summary_path}")
        
        return summary_path
    
    def run_full_parse(self):
        """Chạy toàn bộ quá trình parse"""
        print("=" * 70)
        print("APS/APU LOG PARSER")
        print("=" * 70)
        
        # Đọc dữ liệu
        self.read_raw_data()
        
        # Parse headers và nhóm dữ liệu
        log_types = self.parse_headers()
        
        # Trích xuất dữ liệu cho từng nhóm
        self.extract_group_data(log_types)
        
        # Lưu các file CSV
        saved_files = self.save_parsed_logs()
        
        # Tạo báo cáo tóm tắt
        summary_path = self.generate_summary_report()
        
        print("\n" + "=" * 70)
        print("Parsing Complete!")
        print("=" * 70)
        print(f"\nOutput directory: {self.output_dir}/")
        print(f"Files created: {len(saved_files)}")
        print(f"Summary report: {summary_path}")
        
        return {
            'parsed_groups': self.parsed_groups,
            'saved_files': saved_files,
            'summary_path': summary_path
        }


def main():
    """Hàm chính"""
    csv_path = 'dataset/APS-000258_20251001_000000.csv'
    
    parser = APSLogParser(csv_path)
    results = parser.run_full_parse()
    
    return results


if __name__ == "__main__":
    results = main()

