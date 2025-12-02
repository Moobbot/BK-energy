"""
Script xử lý dữ liệu Energy Reports:
- Đọc file Excel gốc (có thể có header 2 tầng)
- Chuẩn hóa cột thời gian DateTime (định dạng dd/mm/yyyy hh:mm)
- Lọc và tách dữ liệu theo từng tháng
- Lưu ra các file Excel/CSV riêng cho từng tháng
"""

import sys
import io
from pathlib import Path
from typing import Optional

import pandas as pd


# Cấu hình encoding UTF-8 cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


def load_energy_reports(file_path: str) -> pd.DataFrame:
    """
    Đọc dữ liệu Energy Reports từ file Excel và đảm bảo có cột DateTime.

    Hỗ trợ file Excel với header 2 tầng như:
        level_0: (trống)   | Date Time | ...
        level_1: (trống)   | Unnamed:1 | ...

    Args:
        file_path: Đường dẫn tới file Excel (.xls, .xlsx, ...)

    Returns:
        DataFrame đã có cột DateTime dạng datetime.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    print("=" * 70)
    print(f"ĐANG ĐỌC DỮ LIỆU ENERGY REPORTS TỪ FILE: {file_path}")
    print("=" * 70)

    # Đọc sheet đầu tiên, header 2 tầng.
    # File Energy reports thực tế có 3 dòng mô tả đầu → header bắt đầu từ dòng thứ 4.
    # Vì vậy dùng header=[3, 4] để lấy 2 dòng 4–5 làm header (0-based index: 3,4).
    df = pd.read_excel(file_path, header=[3, 4])

    # Nếu cột là MultiIndex thì gộp 2 tầng header thành 1 tên cột
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for lvl0, lvl1 in df.columns:
            lvl0_str = str(lvl0).strip() if pd.notna(lvl0) else ""
            lvl1_str = str(lvl1).strip() if pd.notna(lvl1) else ""

            # Bỏ "Unnamed: x_level_y" ở tầng 2
            if "unnamed" in lvl1_str.lower():
                lvl1_str = ""

            parts = [lvl0_str, lvl1_str]
            name = " ".join(p for p in parts if p).strip()

            # Chuẩn hóa tên DateTime
            lower_name_no_space = name.lower().replace(" ", "")
            if (
                lower_name_no_space in ("datetime", "date_time", "date/time")
                or ("date" in lower_name_no_space and "time" in lower_name_no_space)
            ):
                name = "DateTime"

            new_cols.append(name if name else "Unnamed")

        df.columns = new_cols

    # Loại bỏ các cột hoàn toàn rỗng (dùng isna().all(axis=0) để tránh lỗi mơ hồ)
    empty_mask = df.isna().all(axis=0)
    empty_cols = empty_mask[empty_mask].index.tolist()
    if len(empty_cols) > 0:
        df = df.drop(columns=empty_cols)

    if df.empty:
        raise ValueError("File dữ liệu trống hoặc không đọc được dữ liệu!")

    # Chuẩn hóa cột DateTime
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(
            df["DateTime"], errors="coerce", dayfirst=True
        )
    else:
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
        df["DateTime"] = pd.to_datetime(
            df[datetime_col], errors="coerce", dayfirst=True
        )

    # Loại bỏ các dòng không có DateTime hợp lệ
    before = len(df)
    df = df[df["DateTime"].notna()].copy()
    after = len(df)

    print(f"✓ Tổng số bản ghi ban đầu : {before}")
    print(f"✓ Số bản ghi hợp lệ (có DateTime) : {after}")
    if after > 0:
        print(f"✓ Khoảng thời gian: {df['DateTime'].min()} -> {df['DateTime'].max()}")

    return df


def split_by_month(
    df: pd.DataFrame,
    output_dir: str,
    base_name: str = "Energy_reports",
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

    ym_groups = sorted(df.groupby(["Year", "Month"]).size().index.tolist())

    print("\nBẮT ĐẦU TÁCH DỮ LIỆU ENERGY REPORTS THEO TỪNG THÁNG...")
    total_files = 0

    for y, m in ym_groups:
        month_df = df[(df["Year"] == y) & (df["Month"] == m)].copy()
        if month_df.empty:
            continue

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
        print("HOÀN THÀNH TÁCH DỮ LIỆU ENERGY REPORTS THEO THÁNG")
        print("=" * 70)
        print(f"✓ Số file đã tạo: {total_files}")
        print(f"✓ Thư mục đầu ra: {output_dir_path.resolve()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Xử lý dữ liệu Energy Reports: tách dữ liệu theo từng tháng",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Dùng file mặc định, tách toàn bộ dữ liệu theo từng tháng
  python process_energy_reports_monthly.py

  # Chỉ tách dữ liệu cho năm 2025
  python process_energy_reports_monthly.py --year 2025

  # Chỉ định file nguồn và thư mục đầu ra
  python process_energy_reports_monthly.py \\
      --file "datasets/Energy reports 01102025 - 27102025.xls" \\
      --output "datasets/monthly_energy_reports"

  # Lưu kết quả dưới dạng CSV
  python process_energy_reports_monthly.py --format csv
""",
    )

    parser.add_argument(
        "--file",
        type=str,
        default="datasets/Energy reports 01102025 - 27102025.xls",
        help="Đường dẫn đến file Energy reports nguồn "
        '(mặc định: "datasets/Energy reports 01102025 - 27102025.xls")',
    )

    parser.add_argument(
        "--output",
        type=str,
        default="datasets/monthly_energy_reports",
        help="Thư mục để lưu các file theo từng tháng "
        "(mặc định: datasets/monthly_energy_reports)",
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
        df = load_energy_reports(args.file)
        split_by_month(
            df=df,
            output_dir=args.output,
            base_name="Energy_reports",
            year=args.year,
            file_format=args.format,
        )
    except Exception as e:
        print(f"\nLỖI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


