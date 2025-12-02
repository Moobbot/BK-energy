# Giải Thích Cấu Trúc Dữ Liệu APS/APU Log

## 📋 Mục Lục

1. [Cấu trúc file CSV gốc](#cấu-trúc-file-csv-gốc)
2. [Các nhóm dữ liệu](#các-nhóm-dữ-liệu)
3. [Quy trình tách dữ liệu](#quy-trình-tách-dữ-liệu)
4. [Cấu trúc file đầu ra](#cấu-trúc-file-đầu-ra)
5. [Ví dụ minh họa](#ví-dụ-minh-họa)

---

## 📁 Cấu Trúc File CSV Gốc

### 1. Tổng quan

File CSV log APS/APU có cấu trúc **multi-row header** (header nhiều dòng), không phải header đơn giản như CSV thông thường.

```
File: APS-000258_20251001_000000.csv
Kích thước: ~58,335 hàng x 27 cột
```

### 2. Cấu trúc Header (3 dòng đầu)

#### **Hàng 1: Header chung**

```
Log Type, System, Time Stamp, Column Header..., [các cột trống]
```

- Đây là hàng mô tả chung về cấu trúc file
- Không chứa dữ liệu thực tế

#### **Hàng 2-12: Header cho từng nhóm log**

Mỗi nhóm log có **1 hàng header riêng** với cấu trúc:

```
[Log Type], [System], [TimeStamp], [Column 1], [Column 2], ..., [Column N]
```

**Ví dụ hàng header cho "APS Energy":**

```
APS Energy, APS, TimeStamp, W_in_APU1/kWh, W_out_APU1/kWh, W_in_APU2/kWh, ...
```

**Ví dụ hàng header cho "APU Stat 10s":**

```
APU Stat 10s, APU, TimeStamp, VL1N/V, VL2N/V, VL3N/V, VL12/V, IL1/A, PL1/kW, ...
```

### 3. Cấu trúc dữ liệu (từ hàng 13 trở đi)

Mỗi hàng dữ liệu có cấu trúc:

```
[Log Type], [System], [TimeStamp], [Value 1], [Value 2], ..., [Value N]
```

**Đặc điểm:**

- **Cột 0**: Log Type (ví dụ: "APS Energy", "APU Stat 10s")
- **Cột 1**: System (ví dụ: "APS", "APU", "APU 1", "APU 2")
- **Cột 2**: TimeStamp (ví dụ: "01/10/2025 0:00")
- **Cột 3+**: Các giá trị dữ liệu tương ứng với header của nhóm log đó

---

## 🗂️ Các Nhóm Dữ Liệu

File CSV gốc chứa **11 loại log chính**, được chia thành 2 hệ thống:

### **I. Hệ thống APS (Auxiliary Power System)**

#### 1. **APS Ctrl Trig** - Trạng thái điều khiển

- **Chu kỳ**: Event-based (khi có sự kiện)
- **Mục đích**: Ghi lại các lệnh điều khiển và trạng thái thiết bị
- **Các trường chính**:
  - `Milliseconds/ms`: Thời gian giữa các trigger
  - `AirAir1State`, `AirAir2State`, `AirAir3State`: Trạng thái quạt gió
  - `ApuCtrl1On` - `ApuCtrl6On`: Tín hiệu điều khiển APU
  - `EnableOn`, `HeatingOn`: Trạng thái hệ thống
  - `WaterPump1`, `WaterPump2`, `WaterPump3`: Trạng thái bơm nước

#### 2. **APS Energy** - Năng lượng vào/ra

- **Chu kỳ**: Tích lũy (cumulative)
- **Mục đích**: Theo dõi năng lượng tiêu thụ và sản xuất
- **Các trường chính**:
  - `W_in_APU1/kWh` - `W_in_APU6/kWh`: Năng lượng đầu vào từng APU
  - `W_out_APU1/kWh` - `W_out_APU6/kWh`: Năng lượng đầu ra từng APU
  - `W_in_APS/kWh`, `W_out_APS/kWh`: Tổng năng lượng hệ thống

#### 3. **APS Stat 10s** - Thông số tức thời

- **Chu kỳ**: 10 giây
- **Mục đích**: Đo các thông số điện và vật lý
- **Các trường chính**:
  - `Irr/(W/m^2)`: Cường độ bức xạ mặt trời

#### 4. **APS Stat 60s** - Thông số môi trường

- **Chu kỳ**: 60 giây (1 phút)
- **Mục đích**: Đo nhiệt độ và điều kiện môi trường
- **Các trường chính**:
  - `Tamb/°C`: Nhiệt độ môi trường
  - `Tpan/°C`: Nhiệt độ bề mặt tấm pin
  - `Ttrans/°C`: Nhiệt độ bộ biến áp
  - `Riso12/k`, `Riso34/kO`, `Riso56/kO`: Điện trở cách điện
  - `Cleak12/µF`, `Cleak34/µF`, `Cleak56/µF`: Điện dung rò rỉ

#### 5. **APS Stat Trig** - Trạng thái và lỗi

- **Chu kỳ**: Event-based
- **Mục đích**: Ghi lại lỗi, cảnh báo và trạng thái vận hành
- **Các trường chính**:
  - `OpState`: Trạng thái hoạt động
  - `Error1` - `Error8`: Mã lỗi hệ thống
  - `Warning1` - `Warning8`: Cảnh báo

#### 6. **APS Switching Cycles** - Chu kỳ đóng cắt

- **Chu kỳ**: Event count
- **Mục đích**: Đếm số lần đóng/ngắt mạch
- **Các trường chính**:
  - `APU1_AC`, `APU1_DC`, ..., `APU6_AC`, `APU6_DC`: Số chu kỳ AC/DC

### **II. Hệ thống APU (Auxiliary Power Unit)**

#### 7. **APU Ctrl Trig** - Lệnh điều khiển

- **Chu kỳ**: Event-based
- **Mục đích**: Lệnh điều khiển đầu ra từng APU
- **Các trường chính**:
  - `PSetL1/kW` - `PSetL3/kW`: Công suất đặt trên các pha
  - `QSetL1/kvar` - `QSetL3/kvar`: Công suất phản kháng đặt
  - `VislSet/V`, `fislSet/Hz`: Điện áp và tần số điều khiển
  - `OpMode`: Chế độ hoạt động

#### 8. **APU Stat 10s** - Thông số điện

- **Chu kỳ**: 10 giây
- **Mục đích**: Đo điện áp, dòng, công suất
- **Các trường chính**:
  - `VL1N/V` - `VL3N/V`: Điện áp pha-trung tính
  - `VL12/V`, `VL23/V`, `VL31/V`: Điện áp dây-dây
  - `IL1/A` - `IL3/A`: Dòng điện các pha
  - `PL1/kW` - `PL3/kW`: Công suất tác dụng
  - `Vdc/V`, `Idc/A`, `Pdc/kW`: Điện áp, dòng và công suất DC

#### 9. **APU Stat 60s** - Nhiệt độ và độ ẩm

- **Chu kỳ**: 60 giây
- **Mục đích**: Đo nhiệt độ và độ ẩm bên trong APU
- **Các trường chính**:
  - `TInd/°C`: Nhiệt độ bên trong APU
  - `TL1/°C` - `TL3/°C`: Nhiệt độ từng pha
  - `TPCB/°C`: Nhiệt độ mạch PCB
  - `Hum/%RH`: Độ ẩm

#### 10. **APU Stat Trig** - Trạng thái và giới hạn

- **Chu kỳ**: Event-based
- **Mục đích**: Ghi lại trạng thái, giới hạn và lỗi
- **Các trường chính**:
  - `OpState`: Trạng thái hoạt động
  - `PL1Lim/kW` - `PL3Lim/kW`: Giới hạn công suất
  - `Error1` - `Error8`: Mã lỗi

#### 11. **APU Energy** - Năng lượng tích lũy

- **Chu kỳ**: Tích lũy
- **Mục đích**: Theo dõi năng lượng tích lũy từng kênh
- **Các trường chính**:
  - `CH 1 pos/Ah` - `CH 12 pos/Ah`: Điện lượng nạp vào
  - `CH 1 neg/Ah` - `CH 12 neg/Ah`: Điện lượng xả ra

---

## ⚙️ Quy Trình Tách Dữ Liệu

### Bước 1: Đọc file CSV gốc

```python
# Đọc file không có header để xử lý thủ công
df = pd.read_csv('APS-000258_20251001_000000.csv', header=None)
```

**Kết quả**: DataFrame với tất cả dữ liệu, không có header tự động.

### Bước 2: Xác định các hàng header

Script quét các hàng 1-15 để tìm các hàng header của từng nhóm log:

```python
for idx in range(1, 15):
    log_type = df.iloc[idx, 0]  # Cột 0: Log Type
    system = df.iloc[idx, 1]    # Cột 1: System

    # Kiểm tra xem có phải log type hợp lệ không
    if log_type in valid_log_types:
        # Lấy tên các cột từ hàng này (bắt đầu từ cột 3)
        columns = []
        for col_idx in range(3, df.shape[1]):
            col_name = df.iloc[idx, col_idx]
            if col_name and col_name != 'nan':
                columns.append({'index': col_idx, 'name': col_name})
```

**Kết quả**: Dictionary chứa thông tin header cho từng nhóm log:

```python
{
    'APS_Energy_APS': {
        'log_type': 'APS Energy',
        'system': 'APS',
        'header_row': 2,
        'columns': [
            {'index': 3, 'name': 'W_in_APU1/kWh'},
            {'index': 4, 'name': 'W_out_APU1/kWh'},
            ...
        ]
    },
    ...
}
```

### Bước 3: Trích xuất dữ liệu theo nhóm

Script quét tất cả các hàng dữ liệu (từ hàng 13 trở đi):

```python
for idx in range(13, len(df)):
    row_log_type = df.iloc[idx, 0]  # Log type của hàng này
    row_system = df.iloc[idx, 1]     # System của hàng này

    # Tìm header tương ứng
    matching_header = find_header(row_log_type, row_system)

    # Trích xuất dữ liệu từ các cột tương ứng
    row_data = {}
    for col_info in matching_header['columns']:
        col_idx = col_info['index']
        col_name = col_info['name']
        row_data[col_name] = df.iloc[idx, col_idx]

    # Thêm vào nhóm dữ liệu tương ứng
    grouped_data[matching_header].append(row_data)
```

**Kết quả**: Dictionary chứa dữ liệu đã nhóm:

```python
{
    'APS_Energy_APS': [
        {'TimeStamp': '01/10/2025 0:00', 'W_in_APU1/kWh': 2361, ...},
        {'TimeStamp': '01/10/2025 0:01', 'W_in_APU1/kWh': 2361, ...},
        ...
    ],
    ...
}
```

### Bước 4: Chuyển đổi thành DataFrame

```python
for group_key, rows in grouped_data.items():
    # Tạo DataFrame
    group_df = pd.DataFrame(rows)

    # Parse TimeStamp
    group_df['TimeStamp'] = pd.to_datetime(group_df['TimeStamp'], ...)

    # Chuyển đổi các cột số thành numeric
    for col in group_df.columns:
        if col != 'TimeStamp':
            group_df[col] = pd.to_numeric(group_df[col], errors='coerce')
```

### Bước 5: Lưu ra file CSV riêng

```python
# Mapping tên file thân thiện
file_name_mapping = {
    'APS_Energy_APS': 'APS_Energy',
    'APU_Stat_10s_APU': 'APU_Stat10s',
    ...
}

for group_key, group_df in parsed_groups.items():
    file_name = file_name_mapping.get(group_key, group_key)
    file_path = f'parsed_logs/{file_name}.csv'
    group_df.to_csv(file_path, index=False, encoding='utf-8-sig')
```

---

## 📤 Cấu Trúc File Đầu Ra

### Thư mục `parsed_logs/`

Sau khi chạy script, thư mục sẽ chứa:

```
parsed_logs/
├── APS_CtrlTrig.csv          # Trạng thái điều khiển APS
├── APS_Energy.csv            # Năng lượng vào/ra APS
├── APS_Stat10s.csv           # Thông số tức thời (10s)
├── APS_Stat60s.csv           # Thông số môi trường (60s)
├── APS_StatTrig.csv          # Trạng thái và lỗi APS
├── APS_SwitchingCycles.csv   # Chu kỳ đóng cắt
├── APU_CtrlTrig.csv          # Lệnh điều khiển APU
├── APU_Stat10s.csv           # Thông số điện (10s)
├── APU_Stat60s.csv           # Nhiệt độ và độ ẩm (60s)
├── APU_StatTrig.csv          # Trạng thái và lỗi APU
├── APU_Energy.csv            # Năng lượng tích lũy
└── SUMMARY.md                # Báo cáo tóm tắt
```

### Cấu trúc mỗi file CSV

Mỗi file CSV có cấu trúc chuẩn:

```csv
TimeStamp,Column1,Column2,Column3,...
2025-10-01 00:00:00,value1,value2,value3,...
2025-10-01 00:00:10,value1,value2,value3,...
...
```

**Đặc điểm:**

- ✅ Header đơn giản (1 dòng)
- ✅ TimeStamp đã được parse thành datetime
- ✅ Các cột số đã được chuyển đổi thành numeric
- ✅ Dữ liệu đã được sắp xếp theo thời gian
- ✅ Loại bỏ các hàng không hợp lệ

---

## 📊 Ví Dụ Minh Họa

### Ví dụ 1: Tách nhóm "APS Energy"

**Trong file gốc:**

**Hàng header (hàng 3):**

```
APS Energy, APS, TimeStamp, W_in_APU1/kWh, W_out_APU1/kWh, W_in_APU2/kWh, ...
```

**Các hàng dữ liệu:**

```
APS Energy, APS, 01/10/2025 0:00, 2361, 9848165, 2359, ...
APS Energy, APS, 01/10/2025 0:01, 2361, 9848165, 2359, ...
...
```

**Sau khi tách (file `APS_Energy.csv`):**

```csv
TimeStamp,W_in_APU1/kWh,W_out_APU1/kWh,W_in_APU2/kWh,...
2025-10-01 00:00:00,2361,9848165,2359,...
2025-10-01 00:01:00,2361,9848165,2359,...
...
```

### Ví dụ 2: Tách nhóm "APU Stat 10s"

**Trong file gốc:**

**Hàng header (hàng 9):**

```
APU Stat 10s, APU, TimeStamp, VL1N/V, VL2N/V, VL3N/V, IL1/A, PL1/kW, ...
```

**Các hàng dữ liệu:**

```
APU Stat 10s, APU 1, 01/10/2025 0:00, 380.5441, 382.109, 380.4408, 0.4364788, 0, ...
APU Stat 10s, APU 2, 01/10/2025 0:00, 380.5441, 382.109, 380.4408, 0.4583391, 0, ...
...
```

**Sau khi tách (file `APU_Stat10s.csv`):**

```csv
TimeStamp,VL1N/V,VL2N/V,VL3N/V,IL1/A,PL1/kW,...
2025-10-01 00:00:00,380.5441,382.109,380.4408,0.4364788,0,...
2025-10-01 00:00:00,380.5441,382.109,380.4408,0.4583391,0,...
...
```

### Ví dụ 3: Xử lý nhiều APU

Một số nhóm log có thể có nhiều instance (ví dụ: APU 1, APU 2, APU 3, APU 4).

**Trong file gốc:**

```
APU Energy, APU 1, 01/10/2025 0:00, 1636615, 414112.7, ...
APU Energy, APU 2, 01/10/2025 0:00, 985.673, 446695.9, ...
APU Energy, APU 3, 01/10/2025 0:00, 1688996, 440548.1, ...
APU Energy, APU 4, 01/10/2025 0:00, 1632.743, 356514, ...
```

**Sau khi tách:**

- Tất cả các instance được gộp vào cùng một file `APU_Energy.csv`
- Hoặc có thể tách riêng thành `APU_Energy_APU1.csv`, `APU_Energy_APU2.csv`, ... (tùy cấu hình)

---

## 🔍 Lưu Ý Quan Trọng

### 1. **Không phải tất cả nhóm log đều có dữ liệu**

Một số nhóm log có thể chỉ có header mà không có dữ liệu thực tế trong file. Script sẽ bỏ qua các nhóm này.

### 2. **TimeStamp có thể khác nhau**

- Một số nhóm có TimeStamp ở cột 2
- Một số nhóm có thể có tên cột khác (ví dụ: "Date Time")
- Script tự động phát hiện và xử lý

### 3. **Dữ liệu có thể không đồng bộ**

- Các nhóm log khác nhau có thể có tần số lấy mẫu khác nhau
- Khi merge dữ liệu, cần sử dụng `merge_asof` với tolerance phù hợp

### 4. **Encoding và ký tự đặc biệt**

- File gốc có thể chứa ký tự đặc biệt (ví dụ: °C, µF)
- Script sử dụng `utf-8-sig` khi lưu để đảm bảo tương thích với Excel

---

## 📝 Tóm Tắt

1. **File gốc**: CSV với header nhiều dòng, mỗi nhóm log có header riêng
2. **Quy trình**:
   - Đọc file → Xác định header → Nhóm dữ liệu → Chuyển đổi → Lưu file
3. **Kết quả**: Các file CSV riêng biệt, dễ sử dụng cho phân tích
4. **Lợi ích**:
   - Dễ đọc và xử lý
   - Có thể phân tích từng nhóm độc lập
   - TimeStamp đã được chuẩn hóa
   - Dữ liệu số đã được chuyển đổi

---
