"""
Data Loaders Module
Module để load dữ liệu từ các nguồn khác nhau
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Optional
import warnings

warnings.filterwarnings('ignore')


class PVForecastLoader:
    """Loader cho file PV Forecast CSV"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def load(self) -> pd.DataFrame:
        """Load và parse file PV Forecast"""
        print(f"Loading PV Forecast from {self.file_path}...")
        
        df = pd.read_csv(self.file_path, sep='\t')
        
        # Tạo datetime từ Date và Time
        df['DateTime'] = pd.to_datetime(
            df['Date'] + ' ' + df['Time'],
            format='%d/%m/%Y %H:%M',
            errors='coerce'
        )
        
        # Sắp xếp theo thời gian
        df = df.sort_values('DateTime').reset_index(drop=True)
        
        # Đổi tên cột Power (MW) thành Power_MW
        if 'Power (MW)' in df.columns:
            df = df.rename(columns={'Power (MW)': 'Power_MW'})
        
        print(f"Loaded {len(df)} records from PV Forecast")
        return df[['DateTime', 'Power_MW']]


class PowerReportsLoader:
    """Loader cho file Power Reports Excel"""
    
    def __init__(self, file_paths: List[str]):
        self.file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        
    def load(self) -> pd.DataFrame:
        """Load và parse file Power Reports"""
        print(f"Loading Power Reports from {len(self.file_paths)} file(s)...")
        
        all_dfs = []
        
        for file_path in self.file_paths:
            print(f"  Processing {os.path.basename(file_path)}...")
            
            # Đọc file Excel
            df = pd.read_excel(file_path, header=None, engine='openpyxl')
            
            # Tìm hàng chứa DateTime
            date_time_row = None
            for idx in range(min(20, len(df))):
                row_str = ' '.join([str(x) for x in df.iloc[idx].values if pd.notna(x)])
                if 'DateTime' in row_str or 'Date' in row_str:
                    date_time_row = idx
                    break
            
            if date_time_row is None:
                print(f"  Warning: Could not find DateTime header in {file_path}")
                continue
            
            # Lấy tên cột từ hàng header
            column_names = []
            for col_idx in range(df.shape[1]):
                col_name = df.iloc[date_time_row, col_idx]
                if pd.notna(col_name) and str(col_name).strip():
                    column_names.append(str(col_name).strip())
                else:
                    column_names.append(f'Column_{col_idx}')
            
            # Lấy dữ liệu từ hàng sau header
            data_start_row = date_time_row + 2
            data_df = df.iloc[data_start_row:].copy()
            data_df.columns = column_names[:len(data_df.columns)]
            
            # Reset index
            data_df = data_df.reset_index(drop=True)
            
            # Parse DateTime
            datetime_col = None
            for col in ['DateTime', 'Date', 'Time']:
                if col in data_df.columns:
                    datetime_col = col
                    break
            
            if datetime_col:
                data_df['DateTime'] = pd.to_datetime(
                    data_df[datetime_col],
                    format='%d/%m/%Y %H:%M',
                    errors='coerce'
                )
                data_df = data_df[data_df['DateTime'].notna()].copy()
            
            # Chuyển đổi các cột số thành numeric
            for col in data_df.columns:
                if col != 'DateTime' and col in data_df.columns:
                    try:
                        data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
                    except (TypeError, ValueError):
                        pass
            
            all_dfs.append(data_df)
        
        # Gộp tất cả các dataframe
        if all_dfs:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            combined_df = combined_df.sort_values('DateTime').reset_index(drop=True)
            print(f"Loaded {len(combined_df)} records from Power Reports")
            return combined_df
        else:
            return pd.DataFrame()


class WeatherReportsLoader:
    """Loader cho file Weather Reports Excel"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def load(self) -> pd.DataFrame:
        """Load và parse file Weather Reports"""
        print(f"Loading Weather Reports from {self.file_path}...")
        
        # Đọc file Excel
        df = pd.read_excel(self.file_path, header=None, engine='openpyxl')
        
        # Tìm hàng chứa DateTime
        date_time_row = None
        for idx in range(min(20, len(df))):
            row_str = ' '.join([str(x) for x in df.iloc[idx].values if pd.notna(x)])
            if 'DateTime' in row_str or 'Date' in row_str:
                date_time_row = idx
                break
        
        if date_time_row is None:
            print("Warning: Could not find DateTime header")
            return pd.DataFrame()
        
        # Lấy tên cột từ hàng header
        column_names = []
        for col_idx in range(df.shape[1]):
            col_name = df.iloc[date_time_row, col_idx]
            if pd.notna(col_name) and str(col_name).strip():
                column_names.append(str(col_name).strip())
            else:
                column_names.append(f'Column_{col_idx}')
        
        # Lấy dữ liệu từ hàng sau header
        data_start_row = date_time_row + 2
        data_df = df.iloc[data_start_row:].copy()
        data_df.columns = column_names[:len(data_df.columns)]
        
        # Reset index
        data_df = data_df.reset_index(drop=True)
        
        # Parse DateTime
        datetime_col = None
        for col in ['DateTime', 'Date', 'Time']:
            if col in data_df.columns:
                datetime_col = col
                break
        
        if datetime_col:
            data_df['DateTime'] = pd.to_datetime(
                data_df[datetime_col],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            data_df = data_df[data_df['DateTime'].notna()].copy()
        
        # Chuyển đổi các cột số thành numeric
        for col in data_df.columns:
            if col != 'DateTime' and col in data_df.columns:
                try:
                    data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
                except (TypeError, ValueError):
                    pass
        
        print(f"Loaded {len(data_df)} records from Weather Reports")
        return data_df


class EnergyReportsLoader:
    """Loader cho file Energy Reports Excel"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def load(self) -> pd.DataFrame:
        """Load và parse file Energy Reports"""
        print(f"Loading Energy Reports from {self.file_path}...")
        
        # Đọc file Excel
        df = pd.read_excel(self.file_path, header=None, engine='openpyxl')
        
        # Tìm hàng chứa DateTime
        date_time_row = None
        for idx in range(min(20, len(df))):
            row_str = ' '.join([str(x) for x in df.iloc[idx].values if pd.notna(x)])
            if 'DateTime' in row_str or 'Date' in row_str:
                date_time_row = idx
                break
        
        if date_time_row is None:
            print("Warning: Could not find DateTime header")
            return pd.DataFrame()
        
        # Lấy tên cột từ hàng header
        column_names = []
        for col_idx in range(df.shape[1]):
            col_name = df.iloc[date_time_row, col_idx]
            if pd.notna(col_name) and str(col_name).strip():
                column_names.append(str(col_name).strip())
            else:
                column_names.append(f'Column_{col_idx}')
        
        # Lấy dữ liệu từ hàng sau header
        data_start_row = date_time_row + 2
        data_df = df.iloc[data_start_row:].copy()
        data_df.columns = column_names[:len(data_df.columns)]
        
        # Reset index
        data_df = data_df.reset_index(drop=True)
        
        # Parse DateTime
        datetime_col = None
        for col in ['DateTime', 'Date', 'Time']:
            if col in data_df.columns:
                datetime_col = col
                break
        
        if datetime_col:
            data_df['DateTime'] = pd.to_datetime(
                data_df[datetime_col],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )
            data_df = data_df[data_df['DateTime'].notna()].copy()
        
        # Chuyển đổi các cột số thành numeric
        for col in data_df.columns:
            if col != 'DateTime' and col in data_df.columns:
                try:
                    data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
                except (TypeError, ValueError):
                    pass
        
        print(f"Loaded {len(data_df)} records from Energy Reports")
        return data_df


class APSLogLoader:
    """Loader cho các file APS Log CSV"""
    
    def __init__(self, log_directory: str):
        self.log_directory = log_directory
        
    def load(self, log_types: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Load tất cả các file log APS
        
        Args:
            log_types: Danh sách các log types cần load. Nếu None, load tất cả.
                      Ví dụ: ['APU Stat 10s', 'APS Stat 10s', 'APS Energy']
        
        Returns:
            Dictionary với key là log type và value là DataFrame
        """
        print(f"Loading APS Logs from {self.log_directory}...")
        
        log_dir = Path(self.log_directory)
        if not log_dir.exists():
            print(f"Error: Directory {self.log_directory} does not exist")
            return {}
        
        # Tìm tất cả file CSV
        csv_files = list(log_dir.glob('*.csv'))
        print(f"Found {len(csv_files)} CSV files")
        
        # Dictionary để lưu dữ liệu theo log type
        log_data = {}
        
        for csv_file in csv_files:
            print(f"  Processing {csv_file.name}...")
            
            # Đọc file không có header
            df = pd.read_csv(csv_file, header=None, low_memory=False)
            
            # Parse header và dữ liệu
            parsed_logs = self._parse_log_file(df)
            
            # Gộp vào log_data
            for log_type, log_df in parsed_logs.items():
                if log_types is None or log_type in log_types:
                    if log_type not in log_data:
                        log_data[log_type] = []
                    log_data[log_type].append(log_df)
        
        # Gộp tất cả các dataframe cùng log type
        result = {}
        for log_type, dfs in log_data.items():
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                combined_df = combined_df.sort_values('TimeStamp').reset_index(drop=True)
                result[log_type] = combined_df
                print(f"  {log_type}: {len(combined_df)} records")
        
        return result
    
    def _parse_log_file(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Parse một file log CSV"""
        parsed_logs = {}
        
        # Tìm các hàng header (thường từ hàng 1-12)
        log_headers = {}
        
        for idx in range(1, min(15, len(df))):
            log_type = df.iloc[idx, 0] if df.shape[1] > 0 else None
            system = df.iloc[idx, 1] if df.shape[1] > 1 else None
            
            if pd.notna(log_type) and str(log_type) != 'Log Type':
                # Lấy tên các cột từ hàng này
                columns = []
                for col_idx in range(3, df.shape[1]):
                    col_name = df.iloc[idx, col_idx]
                    if pd.notna(col_name) and str(col_name).strip() and str(col_name) != 'nan':
                        columns.append(str(col_name).strip())
                    else:
                        break
                
                if columns:
                    key = f"{log_type}_{system}"
                    log_headers[key] = {
                        'log_type': str(log_type),
                        'system': str(system) if pd.notna(system) else '',
                        'header_row': idx,
                        'columns': columns
                    }
        
        # Trích xuất dữ liệu cho từng log type
        data_start_row = 12  # Dữ liệu thường bắt đầu từ hàng 12
        
        for key, header_info in log_headers.items():
            log_type = header_info['log_type']
            system = header_info['system']
            columns = header_info['columns']
            
            # Tìm tất cả các hàng có log type và system này
            rows = []
            for idx in range(data_start_row, len(df)):
                row_log_type = df.iloc[idx, 0] if df.shape[1] > 0 else None
                row_system = df.iloc[idx, 1] if df.shape[1] > 1 else None
                
                if (pd.notna(row_log_type) and str(row_log_type) == log_type and
                    pd.notna(row_system) and str(row_system) == system):
                    
                    # Lấy dữ liệu từ hàng này
                    row_data = {'TimeStamp': df.iloc[idx, 2]}
                    for col_idx, col_name in enumerate(columns):
                        if col_idx + 3 < df.shape[1]:
                            value = df.iloc[idx, col_idx + 3]
                            row_data[col_name] = value
                    rows.append(row_data)
            
            if rows:
                log_df = pd.DataFrame(rows)
                
                # Parse TimeStamp
                log_df['TimeStamp'] = pd.to_datetime(
                    log_df['TimeStamp'],
                    format='%d/%m/%Y %H:%M',
                    errors='coerce'
                )
                log_df = log_df[log_df['TimeStamp'].notna()].copy()
                
                # Chuyển đổi các cột số thành numeric
                for col in log_df.columns:
                    if col != 'TimeStamp':
                        try:
                            log_df[col] = pd.to_numeric(log_df[col], errors='coerce')
                        except (TypeError, ValueError):
                            pass
                
                # Lưu với key là log_type (không bao gồm system)
                if log_type not in parsed_logs:
                    parsed_logs[log_type] = []
                parsed_logs[log_type].append(log_df)
        
        # Gộp các dataframe cùng log type
        result = {}
        for log_type, dfs in parsed_logs.items():
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                result[log_type] = combined_df
        
        return result

