"""
Script xử lý dữ liệu Weather Reports:
- Đọc file Excel gốc
- Chuẩn hóa cột thời gian DateTime
- Lọc và tách dữ liệu theo từng tháng
- Lưu ra các file Excel/CSV riêng cho từng tháng

Có thể dùng độc lập hoặc kết hợp với visualize_weather_reports.py.
"""

import sys
import io
from pathlib import Path
from typing import Optional

import pandas as pd


# Cấu hình encoding UTF-8 cho Windows console (tương tự visualize_weather_reports.py)
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


def load_weather_reports(file_path: str) -> pd.DataFrame:
    """
    Đọc dữ liệu Weather Reports từ file Excel và đảm bảo có cột DateTime.

    Args:
        file_path: Đường dẫn tới file Excel (.xls, .xlsx, .xlsm, ...)

    Returns:
        DataFrame đã có cột DateTime dạng datetime.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    print("=" * 70)
    print(f"ĐANG ĐỌC DỮ LIỆU TỪ FILE: {file_path}")
    print("=" * 70)

    # Đọc toàn bộ sheet đầu tiên
    # File có thể có header 2 tầng → dùng header=[0, 1] rồi "flatten" tên cột
    df = pd.read_excel(file_path, header=[0, 1])

    # Nếu cột là MultiIndex thì gộp 2 tầng header thành 1 tên cột
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for lvl0, lvl1 in df.columns:
            # Bỏ qua các nhãn "Unnamed: x_level_y" vì chỉ là placeholder
            lvl0_str = str(lvl0).strip() if pd.notna(lvl0) else ""
            lvl1_str = str(lvl1).strip() if pd.notna(lvl1) else ""
            if "unnamed" in lvl1_str.lower():
                lvl1_str = ""

            parts = [lvl0_str, lvl1_str]
            name = " ".join(p for p in parts if p).strip()
            # Chuẩn hóa một số tên thường gặp
            lower_name_no_space = name.lower().replace(" ", "")
            if (
                lower_name_no_space in ("datetime", "date_time", "date/time")
                or ("date" in lower_name_no_space and "time" in lower_name_no_space)
            ):
                name = "DateTime"
            new_cols.append(name if name else "Unnamed")
        df.columns = new_cols

    # Loại bỏ các cột hoàn toàn rỗng (toàn NaN) – thường là cột thừa từ header nhiều tầng
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)

    if df.empty:
        raise ValueError("File dữ liệu trống hoặc không đọc được dữ liệu!")

    # Chuẩn hóa cột DateTime
    if "DateTime" in df.columns:
        # Dữ liệu đang ở format dd/mm/yyyy hh:mm nên cần dayfirst=True
        df["DateTime"] = pd.to_datetime(
            df["DateTime"], errors="coerce", dayfirst=True
        )
        datetime_col = "DateTime"
    else:
        # Tìm cột có chứa thông tin ngày/giờ
        datetime_cols = [
            col
            for col in df.columns
            if "date" in str(col).lower() or "time" in str(col).lower()
        ]
        if not datetime_cols:
            raise ValueError(
                "Không tìm thấy cột thời gian (Date/Time) trong dữ liệu! "
                "Vui lòng kiểm tra lại file."
            )

        datetime_col = datetime_cols[0]
        # Parse với dayfirst=True để không bị đảo ngày/tháng
        df["DateTime"] = pd.to_datetime(
            df[datetime_col], errors="coerce", dayfirst=True
        )

    # Loại bỏ các dòng không có DateTime hợp lệ
    before = len(df)
    df = df[df["DateTime"].notna()].copy()
    after = len(df)

    print(f"✓ Tổng số bản ghi ban đầu : {before}")
    print(f"✓ Số bản ghi hợp lệ (có DateTime) : {after}")
    print(f"✓ Khoảng thời gian: {df['DateTime'].min()} -> {df['DateTime'].max()}")

    return df


def split_by_month(
    df: pd.DataFrame,
    output_dir: str,
    base_name: str = "Weather_reports",
    year: Optional[int] = None,
    file_format: str = "xlsx",
) -> None:
    """
    Tách dữ liệu theo từng tháng dựa trên cột DateTime và lưu ra file.

    Args:
        df: DataFrame đã có cột DateTime (kiểu datetime).
        output_dir: Thư mục đầu ra để lưu các file theo tháng.
        base_name: Tên cơ sở cho file đầu ra.
        year: Nếu truyền vào, chỉ tách & lưu cho năm này; nếu None thì lấy tất cả.
        file_format: Định dạng file đầu ra ('xlsx' hoặc 'csv').
    """
    if "DateTime" not in df.columns:
        raise ValueError("DataFrame không có cột 'DateTime'!")

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Tạo thêm cột năm & tháng
    df["Year"] = df["DateTime"].dt.year
    df["Month"] = df["DateTime"].dt.month

    # Đưa các cột DateTime, Year, Month ra đầu tiên
    base_cols = ["DateTime", "Year", "Month"]
    other_cols = [c for c in df.columns if c not in base_cols]
    df = df[base_cols + other_cols]

    if year is not None:
        df = df[df["Year"] == year].copy()
        if df.empty:
            print(f"⚠ Không có dữ liệu cho năm {year}. Không tạo file nào.")
            return

    # Lấy danh sách (year, month) có dữ liệu
    ym_groups = sorted(df.groupby(["Year", "Month"]).size().index.tolist())

    print("\nBẮT ĐẦU TÁCH DỮ LIỆU THEO TỪNG THÁNG...")
    total_files = 0

    for y, m in ym_groups:
        month_df = df[(df["Year"] == y) & (df["Month"] == m)].copy()
        if month_df.empty:
            continue

        # Đặt tên file theo dạng Weather_reports_YYYY_MM.xxx
        file_stem = f"{base_name}_{y}_{m:02d}"
        if file_format.lower() == "csv":
            out_path = output_dir_path / f"{file_stem}.csv"
            month_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        else:
            out_path = output_dir_path / f"{file_stem}.xlsx"
            month_df.to_excel(out_path, index=False)

        total_files += 1
        print(
            f"✓ Đã lưu tháng {m:02d}/{y} -> {out_path} "
            f"(số bản ghi: {len(month_df)})"
        )

    if total_files == 0:
        print("⚠ Không có dữ liệu để tách theo tháng.")
    else:
        print("\n" + "=" * 70)
        print("HOÀN THÀNH TÁCH DỮ LIỆU THEO THÁNG")
        print("=" * 70)
        print(f"✓ Số file đã tạo: {total_files}")
        print(f"✓ Thư mục đầu ra: {output_dir_path.resolve()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Xử lý dữ liệu Weather Reports: tách dữ liệu theo từng tháng",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Dùng file mặc định, tách toàn bộ dữ liệu theo từng tháng, lưu ra thư mục mặc định
  python process_weather_reports_monthly.py

  # Chỉ tách dữ liệu cho năm 2025
  python process_weather_reports_monthly.py --year 2025

  # Chỉ định file nguồn và thư mục đầu ra
  python process_weather_reports_monthly.py \\
      --file "datasets/Weather reports (1-27)10.xlsm" \\
      --output "datasets/monthly_weather_reports"

  # Lưu kết quả dưới dạng CSV thay vì Excel
  python process_weather_reports_monthly.py --format csv
""",
    )

    parser.add_argument(
        "--file",
        type=str,
        default="datasets/Weather reports (1-27)10.xlsm",
        help="Đường dẫn đến file Weather reports nguồn "
        "(mặc định: datasets/Weather reports (1-27)10.xlsm)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="datasets/monthly_weather_reports",
        help="Thư mục để lưu các file theo từng tháng "
        "(mặc định: datasets/monthly_weather_reports)",
    )

    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Chỉ xử lý dữ liệu cho 1 năm cụ thể (vd: 2025). "
        "Nếu bỏ trống sẽ lấy tất cả các năm có trong dữ liệu.",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["xlsx", "csv"],
        default="xlsx",
        help="Định dạng file đầu ra: xlsx hoặc csv (mặc định: xlsx)",
    )

    args = parser.parse_args()

    try:
        df = load_weather_reports(args.file)
        split_by_month(
            df=df,
            output_dir=args.output,
            base_name="Weather_reports",
            year=args.year,
            file_format=args.format,
        )
    except Exception as e:
        print(f"\nLỖI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


