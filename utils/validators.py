"""
Validate cấu trúc cột file Excel trước khi insert vào DB.
Tất cả file FC và KHSX đều dùng cùng schema, chỉ khác 1 cột thời gian.
"""
import pandas as pd

# Cột chuẩn cho tất cả bảng FC (muf, target, le_gt_ambient, le_mt_ambient, le_mt_chillfrozen)
FC_REQUIRED = [
    "From_date", "To_date", "Factory", "Region", "Channel",
    "Group_Customer", "Customer", "Item_Code", "Item_Des",
    "Qty_1", "Unit_1", "Qty_2", "Unit_2",
]

# Cột chuẩn cho bảng KHSX (prd_weeklyplan)
KHSX_REQUIRED = [
    "Date_nhap", "Factory", "Region", "Channel", "Group_Customer",
    "Customer", "Item_Code", "Item_Des", "Qty_1", "Unit_1", "Qty_2", "Unit_2",
]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip khoảng trắng tên cột"""
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _find_missing(df: pd.DataFrame, required: list[str]) -> list[str]:
    """Trả về danh sách cột required không có trong df (case-insensitive)"""
    df_cols_lower = {c.lower(): c for c in df.columns}
    missing = []
    for req in required:
        if req.lower() not in df_cols_lower:
            missing.append(req)
    return missing


def _rename_to_required(df: pd.DataFrame, required: list[str]) -> pd.DataFrame:
    """Rename cột về đúng tên chuẩn (giải quyết khác hoa-thường)"""
    df_cols_lower = {c.lower(): c for c in df.columns}
    rename_map = {}
    for req in required:
        actual = df_cols_lower.get(req.lower())
        if actual and actual != req:
            rename_map[actual] = req
    return df.rename(columns=rename_map)


def validate_fc_file(df: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
    """
    Validate file FC (muf / target / le_gt_ambient / le_mt_ambient / le_mt_chillfrozen).
    Trả về (success, message, cleaned_df).
    cleaned_df chỉ chứa các cột FC_REQUIRED với kiểu dữ liệu đã chuẩn hóa.
    """
    df = _normalize_columns(df.copy())
    missing = _find_missing(df, FC_REQUIRED)
    if missing:
        return False, f"File thiếu cột: {', '.join(missing)}", df

    df = _rename_to_required(df, FC_REQUIRED)
    df = df[FC_REQUIRED].copy()

    # Chuẩn hóa kiểu dữ liệu
    df["From_date"] = pd.to_datetime(df["From_date"], errors="coerce")
    df["To_date"] = pd.to_datetime(df["To_date"], errors="coerce")
    df["Qty_1"] = pd.to_numeric(df["Qty_1"], errors="coerce")
    df["Qty_2"] = pd.to_numeric(df["Qty_2"], errors="coerce")

    # Xóa dòng không có Item_Code
    before = len(df)
    df = df.dropna(subset=["Item_Code"])
    df["Item_Code"] = df["Item_Code"].astype(str).str.strip()
    dropped = before - len(df)

    msg = f"✅ {len(df)} dòng hợp lệ"
    if dropped:
        msg += f" (đã bỏ {dropped} dòng thiếu Item_Code)"
    return True, msg, df


def validate_khsx_file(df: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
    """
    Validate file KHSX (prd_weeklyplan).
    Trả về (success, message, cleaned_df).
    """
    df = _normalize_columns(df.copy())
    missing = _find_missing(df, KHSX_REQUIRED)
    if missing:
        return False, f"File thiếu cột: {', '.join(missing)}", df

    df = _rename_to_required(df, KHSX_REQUIRED)
    df = df[KHSX_REQUIRED].copy()

    df["Date_nhap"] = pd.to_datetime(df["Date_nhap"], errors="coerce")
    df["Qty_1"] = pd.to_numeric(df["Qty_1"], errors="coerce")
    df["Qty_2"] = pd.to_numeric(df["Qty_2"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["Item_Code"])
    df["Item_Code"] = df["Item_Code"].astype(str).str.strip()
    dropped = before - len(df)

    msg = f"✅ {len(df)} dòng hợp lệ"
    if dropped:
        msg += f" (đã bỏ {dropped} dòng thiếu Item_Code)"
    return True, msg, df
