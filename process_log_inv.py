import sys
import os
import io
import pandas as pd


column_name = [
    "APS Ctrl Trig",
    "APS Energy",
    "APS Stat 10s",
    "APS Stat 60s",
    "APS Stat Trig",
    "APS Switching Cycles",
    "APU Ctrl Trig",
    "APU Stat 10s",
    "APU Stat 60s",
    "APU Stat Trig",
    "APU Energy",
]

# Dùng encoding phù hợp với file log từ inverter (thường là Latin-1/Windows-1252)
# Nếu vẫn lỗi, có thể thử đổi 'latin1' thành 'cp1252'


input_folder = "datasets/inv 24.5/log"

for file_path in os.listdir(input_folder):
    if file_path.endswith(".csv"):
        df = pd.read_csv(os.path.join(input_folder, file_path), encoding="latin1")
        # Kiểm tra từng dòng ở cột đầu tiên (cột index 0) có chứa chuỗi "APS Ctrl Trig"
        first_col = df.iloc[:, 0].astype(str)
        for column in column_name:
            mask = first_col.str.contains(column, na=False)
            matching_rows = df[mask]
            print(f"Số dòng có cột 1 chứa '{column}': {mask.sum()}")
            name_file = column.replace(" ", "_").lower()
            folder_name = file_path.split("/")[-1].split(".")[0]
            output_folder = f"datasets/log/{folder_name}"
            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, f"{name_file}.csv")
            matching_rows.to_csv(
                output_path, index=False, header=False, encoding="utf-8"
            )
            print(f"Đã lưu các dòng matching vào: {output_path}")
