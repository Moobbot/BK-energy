"""
Script trực quan hóa dữ liệu Weather Reports
Tạo các loại biểu đồ khác nhau để phân tích dữ liệu thời tiết
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import warnings
import io
import argparse
from datetime import datetime, timedelta
from typing import Optional, List

# Cấu hình encoding UTF-8 cho Windows console
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass  # Nếu không thể thay đổi encoding, bỏ qua

# Thêm thư mục preprocessing vào path để import loader
sys.path.append(str(Path(__file__).parent / 'preprocessing'))
from loaders import WeatherReportsLoader

warnings.filterwarnings('ignore')

# Cấu hình matplotlib để hiển thị tiếng Việt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['figure.dpi'] = 100

# Cấu hình seaborn
sns.set_style("whitegrid")
sns.set_palette("husl")


class WeatherReportsVisualizer:
    """Class để trực quan hóa dữ liệu Weather Reports"""
    
    def __init__(self, file_path: str, start_date: Optional[str] = None, 
                 end_date: Optional[str] = None, show_progress: bool = True):
        """
        Khởi tạo visualizer
        
        Args:
            file_path: Đường dẫn đến file Weather reports (1-27)10.xlsm
            start_date: Ngày bắt đầu lọc dữ liệu (format: 'YYYY-MM-DD'), None nếu không lọc
            end_date: Ngày kết thúc lọc dữ liệu (format: 'YYYY-MM-DD'), None nếu không lọc
            show_progress: Hiển thị tiến trình khi vẽ biểu đồ
        """
        self.file_path = file_path
        self.df = None
        self.output_dir = Path('visualizations/weather_reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.datetime_col = 'DateTime'  # Tên cột datetime mặc định
        self.start_date = start_date
        self.end_date = end_date
        self.show_progress = show_progress
        self.charts_created = 0
    
    def _save_figure(self, filename: str, dpi: int = 150) -> Path:
        """
        Helper method để lưu figure và đếm số biểu đồ đã tạo
        
        Args:
            filename: Tên file để lưu
            dpi: Độ phân giải (mặc định: 150)
        
        Returns:
            Path đến file đã lưu
        """
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
        self.charts_created += 1
        return filepath
        
    def load_data(self):
        """Load dữ liệu từ file Excel"""
        print("=" * 60)
        print("ĐANG TẢI DỮ LIỆU WEATHER REPORTS...")
        print("=" * 60)
        
        loader = WeatherReportsLoader(self.file_path)
        self.df = loader.load()
        
        if self.df.empty:
            raise ValueError("Không thể load dữ liệu từ file!")
        
        # Kiểm tra và đảm bảo có cột DateTime
        if 'DateTime' not in self.df.columns:
            # Tìm cột datetime với các tên khác nhau
            datetime_cols = [col for col in self.df.columns 
                           if 'date' in col.lower() or 'time' in col.lower()]
            if datetime_cols:
                # Sử dụng cột đầu tiên tìm được
                datetime_col = datetime_cols[0]
                # Dữ liệu hiện tại có format dd/mm/yyyy hh:mm → dùng dayfirst=True
                self.df['DateTime'] = pd.to_datetime(
                    self.df[datetime_col],
                    errors='coerce',
                    dayfirst=True
                )
                self.datetime_col = 'DateTime'
            else:
                raise ValueError("Không tìm thấy cột thời gian trong dữ liệu!")
        else:
            # Cột DateTime đã tồn tại → parse lại với dayfirst=True cho chắc chắn
            self.df['DateTime'] = pd.to_datetime(
                self.df['DateTime'],
                errors='coerce',
                dayfirst=True
            )
            self.datetime_col = 'DateTime'
        
        # Loại bỏ các hàng không có DateTime hợp lệ
        self.df = self.df[self.df[self.datetime_col].notna()].copy()
        
        # Lọc dữ liệu theo khoảng thời gian nếu có
        if self.start_date or self.end_date:
            original_count = len(self.df)
            if self.start_date:
                start_dt = pd.to_datetime(self.start_date)
                self.df = self.df[self.df[self.datetime_col] >= start_dt].copy()
            if self.end_date:
                end_dt = pd.to_datetime(self.end_date) + timedelta(days=1)  # Bao gồm cả ngày cuối
                self.df = self.df[self.df[self.datetime_col] < end_dt].copy()
            print(f"✓ Đã lọc dữ liệu: {original_count} -> {len(self.df)} bản ghi")
        
        # Hiển thị thông tin cơ bản về dữ liệu
        print(f"\n✓ Đã load thành công {len(self.df)} bản ghi")
        print(f"✓ Số cột: {len(self.df.columns)}")
        if 'DateTime' in self.df.columns and len(self.df) > 0:
            print(f"✓ Thời gian: {self.df['DateTime'].min()} đến {self.df['DateTime'].max()}")
        print(f"\nCác cột trong dữ liệu (10 cột đầu):")
        for col in list(self.df.columns)[:10]:
            print(f"  - {col}")
        if len(self.df.columns) > 10:
            print(f"  ... và {len(self.df.columns) - 10} cột khác")
        
        return self.df
    
    def show_data_info(self):
        """Hiển thị thông tin tổng quan về dữ liệu"""
        print("\n" + "=" * 60)
        print("THÔNG TIN TỔNG QUAN VỀ DỮ LIỆU")
        print("=" * 60)
        
        # Hiển thị 5 dòng đầu
        print("\n5 dòng đầu tiên:")
        print(self.df.head())
        
        # Thống kê mô tả
        print("\n\nThống kê mô tả:")
        print(self.df.describe())
        
        # Thông tin về missing values
        print("\n\nGiá trị thiếu (Missing Values):")
        missing = self.df.isnull().sum()
        missing = missing[missing > 0]
        if len(missing) > 0:
            print(missing)
        else:
            print("Không có giá trị thiếu!")
    
    # ============================================================================
    # LOẠI 1: BIỂU ĐỒ ĐƯỜNG (LINE CHART) - THEO DÕI THEO THỜI GIAN
    # ============================================================================
    
    def plot_line_charts(self):
        """
        Vẽ biểu đồ đường (Line Chart) cho các biến thời tiết theo thời gian
        Biểu đồ này giúp theo dõi xu hướng thay đổi của các yếu tố thời tiết
        """
        print("\n" + "=" * 60)
        print("LOẠI 1: BIỂU ĐỒ ĐƯỜNG (LINE CHARTS)")
        print("=" * 60)
        
        # Tìm các cột số (loại trừ DateTime)
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Vẽ từng biến riêng biệt
        for col in numeric_cols[:10]:  # Giới hạn 10 cột đầu để không quá nhiều
            try:
                fig, ax = plt.subplots(figsize=(16, 6))
                
                # Vẽ đường
                ax.plot(self.df['DateTime'], self.df[col], 
                       linewidth=1.5, alpha=0.8, color='steelblue')
                
                # Tùy chỉnh biểu đồ
                ax.set_title(f'Biểu Đồ Đường: {col} Theo Thời Gian', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Thời Gian', fontsize=12)
                ax.set_ylabel(col, fontsize=12)
                ax.grid(True, alpha=0.3)
                
                # Xoay nhãn trục x để dễ đọc
                plt.xticks(rotation=45, ha='right')
                
                # Định dạng trục x
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                
                plt.tight_layout()
                
                # Lưu file
                filename = f"01_line_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ {col}: {e}")
        
        # Vẽ nhiều biến trên cùng 1 biểu đồ (nếu có các biến quan trọng)
        important_vars = []
        for var in ['Temperature', 'Humidity', 'Irradiance', 'Wind', 'Pressure']:
            matching_cols = [col for col in numeric_cols if var.lower() in col.lower()]
            if matching_cols:
                important_vars.extend(matching_cols[:1])  # Lấy 1 cột đầu tiên
        
        if len(important_vars) >= 2:
            fig, axes = plt.subplots(len(important_vars), 1, figsize=(16, 4*len(important_vars)))
            if len(important_vars) == 1:
                axes = [axes]
            
            for idx, col in enumerate(important_vars):
                axes[idx].plot(self.df['DateTime'], self.df[col], 
                              linewidth=1.5, alpha=0.8, label=col)
                axes[idx].set_title(f'{col} Theo Thời Gian', fontsize=14, fontweight='bold')
                axes[idx].set_ylabel(col, fontsize=11)
                axes[idx].grid(True, alpha=0.3)
                axes[idx].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                if idx == len(important_vars) - 1:
                    axes[idx].set_xlabel('Thời Gian', fontsize=12)
                    plt.setp(axes[idx].xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            filename = "01_line_multiple_variables.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✓ Đã lưu: {filepath}")
            plt.close()
    
    # ============================================================================
    # LOẠI 2: BIỂU ĐỒ CỘT (BAR CHART) - SO SÁNH GIÁ TRỊ TRUNG BÌNH
    # ============================================================================
    
    def plot_bar_charts(self):
        """
        Vẽ biểu đồ cột (Bar Chart) để so sánh giá trị trung bình theo ngày/giờ
        Biểu đồ này giúp so sánh các giá trị giữa các khoảng thời gian khác nhau
        """
        print("\n" + "=" * 60)
        print("LOẠI 2: BIỂU ĐỒ CỘT (BAR CHARTS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Tạo cột ngày và giờ
        self.df['Date'] = self.df['DateTime'].dt.date
        self.df['Hour'] = self.df['DateTime'].dt.hour
        
        # 2.1. Biểu đồ cột: Giá trị trung bình theo giờ trong ngày
        print("\n2.1. Vẽ biểu đồ cột: Giá trị trung bình theo giờ...")
        for col in numeric_cols[:8]:  # Giới hạn 8 cột
            try:
                hourly_avg = self.df.groupby('Hour')[col].mean()
                
                fig, ax = plt.subplots(figsize=(14, 6))
                
                bars = ax.bar(hourly_avg.index, hourly_avg.values, 
                             color='coral', alpha=0.7, edgecolor='black', linewidth=1)
                
                ax.set_title(f'Giá Trị Trung Bình {col} Theo Giờ Trong Ngày', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Giờ Trong Ngày', fontsize=12)
                ax.set_ylabel(f'Trung Bình {col}', fontsize=12)
                ax.set_xticks(range(24))
                ax.grid(True, alpha=0.3, axis='y')
                
                # Thêm giá trị trên mỗi cột
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=9)
                
                plt.tight_layout()
                
                filename = f"02_bar_hourly_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ {col}: {e}")
        
        # 2.2. Biểu đồ cột: Giá trị trung bình theo ngày
        print("\n2.2. Vẽ biểu đồ cột: Giá trị trung bình theo ngày...")
        for col in numeric_cols[:5]:  # Giới hạn 5 cột
            try:
                daily_avg = self.df.groupby('Date')[col].mean()
                
                fig, ax = plt.subplots(figsize=(16, 6))
                
                bars = ax.bar(range(len(daily_avg)), daily_avg.values, 
                             color='lightblue', alpha=0.7, edgecolor='black', linewidth=1)
                
                ax.set_title(f'Giá Trị Trung Bình {col} Theo Ngày', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Ngày', fontsize=12)
                ax.set_ylabel(f'Trung Bình {col}', fontsize=12)
                ax.set_xticks(range(0, len(daily_avg), max(1, len(daily_avg)//10)))
                ax.set_xticklabels([str(daily_avg.index[i]) for i in range(0, len(daily_avg), max(1, len(daily_avg)//10))], 
                                  rotation=45, ha='right')
                ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                filename = f"02_bar_daily_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ {col}: {e}")
    
    # ============================================================================
    # LOẠI 3: BIỂU ĐỒ PHÂN TÁN (SCATTER PLOT) - TƯƠNG QUAN GIỮA 2 BIẾN
    # ============================================================================
    
    def plot_scatter_plots(self):
        """
        Vẽ biểu đồ phân tán (Scatter Plot) để xem mối tương quan giữa 2 biến
        Biểu đồ này giúp phát hiện mối quan hệ giữa các yếu tố thời tiết
        """
        print("\n" + "=" * 60)
        print("LOẠI 3: BIỂU ĐỒ PHÂN TÁN (SCATTER PLOTS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            print("Cần ít nhất 2 cột số để vẽ scatter plot!")
            return
        
        # Tìm các cặp biến quan trọng để vẽ
        important_pairs = []
        
        # Tìm Temperature và Irradiance
        temp_cols = [col for col in numeric_cols if 'temp' in col.lower() or 'temperature' in col.lower()]
        irrad_cols = [col for col in numeric_cols if 'irrad' in col.lower() or 'radiation' in col.lower()]
        if temp_cols and irrad_cols:
            important_pairs.append((temp_cols[0], irrad_cols[0]))
        
        # Tìm Humidity và Temperature
        humidity_cols = [col for col in numeric_cols if 'humid' in col.lower()]
        if temp_cols and humidity_cols:
            important_pairs.append((temp_cols[0], humidity_cols[0]))
        
        # Vẽ các cặp quan trọng
        for x_col, y_col in important_pairs:
            try:
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Vẽ scatter plot
                scatter = ax.scatter(self.df[x_col], self.df[y_col], 
                                   alpha=0.5, s=20, c='steelblue', edgecolors='black', linewidth=0.5)
                
                # Tính hệ số tương quan
                correlation = self.df[[x_col, y_col]].corr().iloc[0, 1]
                
                ax.set_title(f'Mối Tương Quan: {x_col} vs {y_col}\n(Hệ số tương quan: {correlation:.3f})', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel(x_col, fontsize=12)
                ax.set_ylabel(y_col, fontsize=12)
                ax.grid(True, alpha=0.3)
                
                # Thêm đường hồi quy
                z = np.polyfit(self.df[x_col].dropna(), self.df[y_col].dropna(), 1)
                p = np.poly1d(z)
                ax.plot(self.df[x_col].dropna(), p(self.df[x_col].dropna()), 
                       "r--", alpha=0.8, linewidth=2, label=f'Trend line')
                ax.legend()
                
                plt.tight_layout()
                
                filename = f"03_scatter_{x_col.replace(' ', '_')}_vs_{y_col.replace(' ', '_')}.png"
                filename = filename.replace('/', '_')
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ scatter plot {x_col} vs {y_col}: {e}")
        
        # Vẽ ma trận scatter plot cho nhiều biến
        if len(numeric_cols) >= 3:
            try:
                # Chọn 4-5 biến đầu tiên
                selected_cols = numeric_cols[:min(5, len(numeric_cols))]
                
                fig = plt.figure(figsize=(16, 16))
                gs = fig.add_gridspec(len(selected_cols), len(selected_cols), hspace=0.3, wspace=0.3)
                
                for i, x_col in enumerate(selected_cols):
                    for j, y_col in enumerate(selected_cols):
                        ax = fig.add_subplot(gs[i, j])
                        
                        if i == j:
                            # Đường chéo: vẽ histogram
                            ax.hist(self.df[x_col].dropna(), bins=30, color='steelblue', alpha=0.7, edgecolor='black')
                            ax.set_title(x_col, fontsize=10, fontweight='bold')
                        else:
                            # Vẽ scatter plot
                            ax.scatter(self.df[x_col], self.df[y_col], 
                                     alpha=0.3, s=10, c='steelblue', edgecolors='none')
                            if i == len(selected_cols) - 1:
                                ax.set_xlabel(x_col, fontsize=9)
                            if j == 0:
                                ax.set_ylabel(y_col, fontsize=9)
                        
                        ax.tick_params(labelsize=8)
                        ax.grid(True, alpha=0.2)
                
                plt.suptitle('Ma Trận Scatter Plot - Mối Tương Quan Giữa Các Biến', 
                           fontsize=16, fontweight='bold', y=0.995)
                
                filename = "03_scatter_matrix.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ scatter matrix: {e}")
    
    # ============================================================================
    # LOẠI 4: BIỂU ĐỒ NHIỆT (HEATMAP) - MA TRẬN TƯƠNG QUAN
    # ============================================================================
    
    def plot_heatmaps(self):
        """
        Vẽ biểu đồ nhiệt (Heatmap) để hiển thị ma trận tương quan
        Biểu đồ này giúp phát hiện các biến có mối tương quan mạnh với nhau
        """
        print("\n" + "=" * 60)
        print("LOẠI 4: BIỂU ĐỒ NHIỆT (HEATMAPS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            print("Cần ít nhất 2 cột số để vẽ heatmap!")
            return
        
        # 4.1. Heatmap tương quan
        print("\n4.1. Vẽ heatmap ma trận tương quan...")
        try:
            # Tính ma trận tương quan
            corr_matrix = self.df[numeric_cols].corr()
            
            fig, ax = plt.subplots(figsize=(14, 12))
            
            # Vẽ heatmap
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                       center=0, square=True, linewidths=1, 
                       cbar_kws={"shrink": 0.8}, ax=ax,
                       xticklabels=True, yticklabels=True)
            
            ax.set_title('Ma Trận Tương Quan Giữa Các Biến Thời Tiết', 
                        fontsize=16, fontweight='bold', pad=20)
            
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            
            filename = "04_heatmap_correlation.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✓ Đã lưu: {filepath}")
            
            plt.close()
            
        except Exception as e:
            print(f"✗ Lỗi khi vẽ heatmap tương quan: {e}")
        
        # 4.2. Heatmap theo thời gian (nếu có đủ dữ liệu)
        print("\n4.2. Vẽ heatmap theo thời gian...")
        try:
            # Tạo pivot table: giờ (rows) x ngày (columns)
            if 'Hour' not in self.df.columns:
                self.df['Hour'] = self.df['DateTime'].dt.hour
            if 'Date' not in self.df.columns:
                self.df['Date'] = self.df['DateTime'].dt.date
            
            # Chọn 1 biến quan trọng để vẽ (ví dụ: Temperature hoặc Irradiance)
            var_to_plot = None
            for var_name in ['Temperature', 'Irradiance', 'Humidity']:
                matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
                if matching_cols:
                    var_to_plot = matching_cols[0]
                    break
            
            if var_to_plot:
                pivot_data = self.df.pivot_table(values=var_to_plot, 
                                                 index='Hour', 
                                                 columns='Date', 
                                                 aggfunc='mean')
                
                fig, ax = plt.subplots(figsize=(20, 8))
                
                sns.heatmap(pivot_data, cmap='YlOrRd', annot=False, 
                           fmt='.1f', cbar_kws={'label': var_to_plot},
                           ax=ax, linewidths=0.5)
                
                ax.set_title(f'Heatmap {var_to_plot} - Giờ (Dọc) x Ngày (Ngang)', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Ngày', fontsize=12)
                ax.set_ylabel('Giờ Trong Ngày', fontsize=12)
                
                # Giảm số lượng nhãn trên trục x
                n_dates = len(pivot_data.columns)
                step = max(1, n_dates // 10)
                ax.set_xticks(range(0, n_dates, step))
                ax.set_xticklabels([str(pivot_data.columns[i]) for i in range(0, n_dates, step)], 
                                   rotation=45, ha='right')
                
                plt.tight_layout()
                
                filename = f"04_heatmap_temporal_{var_to_plot.replace(' ', '_')}.png"
                filename = filename.replace('/', '_')
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
        except Exception as e:
            print(f"✗ Lỗi khi vẽ heatmap temporal: {e}")
    
    # ============================================================================
    # LOẠI 5: BIỂU ĐỒ HỘP (BOX PLOT) - PHÂN BỐ DỮ LIỆU
    # ============================================================================
    
    def plot_box_plots(self):
        """
        Vẽ biểu đồ hộp (Box Plot) để xem phân bố và outliers của dữ liệu
        Biểu đồ này giúp phát hiện giá trị bất thường và so sánh phân bố
        """
        print("\n" + "=" * 60)
        print("LOẠI 5: BIỂU ĐỒ HỘP (BOX PLOTS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # 5.1. Box plot cho từng biến
        print("\n5.1. Vẽ box plot cho từng biến...")
        for col in numeric_cols[:10]:  # Giới hạn 10 cột
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Vẽ box plot
                bp = ax.boxplot(self.df[col].dropna(), vert=True, patch_artist=True,
                               boxprops=dict(facecolor='lightblue', alpha=0.7),
                               medianprops=dict(color='red', linewidth=2),
                               whiskerprops=dict(linewidth=1.5),
                               capprops=dict(linewidth=1.5))
                
                ax.set_title(f'Box Plot: {col}', fontsize=16, fontweight='bold', pad=20)
                ax.set_ylabel(col, fontsize=12)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Thêm thống kê
                stats = self.df[col].describe()
                textstr = f'Mean: {stats["mean"]:.2f}\nMedian: {stats["50%"]:.2f}\nStd: {stats["std"]:.2f}'
                ax.text(0.02, 0.98, textstr, transform=ax.transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                plt.tight_layout()
                
                filename = f"05_boxplot_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ box plot {col}: {e}")
        
        # 5.2. Box plot so sánh theo giờ
        print("\n5.2. Vẽ box plot so sánh theo giờ...")
        if 'Hour' not in self.df.columns:
            self.df['Hour'] = self.df['DateTime'].dt.hour
        
        for col in numeric_cols[:5]:  # Giới hạn 5 cột
            try:
                fig, ax = plt.subplots(figsize=(16, 6))
                
                # Chuẩn bị dữ liệu
                data_to_plot = [self.df[self.df['Hour'] == hour][col].dropna().values 
                               for hour in range(24)]
                
                # Vẽ box plot
                bp = ax.boxplot(data_to_plot, labels=range(24), patch_artist=True,
                               boxprops=dict(facecolor='lightgreen', alpha=0.7),
                               medianprops=dict(color='red', linewidth=1.5))
                
                ax.set_title(f'Box Plot {col} Theo Giờ Trong Ngày', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Giờ Trong Ngày', fontsize=12)
                ax.set_ylabel(col, fontsize=12)
                ax.set_xticks(range(0, 24, 2))
                ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                filename = f"05_boxplot_hourly_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ box plot theo giờ {col}: {e}")
    
    # ============================================================================
    # LOẠI 6: BIỂU ĐỒ HISTOGRAM - PHÂN BỐ TẦN SUẤT
    # ============================================================================
    
    def plot_histograms(self):
        """
        Vẽ biểu đồ histogram để xem phân bố tần suất của dữ liệu
        Biểu đồ này giúp hiểu dữ liệu có phân bố như thế nào (chuẩn, lệch, đa đỉnh...)
        """
        print("\n" + "=" * 60)
        print("LOẠI 6: BIỂU ĐỒ HISTOGRAM")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Vẽ histogram cho từng biến
        for col in numeric_cols[:10]:  # Giới hạn 10 cột
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Vẽ histogram
                n, bins, patches = ax.hist(self.df[col].dropna(), bins=50, 
                                         color='steelblue', alpha=0.7, 
                                         edgecolor='black', linewidth=1)
                
                # Tô màu theo độ cao
                cm = plt.cm.get_cmap('viridis')
                for i, patch in enumerate(patches):
                    patch.set_facecolor(cm(n[i] / n.max()))
                
                # Thêm đường phân bố chuẩn (nếu có thể)
                try:
                    from scipy import stats
                    mu, sigma = self.df[col].dropna().mean(), self.df[col].dropna().std()
                    x = np.linspace(self.df[col].min(), self.df[col].max(), 100)
                    y = stats.norm.pdf(x, mu, sigma) * len(self.df[col].dropna()) * (bins[1] - bins[0])
                    ax.plot(x, y, 'r--', linewidth=2, label='Normal Distribution')
                    ax.legend()
                except:
                    pass
                
                ax.set_title(f'Histogram: Phân Bố {col}', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel(col, fontsize=12)
                ax.set_ylabel('Tần Suất', fontsize=12)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Thêm thống kê
                stats_text = f'Mean: {self.df[col].mean():.2f}\nStd: {self.df[col].std():.2f}'
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                plt.tight_layout()
                
                filename = f"06_histogram_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ histogram {col}: {e}")
    
    # ============================================================================
    # LOẠI 7: BIỂU ĐỒ VÙNG (AREA CHART) - TỔNG HỢP THEO THỜI GIAN
    # ============================================================================
    
    def plot_area_charts(self):
        """
        Vẽ biểu đồ vùng (Area Chart) để hiển thị tổng hợp nhiều biến theo thời gian
        Biểu đồ này giúp xem tổng hợp và so sánh nhiều yếu tố cùng lúc
        """
        print("\n" + "=" * 60)
        print("LOẠI 7: BIỂU ĐỒ VÙNG (AREA CHARTS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            print("Cần ít nhất 2 cột số để vẽ area chart!")
            return
        
        # Tìm các biến quan trọng
        important_vars = []
        for var_name in ['Temperature', 'Humidity', 'Irradiance', 'Wind', 'Pressure']:
            matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
            if matching_cols:
                important_vars.append(matching_cols[0])
        
        if len(important_vars) >= 2:
            try:
                # Chuẩn hóa dữ liệu để vẽ trên cùng 1 scale
                normalized_df = self.df[important_vars].copy()
                for col in important_vars:
                    col_min = normalized_df[col].min()
                    col_max = normalized_df[col].max()
                    if col_max > col_min:
                        normalized_df[col] = (normalized_df[col] - col_min) / (col_max - col_min)
                
                fig, ax = plt.subplots(figsize=(16, 8))
                
                # Vẽ area chart
                ax.stackplot(self.df['DateTime'], 
                           *[normalized_df[col] for col in important_vars],
                           labels=important_vars, alpha=0.7)
                
                ax.set_title('Biểu Đồ Vùng: Tổng Hợp Các Yếu Tố Thời Tiết (Đã Chuẩn Hóa)', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Thời Gian', fontsize=12)
                ax.set_ylabel('Giá Trị Chuẩn Hóa (0-1)', fontsize=12)
                ax.legend(loc='upper left', fontsize=10)
                ax.grid(True, alpha=0.3)
                
                plt.xticks(rotation=45, ha='right')
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                
                plt.tight_layout()
                
                filename = "07_area_chart_multiple_variables.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ area chart: {e}")
    
    # ============================================================================
    # LOẠI 8: BIỂU ĐỒ VIOLIN - PHÂN BỐ CHI TIẾT
    # ============================================================================
    
    def plot_violin_plots(self):
        """
        Vẽ biểu đồ violin để xem phân bố chi tiết của dữ liệu
        Biểu đồ này kết hợp box plot và density plot, cho thấy phân bố chi tiết hơn
        """
        print("\n" + "=" * 60)
        print("LOẠI 8: BIỂU ĐỒ VIOLIN")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Vẽ violin plot so sánh theo giờ
        if 'Hour' not in self.df.columns:
            self.df['Hour'] = self.df['DateTime'].dt.hour
        
        for col in numeric_cols[:5]:  # Giới hạn 5 cột
            try:
                fig, ax = plt.subplots(figsize=(16, 6))
                
                # Chuẩn bị dữ liệu
                data_list = []
                hour_list = []
                for hour in range(24):
                    hour_data = self.df[self.df['Hour'] == hour][col].dropna()
                    if len(hour_data) > 0:
                        data_list.append(hour_data.values)
                        hour_list.append(hour)
                
                # Vẽ violin plot
                parts = ax.violinplot(data_list, positions=hour_list, 
                                     showmeans=True, showmedians=True)
                
                # Tùy chỉnh màu sắc
                for pc in parts['bodies']:
                    pc.set_facecolor('lightblue')
                    pc.set_alpha(0.7)
                
                ax.set_title(f'Violin Plot: {col} Theo Giờ Trong Ngày', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Giờ Trong Ngày', fontsize=12)
                ax.set_ylabel(col, fontsize=12)
                ax.set_xticks(range(0, 24, 2))
                ax.grid(True, alpha=0.3, axis='y')
                
                plt.tight_layout()
                
                filename = f"08_violin_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ violin plot {col}: {e}")
    
    # ============================================================================
    # LOẠI 9: BIỂU ĐỒ PIE CHART - PHÂN BỐ PHẦN TRĂM
    # ============================================================================
    
    def plot_pie_charts(self):
        """
        Vẽ biểu đồ tròn (Pie Chart) để xem phân bố phần trăm
        Biểu đồ này phù hợp cho dữ liệu phân loại hoặc tỷ lệ
        """
        print("\n" + "=" * 60)
        print("LOẠI 9: BIỂU ĐỒ TRÒN (PIE CHARTS)")
        print("=" * 60)
        
        # Tạo cột phân loại thời gian trong ngày
        if 'Hour' not in self.df.columns:
            self.df['Hour'] = self.df['DateTime'].dt.hour
        
        def categorize_time(hour):
            """Phân loại thời gian trong ngày"""
            if 5 <= hour < 12:
                return 'Sáng (5h-12h)'
            elif 12 <= hour < 17:
                return 'Trưa (12h-17h)'
            elif 17 <= hour < 20:
                return 'Chiều (17h-20h)'
            else:
                return 'Tối/Đêm (20h-5h)'
        
        self.df['TimeCategory'] = self.df['Hour'].apply(categorize_time)
        
        # Vẽ pie chart cho phân bố thời gian
        try:
            time_counts = self.df['TimeCategory'].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            wedges, texts, autotexts = ax.pie(time_counts.values, 
                                             labels=time_counts.index,
                                             autopct='%1.1f%%',
                                             startangle=90,
                                             colors=colors[:len(time_counts)],
                                             explode=[0.05] * len(time_counts))
            
            # Tùy chỉnh text
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)
            
            ax.set_title('Phân Bố Dữ Liệu Theo Thời Gian Trong Ngày', 
                        fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            filename = "09_pie_time_distribution.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"✓ Đã lưu: {filepath}")
            
            plt.close()
            
        except Exception as e:
            print(f"✗ Lỗi khi vẽ pie chart: {e}")
    
    # ============================================================================
    # LOẠI 10: BIỂU ĐỒ 3D - MỐI QUAN HỆ 3 CHIỀU
    # ============================================================================
    
    def plot_3d_scatter(self):
        """
        Vẽ biểu đồ 3D scatter plot để xem mối quan hệ giữa 3 biến
        Biểu đồ này giúp hiểu mối tương quan phức tạp giữa nhiều yếu tố
        """
        print("\n" + "=" * 60)
        print("LOẠI 10: BIỂU ĐỒ 3D SCATTER")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 3:
            print("Cần ít nhất 3 cột số để vẽ 3D scatter plot!")
            return
        
        # Tìm 3 biến quan trọng
        x_var = None
        y_var = None
        z_var = None
        
        for var_name in ['Temperature', 'Irradiance', 'Humidity']:
            matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
            if matching_cols:
                if x_var is None:
                    x_var = matching_cols[0]
                elif y_var is None:
                    y_var = matching_cols[0]
                elif z_var is None:
                    z_var = matching_cols[0]
                    break
        
        if x_var and y_var and z_var:
            try:
                from mpl_toolkits.mplot3d import Axes3D
                
                fig = plt.figure(figsize=(14, 10))
                ax = fig.add_subplot(111, projection='3d')
                
                # Lấy mẫu dữ liệu để vẽ nhanh hơn (nếu quá nhiều điểm)
                sample_size = min(5000, len(self.df))
                sample_df = self.df.sample(n=sample_size) if len(self.df) > sample_size else self.df
                
                # Vẽ scatter plot 3D
                scatter = ax.scatter(sample_df[x_var], 
                                   sample_df[y_var], 
                                   sample_df[z_var],
                                   c=sample_df[z_var], 
                                   cmap='viridis',
                                   alpha=0.6,
                                   s=20)
                
                ax.set_xlabel(x_var, fontsize=12)
                ax.set_ylabel(y_var, fontsize=12)
                ax.set_zlabel(z_var, fontsize=12)
                ax.set_title(f'3D Scatter Plot: {x_var} vs {y_var} vs {z_var}', 
                           fontsize=16, fontweight='bold', pad=20)
                
                # Thêm colorbar
                plt.colorbar(scatter, ax=ax, label=z_var)
                
                plt.tight_layout()
                
                filename = f"10_3d_scatter_{x_var.replace(' ', '_')}_{y_var.replace(' ', '_')}_{z_var.replace(' ', '_')}.png"
                filename = filename.replace('/', '_')
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ 3D scatter plot: {e}")
        else:
            print("Không tìm đủ 3 biến để vẽ 3D scatter plot!")
    
    # ============================================================================
    # LOẠI 11: BIỂU ĐỒ PHÂN TÍCH NÂNG CAO - ROLLING STATISTICS
    # ============================================================================
    
    def plot_rolling_statistics(self):
        """
        Vẽ biểu đồ thống kê trượt (Rolling Statistics) để xem xu hướng và biến động
        Biểu đồ này giúp làm mịn dữ liệu và phát hiện xu hướng dài hạn
        """
        print("\n" + "=" * 60)
        print("LOẠI 11: BIỂU ĐỒ THỐNG KÊ TRƯỢT (ROLLING STATISTICS)")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Tìm các biến quan trọng
        important_vars = []
        for var_name in ['Temperature', 'Irradiance', 'Humidity', 'Wind']:
            matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
            if matching_cols:
                important_vars.append(matching_cols[0])
        
        # Vẽ rolling statistics cho các biến quan trọng
        for col in important_vars[:5]:  # Giới hạn 5 biến
            try:
                # Tính toán rolling statistics
                window_sizes = [6, 24, 168]  # 6 giờ, 24 giờ, 1 tuần (nếu có đủ dữ liệu)
                window_labels = ['6 giờ', '24 giờ', '1 tuần']
                
                fig, axes = plt.subplots(2, 1, figsize=(16, 10))
                
                # Plot 1: Rolling mean
                ax1 = axes[0]
                ax1.plot(self.df['DateTime'], self.df[col], 
                        alpha=0.3, color='lightblue', label='Giá trị gốc', linewidth=0.5)
                
                for window, label in zip(window_sizes, window_labels):
                    if len(self.df) >= window:
                        rolling_mean = self.df[col].rolling(window=window, center=True).mean()
                        ax1.plot(self.df['DateTime'], rolling_mean, 
                               label=f'Trung bình trượt {label}', linewidth=2)
                
                ax1.set_title(f'Rolling Mean: {col}', fontsize=16, fontweight='bold', pad=20)
                ax1.set_ylabel(col, fontsize=12)
                ax1.legend(loc='best')
                ax1.grid(True, alpha=0.3)
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
                ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                
                # Plot 2: Rolling std
                ax2 = axes[1]
                for window, label in zip(window_sizes, window_labels):
                    if len(self.df) >= window:
                        rolling_std = self.df[col].rolling(window=window, center=True).std()
                        ax2.plot(self.df['DateTime'], rolling_std, 
                               label=f'Độ lệch chuẩn trượt {label}', linewidth=2)
                
                ax2.set_title(f'Rolling Standard Deviation: {col}', 
                            fontsize=16, fontweight='bold', pad=20)
                ax2.set_xlabel('Thời Gian', fontsize=12)
                ax2.set_ylabel(f'Std {col}', fontsize=12)
                ax2.legend(loc='best')
                ax2.grid(True, alpha=0.3)
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
                ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                
                plt.tight_layout()
                
                filename = f"11_rolling_stats_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                self.charts_created += 1
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ rolling statistics {col}: {e}")
    
    # ============================================================================
    # LOẠI 12: BIỂU ĐỒ SO SÁNH THEO NGÀY TRONG TUẦN/THÁNG
    # ============================================================================
    
    def plot_time_comparison(self):
        """
        Vẽ biểu đồ so sánh theo ngày trong tuần và tháng
        Biểu đồ này giúp phát hiện patterns theo chu kỳ tuần/tháng
        """
        print("\n" + "=" * 60)
        print("LOẠI 12: BIỂU ĐỒ SO SÁNH THEO THỜI GIAN")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Tạo các cột thời gian
        if 'Hour' not in self.df.columns:
            self.df['Hour'] = self.df['DateTime'].dt.hour
        self.df['DayOfWeek'] = self.df['DateTime'].dt.dayofweek
        self.df['Month'] = self.df['DateTime'].dt.month
        self.df['DayName'] = self.df['DateTime'].dt.day_name()
        
        # Tìm biến quan trọng
        important_vars = []
        for var_name in ['Temperature', 'Irradiance', 'Humidity']:
            matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
            if matching_cols:
                important_vars.append(matching_cols[0])
        
        # 12.1. So sánh theo ngày trong tuần
        print("\n12.1. Vẽ biểu đồ so sánh theo ngày trong tuần...")
        for col in important_vars[:3]:
            try:
                day_avg = self.df.groupby('DayOfWeek')[col].mean()
                day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
                
                fig, ax = plt.subplots(figsize=(12, 6))
                
                bars = ax.bar(range(7), [day_avg.get(i, 0) for i in range(7)], 
                            color='steelblue', alpha=0.7, edgecolor='black', linewidth=1)
                
                ax.set_title(f'Giá Trị Trung Bình {col} Theo Ngày Trong Tuần', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Ngày Trong Tuần', fontsize=12)
                ax.set_ylabel(f'Trung Bình {col}', fontsize=12)
                ax.set_xticks(range(7))
                ax.set_xticklabels(day_names, rotation=45, ha='right')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Thêm giá trị trên cột
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                filename = f"12_weekly_comparison_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                self.charts_created += 1
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ so sánh theo tuần {col}: {e}")
        
        # 12.2. So sánh theo tháng
        print("\n12.2. Vẽ biểu đồ so sánh theo tháng...")
        for col in important_vars[:3]:
            try:
                month_avg = self.df.groupby('Month')[col].mean()
                month_names = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 
                             'T7', 'T8', 'T9', 'T10', 'T11', 'T12']
                
                fig, ax = plt.subplots(figsize=(12, 6))
                
                bars = ax.bar(month_avg.index, month_avg.values, 
                            color='coral', alpha=0.7, edgecolor='black', linewidth=1)
                
                ax.set_title(f'Giá Trị Trung Bình {col} Theo Tháng', 
                           fontsize=16, fontweight='bold', pad=20)
                ax.set_xlabel('Tháng', fontsize=12)
                ax.set_ylabel(f'Trung Bình {col}', fontsize=12)
                ax.set_xticks(range(1, 13))
                ax.set_xticklabels(month_names)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Thêm giá trị trên cột
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                
                filename = f"12_monthly_comparison_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                self.charts_created += 1
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ so sánh theo tháng {col}: {e}")
    
    # ============================================================================
    # LOẠI 13: BIỂU ĐỒ PHÂN TÍCH OUTLIERS
    # ============================================================================
    
    def plot_outlier_analysis(self):
        """
        Vẽ biểu đồ phân tích outliers để phát hiện giá trị bất thường
        Biểu đồ này giúp xác định các điểm dữ liệu ngoại lai
        """
        print("\n" + "=" * 60)
        print("LOẠI 13: BIỂU ĐỒ PHÂN TÍCH OUTLIERS")
        print("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            print("Không tìm thấy cột số để vẽ!")
            return
        
        # Tìm các biến quan trọng
        important_vars = []
        for var_name in ['Temperature', 'Irradiance', 'Humidity', 'Wind']:
            matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
            if matching_cols:
                important_vars.append(matching_cols[0])
        
        for col in important_vars[:5]:
            try:
                # Tính IQR để xác định outliers
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Xác định outliers
                outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
                
                fig, axes = plt.subplots(2, 1, figsize=(14, 10))
                
                # Plot 1: Time series với outliers được đánh dấu
                ax1 = axes[0]
                ax1.plot(self.df['DateTime'], self.df[col], 
                        alpha=0.5, color='lightblue', label='Dữ liệu bình thường', linewidth=0.5)
                
                if len(outliers) > 0:
                    ax1.scatter(outliers['DateTime'], outliers[col], 
                              color='red', s=30, alpha=0.7, label='Outliers', zorder=5)
                
                ax1.axhline(y=upper_bound, color='orange', linestyle='--', 
                          linewidth=2, label=f'Upper bound ({upper_bound:.2f})')
                ax1.axhline(y=lower_bound, color='orange', linestyle='--', 
                          linewidth=2, label=f'Lower bound ({lower_bound:.2f})')
                
                ax1.set_title(f'Phân Tích Outliers: {col}\n(Số outliers: {len(outliers)})', 
                            fontsize=16, fontweight='bold', pad=20)
                ax1.set_ylabel(col, fontsize=12)
                ax1.legend(loc='best')
                ax1.grid(True, alpha=0.3)
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
                ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m/%Y %H:%M'))
                
                # Plot 2: Box plot với outliers
                ax2 = axes[1]
                bp = ax2.boxplot(self.df[col].dropna(), vert=True, patch_artist=True,
                                boxprops=dict(facecolor='lightblue', alpha=0.7),
                                medianprops=dict(color='red', linewidth=2),
                                showfliers=True)
                
                ax2.set_title(f'Box Plot: {col} (Outliers được hiển thị)', 
                            fontsize=14, fontweight='bold')
                ax2.set_ylabel(col, fontsize=12)
                ax2.grid(True, alpha=0.3, axis='y')
                
                # Thêm thống kê
                stats_text = f'Q1: {Q1:.2f}\nQ3: {Q3:.2f}\nIQR: {IQR:.2f}\nOutliers: {len(outliers)} ({len(outliers)/len(self.df)*100:.1f}%)'
                ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                
                plt.tight_layout()
                
                filename = f"13_outliers_{col.replace(' ', '_').replace('/', '_')}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                print(f"✓ Đã lưu: {filepath}")
                self.charts_created += 1
                
                plt.close()
                
            except Exception as e:
                print(f"✗ Lỗi khi vẽ outlier analysis {col}: {e}")
    
    # ============================================================================
    # LOẠI 14: TẠO BÁO CÁO TỔNG HỢP
    # ============================================================================
    
    def generate_summary_report(self):
        """
        Tạo file báo cáo tổng hợp thống kê về dữ liệu
        """
        print("\n" + "=" * 60)
        print("LOẠI 14: TẠO BÁO CÁO TỔNG HỢP")
        print("=" * 60)
        
        try:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("BÁO CÁO TỔNG HỢP DỮ LIỆU WEATHER REPORTS")
            report_lines.append("=" * 80)
            report_lines.append(f"\nNgày tạo báo cáo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"\nThông tin dữ liệu:")
            report_lines.append(f"  - Tổng số bản ghi: {len(self.df):,}")
            report_lines.append(f"  - Số cột: {len(self.df.columns)}")
            report_lines.append(f"  - Số cột số: {len(numeric_cols)}")
            
            if 'DateTime' in self.df.columns and len(self.df) > 0:
                report_lines.append(f"  - Thời gian bắt đầu: {self.df['DateTime'].min()}")
                report_lines.append(f"  - Thời gian kết thúc: {self.df['DateTime'].max()}")
                duration = self.df['DateTime'].max() - self.df['DateTime'].min()
                report_lines.append(f"  - Khoảng thời gian: {duration.days} ngày")
            
            report_lines.append("\n" + "=" * 80)
            report_lines.append("THỐNG KÊ MÔ TẢ CÁC BIẾN QUAN TRỌNG")
            report_lines.append("=" * 80)
            
            # Thống kê cho các biến quan trọng
            important_vars = []
            for var_name in ['Temperature', 'Irradiance', 'Humidity', 'Wind', 'Pressure']:
                matching_cols = [col for col in numeric_cols if var_name.lower() in col.lower()]
                if matching_cols:
                    important_vars.append(matching_cols[0])
            
            for col in important_vars[:10]:
                stats = self.df[col].describe()
                report_lines.append(f"\n{col}:")
                report_lines.append(f"  - Count: {stats['count']:,.0f}")
                report_lines.append(f"  - Mean: {stats['mean']:.2f}")
                report_lines.append(f"  - Std: {stats['std']:.2f}")
                report_lines.append(f"  - Min: {stats['min']:.2f}")
                report_lines.append(f"  - 25%: {stats['25%']:.2f}")
                report_lines.append(f"  - 50% (Median): {stats['50%']:.2f}")
                report_lines.append(f"  - 75%: {stats['75%']:.2f}")
                report_lines.append(f"  - Max: {stats['max']:.2f}")
                report_lines.append(f"  - Missing values: {self.df[col].isnull().sum()} ({self.df[col].isnull().sum()/len(self.df)*100:.1f}%)")
            
            report_lines.append("\n" + "=" * 80)
            report_lines.append("MA TRẬN TƯƠNG QUAN")
            report_lines.append("=" * 80)
            
            if len(important_vars) >= 2:
                corr_matrix = self.df[important_vars].corr()
                report_lines.append("\n" + corr_matrix.to_string())
            
            report_lines.append("\n" + "=" * 80)
            report_lines.append("KẾT THÚC BÁO CÁO")
            report_lines.append("=" * 80)
            
            # Lưu báo cáo
            report_path = self.output_dir / "summary_report.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            print(f"✓ Đã tạo báo cáo: {report_path}")
            self.charts_created += 1
            
        except Exception as e:
            print(f"✗ Lỗi khi tạo báo cáo: {e}")
    
    # ============================================================================
    # HÀM CHẠY TẤT CẢ CÁC BIỂU ĐỒ
    # ============================================================================
    
    def visualize_all(self, chart_types: Optional[List[str]] = None):
        """
        Chạy tất cả các loại biểu đồ hoặc chỉ các loại được chỉ định
        
        Args:
            chart_types: Danh sách các loại biểu đồ cần vẽ. 
                        Nếu None, vẽ tất cả. 
                        Các giá trị có thể: 'line', 'bar', 'scatter', 'heatmap', 
                        'box', 'histogram', 'area', 'violin', 'pie', '3d', 
                        'rolling', 'time_comparison', 'outliers', 'summary'
        """
        print("\n" + "=" * 80)
        print("BẮT ĐẦU TRỰC QUAN HÓA DỮ LIỆU WEATHER REPORTS")
        print("=" * 80)
        
        # Load dữ liệu
        self.load_data()
        
        # Hiển thị thông tin
        self.show_data_info()
        
        # Định nghĩa mapping các loại biểu đồ
        chart_functions = {
            'line': self.plot_line_charts,
            'bar': self.plot_bar_charts,
            'scatter': self.plot_scatter_plots,
            'heatmap': self.plot_heatmaps,
            'box': self.plot_box_plots,
            'histogram': self.plot_histograms,
            'area': self.plot_area_charts,
            'violin': self.plot_violin_plots,
            'pie': self.plot_pie_charts,
            '3d': self.plot_3d_scatter,
            'rolling': self.plot_rolling_statistics,
            'time_comparison': self.plot_time_comparison,
            'outliers': self.plot_outlier_analysis,
            'summary': self.generate_summary_report
        }
        
        # Nếu không chỉ định, vẽ tất cả
        if chart_types is None:
            chart_types = list(chart_functions.keys())
        
        # Vẽ các biểu đồ được chỉ định
        total_charts = len(chart_types)
        for idx, chart_type in enumerate(chart_types, 1):
            if chart_type in chart_functions:
                if self.show_progress:
                    print(f"\n[{idx}/{total_charts}] Đang vẽ: {chart_type}...")
                try:
                    chart_functions[chart_type]()
                except Exception as e:
                    print(f"✗ Lỗi khi vẽ {chart_type}: {e}")
            else:
                print(f"⚠ Cảnh báo: Loại biểu đồ '{chart_type}' không được hỗ trợ!")
        
        print("\n" + "=" * 80)
        print("HOÀN THÀNH TRỰC QUAN HÓA!")
        print("=" * 80)
        print(f"\nTất cả biểu đồ đã được lưu vào thư mục: {self.output_dir}")
        total_files = len(list(self.output_dir.glob('*.png'))) + len(list(self.output_dir.glob('*.txt')))
        print(f"Tổng số file đã tạo: {total_files}")
        print(f"  - Biểu đồ PNG: {len(list(self.output_dir.glob('*.png')))}")
        print(f"  - Báo cáo TXT: {len(list(self.output_dir.glob('*.txt')))}")


# ============================================================================
# HÀM MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Trực quan hóa dữ liệu Weather Reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Vẽ tất cả biểu đồ
  python visualize_weather_reports.py
  
  # Vẽ chỉ một số loại biểu đồ
  python visualize_weather_reports.py --charts line bar scatter
  
  # Lọc dữ liệu theo khoảng thời gian
  python visualize_weather_reports.py --start-date 2025-01-01 --end-date 2025-01-31
  
  # Kết hợp các tùy chọn
  python visualize_weather_reports.py --charts line heatmap --start-date 2025-01-01
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        default="datasets/Weather reports (1-27)10.xlsm",
        help='Đường dẫn đến file Weather reports (mặc định: datasets/Weather reports (1-27)10.xlsm)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Ngày bắt đầu lọc dữ liệu (format: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='Ngày kết thúc lọc dữ liệu (format: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--charts',
        type=str,
        nargs='+',
        default=None,
        choices=['line', 'bar', 'scatter', 'heatmap', 'box', 'histogram', 
                'area', 'violin', 'pie', '3d', 'rolling', 'time_comparison', 
                'outliers', 'summary', 'all'],
        help='Các loại biểu đồ cần vẽ (mặc định: tất cả)'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Không hiển thị tiến trình'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra file có tồn tại không
    if not Path(args.file).exists():
        print(f"Lỗi: Không tìm thấy file {args.file}")
        print("Vui lòng kiểm tra đường dẫn file!")
        sys.exit(1)
    
    # Xử lý chart types
    chart_types = args.charts
    if chart_types and 'all' in chart_types:
        chart_types = None
    
    # Tạo visualizer và chạy
    visualizer = WeatherReportsVisualizer(
        file_path=args.file,
        start_date=args.start_date,
        end_date=args.end_date,
        show_progress=not args.no_progress
    )
    visualizer.visualize_all(chart_types=chart_types)

