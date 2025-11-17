# 📚 Hướng Dẫn Hiểu Dữ Liệu Năng Lượng - Từng Bước

Tài liệu này giải thích chi tiết về dữ liệu năng lượng mặt trời và cách pipeline xử lý chúng, dành cho những người chưa quen với loại dữ liệu này.

---

## 🎯 Mục Đích Của Dữ Liệu

Dự án này thu thập và phân tích dữ liệu từ một **hệ thống điện mặt trời (solar power system)** để:

- Dự đoán công suất sản xuất điện
- Phân tích hiệu suất hệ thống
- Tìm hiểu các yếu tố ảnh hưởng đến sản xuất điện (thời tiết, nhiệt độ, bức xạ mặt trời...)

---

## 📦 Tổng Quan Về Các Nguồn Dữ Liệu

Dự án có **5 nguồn dữ liệu chính**:

| Nguồn Dữ Liệu          | File                                                                  | Mô Tả Ngắn Gọn                                 |
| ---------------------- | --------------------------------------------------------------------- | ---------------------------------------------- |
| **1. PV Forecast**     | `28_10_25_PV_Forecast.csv`                                            | Dự báo công suất điện mặt trời                 |
| **2. Power Reports**   | `Power reports (1-15)102025.xls`<br>`Power reports (16-27)102025.xls` | Báo cáo công suất thực tế                      |
| **3. Weather Reports** | `Weather reports (1-27)10.xlsm`                                       | Dữ liệu thời tiết (nhiệt độ, độ ẩm, bức xạ...) |
| **4. Energy Reports**  | `Energy reports 01102025 - 27102025.xls`                              | Báo cáo năng lượng tích lũy                    |
| **5. APS Logs**        | `inv 24.5/log/*.csv`                                                  | Log chi tiết từ hệ thống inverter              |

---

## 📖 Chi Tiết Từng Nguồn Dữ Liệu

### 1. 📊 PV Forecast (Dự Báo Công Suất)

**File:** `28_10_25_PV_Forecast.csv`

**Mục đích:** Chứa dự báo công suất điện mặt trời cho một ngày cụ thể.

**Cấu trúc:**

```
Date        | Time  | Power (MW)
28/10/2025  | 0:00  | 0
28/10/2025  | 0:15  | 0
28/10/2025  | 0:30  | 0
...
28/10/2025  | 6:00  | 9.40579
28/10/2025  | 12:00 | 119.5943
...
28/10/2025  | 18:00 | 0
```

**Giải thích:**

- **Date**: Ngày dự báo
- **Time**: Thời gian trong ngày (mỗi 15 phút)
- **Power (MW)**: Công suất dự báo tính bằng Megawatt (MW)
  - Ban đêm (0:00-5:00): Thường = 0 (không có ánh sáng mặt trời)
  - Buổi sáng (6:00-12:00): Tăng dần
  - Buổi trưa (12:00-14:00): Đạt đỉnh (nhiều ánh sáng nhất)
  - Buổi chiều (14:00-18:00): Giảm dần
  - Buổi tối (18:00-24:00): Thường = 0

**Ví dụ thực tế:**

- Lúc 6:00 sáng: 9.4 MW (mặt trời mới mọc, công suất thấp)
- Lúc 12:00 trưa: 119.6 MW (mặt trời cao nhất, công suất cao nhất)
- Lúc 18:00 tối: 0 MW (mặt trời lặn, không có điện)

---

### 2. ⚡ Power Reports (Báo Cáo Công Suất)

**Files:**

- `Power reports (1-15)102025.xls`
- `Power reports (16-27)102025.xls`

**Mục đích:** Ghi lại công suất thực tế của hệ thống theo thời gian.

**Cấu trúc:**

```
DateTime            | Power_MW | Voltage_V | Current_A | ...
01/10/2025 00:00   | 0        | 380       | 0         | ...
01/10/2025 00:15   | 0        | 380       | 0         | ...
01/10/2025 06:00   | 8.5      | 380       | 22.4      | ...
01/10/2025 12:00   | 115.3    | 380       | 303.4     | ...
```

**Giải thích:**

- **DateTime**: Thời gian ghi nhận dữ liệu
- **Power_MW**: Công suất thực tế (MW)
- **Voltage_V**: Điện áp (Volt)
- **Current_A**: Dòng điện (Ampere)
- Các cột khác: Thông số kỹ thuật khác của hệ thống

**Khác biệt với PV Forecast:**

- **PV Forecast**: Dự báo (dự đoán trước)
- **Power Reports**: Thực tế (đo được sau đó)

**Tại sao cần cả 2?**

- So sánh dự báo vs thực tế để đánh giá độ chính xác
- Tìm hiểu tại sao dự báo sai (thời tiết xấu, thiết bị hỏng...)

---

### 3. 🌤️ Weather Reports (Báo Cáo Thời Tiết)

**File:** `Weather reports (1-27)10.xlsm`

**Mục đích:** Ghi lại các yếu tố thời tiết ảnh hưởng đến sản xuất điện.

**Cấu trúc:**

```
DateTime            | Temperature_C | Humidity_% | Irradiance_W_m2 | ...
01/10/2025 00:00   | 25            | 80         | 0              | ...
01/10/2025 06:00   | 28            | 75         | 150            | ...
01/10/2025 12:00   | 35            | 60         | 850            | ...
01/10/2025 18:00   | 30            | 70         | 0              | ...
```

**Giải thích:**

- **DateTime**: Thời gian
- **Temperature_C**: Nhiệt độ môi trường (°C)
- **Humidity\_%**: Độ ẩm (%)
- **Irradiance_W_m2**: Bức xạ mặt trời (Watt/m²)
  - 0: Ban đêm hoặc không có ánh sáng
  - 100-500: Sáng sớm/chiều tối
  - 500-1000: Trưa, trời nắng tốt
- Các cột khác: Gió, mây, áp suất...

**Tại sao quan trọng?**

- **Bức xạ mặt trời** ảnh hưởng trực tiếp đến công suất
- **Nhiệt độ** quá cao làm giảm hiệu suất tấm pin
- **Độ ẩm** ảnh hưởng đến điều kiện vận hành

**Mối quan hệ:**

```
Bức xạ cao + Nhiệt độ vừa phải = Công suất cao ✅
Bức xạ thấp + Nhiệt độ cao = Công suất thấp ❌
```

---

### 4. 🔋 Energy Reports (Báo Cáo Năng Lượng)

**File:** `Energy reports 01102025 - 27102025.xls`

**Mục đích:** Ghi lại **năng lượng tích lũy** (tổng năng lượng đã sản xuất từ đầu đến thời điểm đó).

**Cấu trúc:**

```
DateTime            | BLOCK 1_INV 1 | BLOCK 1_INV 2 | BLOCK 2_INV 1 | ...
01/10/2025 00:00   | 35001.464     | 39246.96     | 39380.108     | ...
01/10/2025 01:00   | 35005.120     | 39250.15     | 39383.250     | ...
01/10/2025 02:00   | 35008.500     | 39253.20     | 39386.100     | ...
```

**Giải thích:**

- **DateTime**: Thời gian
- **BLOCK X_INV Y**: Năng lượng tích lũy của Inverter Y trong Block X
- **Giá trị**: Tổng năng lượng từ đầu đến thời điểm đó (MWh)

**⚠️ Lưu ý quan trọng:**

- Đây là **giá trị tích lũy**, không phải năng lượng sản xuất trong 1 giờ
- Để tính năng lượng sản xuất trong 1 giờ, cần lấy hiệu số:
  ```
  Năng lượng 1 giờ = Giá trị hiện tại - Giá trị 1 giờ trước
  ```

**Ví dụ:**

```
00:00: 35001.464 MWh
01:00: 35005.120 MWh
→ Năng lượng sản xuất từ 00:00-01:00 = 35005.120 - 35001.464 = 3.656 MWh
```

**Cấu trúc hệ thống:**

```
Hệ thống
├── BLOCK 1
│   ├── INV 1 (Inverter 1)
│   ├── INV 2 (Inverter 2)
│   └── ...
├── BLOCK 2
│   ├── INV 1
│   └── ...
└── ... (có thể có 24 Blocks)
```

**Tại sao cần?**

- Theo dõi tổng năng lượng sản xuất
- So sánh hiệu suất giữa các Block/Inverter
- Tính toán năng lượng sản xuất theo ngày/tuần/tháng

---

### 5. 📝 APS Logs (Log Hệ Thống Inverter)

**Files:** `inv 24.5/log/APS-*.csv` (nhiều file, mỗi file cho 1 ngày)

**Mục đích:** Ghi lại chi tiết kỹ thuật từ hệ thống inverter với tần suất cao (10 giây, 60 giây).

**Cấu trúc đặc biệt:**
File này có cấu trúc phức tạp hơn, chứa nhiều loại log khác nhau trong cùng 1 file.

**Các loại log chính:**

#### a) **APU Stat 10s** - Thông số điện mỗi 10 giây

```
TimeStamp           | VL1N/V | VL2N/V | IL1/A | PL1/kW | PL2/kW | ...
01/10/2025 0:00:00 | 380.5  | 382.1  | 0.43  | 0      | 0      | ...
01/10/2025 0:00:10 | 380.4  | 382.1  | 0.41  | 0      | 0      | ...
01/10/2025 0:00:20 | 380.5  | 382.1  | 0.44  | 0      | 0      | ...
```

**Giải thích:**

- **VL1N/V, VL2N/V, VL3N/V**: Điện áp pha (Volt)
- **IL1/A, IL2/A, IL3/A**: Dòng điện pha (Ampere)
- **PL1/kW, PL2/kW, PL3/kW**: Công suất pha (kW)
- **Vdc/V, Idc/A, Pdc/kW**: Điện áp/dòng/công suất DC

**Tại sao quan trọng?**

- Theo dõi công suất thời gian thực với độ chính xác cao
- Phát hiện sự cố nhanh chóng

#### b) **APS Stat 10s** - Bức xạ mặt trời mỗi 10 giây

```
TimeStamp           | Irr/(W/m^2)
01/10/2025 0:00:00  | 0
01/10/2025 0:00:10  | 0
01/10/2025 6:00:00  | 150
01/10/2025 12:00:00 | 850
```

**Giải thích:**

- **Irr/(W/m^2)**: Cường độ bức xạ mặt trời
- Đo mỗi 10 giây → Dữ liệu chi tiết hơn Weather Reports

#### c) **APS Stat 60s** - Nhiệt độ và điều kiện môi trường mỗi 60 giây

```
TimeStamp           | Tamb/°C | Tpan/°C | Ttrans/°C | Riso12/k | ...
01/10/2025 0:00:00  | 27.6    | 0       | 47.5      | 663.8    | ...
01/10/2025 0:01:00  | 27.7    | 0       | 47.6      | 663.9    | ...
```

**Giải thích:**

- **Tamb/°C**: Nhiệt độ môi trường
- **Tpan/°C**: Nhiệt độ bề mặt tấm pin
- **Ttrans/°C**: Nhiệt độ bộ biến áp
- **Riso12/k, Riso34/kO, Riso56/kO**: Điện trở cách điện (kiểm tra an toàn)
- **Cleak12/µF, Cleak34/µF, Cleak56/µF**: Điện dung rò rỉ (phát hiện lỗi)

**Tại sao quan trọng?**

- Nhiệt độ cao → Giảm hiệu suất tấm pin
- Điện trở cách điện thấp → Có thể có lỗi, nguy hiểm
- Điện dung rò rỉ cao → Tấm pin có thể bị hỏng

#### d) **APS Energy** - Năng lượng tích lũy

```
TimeStamp           | W_in_APU1/kWh | W_out_APU1/kWh | W_in_APS/kWh | ...
01/10/2025 0:00    | 2361          | 9848165        | 6321         | ...
```

**Giải thích:**

- **W_in_APU1/kWh**: Năng lượng đầu vào APU 1 (tích lũy)
- **W_out_APU1/kWh**: Năng lượng đầu ra APU 1 (tích lũy)
- Tương tự cho APU 2, 3, 4, 5, 6
- **W_in_APS/kWh, W_out_APS/kWh**: Tổng năng lượng hệ thống

#### e) **APU Stat 60s** - Nhiệt độ và độ ẩm mỗi 60 giây

```
TimeStamp           | TInd/°C | TL1/°C | TL2/°C | TL3/°C | TPCB/°C | Hum/%RH
01/10/2025 0:00:00  | 38.79   | 39.87  | 39.99  | 40.01  | 37.3    | 48.8
```

**Giải thích:**

- **TInd/°C**: Nhiệt độ bên trong inverter
- **TL1/°C, TL2/°C, TL3/°C**: Nhiệt độ các pha
- **TPCB/°C**: Nhiệt độ bo mạch
- **Hum/%RH**: Độ ẩm

#### f) **APS Stat Trig** - Trạng thái và lỗi

```
TimeStamp           | OpState | Error1 | Error2 | Warning1 | ...
01/10/2025 0:00    | 20000   | 0      | 0      | 49       | ...
```

**Giải thích:**

- **OpState**: Trạng thái hoạt động
- **Error1-Error8**: Mã lỗi (0 = không lỗi)
- **Warning1-Warning8**: Mã cảnh báo

**Tại sao quan trọng?**

- Phát hiện lỗi và cảnh báo
- Phân tích nguyên nhân giảm hiệu suất

---

## 🔄 Pipeline Xử Lý Dữ Liệu - Từng Bước

Pipeline xử lý dữ liệu qua **5 bước chính**:

```
[1. LOAD] → [2. CLEAN] → [3. MERGE] → [4. FEATURE ENGINEERING] → [5. SAVE]
```

---

### BƯỚC 1: LOADING DATA (Tải Dữ Liệu)

**Mục đích:** Đọc tất cả các file từ các nguồn khác nhau vào bộ nhớ.

**Quá trình:**

1. **Đọc PV Forecast CSV**

   - Đọc file CSV đơn giản
   - Tạo cột DateTime từ Date + Time
   - Kết quả: DataFrame với cột `DateTime` và `Power_MW`

2. **Đọc Power Reports Excel**

   - Đọc 2 file Excel
   - Tìm hàng header (có chứa "DateTime")
   - Parse dữ liệu từ hàng sau header
   - Gộp 2 file thành 1 DataFrame
   - Kết quả: DataFrame với nhiều cột (Power, Voltage, Current...)

3. **Đọc Weather Reports Excel**

   - Tương tự Power Reports
   - Kết quả: DataFrame với Temperature, Humidity, Irradiance...

4. **Đọc Energy Reports Excel**

   - Parse header 2 dòng (Block names + Inverter names)
   - Tạo tên cột: `BLOCK X_INV Y`
   - Kết quả: DataFrame với năng lượng tích lũy từng Block/Inverter

5. **Đọc APS Logs CSV**
   - Đọc tất cả file CSV trong thư mục `log/`
   - Parse header phức tạp (nhiều loại log trong 1 file)
   - Tách thành các DataFrame riêng theo loại log:
     - `aps_apu_stat_10s`: Thông số điện mỗi 10s
     - `aps_aps_stat_10s`: Bức xạ mỗi 10s
     - `aps_aps_stat_60s`: Nhiệt độ mỗi 60s
     - `aps_aps_energy`: Năng lượng tích lũy
     - `aps_apu_stat_60s`: Nhiệt độ/độ ẩm mỗi 60s
   - Gộp tất cả file cùng loại log thành 1 DataFrame

**Kết quả sau bước 1:**

- Dictionary chứa nhiều DataFrame:
  ```python
  {
    'pv_forecast': DataFrame,
    'power_reports': DataFrame,
    'weather_reports': DataFrame,
    'energy_reports': DataFrame,
    'aps_apu_stat_10s': DataFrame,
    'aps_aps_stat_10s': DataFrame,
    ...
  }
  ```

---

### BƯỚC 2: CLEANING DATA (Làm Sạch Dữ Liệu)

**Mục đích:** Loại bỏ dữ liệu không hợp lệ, xử lý missing values, outliers.

**Các bước làm sạch:**

#### 2.1. Chuẩn hóa DateTime

- Chuyển tất cả cột thời gian về định dạng chuẩn
- Sắp xếp theo thời gian
- Loại bỏ các hàng không có DateTime hợp lệ

**Ví dụ:**

```
Trước: "01/10/2025 0:00", "2025-10-01 00:00:00", "invalid"
Sau:  Tất cả đều là datetime object, sắp xếp tăng dần
```

#### 2.2. Xóa Duplicates (Trùng Lặp)

- Tìm các hàng trùng lặp (cùng DateTime)
- Giữ lại 1 hàng, xóa các hàng còn lại

**Ví dụ:**

```
Trước:
01/10/2025 0:00 | 100
01/10/2025 0:00 | 100  ← Duplicate
01/10/2025 0:00 | 105  ← Duplicate (giá trị khác)

Sau:
01/10/2025 0:00 | 100  ← Giữ lại 1 hàng
```

#### 2.3. Xử Lý Missing Values (Giá Trị Thiếu)

Có 4 phương pháp:

**a) Drop (Xóa):**

```
Trước:
01/10/2025 0:00 | 100
01/10/2025 0:15 | NaN  ← Xóa hàng này
01/10/2025 0:30 | 105

Sau:
01/10/2025 0:00 | 100
01/10/2025 0:30 | 105
```

**b) Fill Zero (Điền 0):**

```
Trước:
01/10/2025 0:00 | 100
01/10/2025 0:15 | NaN  ← Điền 0
01/10/2025 0:30 | 105

Sau:
01/10/2025 0:00 | 100
01/10/2025 0:15 | 0
01/10/2025 0:30 | 105
```

**c) Interpolate (Nội Suy):** ⭐ (Thường dùng nhất)

```
Trước:
01/10/2025 0:00 | 100
01/10/2025 0:15 | NaN  ← Nội suy từ 100 và 105
01/10/2025 0:30 | 105

Sau:
01/10/2025 0:00 | 100
01/10/2025 0:15 | 102.5  ← (100 + 105) / 2
01/10/2025 0:30 | 105
```

**d) Forward Fill (Điền Giá Trị Trước):**

```
Trước:
01/10/2025 0:00 | 100
01/10/2025 0:15 | NaN  ← Điền giá trị trước (100)
01/10/2025 0:30 | 105

Sau:
01/10/2025 0:00 | 100
01/10/2025 0:15 | 100
01/10/2025 0:30 | 105
```

#### 2.4. Xử Lý Outliers (Giá Trị Bất Thường)

**Outlier là gì?**

- Giá trị quá cao hoặc quá thấp so với bình thường
- Ví dụ: Công suất = 1000 MW (bình thường chỉ 100-200 MW)

**Phương pháp IQR (Interquartile Range):**

```
1. Tính Q1 (25%), Q3 (75%)
2. Tính IQR = Q3 - Q1
3. Outlier nếu: < Q1 - 3*IQR hoặc > Q3 + 3*IQR
4. Thay thế outlier bằng giá trị nội suy
```

**Ví dụ:**

```
Dữ liệu: [100, 105, 110, 115, 120, 1000]  ← 1000 là outlier
Q1 = 105, Q3 = 120, IQR = 15
Outlier: > 120 + 3*15 = 165
→ 1000 là outlier
→ Thay bằng giá trị nội suy: ~117.5
```

**Kết quả sau bước 2:**

- Tất cả DataFrame đã được làm sạch
- Không còn duplicates, missing values, outliers

---

### BƯỚC 3: MERGING DATA (Gộp Dữ Liệu)

**Mục đích:** Gộp tất cả các DataFrame thành 1 DataFrame duy nhất theo thời gian.

**Quá trình:**

1. **Chuẩn hóa cột DateTime**

   - Đảm bảo tất cả DataFrame có cột `DateTime`
   - Đổi `TimeStamp` → `DateTime` nếu cần

2. **Merge theo DateTime**
   - Sử dụng `outer join`: Giữ tất cả thời điểm từ tất cả nguồn
   - Nếu 1 nguồn không có dữ liệu ở thời điểm đó → Điền NaN

**Ví dụ:**

**Trước khi merge:**

```
pv_forecast:
DateTime           | Power_MW
01/10/2025 0:00    | 0
01/10/2025 0:15    | 0

weather_reports:
DateTime           | Temperature_C | Irradiance
01/10/2025 0:00   | 25            | 0
01/10/2025 0:30   | 26            | 0
```

**Sau khi merge:**

```
DateTime           | Power_MW | Temperature_C | Irradiance
01/10/2025 0:00   | 0        | 25            | 0
01/10/2025 0:15   | 0        | NaN           | NaN      ← Không có dữ liệu weather
01/10/2025 0:30   | NaN      | 26            | 0        ← Không có dữ liệu PV
```

**Xử lý cột trùng tên:**

- Nếu 2 nguồn có cột cùng tên → Thêm suffix: `Power_MW_power_reports`, `Power_MW_pv_forecast`

**Kết quả sau bước 3:**

- 1 DataFrame duy nhất chứa tất cả thông tin
- Có thể có nhiều cột (100+ cột)
- Mỗi hàng = 1 thời điểm, mỗi cột = 1 thông số

---

### BƯỚC 4: FEATURE ENGINEERING (Tạo Features)

**Mục đích:** Tạo thêm các cột (features) mới từ dữ liệu hiện có để giúp mô hình học tốt hơn.

**Các loại features được tạo:**

#### 4.1. Time Features (Features Về Thời Gian)

**Mục đích:** Mô hình cần biết thời gian để học pattern (ví dụ: ban ngày có điện, ban đêm không có).

**Các features:**

- `hour`: Giờ trong ngày (0-23)
- `day_of_week`: Thứ trong tuần (0=Thứ 2, 6=Chủ nhật)
- `day_of_month`: Ngày trong tháng (1-31)
- `month`: Tháng (1-12)
- `year`: Năm
- `is_weekend`: Có phải cuối tuần không (0 hoặc 1)
- `time_of_day`: Phân loại (Night, Morning, Afternoon, Evening)
- `hour_sin`, `hour_cos`: Mã hóa vòng tròn cho giờ (0h = 24h)
- `day_of_week_sin`, `day_of_week_cos`: Mã hóa vòng tròn cho thứ

**Ví dụ:**

```
DateTime           | hour | day_of_week | is_weekend | hour_sin | hour_cos
01/10/2025 0:00   | 0    | 2           | 0          | 0        | 1
01/10/2025 12:00  | 12   | 2           | 0          | 1        | 0
01/10/2025 18:00  | 18   | 2           | 0          | -0.707   | -0.707
```

**Tại sao cần cyclical encoding?**

- Giờ 0 và giờ 24 là giống nhau (nửa đêm)
- Mã hóa vòng tròn giúp mô hình hiểu điều này

#### 4.2. Lag Features (Features Trễ)

**Mục đích:** Sử dụng giá trị ở các thời điểm trước để dự đoán giá trị hiện tại.

**Ví dụ:**

```
DateTime           | Power_MW | Power_MW_lag_1 | Power_MW_lag_2 | Power_MW_lag_3
01/10/2025 0:00   | 0        | NaN            | NaN            | NaN
01/10/2025 0:15   | 0        | 0              | NaN            | NaN
01/10/2025 0:30   | 0        | 0              | 0              | NaN
01/10/2025 0:45   | 0        | 0              | 0              | 0
01/10/2025 1:00   | 0        | 0              | 0              | 0
```

**Giải thích:**

- `Power_MW_lag_1`: Giá trị 1 bước trước (15 phút trước)
- `Power_MW_lag_2`: Giá trị 2 bước trước (30 phút trước)
- `Power_MW_lag_3`: Giá trị 3 bước trước (45 phút trước)

**Tại sao cần?**

- Công suất hiện tại thường phụ thuộc vào công suất trước đó
- Ví dụ: Nếu 15 phút trước = 100 MW, bây giờ thường cũng ~100 MW

#### 4.3. Rolling Features (Features Trượt)

**Mục đích:** Tính thống kê trong một khoảng thời gian trước đó.

**Các features:**

- `Power_MW_rolling_mean_3`: Trung bình 3 bước trước
- `Power_MW_rolling_std_3`: Độ lệch chuẩn 3 bước trước
- `Power_MW_rolling_min_3`: Giá trị nhỏ nhất 3 bước trước
- `Power_MW_rolling_max_3`: Giá trị lớn nhất 3 bước trước

**Ví dụ:**

```
DateTime           | Power_MW | rolling_mean_3 | rolling_std_3
01/10/2025 0:00   | 0        | 0              | 0
01/10/2025 0:15   | 0        | 0              | 0
01/10/2025 0:30   | 0        | 0              | 0
01/10/2025 0:45   | 5        | 0              | 2.89        ← Mean của [0,0,0]
01/10/2025 1:00   | 10       | 1.67           | 4.08        ← Mean của [0,0,5]
01/10/2025 1:15   | 15       | 5              | 5           ← Mean của [0,5,10]
```

**Tại sao cần?**

- Phát hiện xu hướng (trend)
- Phát hiện biến động (volatility)

#### 4.4. Difference Features (Features Chênh Lệch)

**Mục đích:** Tính sự thay đổi giữa các thời điểm.

**Ví dụ:**

```
DateTime           | Power_MW | Power_MW_diff_1
01/10/2025 0:00   | 0        | NaN
01/10/2025 0:15   | 0        | 0              ← 0 - 0
01/10/2025 0:30   | 0        | 0              ← 0 - 0
01/10/2025 0:45   | 5        | 5              ← 5 - 0
01/10/2025 1:00   | 10       | 5              ← 10 - 5
```

**Tại sao cần?**

- Phát hiện tốc độ thay đổi
- Ví dụ: Công suất tăng nhanh hay chậm?

#### 4.5. Interaction Features (Features Tương Tác)

**Mục đích:** Kết hợp 2 features để tạo feature mới.

**Ví dụ:**

```
Irradiance | Temperature | Irradiance_x_Temperature
850        | 35          | 29750                   ← 850 * 35
500        | 30          | 15000                   ← 500 * 30
```

**Tại sao cần?**

- Một số mối quan hệ không tuyến tính
- Ví dụ: Công suất phụ thuộc vào cả bức xạ VÀ nhiệt độ

**Kết quả sau bước 4:**

- DataFrame có thể có 200+ cột (từ ~50 cột ban đầu)
- Mỗi cột là 1 feature có thể dùng để train mô hình

---

### BƯỚC 5: SAVING DATA (Lưu Dữ Liệu)

**Mục đích:** Lưu dữ liệu đã xử lý để sử dụng sau.

**Kết quả:**

1. **File chính:** `processed_data/processed_data.csv`

   - Chứa tất cả dữ liệu đã merge và có features
   - Sẵn sàng để train mô hình

2. **Thư mục individual:** `processed_data/individual/`
   - `pv_forecast.csv`: Dữ liệu PV Forecast đã làm sạch
   - `power_reports.csv`: Dữ liệu Power Reports đã làm sạch
   - `weather_reports.csv`: Dữ liệu Weather Reports đã làm sạch
   - `energy_reports.csv`: Dữ liệu Energy Reports đã làm sạch
   - `aps_apu_stat_10s.csv`: Dữ liệu APU Stat 10s đã làm sạch
   - ...

**Cách sử dụng sau khi lưu:**

```python
import pandas as pd

# Load dữ liệu đã xử lý
df = pd.read_csv('processed_data/processed_data.csv')

# Sử dụng để train mô hình
X = df.drop('Power_MW', axis=1)  # Features
y = df['Power_MW']                # Target
```

---

## 📊 Tóm Tắt Quy Trình

```
┌─────────────────────────────────────────────────────────────┐
│                    DỮ LIỆU GỐC                              │
│  PV Forecast | Power Reports | Weather | Energy | APS Logs │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 1: LOADING                                            │
│  → Đọc tất cả file → Tạo DataFrame riêng cho mỗi nguồn      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 2: CLEANING                                           │
│  → Xóa duplicates → Xử lý missing → Xử lý outliers          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 3: MERGING                                            │
│  → Gộp tất cả DataFrame theo DateTime                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 4: FEATURE ENGINEERING                                │
│  → Time features → Lag → Rolling → Difference → Interaction│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 5: SAVING                                             │
│  → Lưu file CSV sẵn sàng cho mô hình                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    DỮ LIỆU ĐÃ XỬ LÝ                         │
│  processed_data.csv (200+ features, sẵn sàng train)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Kiến Thức Bổ Sung

### Đơn Vị Đo

- **MW (Megawatt)**: Đơn vị công suất

  - 1 MW = 1,000,000 Watt
  - Ví dụ: Nhà máy 100 MW có thể cung cấp điện cho ~100,000 hộ gia đình

- **MWh (Megawatt-hour)**: Đơn vị năng lượng

  - 1 MWh = Năng lượng sản xuất 1 MW trong 1 giờ
  - Ví dụ: Sản xuất 100 MWh = Sản xuất 100 MW trong 1 giờ

- **W/m² (Watt per square meter)**: Đơn vị bức xạ
  - Cường độ ánh sáng mặt trời trên 1 m²
  - Trưa nắng tốt: ~800-1000 W/m²
  - Ban đêm: 0 W/m²

### Các Khái Niệm Quan Trọng

- **Cumulative (Tích lũy)**: Tổng từ đầu đến thời điểm đó
- **Instantaneous (Tức thời)**: Giá trị tại 1 thời điểm
- **Outlier**: Giá trị bất thường, có thể do lỗi đo
- **Missing Value**: Giá trị thiếu, không có dữ liệu
- **Feature**: Cột dữ liệu dùng để train mô hình
- **Target**: Cột cần dự đoán (ví dụ: Power_MW)

---

## ❓ Câu Hỏi Thường Gặp

**Q: Tại sao cần nhiều nguồn dữ liệu?**
A: Mỗi nguồn cung cấp thông tin khác nhau. Kết hợp lại giúp mô hình hiểu đầy đủ hơn.

**Q: Tại sao phải làm sạch dữ liệu?**
A: Dữ liệu thực tế thường có lỗi, thiếu sót. Làm sạch giúp mô hình học tốt hơn.

**Q: Tại sao cần tạo features?**
A: Mô hình cần features phù hợp để học. Features tốt → Mô hình tốt.

**Q: Pipeline mất bao lâu?**
A: Tùy vào kích thước dữ liệu. Thường vài phút đến vài chục phút.

**Q: Có thể bỏ qua bước nào không?**
A: Không nên. Mỗi bước đều quan trọng. Có thể tùy chỉnh tham số.

---

## 📝 Kết Luận

Pipeline preprocessing giúp:

1. ✅ Tải dữ liệu từ nhiều nguồn
2. ✅ Làm sạch và chuẩn hóa
3. ✅ Gộp thành 1 dataset thống nhất
4. ✅ Tạo features phù hợp
5. ✅ Lưu sẵn sàng cho mô hình

Sau khi chạy pipeline, bạn có file `processed_data.csv` sẵn sàng để train mô hình machine learning!

---

**Tác giả:** Preprocessing Pipeline  
**Ngày cập nhật:** 2025  
**Phiên bản:** 1.0
