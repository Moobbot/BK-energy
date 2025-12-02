# Giải Thích Cấu Trúc Dữ Liệu Energy Reports

## 📋 Mục Lục

1. [Cấu trúc file Excel gốc](#cấu-trúc-file-excel-gốc)
2. [Cấu trúc bảng dữ liệu](#cấu-trúc-bảng-dữ-liệu)
3. [Các nhóm dữ liệu](#các-nhóm-dữ-liệu)
4. [Quy trình phân tích dữ liệu](#quy-trình-phân-tích-dữ-liệu)
5. [Cấu trúc dữ liệu đầu ra](#cấu-trúc-dữ-liệu-đầu-ra)
6. [Ví dụ minh họa](#ví-dụ-minh-họa)

---

## 📁 Cấu Trúc File Excel Gốc

### 1. Tổng quan

File Excel Energy Reports có cấu trúc **multi-row header** (header nhiều dòng) với thông tin về Blocks và Inverters.

```
File: Energy reports 01102025 - 27102025.xls
Sheet: Energy Report
Kích thước: ~639 hàng x 104 cột
Khoảng thời gian: 01/10/2025 đến 27/10/2025
```

### 2. Cấu trúc Header (3-4 dòng đầu)

#### **Hàng 1-2: Tiêu đề và thông tin chung**

```
Hàng 1: [Trống hoặc tiêu đề]
Hàng 2: [Trống hoặc thông tin hệ thống]
```

#### **Hàng 3: Header chính - Date Time và Block names**

```
Cột 0: [Trống]
Cột 1: "Date Time"
Cột 2+: Tên các Block (BLOCK 1, BLOCK 2, ..., BLOCK 24)
```

**Ví dụ:**

```
, Date Time, BLOCK 1, BLOCK 2, BLOCK 3, ..., BLOCK 24
```

#### **Hàng 4: Header phụ - Inverter names**

```
Cột 0: [Trống]
Cột 1: [Trống]
Cột 2+: Tên các Inverter (INV 1, INV 2, ...)
```

**Ví dụ:**

```
, , INV 1, INV 1, INV 1, ..., INV 1
```

**Lưu ý:** Mỗi Block có thể có nhiều Inverter, nên có thể có nhiều cột "INV 1" cho các Block khác nhau.

### 3. Cấu trúc dữ liệu (từ hàng 5 trở đi)

Mỗi hàng dữ liệu có cấu trúc:

```
[Trống], [DateTime], [Value Block1_INV1], [Value Block1_INV2], ..., [Value BlockN_INVX]
```

**Ví dụ:**

```
, 01/10/2025 00:00, 35001.464, 39246.96, 39380.108, 39783.128, ...
```

**Đặc điểm:**

- **Cột 0**: Thường trống hoặc chứa thông tin phụ
- **Cột 1**: DateTime (ví dụ: "01/10/2025 00:00")
- **Cột 2+**: Giá trị năng lượng tích lũy (cumulative energy) cho từng Block/Inverter

---

## 🗂️ Các Nhóm Dữ Liệu

### 1. Cấu trúc Block và Inverter

File Energy Reports tổ chức dữ liệu theo cấu trúc phân cấp:

```
Hệ thống
└── Block 1
    ├── INV 1
    ├── INV 2
    └── ...
└── Block 2
    ├── INV 1
    ├── INV 2
    └── ...
...
└── Block 24
    ├── INV 1
    └── ...
```

### 2. Tên cột được tạo

Khi parse file, tên cột được tạo bằng cách kết hợp Block name và Inverter name:

**Quy tắc:**

- Nếu có cả Block name và Inverter name: `{Block}_{Inverter}`
- Nếu chỉ có Block name: `{Block}`
- Nếu chỉ có Inverter name: `{Inverter}`
- Nếu không có: `Column_{index}`

**Ví dụ tên cột:**

```
DateTime, BLOCK 1_INV 1, BLOCK 1_INV 2, BLOCK 2_INV 1, BLOCK 2_INV 2, ...
```

### 3. Phân loại cột dữ liệu

Sau khi parse, các cột được phân loại:

#### **a. Inverter Columns (24 cột)**

Các cột chứa "INV" trong tên:

- `BLOCK 1_INV 1`, `BLOCK 2_INV 1`, ..., `BLOCK 24_INV 1`
- Đại diện cho năng lượng tích lũy của từng inverter

#### **b. Block Columns (24 cột)**

Các cột chứa "BLOCK" trong tên (nếu có cột tổng hợp theo block):

- `BLOCK 1`, `BLOCK 2`, ..., `BLOCK 24`
- Đại diện cho năng lượng tổng hợp của từng block

#### **c. Other Columns**

Các cột khác không thuộc 2 loại trên:

- `DateTime`: Thời gian
- Các cột phụ khác (nếu có)

---

## ⚙️ Quy Trình Phân Tích Dữ Liệu

### Bước 1: Đọc file Excel

```python
# Đọc file Excel không có header để xử lý thủ công
df = pd.read_excel('Energy reports 01102025 - 27102025.xls',
                   sheet_name=0, header=None)
```

**Kết quả**: DataFrame với tất cả dữ liệu, không có header tự động.

### Bước 2: Tìm hàng header

Script tìm hàng chứa "Date Time":

```python
for idx in range(min(10, len(df))):
    if df.iloc[idx, 1] == 'Date Time' or 'Date Time' in str(df.iloc[idx, 1]):
        date_time_row = idx  # Thường là hàng 3 (index 3)
        break
```

**Kết quả**: Xác định được hàng header (thường là hàng 3).

### Bước 3: Tạo tên cột từ 2 hàng header

```python
header_row1 = df.iloc[date_time_row].values      # Hàng 3: Date Time + Block names
header_row2 = df.iloc[date_time_row + 1].values  # Hàng 4: Inverter names

column_names = []
for i in range(len(header_row1)):
    col1 = str(header_row1[i]) if pd.notna(header_row1[i]) else ''
    col2 = str(header_row2[i]) if pd.notna(header_row2[i]) else ''

    if col1 == 'Date Time':
        column_names.append('DateTime')
    elif col1 and col1 != 'nan':
        # Có Block name
        if col2 and col2 != 'nan':
            column_names.append(f"{col1}_{col2}")  # BLOCK 1_INV 1
        else:
            column_names.append(col1)  # BLOCK 1
    elif col2 and col2 != 'nan':
        column_names.append(col2)  # INV 1
    else:
        column_names.append(f"Column_{i}")
```

**Kết quả**: Danh sách tên cột:

```
['DateTime', 'BLOCK 1_INV 1', 'BLOCK 1_INV 2', 'BLOCK 2_INV 1', ...]
```

### Bước 4: Trích xuất dữ liệu

```python
# Dữ liệu bắt đầu từ hàng sau header (hàng 5)
data_start_row = date_time_row + 2
data_df = df.iloc[data_start_row:].copy()
data_df.columns = column_names[:len(data_df.columns)]
```

**Kết quả**: DataFrame với header đã được gán tên cột.

### Bước 5: Xử lý DateTime

```python
data_df['DateTime'] = pd.to_datetime(
    data_df['DateTime'],
    format='%d/%m/%Y %H:%M',
    errors='coerce'
)
# Loại bỏ hàng không có DateTime hợp lệ
data_df = data_df[data_df['DateTime'].notna()].copy()
```

**Kết quả**: DateTime đã được parse thành datetime object.

### Bước 6: Chuyển đổi dữ liệu số

```python
for col in data_df.columns:
    if col != 'DateTime':
        data_df[col] = pd.to_numeric(data_df[col], errors='coerce')
```

**Kết quả**: Tất cả các cột số đã được chuyển đổi thành numeric.

### Bước 7: Tính toán năng lượng sản xuất

**Quan trọng:** Dữ liệu trong file là **năng lượng tích lũy** (cumulative), không phải năng lượng sản xuất trong từng khoảng thời gian.

Để tính năng lượng sản xuất, cần tính **sự thay đổi** (diff):

```python
# Tính năng lượng sản xuất trong khoảng thời gian
for col in numeric_cols:
    # Diff = năng lượng sản xuất trong khoảng thời gian
    energy_production = data_df[col].diff().fillna(0)

    # Tổng năng lượng sản xuất
    total_production = energy_production.sum()
```

**Ví dụ:**

```
Thời điểm        | Năng lượng tích lũy | Năng lượng sản xuất (diff)
01/10/2025 00:00 | 35001.464          | 0 (giá trị đầu tiên)
01/10/2025 01:00 | 35001.464          | 0 (không thay đổi)
01/10/2025 06:00 | 35001.525          | 0.061 (35001.525 - 35001.464)
01/10/2025 07:00 | 35002.395          | 0.870 (35002.395 - 35001.525)
```

---

## 📊 Cấu Trúc Dữ Liệu Đầu Ra

### 1. DataFrame đã xử lý

Sau khi parse, DataFrame có cấu trúc:

```python
DataFrame:
- Index: 0, 1, 2, ..., N
- Columns: DateTime, BLOCK 1_INV 1, BLOCK 1_INV 2, ..., BLOCK 24_INV 1
- Dtypes:
  - DateTime: datetime64[ns]
  - Các cột khác: float64
```

### 2. Phân loại cột

```python
# Inverter columns
inv_cols = [col for col in df.columns if 'INV' in str(col).upper()]
# Kết quả: ['BLOCK 1_INV 1', 'BLOCK 2_INV 1', ..., 'BLOCK 24_INV 1']

# Block columns (nếu có)
block_cols = [col for col in df.columns if 'BLOCK' in str(col).upper()
              and 'INV' not in str(col).upper()]

# Other columns
other_cols = [col for col in df.columns
              if col not in inv_cols and col not in block_cols]
```

### 3. Tính toán thống kê

#### **a. Thống kê mô tả cho từng cột**

```python
stats = {}
for col in numeric_cols:
    data = df[col].dropna()
    stats[col] = {
        'mean': data.mean(),      # Trung bình
        'median': data.median(),  # Trung vị
        'std': data.std(),        # Độ lệch chuẩn
        'min': data.min(),        # Giá trị nhỏ nhất
        'max': data.max(),        # Giá trị lớn nhất
        'sum': data.sum(),        # Tổng (tích lũy cuối cùng)
        'count': len(data)        # Số lượng bản ghi
    }
```

#### **b. Tính tổng năng lượng sản xuất**

```python
total_production = 0
for col in numeric_cols:
    data = df[col].dropna()
    if len(data) > 1:
        # Tính diff (năng lượng sản xuất)
        diff = data.diff().fillna(0)
        # Tổng năng lượng sản xuất
        total_production += diff.sum()
```

#### **c. Top Inverters theo năng lượng sản xuất**

```python
inv_totals = {}
for col in inv_cols:
    data = df[col].dropna()
    if len(data) > 1:
        diff = data.diff().fillna(0)
        inv_totals[col] = diff.sum()

# Sắp xếp và lấy top 10
top_inverters = sorted(inv_totals.items(),
                      key=lambda x: x[1],
                      reverse=True)[:10]
```

---

## 📈 Ví Dụ Minh Họa

### Ví dụ 1: Cấu trúc header trong file Excel

**Hàng 3 (Block names):**

```
, Date Time, BLOCK 1, BLOCK 2, BLOCK 3, ..., BLOCK 24
```

**Hàng 4 (Inverter names):**

```
, , INV 1, INV 1, INV 1, ..., INV 1
```

**Kết quả tên cột:**

```
DateTime, BLOCK 1_INV 1, BLOCK 2_INV 1, BLOCK 3_INV 1, ..., BLOCK 24_INV 1
```

### Ví dụ 2: Dữ liệu thực tế

**Hàng dữ liệu trong file Excel:**

```
, 01/10/2025 00:00, 35001.464, 39246.96, 39380.108, 39783.128, ...
```

**Sau khi parse thành DataFrame:**

```python
DateTime              | BLOCK 1_INV 1 | BLOCK 2_INV 1 | BLOCK 3_INV 1 | ...
2025-10-01 00:00:00  | 35001.464     | 39246.96      | 39380.108     | ...
2025-10-01 01:00:00  | 35001.464     | 39246.96      | 39380.108     | ...
2025-10-01 06:00:00  | 35001.525     | 39247.02      | 39380.169     | ...
```

### Ví dụ 3: Tính năng lượng sản xuất

**Dữ liệu tích lũy:**

```
DateTime              | BLOCK 1_INV 1
2025-10-01 00:00:00  | 35001.464
2025-10-01 01:00:00  | 35001.464  (không thay đổi)
2025-10-01 06:00:00  | 35001.525  (tăng 0.061)
2025-10-01 07:00:00  | 35002.395  (tăng 0.870)
```

**Tính diff (năng lượng sản xuất):**

```python
df['BLOCK 1_INV 1_diff'] = df['BLOCK 1_INV 1'].diff().fillna(0)

Kết quả:
DateTime              | BLOCK 1_INV 1 | BLOCK 1_INV 1_diff
2025-10-01 00:00:00  | 35001.464     | 0.000
2025-10-01 01:00:00  | 35001.464     | 0.000
2025-10-01 06:00:00  | 35001.525     | 0.061
2025-10-01 07:00:00  | 35002.395     | 0.870
```

**Tổng năng lượng sản xuất:**

```python
total = df['BLOCK 1_INV 1_diff'].sum()
# = 0.000 + 0.000 + 0.061 + 0.870 + ... = Tổng năng lượng sản xuất
```

### Ví dụ 4: Phân tích theo giờ trong ngày

```python
# Thêm cột Hour
df['Hour'] = df['DateTime'].dt.hour

# Tính tổng năng lượng theo giờ
hourly_energy = df.groupby('Hour')[numeric_cols].sum().sum(axis=1)

Kết quả:
Hour | Total Energy (MWh)
0    | 1250.5
1    | 1180.3
...
12   | 2450.8  (giờ cao điểm - giữa trưa)
...
23   | 850.2
```

### Ví dụ 5: Heatmap theo ngày và giờ

```python
# Thêm cột Date và Hour
df['Date'] = df['DateTime'].dt.date
df['Hour'] = df['DateTime'].dt.hour

# Tính tổng năng lượng theo ngày và giờ
daily_hourly = df.groupby(['Date', 'Hour'])[numeric_cols].sum().sum(axis=1)

# Tạo pivot table
pivot = daily_hourly.reset_index().pivot(
    index='Date',
    columns='Hour',
    values='Energy'
)

Kết quả (pivot table):
Date       | 0    | 1    | 2    | ... | 12   | ... | 23
2025-10-01| 1250 | 1180 | 1100 | ... | 2450 | ... | 850
2025-10-02| 1280 | 1200 | 1120 | ... | 2500 | ... | 880
...
```

---

## 🔍 Các Phân Tích Chính

### 1. Phân tích theo thời gian

**Mục đích:** Theo dõi xu hướng năng lượng sản xuất theo thời gian

```python
# Tính tổng năng lượng cho mỗi thời điểm
total_energy = df[numeric_cols].sum(axis=1)

# Vẽ biểu đồ
plt.plot(df['DateTime'], total_energy)
```

**Kết quả:** Biểu đồ đường thể hiện tổng năng lượng tích lũy theo thời gian.

### 2. Phân tích theo Inverter

**Mục đích:** So sánh hiệu suất giữa các inverter

```python
# Tính năng lượng sản xuất cho mỗi inverter
inv_production = {}
for col in inv_cols:
    diff = df[col].diff().fillna(0)
    inv_production[col] = diff.sum()

# Sắp xếp và lấy top 10
top_10 = sorted(inv_production.items(),
                key=lambda x: x[1],
                reverse=True)[:10]
```

**Kết quả:** Danh sách top 10 inverter sản xuất nhiều năng lượng nhất.

### 3. Phân tích theo giờ trong ngày

**Mục đích:** Xác định giờ cao điểm sản xuất năng lượng

```python
# Tính tổng năng lượng theo giờ
hourly = df.groupby(df['DateTime'].dt.hour)[numeric_cols].sum().sum(axis=1)
```

**Kết quả:** Biểu đồ cột thể hiện phân bố năng lượng theo giờ (0-23h).

### 4. Phân tích theo ngày và giờ (Heatmap)

**Mục đích:** Xem mẫu sản xuất năng lượng theo ngày và giờ

```python
# Tạo heatmap
pivot = df.groupby(['Date', 'Hour'])[numeric_cols].sum().sum(axis=1)
pivot_table = pivot.reset_index().pivot(index='Date',
                                        columns='Hour',
                                        values='Energy')
sns.heatmap(pivot_table)
```

**Kết quả:** Heatmap màu sắc thể hiện mức độ năng lượng sản xuất.

---

## 📝 Lưu Ý Quan Trọng

### 1. **Dữ liệu là tích lũy (Cumulative)**

⚠️ **Quan trọng:** Giá trị trong file là **năng lượng tích lũy**, không phải năng lượng sản xuất trong từng khoảng thời gian.

- Để tính năng lượng sản xuất: dùng `diff()`
- Để tính tổng năng lượng: lấy giá trị cuối cùng hoặc tổng các `diff()`

### 2. **Tần số lấy mẫu**

- Dữ liệu được ghi **mỗi giờ** (hourly)
- Có thể có khoảng trống nếu hệ thống không hoạt động

### 3. **Cấu trúc Block và Inverter**

- Mỗi Block có thể có nhiều Inverter
- Tên cột được tạo bằng cách kết hợp: `{BLOCK}_{INV}`
- Có thể có 24 Blocks và mỗi Block có 1 hoặc nhiều Inverters

### 4. **Xử lý giá trị thiếu**

- Một số thời điểm có thể không có dữ liệu
- Script tự động loại bỏ các hàng không có DateTime hợp lệ
- Giá trị NaN được xử lý bằng `dropna()` hoặc `fillna()`

### 5. **Đơn vị đo**

- Tất cả giá trị năng lượng đều tính bằng **MWh** (Megawatt-hour)
- Giá trị tích lũy có thể rất lớn (hàng triệu MWh)

---

## 📋 Tóm Tắt

1. **File gốc**: Excel với header 2 dòng (Block names + Inverter names)
2. **Quy trình**:
   - Đọc Excel → Tìm header → Tạo tên cột → Parse DateTime → Chuyển đổi số → Tính diff
3. **Kết quả**:
   - DataFrame với DateTime và các cột Block/Inverter
   - Có thể tính năng lượng sản xuất bằng diff()
   - Có thể phân tích theo thời gian, inverter, giờ, ngày
4. **Lợi ích**:
   - Dễ phân tích hiệu suất từng inverter
   - Xác định giờ cao điểm sản xuất
   - So sánh hiệu suất giữa các block/inverter
   - Phát hiện vấn đề hoặc xu hướng

---

## 🔗 Liên Kết

- **Script phân tích**: `energy_reports_analysis.py`
- **Báo cáo kết quả**: `energy_reports_analysis.md`
- **Biểu đồ**: Thư mục `output/`

---

_Tài liệu này được tạo tự động bởi Energy Reports Analyzer_
