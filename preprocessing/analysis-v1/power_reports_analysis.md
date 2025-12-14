# Power Reports Analysis

## Phân tích báo cáo công suất

**Ngày tạo:** 2025-11-13 01:25:58  
**Nguồn dữ liệu:** `dataset/Power reports (1-15)102025.xls`  

---

## 1. Tổng quan dữ liệu

- **Tổng số bản ghi:** 20,968
- **Khoảng thời gian:** 2025-10-01 05:15:00 đến 2025-10-15 18:59:00
- **Số cột dữ liệu:** 209

## 2. Cấu trúc dữ liệu

- **Số cột Bức xạ mặt trời:** 1
- **Số cột Công suất AC:** 102
- **Số cột Công suất DC:** 102
- **Số cột Block:** 204
- **Số cột Inverter:** 204

## 3. Thống kê tổng hợp

- **Công suất AC trung bình:** 91301.56 kW
- **Công suất AC tối đa:** 453478.00 kW
- **Công suất AC tối thiểu:** -14.00 kW

- **Công suất DC trung bình:** 91673.49 kW
- **Công suất DC tối đa:** 457414.00 kW
- **Công suất DC tối thiểu:** -2.00 kW

- **Bức xạ mặt trời trung bình:** 215.88 W/m²
- **Bức xạ mặt trời tối đa:** 1029.50 W/m²

### Top 10 Inverter - Công suất AC trung bình

| Inverter | Công suất trung bình (kW) |
|----------|---------------------------|
| BLOCK 6 INV2 AC | 1,002.52 |
| BLOCK 7 INV1 AC | 981.10 |
| BLOCK 7 INV2 AC | 971.65 |
| BLOCK 18 INV2 AC | 966.71 |
| BLOCK 6 INV1 AC | 966.70 |
| BLOCK 8 INV4 AC | 966.15 |
| BLOCK 7 INV4 AC | 955.68 |
| BLOCK 8 INV3 AC | 955.07 |
| BLOCK 15 INV4 AC | 952.94 |
| BLOCK 12 INV3 AC | 948.73 |

## 4. Biểu đồ trực quan

### 4.1. Công suất theo thời gian

![Power Over Time](output/power_over_time.png)

### 4.2. Bức xạ mặt trời và công suất

![Radiation vs Power](output/radiation_vs_power.png)

### 4.3. Top 10 Inverter

![Top Inverters Power](output/top_inverters_power.png)

### 4.4. Phân bố theo giờ trong ngày

![Hourly Power Distribution](output/hourly_power_distribution.png)

### 4.5. Heatmap: Công suất theo ngày và giờ

![Daily Hourly Power Heatmap](output/daily_hourly_power_heatmap.png)

### 4.6. So sánh AC vs DC Power

![AC vs DC Power](output/ac_vs_dc_power.png)

## 5. Kết luận

Báo cáo này phân tích công suất AC/DC từ hệ thống điện mặt trời.
Các yếu tố quan trọng:

- **Theo dõi công suất theo thời gian** để đánh giá hiệu suất
- **Phân tích mối quan hệ giữa bức xạ mặt trời và công suất** để tối ưu hóa
- **So sánh công suất AC và DC** để đánh giá hiệu suất bộ nghịch lưu
- **Phân tích theo giờ trong ngày** để xác định giờ cao điểm
- **So sánh hiệu suất giữa các inverter** để phát hiện vấn đề

---

*Báo cáo được tạo tự động bởi Power Reports Analyzer*
