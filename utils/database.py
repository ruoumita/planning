"""
Kết nối database và các hàm truy vấn chung.
Hỗ trợ MariaDB / MySQL qua PyMySQL.
DATABASE_URL ưu tiên: config.json > biến môi trường .env
"""
import os
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = Path(__file__).parent.parent / "config.json"


# ────────────────────────────────────────────────────────────
# Config helpers
# ────────────────────────────────────────────────────────────

def get_database_url() -> str | None:
    # 1. config.json (local dev)
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if cfg.get("database_url"):
                return cfg["database_url"]
        except Exception:
            pass
    # 2. Streamlit Cloud secrets
    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return str(url)
    except Exception:
        pass
    # 3. Environment variable
    return os.environ.get("DATABASE_URL")


def save_database_url(url: str) -> None:
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    cfg["database_url"] = url
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def build_mysql_url(host: str, port: int, database: str, user: str, password: str) -> str:
    """
    Xây DATABASE_URL an toàn — tự encode ký tự đặc biệt trong password (@ ! # ...).
    """
    return f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}?charset=utf8mb4"


@st.cache_resource
def _create_engine(url: str):
    return create_engine(url, pool_pre_ping=True)


def get_engine(url: str | None = None):
    db_url = url or get_database_url()
    if not db_url:
        raise EnvironmentError("Database chưa được cấu hình. Vào Cài đặt để thiết lập.")
    return _create_engine(db_url)


def test_connection(url: str) -> tuple[bool, str]:
    """Kiểm tra kết nối, trả về (success, message)"""
    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Kết nối thành công!"
    except Exception as e:
        return False, f"Lỗi kết nối: {e}"


def is_db_initialized() -> bool:
    """Kiểm tra bảng users đã tồn tại chưa"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM users LIMIT 1"))
        return True
    except Exception:
        return False


# ────────────────────────────────────────────────────────────
# DDL — tạo toàn bộ bảng (idempotent: IF NOT EXISTS)
# Tương thích MariaDB / MySQL
# ────────────────────────────────────────────────────────────

_TABLE_OPTIONS = "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"

DDL_STATEMENTS = [
    # Users
    f"""
    CREATE TABLE IF NOT EXISTS `users` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `email` VARCHAR(255) UNIQUE NOT NULL,
        `full_name` VARCHAR(255),
        `password_hash` VARCHAR(255) NOT NULL,
        `business_role` VARCHAR(10) NOT NULL,
        `system_role` VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
        `is_active` TINYINT(1) DEFAULT 1,
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # fc_muf
    f"""
    CREATE TABLE IF NOT EXISTS `fc_muf` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `from_date` DATE,
        `to_date` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # fc_target
    f"""
    CREATE TABLE IF NOT EXISTS `fc_target` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `from_date` DATE,
        `to_date` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # fc_le_gt_ambient
    f"""
    CREATE TABLE IF NOT EXISTS `fc_le_gt_ambient` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `from_date` DATE,
        `to_date` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # fc_le_mt_ambient
    f"""
    CREATE TABLE IF NOT EXISTS `fc_le_mt_ambient` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `from_date` DATE,
        `to_date` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # fc_le_mt_chillfrozen
    f"""
    CREATE TABLE IF NOT EXISTS `fc_le_mt_chillfrozen` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `from_date` DATE,
        `to_date` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # khsx
    f"""
    CREATE TABLE IF NOT EXISTS `khsx` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `date_nhap` DATE,
        `factory` VARCHAR(255),
        `region` VARCHAR(255),
        `channel` VARCHAR(255),
        `group_customer` VARCHAR(255),
        `customer` VARCHAR(255),
        `item_code` VARCHAR(100) NOT NULL,
        `item_des` TEXT,
        `qty_1` DECIMAL(18,4),
        `unit_1` VARCHAR(50),
        `qty_2` DECIMAL(18,4),
        `unit_2` VARCHAR(50),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        `based_on_fc_le_gt_ambient_version` INT,
        `based_on_fc_le_mt_ambient_version` INT,
        `based_on_fc_le_mt_chillfrozen_version` INT
    ) {_TABLE_OPTIONS}
    """,
    # md_items
    f"""
    CREATE TABLE IF NOT EXISTS `md_items` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `item_code` VARCHAR(100),
        `item_description` TEXT,
        `industry_dec` VARCHAR(255),
        `division_desc` VARCHAR(255),
        `sub_division_desc` VARCHAR(255),
        `category_desc` VARCHAR(255),
        `sub_category_desc` VARCHAR(255),
        `brand_desc` VARCHAR(255),
        `brandy_desc` VARCHAR(255),
        `variant_desc` VARCHAR(255),
        `product_format_desc` VARCHAR(255),
        `pack_type_desc` VARCHAR(255),
        `pack_size_desc` VARCHAR(255),
        `standard_sku_desc` TEXT,
        `active` VARCHAR(50),
        `create_date` DATE,
        `update_date` DATE,
        `type_nd_xk` VARCHAR(100),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # md_org
    f"""
    CREATE TABLE IF NOT EXISTS `md_org` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `ou_code` VARCHAR(100),
        `ou_name` VARCHAR(255),
        `org_code` VARCHAR(100),
        `org_id` VARCHAR(100),
        `org_name` VARCHAR(255),
        `organization_id` VARCHAR(100),
        `sub_code` VARCHAR(100),
        `sub_name` VARCHAR(255),
        `locator_code` VARCHAR(100),
        `locator_name` VARCHAR(255),
        `org_type` VARCHAR(100),
        `region` VARCHAR(100),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # md_price
    f"""
    CREATE TABLE IF NOT EXISTS `md_price` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `item_code` VARCHAR(100),
        `item_description` TEXT,
        `channel` VARCHAR(255),
        `unit` VARCHAR(100),
        `price` DECIMAL(18,4),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # md_uom
    f"""
    CREATE TABLE IF NOT EXISTS `md_uom` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `item_no` VARCHAR(100),
        `item_name` TEXT,
        `item_gl_class` VARCHAR(255),
        `base_uom` VARCHAR(100),
        `conversion1` DECIMAL(18,6),
        `conversion_code` VARCHAR(100),
        `conversion2` DECIMAL(18,6),
        `um_type` VARCHAR(100),
        `start_date` DATE,
        `end_date` DATE,
        `org_group` VARCHAR(255),
        `status` VARCHAR(100),
        `pallet_chong_doi` VARCHAR(100),
        `item_status` VARCHAR(100),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
    # md_whmatrix
    f"""
    CREATE TABLE IF NOT EXISTS `md_whmatrix` (
        `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        `whs_ship` VARCHAR(255),
        `whs_received` VARCHAR(255),
        `wh_type` VARCHAR(100),
        `wh_region` VARCHAR(100),
        `version_id` INT NOT NULL,
        `uploaded_by` VARCHAR(255),
        `uploaded_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) {_TABLE_OPTIONS}
    """,
]


def create_all_tables(url: str | None = None) -> tuple[bool, str]:
    """Tạo tất cả bảng, trả về (success, message)"""
    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            for stmt in DDL_STATEMENTS:
                conn.execute(text(stmt))
            conn.commit()
        return True, "Tạo bảng thành công! (12 bảng nghiệp vụ + users)"
    except Exception as e:
        return False, f"Lỗi tạo bảng: {e}"


# ────────────────────────────────────────────────────────────
# Version helpers
# ────────────────────────────────────────────────────────────

def get_next_version_id(table_name: str) -> int:  # không cache — phải lấy MAX mới nhất khi upload
    """Lấy version_id tiếp theo cho bảng (trong 1 upload = 1 version)"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COALESCE(MAX(version_id), 0) + 1 FROM `{table_name}`"))
        return result.scalar()


@st.cache_data(ttl=300)
def get_versions(table_name: str) -> list[dict]:
    """Lấy danh sách version theo bảng, mới nhất trước"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT DISTINCT version_id, uploaded_by, uploaded_at
                FROM `{table_name}`
                ORDER BY version_id DESC
            """))
            return [
                {"version_id": r[0], "uploaded_by": r[1], "uploaded_at": r[2]}
                for r in result
            ]
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_table_stats(table_name: str) -> dict:
    """Thống kê nhanh cho Dashboard"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            r = conn.execute(text(f"""
                SELECT
                    COUNT(DISTINCT version_id) AS version_count,
                    MAX(version_id) AS latest_version,
                    MAX(uploaded_at) AS latest_at,
                    COUNT(*) AS total_rows
                FROM `{table_name}`
            """)).fetchone()
            uploader = None
            if r[1]:
                uploader = conn.execute(text(f"""
                    SELECT uploaded_by FROM `{table_name}`
                    WHERE version_id = {r[1]} LIMIT 1
                """)).scalar()
            return {
                "version_count": r[0] or 0,
                "latest_version": r[1],
                "latest_at": r[2],
                "total_rows": r[3] or 0,
                "uploaded_by": uploader,
            }
    except Exception:
        return {"version_count": 0, "latest_version": None, "latest_at": None, "total_rows": 0, "uploaded_by": None}


# ────────────────────────────────────────────────────────────
# Upload helpers
# ────────────────────────────────────────────────────────────

def _backtick_insert(pd_table, conn, keys, data_iter):
    """
    Custom pandas to_sql method — wraps every identifier in backticks.
    Fixes MariaDB syntax errors for reserved-word column names (to_date, etc.).
    """
    cols   = ", ".join(f"`{k}`" for k in keys)
    params = ", ".join(f":{k}" for k in keys)
    sql    = f"INSERT INTO `{pd_table.name}` ({cols}) VALUES ({params})"
    data   = [dict(zip(keys, row)) for row in data_iter]
    if data:
        conn.execute(text(sql), data)


FC_DB_COLS   = ["from_date", "to_date", "factory", "region", "channel",
                "group_customer", "customer", "item_code", "item_des",
                "qty_1", "unit_1", "qty_2", "unit_2"]

KHSX_DB_COLS = ["date_nhap", "factory", "region", "channel", "group_customer",
                "customer", "item_code", "item_des",
                "qty_1", "unit_1", "qty_2", "unit_2"]


def upload_fc_data(df: pd.DataFrame, table_name: str, uploaded_by: str) -> int:
    """
    Bulk insert dữ liệu FC. Mỗi lần upload tạo 1 version_id mới.
    Trả về version_id vừa tạo.
    """
    engine = get_engine()
    with engine.connect() as conn:
        version_id = conn.execute(
            text(f"SELECT COALESCE(MAX(version_id), 0) + 1 FROM `{table_name}`")
        ).scalar()

        df = df.copy()
        df.columns = [c.lower().strip() for c in df.columns]
        df = df[[c for c in FC_DB_COLS if c in df.columns]].copy()
        df["version_id"]   = version_id
        df["uploaded_by"]  = uploaded_by

        df.to_sql(table_name, conn, if_exists="append", index=False, method=_backtick_insert, chunksize=500)
        conn.commit()

    return version_id


def upload_khsx_data(df: pd.DataFrame, uploaded_by: str,
                     ref_gt: int | None, ref_mt_amb: int | None, ref_mt_cf: int | None) -> int:
    """Bulk insert dữ liệu KHSX kèm 3 tham chiếu FC LE (nullable)."""
    engine = get_engine()
    with engine.connect() as conn:
        version_id = conn.execute(
            text("SELECT COALESCE(MAX(version_id), 0) + 1 FROM `khsx`")
        ).scalar()

        df = df.copy()
        df.columns = [c.lower().strip() for c in df.columns]
        df = df[[c for c in KHSX_DB_COLS if c in df.columns]].copy()
        df["version_id"]   = version_id
        df["uploaded_by"]  = uploaded_by
        df["based_on_fc_le_gt_ambient_version"]    = ref_gt
        df["based_on_fc_le_mt_ambient_version"]    = ref_mt_amb
        df["based_on_fc_le_mt_chillfrozen_version"] = ref_mt_cf

        df.to_sql("khsx", conn, if_exists="append", index=False, method=_backtick_insert, chunksize=500)
        conn.commit()

    return version_id


def fmt_ver(version_id, uploaded_at) -> str:
    """Nhãn version chuẩn: v{id}_{YYMMDD}  ví dụ v3_250626"""
    try:
        ds = str(uploaded_at)[:10].replace("-", "")[2:]
    except Exception:
        ds = "000000"
    return f"v{version_id}_{ds}"


def validate_fc_le_version_exists(table_name: str, version_id: int) -> bool:
    """Server-side: kiểm tra version FC LE có tồn tại trong bảng không"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT 1 FROM `{table_name}` WHERE version_id = :v LIMIT 1"),
                {"v": version_id}
            )
            return result.fetchone() is not None
    except Exception:
        return False


# ────────────────────────────────────────────────────────────
# Query helpers cho các trang So sánh
# ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_fc_data_by_version(table_name: str, version_id: int) -> pd.DataFrame:
    """Lấy dữ liệu FC của 1 version, aggregate theo item_code + from_date"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT `item_code`, `item_des`, `from_date`, `to_date`,
                   SUM(`qty_1`) AS qty_1, SUM(`qty_2`) AS qty_2,
                   `factory`, `region`, `channel`
            FROM `{table_name}`
            WHERE `version_id` = :v
            GROUP BY `item_code`, `item_des`, `from_date`, `to_date`,
                     `factory`, `region`, `channel`
            ORDER BY `item_code`, `from_date`
        """), {"v": version_id})
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=result.keys())
    for c in ("qty_1", "qty_2"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=3600)
def get_khsx_data_by_version(version_id: int) -> pd.DataFrame:
    """Lấy dữ liệu KHSX của 1 version"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT `item_code`, `item_des`, `date_nhap`,
                   SUM(`qty_1`) AS qty_1, SUM(`qty_2`) AS qty_2,
                   `factory`, `region`, `channel`,
                   `based_on_fc_le_gt_ambient_version`,
                   `based_on_fc_le_mt_ambient_version`,
                   `based_on_fc_le_mt_chillfrozen_version`
            FROM `khsx`
            WHERE `version_id` = :v
            GROUP BY `item_code`, `item_des`, `date_nhap`, `factory`, `region`, `channel`,
                     `based_on_fc_le_gt_ambient_version`,
                     `based_on_fc_le_mt_ambient_version`,
                     `based_on_fc_le_mt_chillfrozen_version`
            ORDER BY `item_code`, `date_nhap`
        """), {"v": version_id})
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=result.keys())
    for c in ("qty_1", "qty_2"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=3600)
def get_version_rows(table_name: str, version_id: int, limit: int | None = None) -> pd.DataFrame:
    """Lấy dữ liệu thô của 1 version (dùng cho trang Lịch sử phiên bản)"""
    engine = get_engine()
    lim = f"LIMIT {limit}" if limit else ""
    with engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT * FROM `{table_name}` WHERE `version_id` = :v ORDER BY `id` {lim}"
        ), {"v": version_id})
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=result.keys())
    return df.drop(columns=["id"], errors="ignore")


@st.cache_data(ttl=300)
def get_version_totals(table_name: str) -> pd.DataFrame:
    """
    Tổng qty_1, qty_2 và số dòng theo từng version (cũ → mới).
    Dùng cho biểu đồ xu hướng phiên bản (trang Lịch sử & Dashboard).
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT `version_id`,
                   MIN(`uploaded_at`) AS uploaded_at,
                   MIN(`uploaded_by`) AS uploaded_by,
                   COUNT(*)           AS row_count,
                   SUM(`qty_1`)       AS total_qty1,
                   SUM(`qty_2`)       AS total_qty2
            FROM `{table_name}`
            GROUP BY `version_id`
            ORDER BY `version_id`
        """))
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=result.keys())
    for c in ("row_count", "total_qty1", "total_qty2"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


@st.cache_data(ttl=3600)
def get_khsx_version_refs(version_id: int) -> dict:
    """Lấy 3 cột based_on_* của 1 version KHSX"""
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT DISTINCT
                based_on_fc_le_gt_ambient_version,
                based_on_fc_le_mt_ambient_version,
                based_on_fc_le_mt_chillfrozen_version
            FROM `khsx` WHERE version_id = :v LIMIT 1
        """), {"v": version_id}).fetchone()
    if not r:
        return {}
    return {
        "gt_ambient":   r[0],
        "mt_ambient":   r[1],
        "mt_chillfrozen": r[2],
    }


# ────────────────────────────────────────────────────────────
# Dashboard helpers (cached để tránh query lại mỗi lần rerender)
# ────────────────────────────────────────────────────────────

_DASHBOARD_TABLES = [
    "fc_muf", "fc_target", "fc_le_gt_ambient",
    "fc_le_mt_ambient", "fc_le_mt_chillfrozen", "khsx",
]


@st.cache_data(ttl=300)
def get_upload_activity() -> pd.DataFrame:
    """Upload history gộp tất cả bảng — dùng cho activity chart ở Dashboard."""
    engine = get_engine()
    rows = []
    with engine.connect() as conn:
        for tbl in _DASHBOARD_TABLES:
            try:
                result = conn.execute(text(
                    f"SELECT MIN(`uploaded_at`) AS d, `version_id` FROM `{tbl}` GROUP BY `version_id`"
                )).fetchall()
                for r in result:
                    if r[0]:
                        rows.append({"table": tbl, "uploaded_at": r[0]})
            except Exception:
                pass
    return pd.DataFrame(rows, columns=["table", "uploaded_at"]) if rows else pd.DataFrame()


@st.cache_data(ttl=3600)
def get_khsx_spotlight(version_id: int, limit: int = 50) -> pd.DataFrame:
    """Top SKU theo qty_1 của 1 version KHSX — dùng cho Dashboard spotlight."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT `item_code`, SUM(`qty_1`) AS u1, SUM(`qty_2`) AS u2
            FROM `khsx` WHERE `version_id` = :v
            GROUP BY `item_code` ORDER BY u1 DESC LIMIT :lim
        """), conn, params={"v": version_id, "lim": limit})
    for c in ("u1", "u2"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


# ────────────────────────────────────────────────────────────
# Master Data helpers
# ────────────────────────────────────────────────────────────

# DB column definitions for each master data table
MD_COLS = {
    "md_items": [
        "item_code", "item_description", "industry_dec", "division_desc",
        "sub_division_desc", "category_desc", "sub_category_desc", "brand_desc",
        "brandy_desc", "variant_desc", "product_format_desc", "pack_type_desc",
        "pack_size_desc", "standard_sku_desc", "active", "create_date",
        "update_date", "type_nd_xk",
    ],
    "md_org": [
        "ou_code", "ou_name", "org_code", "org_id", "org_name",
        "organization_id", "sub_code", "sub_name", "locator_code",
        "locator_name", "org_type", "region",
    ],
    "md_price": ["item_code", "item_description", "channel", "unit", "price"],
    "md_uom": [
        "item_no", "item_name", "item_gl_class", "base_uom", "conversion1",
        "conversion_code", "conversion2", "um_type", "start_date", "end_date",
        "org_group", "status", "pallet_chong_doi", "item_status",
    ],
    "md_whmatrix": ["whs_ship", "whs_received", "wh_type", "wh_region"],
}

MD_COL_HINTS = {
    "md_items": "Item code · Item Description · Industry Dec · Division Desc · Sub Dvision Desc · Category Desc · Sub Category Desc · Brand Desc · Brandy Desc · Variant Desc · Product Format Desc · Pack Type Desc · Pack Size Desc · Standard SKU Desc · Active · Create Date · Update Date · Type ND/XK",
    "md_org":   "OU_CODE · OU_NAME · ORG_CODE · ORG_ID · ORG_NAME · ORGANIZATION_ID · SUB_CODE · SUB_NAME · LOCATOR_CODE · LOCATOR_NAME · ORG_TYPE · REGION",
    "md_price": "Item code · Item Description · Channel · unit · price",
    "md_uom":   "Item No · Item Name · Item Gl Class · Base Uom · Conversion1 · Conversion Code · Conversion2 · Um Type · Start Date · End Date · Org Group · Status · Pallet chồng đôi · Item Status",
    "md_whmatrix": "Whs Ship · Whs Received · WH Type · WH Region",
}


def _normalize_col(col: str) -> str:
    """Normalize Excel column name → snake_case ASCII."""
    col = unicodedata.normalize("NFKD", str(col)).encode("ascii", "ignore").decode("ascii")
    col = col.lower().strip()
    col = re.sub(r"[\s/\\()\-]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col


@st.cache_data(ttl=60)
def get_md_versions(table_name: str) -> list[dict]:
    """Danh sách version của 1 bảng masterdata, mới nhất trước."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT version_id,
                       MIN(uploaded_by) AS uploaded_by,
                       MIN(uploaded_at) AS uploaded_at,
                       COUNT(*)         AS row_count
                FROM `{table_name}`
                GROUP BY version_id
                ORDER BY version_id DESC
            """))
            return [
                {"version_id": r[0], "uploaded_by": r[1], "uploaded_at": r[2], "row_count": r[3]}
                for r in result
            ]
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_md_preview(table_name: str, version_id: int, limit: int = 10) -> pd.DataFrame:
    """Xem trước N dòng đầu của 1 version masterdata."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT * FROM `{table_name}` WHERE version_id = :v ORDER BY id LIMIT :lim"
            ), {"v": version_id, "lim": limit})
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=result.keys())
        return df.drop(columns=["id", "version_id", "uploaded_by", "uploaded_at"], errors="ignore")
    except Exception:
        return pd.DataFrame()


def upload_md_data(df: pd.DataFrame, table_name: str, uploaded_by: str) -> int:
    """Bulk insert masterdata. Trả về version_id mới."""
    db_cols = MD_COLS.get(table_name, [])
    engine = get_engine()
    with engine.connect() as conn:
        version_id = conn.execute(
            text(f"SELECT COALESCE(MAX(version_id), 0) + 1 FROM `{table_name}`")
        ).scalar()

        df = df.copy()
        # Normalize column names
        norm_map = {c: _normalize_col(c) for c in df.columns}
        df.rename(columns=norm_map, inplace=True)
        # Keep only known DB columns that exist in the file
        keep = [c for c in db_cols if c in df.columns]
        df = df[keep].copy()
        df["version_id"]  = version_id
        df["uploaded_by"] = uploaded_by

        df.to_sql(table_name, conn, if_exists="append", index=False,
                  method=_backtick_insert, chunksize=500)
        conn.commit()

    st.cache_data.clear()
    return version_id


def delete_md_version(table_name: str, version_id: int) -> tuple[bool, str]:
    """Xóa toàn bộ dữ liệu của 1 version trong bảng masterdata."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(
                text(f"DELETE FROM `{table_name}` WHERE version_id = :v"),
                {"v": version_id}
            )
            conn.commit()
        st.cache_data.clear()
        return True, f"Đã xóa phiên bản v{version_id} khỏi `{table_name}`."
    except Exception as e:
        return False, f"Lỗi xóa: {e}"
