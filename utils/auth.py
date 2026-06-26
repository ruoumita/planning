"""
Xác thực người dùng, session persistence, và helper authorization.
"""
import bcrypt
import json
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy import text
from utils.database import get_engine

_SESSION_FILE = Path(__file__).parent.parent / ".sessions.json"
_COOKIE_NAME = "mml_session"
_MAX_AGE_SEC = 30 * 24 * 3600  # 30 ngày
_SESSIONS: Dict[str, dict] = {}


# ────────────────────────────────────────────────────────────
# Password helpers
# ────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ────────────────────────────────────────────────────────────
# Login / Logout
# ────────────────────────────────────────────────────────────

def authenticate(email: str, password: str) -> Optional[dict]:
    """
    Xác thực email + password với bảng users.
    Trả về dict thông tin user nếu hợp lệ và is_active, ngược lại trả về None.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT id, email, full_name, password_hash,
                       business_role, system_role, is_active
                FROM users WHERE email = :email
            """), {"email": email}).fetchone()
    except Exception:
        return None

    if not row:
        return None

    user_id, email_db, full_name, pwd_hash, business_role, system_role, is_active = row

    if not is_active:
        return None

    if not verify_password(password, pwd_hash):
        return None

    return {
        "id": user_id,
        "email": email_db,
        "full_name": full_name or email_db,
        "business_role": business_role,
        "system_role": system_role,
    }


def _execute_transaction(statements: List[Tuple[str, dict]], success_msg: str) -> Tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            for sql, params in statements:
                conn.execute(text(sql), params)
            conn.commit()
        return True, success_msg
    except Exception as e:
        return False, str(e)


# ────────────────────────────────────────────────────────────
# Session guards — dùng ở đầu mỗi trang
# ────────────────────────────────────────────

def require_auth() -> dict:
    """
    Kiểm tra đăng nhập. Nếu chưa login → chuyển về trang Login.
    Trả về dict user nếu đã đăng nhập.
    """
    if "user" not in st.session_state:
        st.warning("⚠️ Vui lòng đăng nhập trước.")
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]


def require_system_role(user: dict, allowed: List[str]) -> None:
    """Dừng execution nếu system_role không nằm trong allowed."""
    if user["system_role"] not in allowed:
        st.error("🚫 Bạn không có quyền truy cập chức năng này.")
        st.stop()


def can_upload(user: dict) -> bool:
    return user["system_role"] in ("ADMIN", "MEMBER")


def is_admin(user: dict) -> bool:
    return user["system_role"] == "ADMIN"




def get_all_users() -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, email, full_name, business_role, system_role, is_active, created_at
            FROM users ORDER BY created_at DESC
        """)).fetchall()
    return [
        {
            "id": r[0], "email": r[1], "full_name": r[2],
            "business_role": r[3], "system_role": r[4],
            "is_active": r[5], "created_at": r[6],
        }
        for r in rows
    ]


def create_user(email: str, full_name: str, plain_password: str,
                business_role: str, system_role: str) -> Tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO users (email, full_name, password_hash, business_role, system_role)
                VALUES (:email, :full_name, :pwd, :br, :sr)
            """), {
                "email": email, "full_name": full_name,
                "pwd": hash_password(plain_password),
                "br": business_role, "sr": system_role,
            })
            conn.commit()
        return True, f"Đã tạo người dùng {email}"
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err:
            return False, "Email đã tồn tại."
        return False, f"Lỗi: {e}"


def toggle_user_active(user_id: int, is_active: bool) -> Tuple[bool, str]:
    status = "kích hoạt" if is_active else "vô hiệu hóa"
    success = _execute_transaction(
        [(
            "UPDATE users SET is_active = :a WHERE id = :id",
            {"a": is_active, "id": user_id},
        )],
        f"Đã {status} tài khoản."
    )
    return success


def change_system_role(user_id: int, new_role: str) -> Tuple[bool, str]:
    return _execute_transaction(
        [(
            "UPDATE users SET system_role = :r WHERE id = :id",
            {"r": new_role, "id": user_id},
        )],
        f"Đã cập nhật quyền thành {new_role}."
    )


def transfer_admin(current_admin_id: int, new_admin_id: int) -> Tuple[bool, str]:
    """
    Chuyển quyền ADMIN sang user khác. Admin hiện tại trở thành MEMBER.
    """
    return _execute_transaction(
        [
            ("UPDATE users SET system_role = 'MEMBER' WHERE id = :id", {"id": current_admin_id}),
            ("UPDATE users SET system_role = 'ADMIN' WHERE id = :id", {"id": new_admin_id}),
        ],
        "Đã chuyển quyền Admin thành công."
    )


def reset_user_password(user_id: int, new_plain: str) -> Tuple[bool, str]:
    return _execute_transaction(
        [(
            "UPDATE users SET password_hash = :h WHERE id = :id",
            {"h": hash_password(new_plain), "id": user_id},
        )],
        "Đã đặt lại mật khẩu."
    )


def change_own_password(user_id: int, old_plain: str, new_plain: str) -> Tuple[bool, str]:
    """Đổi mật khẩu cá nhân — kiểm tra mật khẩu cũ trước"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT password_hash FROM users WHERE id = :id"
            ), {"id": user_id}).fetchone()
        if not row or not verify_password(old_plain, row[0]):
            return False, "Mật khẩu cũ không đúng."
        return reset_user_password(user_id, new_plain)
    except Exception as e:
        return False, str(e)


def create_initial_admin(email: str, full_name: str, plain_password: str,
                         business_role: str = "DP") -> Tuple[bool, str]:
    """Tạo tài khoản ADMIN đầu tiên trong lần khởi tạo hệ thống"""
    return create_user(email, full_name, plain_password, business_role, "ADMIN")


# ────────────────────────────────────────────────────────────
# Session persistence
# ────────────────────────────────────────────────────────────


def _load() -> None:
    global _SESSIONS
    try:
        if _SESSION_FILE.exists():
            raw = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
            now = time.time()
            _SESSIONS = {k: v for k, v in raw.items() if v.get("_exp", 0) > now}
    except Exception:
        _SESSIONS = {}


def _save() -> None:
    try:
        _SESSION_FILE.write_text(
            json.dumps(_SESSIONS, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


# Nạp khi module được import lần đầu
_load()


def create_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {**user, "_exp": time.time() + _MAX_AGE_SEC}
    _save()
    return token


def get_session(token: str) -> Optional[dict]:
    if not token:
        return None
    entry = _SESSIONS.get(token)
    if not entry:
        _load()
        entry = _SESSIONS.get(token)
    if not entry:
        return None
    if entry.get("_exp", 0) < time.time():
        delete_session(token)
        return None
    return {k: v for k, v in entry.items() if not k.startswith("_")}


def delete_session(token: str) -> None:
    _SESSIONS.pop(token, None)
    _save()


def write_session_cookie(token: str) -> None:
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}={token};'
        f'max-age={_MAX_AGE_SEC};path=/;SameSite=Strict";</script>',
        height=0,
    )


def clear_session_cookie() -> None:
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}=;max-age=0;path=/";</script>',
        height=0,
    )


def read_session_cookie() -> Optional[str]:
    try:
        cookies_header = st.context.headers.get("cookie", "")
    except AttributeError:
        return None
    for part in cookies_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k.strip() == _COOKIE_NAME:
            return v.strip() or None
    return None
