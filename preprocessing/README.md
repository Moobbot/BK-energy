# Preprocessing Pipeline

Pipeline xử lý dữ liệu năng lượng từ nhiều nguồn khác nhau để chuẩn bị cho mô hình machine learning.

## Cấu trúc

Pipeline được chia thành các module riêng biệt:

### 1. **loaders.py** - Data Loaders

Module để load dữ liệu từ các nguồn khác nhau:

- `PVForecastLoader`: Load file PV Forecast CSV
- `PowerReportsLoader`: Load file Power Reports Excel
- `WeatherReportsLoader`: Load file Weather Reports Excel
- `EnergyReportsLoader`: Load file Energy Reports Excel
- `APSLogLoader`: Load các file APS Log CSV

### 2. **cleaners.py** - Data Cleaners

Module để làm sạch và chuẩn hóa dữ liệu:

- Xóa duplicates
- Xử lý missing values (drop, fill_zero, interpolate, forward_fill)
- Xóa outliers (IQR method, Z-score method)
- Merge nhiều DataFrame theo datetime

### 3. **feature_engineering.py** - Feature Engineering

Module để tạo features cho mô hình:

- **Time features**: hour, day_of_week, month, is_weekend, cyclical encodings
- **Lag features**: Giá trị ở các thời điểm trước (lag 1, 2, 3, 6, 12, 24)
- **Rolling features**: Mean, std, min, max trong các window (3, 6, 12, 24)
- **Difference features**: Chênh lệch giữa các thời điểm
- **Interaction features**: Tương tác giữa các features (multiply, divide, add, subtract)

### 4. **pipeline.py** - Main Pipeline

Pipeline chính kết hợp tất cả các bước:

- `PreprocessingPipeline`: Class chính để chạy toàn bộ pipeline

## Cách sử dụng

### Sử dụng đơn giản

```python
from preprocessing import PreprocessingPipeline

# Khởi tạo pipeline
pipeline = PreprocessingPipeline(
    datasets_dir='datasets',
    output_dir='processed_data'
)

# Chạy full pipeline
processed_data = pipeline.run_full_pipeline(
    target_column='Power_MW',
    output_filename='processed_data.csv'
)
```

### Sử dụng từng bước

```python
from preprocessing import PreprocessingPipeline

pipeline = PreprocessingPipeline()

# Bước 1: Load dữ liệu
pipeline.load_all_data(
    load_pv_forecast=True,
    load_power_reports=True,
    load_weather_reports=True,
    load_energy_reports=True,
    load_aps_logs=True,
    aps_log_types=['APU Stat 10s', 'APS Stat 10s']
)

# Bước 2: Làm sạch dữ liệu
pipeline.clean_all_data(
    remove_duplicates=True,
    handle_missing='interpolate',
    remove_outliers=True
)

# Bước 3: Merge dữ liệu
pipeline.merge_data(merge_method='outer')

# Bước 4: Tạo features
pipeline.create_features(
    target_column='Power_MW',
    create_time_features=True,
    create_lag_features=True,
    create_rolling_features=True
)

# Bước 5: Lưu dữ liệu
pipeline.save_processed_data(filename='processed_data.csv')
```

### Chạy script example

```bash
python run_preprocessing.py
```

## Các tùy chọn

### Load Options

- `load_pv_forecast`: Load PV Forecast CSV (default: True)
- `load_power_reports`: Load Power Reports Excel (default: True)
- `load_weather_reports`: Load Weather Reports Excel (default: True)
- `load_energy_reports`: Load Energy Reports Excel (default: True)
- `load_aps_logs`: Load APS Logs CSV (default: True)
- `aps_log_types`: Danh sách các log types cần load (None = load tất cả)

### Cleaning Options

- `remove_duplicates`: Xóa duplicates (default: True)
- `handle_missing`: Cách xử lý missing values
  - `'drop'`: Xóa các hàng có missing values
  - `'fill_zero'`: Điền 0
  - `'interpolate'`: Nội suy (default)
  - `'forward_fill'`: Điền giá trị trước đó
- `remove_outliers`: Xóa outliers (default: True)
- `outlier_method`: Phương pháp phát hiện outliers (`'iqr'` hoặc `'zscore'`)
- `outlier_threshold`: Ngưỡng cho outlier detection (default: 3.0)

### Feature Engineering Options

- `create_time_features`: Tạo time features (default: True)
- `create_lag_features`: Tạo lag features (default: True)
- `create_rolling_features`: Tạo rolling features (default: True)
- `create_difference_features`: Tạo difference features (default: False)
- `create_interaction_features`: Tạo interaction features (default: False)

## Output

Pipeline sẽ tạo ra:

1. **processed_data/processed_data.csv**: File CSV chứa tất cả dữ liệu đã được merge và có features
2. **processed_data/individual/**: Thư mục chứa từng dataset riêng biệt đã được làm sạch

## Ví dụ

Xem file `run_preprocessing.py` để có ví dụ đầy đủ về cách sử dụng pipeline.

## Lưu ý

- Pipeline tự động xử lý các định dạng datetime khác nhau
- Các cột numeric sẽ được tự động phát hiện và xử lý
- Missing values sẽ được xử lý theo phương pháp đã chọn
- Outliers sẽ được phát hiện và xử lý (thay thế bằng giá trị nội suy)
- Features sẽ được tạo tự động dựa trên các cột có sẵn
