"""
Kết nối database và các hàm truy vấn chung.
Hỗ trợ MariaDB / MySQL qua PyMySQL.
DATABASE_URL ưu tiên: config.json > biến môi trường .env
"""
import os
import json
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = Path(__file__).parent.parent / "config.json"


# ────────────────────────────────────────────────────────────
# Config helpers
# ────────────────────────────────────────────────────────────

def get_database_url() -> str | None:
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if cfg.get("database_url"):
                return cfg["database_url"]
        except Exception:
            pass
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


def get_engine(url: str | None = None):
    db_url = url or get_database_url()
    if not db_url:
        raise EnvironmentError("Database chưa được cấu hình. Vào Cài đặt để thiết lập.")
    return create_engine(db_url, pool_pre_ping=True)


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
]


def create_all_tables(url: str | None = None) -> tuple[bool, str]:
    """Tạo tất cả bảng, trả về (success, message)"""
    try:
        engine = get_engine(url)
        with engine.connect() as conn:
            for stmt in DDL_STATEMENTS:
                conn.execute(text(stmt))
            conn.commit()
        return True, "Tạo bảng thành công! (7 bảng nghiệp vụ + users)"
    except Exception as e:
        return False, f"Lỗi tạo bảng: {e}"


# ────────────────────────────────────────────────────────────
# Version helpers
# ────────────────────────────────────────────────────────────

def get_next_version_id(table_name: str) -> int:
    """Lấy version_id tiếp theo cho bảng (trong 1 upload = 1 version)"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COALESCE(MAX(version_id), 0) + 1 FROM `{table_name}`"))
        return result.scalar()


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
