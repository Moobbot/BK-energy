"""
Preprocessing Pipeline
Pipeline chính để xử lý dữ liệu từ nhiều nguồn
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import os

from .loaders import (
    PVForecastLoader,
    PowerReportsLoader,
    WeatherReportsLoader,
    EnergyReportsLoader,
    APSLogLoader
)
from .cleaners import DataCleaner
from .feature_engineering import FeatureEngineer


class PreprocessingPipeline:
    """Pipeline chính để preprocessing dữ liệu"""
    
    def __init__(
        self,
        datasets_dir: str = 'datasets',
        output_dir: str = 'processed_data'
    ):
        """
        Khởi tạo pipeline
        
        Args:
            datasets_dir: Thư mục chứa dữ liệu gốc
            output_dir: Thư mục để lưu dữ liệu đã xử lý
        """
        self.datasets_dir = Path(datasets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Khởi tạo các components
        self.cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer()
        
        # Lưu trữ dữ liệu
        self.raw_data = {}
        self.cleaned_data = {}
        self.featured_data = None
        
    def load_all_data(
        self,
        load_pv_forecast: bool = True,
        load_power_reports: bool = True,
        load_weather_reports: bool = True,
        load_energy_reports: bool = True,
        load_aps_logs: bool = True,
        aps_log_types: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Load tất cả dữ liệu từ các nguồn
        
        Args:
            load_pv_forecast: Có load PV Forecast không
            load_power_reports: Có load Power Reports không
            load_weather_reports: Có load Weather Reports không
            load_energy_reports: Có load Energy Reports không
            load_aps_logs: Có load APS Logs không
            aps_log_types: Danh sách các log types cần load (None = load tất cả)
        
        Returns:
            Dictionary chứa tất cả dữ liệu đã load
        """
        print("=" * 60)
        print("STEP 1: LOADING DATA")
        print("=" * 60)
        
        self.raw_data = {}
        
        # 1. Load PV Forecast
        if load_pv_forecast:
            pv_file = self.datasets_dir / '28_10_25_PV_Forecast.csv'
            if pv_file.exists():
                loader = PVForecastLoader(str(pv_file))
                self.raw_data['pv_forecast'] = loader.load()
            else:
                print(f"Warning: PV Forecast file not found: {pv_file}")
        
        # 2. Load Power Reports
        if load_power_reports:
            power_files = [
                self.datasets_dir / 'Power reports (1-15)102025.xls',
                self.datasets_dir / 'Power reports (16-27)102025.xls'
            ]
            existing_files = [str(f) for f in power_files if f.exists()]
            if existing_files:
                loader = PowerReportsLoader(existing_files)
                self.raw_data['power_reports'] = loader.load()
            else:
                print("Warning: Power Reports files not found")
        
        # 3. Load Weather Reports
        if load_weather_reports:
            weather_file = self.datasets_dir / 'Weather reports (1-27)10.xlsm'
            if weather_file.exists():
                loader = WeatherReportsLoader(str(weather_file))
                self.raw_data['weather_reports'] = loader.load()
            else:
                print(f"Warning: Weather Reports file not found: {weather_file}")
        
        # 4. Load Energy Reports
        if load_energy_reports:
            energy_file = self.datasets_dir / 'Energy reports 01102025 - 27102025.xls'
            if energy_file.exists():
                loader = EnergyReportsLoader(str(energy_file))
                self.raw_data['energy_reports'] = loader.load()
            else:
                print(f"Warning: Energy Reports file not found: {energy_file}")
        
        # 5. Load APS Logs
        if load_aps_logs:
            aps_log_dir = self.datasets_dir / 'inv 24.5' / 'log'
            if aps_log_dir.exists():
                loader = APSLogLoader(str(aps_log_dir))
                aps_logs = loader.load(log_types=aps_log_types)
                
                # Lưu từng log type riêng biệt
                for log_type, log_df in aps_logs.items():
                    # Đổi tên TimeStamp thành DateTime để thống nhất
                    if 'TimeStamp' in log_df.columns:
                        log_df = log_df.rename(columns={'TimeStamp': 'DateTime'})
                    self.raw_data[f'aps_{log_type.lower().replace(" ", "_")}'] = log_df
            else:
                print(f"Warning: APS Log directory not found: {aps_log_dir}")
        
        print(f"\nLoaded {len(self.raw_data)} data sources")
        for name, df in self.raw_data.items():
            print(f"  {name}: {len(df)} records, {len(df.columns)} columns")
        
        return self.raw_data
    
    def clean_all_data(
        self,
        remove_duplicates: bool = True,
        handle_missing: str = 'interpolate',
        remove_outliers: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Làm sạch tất cả dữ liệu
        
        Args:
            remove_duplicates: Có xóa duplicates không
            handle_missing: Cách xử lý missing values
            remove_outliers: Có xóa outliers không
        
        Returns:
            Dictionary chứa tất cả dữ liệu đã được làm sạch
        """
        print("\n" + "=" * 60)
        print("STEP 2: CLEANING DATA")
        print("=" * 60)
        
        if not self.raw_data:
            print("Error: No data loaded. Please run load_all_data() first.")
            return {}
        
        self.cleaned_data = self.cleaner.clean_multiple_dataframes(
            self.raw_data,
            datetime_col='DateTime',
            remove_duplicates=remove_duplicates,
            handle_missing=handle_missing,
            remove_outliers=remove_outliers
        )
        
        return self.cleaned_data
    
    def merge_data(
        self,
        merge_method: str = 'outer',
        target_datetime_col: str = 'DateTime'
    ) -> pd.DataFrame:
        """
        Merge tất cả dữ liệu đã làm sạch
        
        Args:
            merge_method: Phương pháp merge ('outer', 'inner', 'left', 'right')
            target_datetime_col: Tên cột datetime trong kết quả
        
        Returns:
            DataFrame đã được merge
        """
        print("\n" + "=" * 60)
        print("STEP 3: MERGING DATA")
        print("=" * 60)
        
        if not self.cleaned_data:
            print("Error: No cleaned data. Please run clean_all_data() first.")
            return pd.DataFrame()
        
        # Chuẩn hóa tên cột datetime
        for name, df in self.cleaned_data.items():
            if 'TimeStamp' in df.columns and 'DateTime' not in df.columns:
                df = df.rename(columns={'TimeStamp': 'DateTime'})
                self.cleaned_data[name] = df
        
        self.featured_data = self.cleaner.merge_dataframes(
            self.cleaned_data,
            datetime_col='DateTime',
            merge_method=merge_method
        )
        
        return self.featured_data
    
    def create_features(
        self,
        target_column: Optional[str] = None,
        create_time_features: bool = True,
        create_lag_features: bool = True,
        create_rolling_features: bool = True
    ) -> pd.DataFrame:
        """
        Tạo features cho mô hình
        
        Args:
            target_column: Tên cột target
            create_time_features: Có tạo time features không
            create_lag_features: Có tạo lag features không
            create_rolling_features: Có tạo rolling features không
        
        Returns:
            DataFrame với features đã được thêm
        """
        print("\n" + "=" * 60)
        print("STEP 4: FEATURE ENGINEERING")
        print("=" * 60)
        
        if self.featured_data is None or self.featured_data.empty:
            print("Error: No merged data. Please run merge_data() first.")
            return pd.DataFrame()
        
        self.featured_data = self.feature_engineer.create_all_features(
            self.featured_data,
            target_column=target_column,
            datetime_col='DateTime',
            create_time_features=create_time_features,
            create_lag_features=create_lag_features,
            create_rolling_features=create_rolling_features,
            create_difference_features=False,
            create_interaction_features=False
        )
        
        return self.featured_data
    
    def save_processed_data(
        self,
        filename: str = 'processed_data.csv',
        save_individual: bool = True
    ):
        """
        Lưu dữ liệu đã xử lý
        
        Args:
            filename: Tên file để lưu dữ liệu đã merge
            save_individual: Có lưu từng dataset riêng không
        """
        print("\n" + "=" * 60)
        print("STEP 5: SAVING DATA")
        print("=" * 60)
        
        # Lưu dữ liệu đã merge và có features
        if self.featured_data is not None and not self.featured_data.empty:
            output_path = self.output_dir / filename
            self.featured_data.to_csv(output_path, index=False)
            print(f"Saved merged data to: {output_path}")
            print(f"  Shape: {self.featured_data.shape}")
        
        # Lưu từng dataset riêng
        if save_individual:
            individual_dir = self.output_dir / 'individual'
            individual_dir.mkdir(exist_ok=True)
            
            for name, df in self.cleaned_data.items():
                if not df.empty:
                    output_path = individual_dir / f"{name}.csv"
                    df.to_csv(output_path, index=False)
                    print(f"Saved {name} to: {output_path}")
    
    def run_full_pipeline(
        self,
        target_column: Optional[str] = None,
        load_options: Optional[Dict] = None,
        cleaning_options: Optional[Dict] = None,
        feature_options: Optional[Dict] = None,
        output_filename: str = 'processed_data.csv'
    ) -> pd.DataFrame:
        """
        Chạy toàn bộ pipeline từ đầu đến cuối
        
        Args:
            target_column: Tên cột target
            load_options: Các tùy chọn cho load_all_data
            cleaning_options: Các tùy chọn cho clean_all_data
            feature_options: Các tùy chọn cho create_features
            output_filename: Tên file output
        
        Returns:
            DataFrame đã được xử lý hoàn chỉnh
        """
        print("\n" + "=" * 60)
        print("PREPROCESSING PIPELINE")
        print("=" * 60)
        
        # Default options
        if load_options is None:
            load_options = {}
        if cleaning_options is None:
            cleaning_options = {}
        if feature_options is None:
            feature_options = {}
        
        # Step 1: Load data
        self.load_all_data(**load_options)
        
        # Step 2: Clean data
        self.clean_all_data(**cleaning_options)
        
        # Step 3: Merge data
        self.merge_data()
        
        # Step 4: Create features
        self.create_features(target_column=target_column, **feature_options)
        
        # Step 5: Save data
        self.save_processed_data(filename=output_filename)
        
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return self.featured_data
    
    def get_data_summary(self) -> Dict:
        """Lấy summary của dữ liệu"""
        summary = {
            'raw_data_sources': len(self.raw_data),
            'cleaned_data_sources': len(self.cleaned_data),
            'final_shape': self.featured_data.shape if self.featured_data is not None else None,
            'final_columns': list(self.featured_data.columns) if self.featured_data is not None else []
        }
        
        return summary

