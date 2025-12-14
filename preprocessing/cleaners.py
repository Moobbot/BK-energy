"""
Data Cleaners Module
Module để làm sạch và chuẩn hóa dữ liệu
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import warnings

warnings.filterwarnings('ignore')


class DataCleaner:
    """Class để làm sạch dữ liệu"""
    
    def __init__(self):
        self.cleaning_stats = {}
    
    def clean_dataframe(
        self,
        df: pd.DataFrame,
        datetime_col: str = 'DateTime',
        remove_duplicates: bool = True,
        handle_missing: str = 'interpolate',  # 'drop', 'fill_zero', 'interpolate', 'forward_fill'
        remove_outliers: bool = True,
        outlier_method: str = 'iqr',  # 'iqr', 'zscore'
        outlier_threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Làm sạch một DataFrame
        
        Args:
            df: DataFrame cần làm sạch
            datetime_col: Tên cột datetime
            remove_duplicates: Có xóa duplicate không
            handle_missing: Cách xử lý missing values
            remove_outliers: Có xóa outliers không
            outlier_method: Phương pháp phát hiện outliers
            outlier_threshold: Ngưỡng cho outlier detection
        
        Returns:
            DataFrame đã được làm sạch
        """
        if df.empty:
            return df
        
        df = df.copy()
        original_len = len(df)
        
        # 1. Chuẩn hóa datetime
        if datetime_col in df.columns:
            df[datetime_col] = pd.to_datetime(df[datetime_col], errors='coerce')
            df = df[df[datetime_col].notna()].copy()
            df = df.sort_values(datetime_col).reset_index(drop=True)
        
        # 2. Xóa duplicates
        if remove_duplicates:
            before_dup = len(df)
            df = df.drop_duplicates(subset=[datetime_col] if datetime_col in df.columns else None)
            removed_dup = before_dup - len(df)
            if removed_dup > 0:
                print(f"  Removed {removed_dup} duplicate records")
        
        # 3. Xử lý missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if datetime_col in numeric_cols:
            numeric_cols.remove(datetime_col)
        
        missing_before = df[numeric_cols].isnull().sum().sum()
        
        if handle_missing == 'drop':
            df = df.dropna(subset=numeric_cols)
        elif handle_missing == 'fill_zero':
            df[numeric_cols] = df[numeric_cols].fillna(0)
        elif handle_missing == 'interpolate':
            if datetime_col in df.columns:
                df = df.set_index(datetime_col)
                df[numeric_cols] = df[numeric_cols].interpolate(method='time', limit_direction='both')
                df = df.reset_index()
            else:
                df[numeric_cols] = df[numeric_cols].interpolate(method='linear', limit_direction='both')
        elif handle_missing == 'forward_fill':
            df[numeric_cols] = df[numeric_cols].fillna(method='ffill').fillna(method='bfill')
        
        missing_after = df[numeric_cols].isnull().sum().sum()
        if missing_before > 0:
            print(f"  Handled {missing_before - missing_after} missing values")
        
        # 4. Xóa outliers
        if remove_outliers and len(numeric_cols) > 0:
            outliers_removed = 0
            for col in numeric_cols:
                if outlier_method == 'iqr':
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - outlier_threshold * IQR
                    upper_bound = Q3 + outlier_threshold * IQR
                    outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
                elif outlier_method == 'zscore':
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    outliers = z_scores > outlier_threshold
                else:
                    outliers = pd.Series([False] * len(df))
                
                outliers_count = outliers.sum()
                if outliers_count > 0:
                    # Thay thế outliers bằng NaN và interpolate
                    df.loc[outliers, col] = np.nan
                    if datetime_col in df.columns:
                        df = df.set_index(datetime_col)
                        df[col] = df[col].interpolate(method='time', limit_direction='both')
                        df = df.reset_index()
                    else:
                        df[col] = df[col].interpolate(method='linear', limit_direction='both')
                    outliers_removed += outliers_count
            
            if outliers_removed > 0:
                print(f"  Handled {outliers_removed} outliers")
        
        final_len = len(df)
        print(f"  Cleaned data: {original_len} -> {final_len} records")
        
        return df
    
    def clean_multiple_dataframes(
        self,
        dataframes: Dict[str, pd.DataFrame],
        datetime_col: str = 'DateTime',
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Làm sạch nhiều DataFrame
        
        Args:
            dataframes: Dictionary với key là tên dataset và value là DataFrame
            datetime_col: Tên cột datetime
            **kwargs: Các tham số khác cho clean_dataframe
        
        Returns:
            Dictionary với các DataFrame đã được làm sạch
        """
        cleaned_dataframes = {}
        
        for name, df in dataframes.items():
            print(f"\nCleaning {name}...")
            cleaned_df = self.clean_dataframe(df, datetime_col=datetime_col, **kwargs)
            cleaned_dataframes[name] = cleaned_df
        
        return cleaned_dataframes
    
    def merge_dataframes(
        self,
        dataframes: Dict[str, pd.DataFrame],
        datetime_col: str = 'DateTime',
        merge_method: str = 'outer'  # 'outer', 'inner', 'left', 'right'
    ) -> pd.DataFrame:
        """
        Merge nhiều DataFrame theo datetime
        
        Args:
            dataframes: Dictionary với key là tên dataset và value là DataFrame
            datetime_col: Tên cột datetime
            merge_method: Phương pháp merge
        
        Returns:
            DataFrame đã được merge
        """
        if not dataframes:
            return pd.DataFrame()
        
        print(f"\nMerging {len(dataframes)} dataframes...")
        
        # Bắt đầu với DataFrame đầu tiên
        result = list(dataframes.values())[0].copy()
        
        if datetime_col not in result.columns:
            print(f"Error: Column '{datetime_col}' not found in first dataframe")
            return pd.DataFrame()
        
        result = result.set_index(datetime_col)
        
        # Merge với các DataFrame còn lại
        for name, df in list(dataframes.items())[1:]:
            if datetime_col not in df.columns:
                print(f"Warning: Skipping {name} - no datetime column")
                continue
            
            df_indexed = df.set_index(datetime_col)
            
            # Thêm prefix cho các cột trùng tên (trừ cột đầu tiên)
            if merge_method == 'outer':
                result = result.join(df_indexed, how='outer', rsuffix=f'_{name}')
            elif merge_method == 'inner':
                result = result.join(df_indexed, how='inner', rsuffix=f'_{name}')
            else:
                result = result.join(df_indexed, how=merge_method, rsuffix=f'_{name}')
        
        result = result.reset_index()
        result = result.sort_values(datetime_col).reset_index(drop=True)
        
        print(f"Merged dataframe: {len(result)} records, {len(result.columns)} columns")
        
        return result

