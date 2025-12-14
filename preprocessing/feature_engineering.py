"""
Feature Engineering Module
Module để tạo features cho mô hình
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import warnings

warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Class để tạo features cho mô hình"""
    
    def __init__(self):
        self.feature_stats = {}
    
    def create_time_features(
        self,
        df: pd.DataFrame,
        datetime_col: str = 'DateTime'
    ) -> pd.DataFrame:
        """
        Tạo các features về thời gian
        
        Args:
            df: DataFrame
            datetime_col: Tên cột datetime
        
        Returns:
            DataFrame với các time features đã được thêm
        """
        if datetime_col not in df.columns:
            print(f"Warning: Column '{datetime_col}' not found")
            return df
        
        df = df.copy()
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        
        # Hour of day (0-23)
        df['hour'] = df[datetime_col].dt.hour
        
        # Day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df[datetime_col].dt.dayofweek
        
        # Day of month (1-31)
        df['day_of_month'] = df[datetime_col].dt.day
        
        # Month (1-12)
        df['month'] = df[datetime_col].dt.month
        
        # Year
        df['year'] = df[datetime_col].dt.year
        
        # Is weekend (0 or 1)
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Time of day categories
        df['time_of_day'] = pd.cut(
            df['hour'],
            bins=[0, 6, 12, 18, 24],
            labels=['Night', 'Morning', 'Afternoon', 'Evening'],
            include_lowest=True
        )
        
        # Cyclical encoding cho hour và day_of_week
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        print(f"Created time features: hour, day_of_week, month, is_weekend, cyclical encodings")
        
        return df
    
    def create_lag_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        lags: List[int] = [1, 2, 3, 6, 12, 24],
        datetime_col: str = 'DateTime'
    ) -> pd.DataFrame:
        """
        Tạo lag features (giá trị ở các thời điểm trước)
        
        Args:
            df: DataFrame
            columns: Danh sách các cột cần tạo lag
            lags: Danh sách các lag (số bước thời gian)
            datetime_col: Tên cột datetime
        
        Returns:
            DataFrame với lag features đã được thêm
        """
        if datetime_col not in df.columns:
            print(f"Warning: Column '{datetime_col}' not found")
            return df
        
        df = df.copy()
        df = df.sort_values(datetime_col).reset_index(drop=True)
        
        for col in columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found, skipping")
                continue
            
            for lag in lags:
                lag_col_name = f'{col}_lag_{lag}'
                df[lag_col_name] = df[col].shift(lag)
        
        print(f"Created lag features for {len(columns)} columns with lags {lags}")
        
        return df
    
    def create_rolling_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        windows: List[int] = [3, 6, 12, 24],
        datetime_col: str = 'DateTime',
        functions: List[str] = ['mean', 'std', 'min', 'max']
    ) -> pd.DataFrame:
        """
        Tạo rolling window features
        
        Args:
            df: DataFrame
            columns: Danh sách các cột cần tạo rolling features
            windows: Danh sách các window size
            datetime_col: Tên cột datetime
            functions: Danh sách các hàm thống kê
        
        Returns:
            DataFrame với rolling features đã được thêm
        """
        if datetime_col not in df.columns:
            print(f"Warning: Column '{datetime_col}' not found")
            return df
        
        df = df.copy()
        df = df.sort_values(datetime_col).reset_index(drop=True)
        
        for col in columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found, skipping")
                continue
            
            for window in windows:
                for func in functions:
                    if func == 'mean':
                        df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window=window, min_periods=1).mean()
                    elif func == 'std':
                        df[f'{col}_rolling_std_{window}'] = df[col].rolling(window=window, min_periods=1).std()
                    elif func == 'min':
                        df[f'{col}_rolling_min_{window}'] = df[col].rolling(window=window, min_periods=1).min()
                    elif func == 'max':
                        df[f'{col}_rolling_max_{window}'] = df[col].rolling(window=window, min_periods=1).max()
        
        print(f"Created rolling features for {len(columns)} columns with windows {windows}")
        
        return df
    
    def create_difference_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        periods: List[int] = [1, 2, 3]
    ) -> pd.DataFrame:
        """
        Tạo difference features (chênh lệch giữa các thời điểm)
        
        Args:
            df: DataFrame
            columns: Danh sách các cột cần tạo difference
            periods: Danh sách các period
        
        Returns:
            DataFrame với difference features đã được thêm
        """
        df = df.copy()
        
        for col in columns:
            if col not in df.columns:
                print(f"Warning: Column '{col}' not found, skipping")
                continue
            
            for period in periods:
                diff_col_name = f'{col}_diff_{period}'
                df[diff_col_name] = df[col].diff(period)
        
        print(f"Created difference features for {len(columns)} columns with periods {periods}")
        
        return df
    
    def create_interaction_features(
        self,
        df: pd.DataFrame,
        feature_pairs: List[tuple],
        operations: List[str] = ['multiply', 'divide', 'add', 'subtract']
    ) -> pd.DataFrame:
        """
        Tạo interaction features giữa các cột
        
        Args:
            df: DataFrame
            feature_pairs: Danh sách các cặp (col1, col2) để tạo interaction
            operations: Danh sách các phép toán
        
        Returns:
            DataFrame với interaction features đã được thêm
        """
        df = df.copy()
        
        for col1, col2 in feature_pairs:
            if col1 not in df.columns or col2 not in df.columns:
                print(f"Warning: Skipping pair ({col1}, {col2}) - column not found")
                continue
            
            for op in operations:
                if op == 'multiply':
                    df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
                elif op == 'divide':
                    # Tránh chia cho 0
                    df[f'{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-8)
                elif op == 'add':
                    df[f'{col1}_plus_{col2}'] = df[col1] + df[col2]
                elif op == 'subtract':
                    df[f'{col1}_minus_{col2}'] = df[col1] - df[col2]
        
        print(f"Created interaction features for {len(feature_pairs)} pairs")
        
        return df
    
    def create_all_features(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        numeric_columns: Optional[List[str]] = None,
        datetime_col: str = 'DateTime',
        create_time_features: bool = True,
        create_lag_features: bool = True,
        create_rolling_features: bool = True,
        create_difference_features: bool = False,
        create_interaction_features: bool = False
    ) -> pd.DataFrame:
        """
        Tạo tất cả các features
        
        Args:
            df: DataFrame
            target_column: Tên cột target (để tạo features liên quan)
            numeric_columns: Danh sách các cột numeric để tạo features
            datetime_col: Tên cột datetime
            create_time_features: Có tạo time features không
            create_lag_features: Có tạo lag features không
            create_rolling_features: Có tạo rolling features không
            create_difference_features: Có tạo difference features không
            create_interaction_features: Có tạo interaction features không
        
        Returns:
            DataFrame với tất cả features đã được thêm
        """
        print("\n=== Creating Features ===")
        
        df = df.copy()
        
        # Xác định numeric columns nếu chưa có
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if datetime_col in numeric_columns:
                numeric_columns.remove(datetime_col)
            # Loại bỏ các cột đã được tạo từ time features
            time_feature_cols = ['hour', 'day_of_week', 'day_of_month', 'month', 'year']
            numeric_columns = [col for col in numeric_columns if col not in time_feature_cols]
        
        # 1. Time features
        if create_time_features:
            df = self.create_time_features(df, datetime_col)
        
        # 2. Lag features (chỉ cho target column hoặc các cột quan trọng)
        if create_lag_features and target_column and target_column in df.columns:
            df = self.create_lag_features(df, [target_column], lags=[1, 2, 3, 6, 12, 24], datetime_col=datetime_col)
        
        # 3. Rolling features (cho các cột numeric quan trọng)
        if create_rolling_features and numeric_columns:
            # Chỉ tạo rolling features cho một số cột quan trọng
            important_cols = [col for col in numeric_columns if any(keyword in col.lower() 
                            for keyword in ['power', 'irr', 'temp', 'voltage', 'current'])]
            if important_cols:
                df = self.create_rolling_features(
                    df,
                    important_cols[:5],  # Giới hạn số lượng để tránh quá nhiều features
                    windows=[3, 6, 12],
                    datetime_col=datetime_col,
                    functions=['mean', 'std']
                )
        
        # 4. Difference features
        if create_difference_features and target_column and target_column in df.columns:
            df = self.create_difference_features(df, [target_column], periods=[1, 2])
        
        # 5. Interaction features (ví dụ)
        if create_interaction_features and len(numeric_columns) >= 2:
            # Tạo một số interaction features quan trọng
            important_cols = [col for col in numeric_columns if any(keyword in col.lower() 
                            for keyword in ['power', 'irr', 'temp'])]
            if len(important_cols) >= 2:
                pairs = [(important_cols[0], important_cols[1])]
                df = self.create_interaction_features(df, pairs, operations=['multiply', 'divide'])
        
        print(f"\nFinal feature count: {len(df.columns)} columns")
        
        return df

