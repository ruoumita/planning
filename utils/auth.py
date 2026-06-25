"""
Xác thực người dùng (bcrypt) + helpers UI chung.
"""
import bcrypt
import streamlit as st
from sqlalchemy import text
from utils.database import get_engine


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

def authenticate(email: str, password: str) -> dict | None:
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


# ────────────────────────────────────────────────────────────
# Session guards — dùng ở đầu mỗi trang
# ────────────────────────────────────────────────────────────

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


def require_system_role(user: dict, allowed: list[str]) -> None:
    """Dừng execution nếu system_role không nằm trong allowed."""
    if user["system_role"] not in allowed:
        st.error("🚫 Bạn không có quyền truy cập chức năng này.")
        st.stop()


def can_upload(user: dict) -> bool:
    return user["system_role"] in ("ADMIN", "MEMBER")


def is_admin(user: dict) -> bool:
    return user["system_role"] == "ADMIN"



def page_header(title: str, subtitle: str = "") -> None:
    """Tiêu đề trang chuẩn — dùng ở đầu mỗi trang nội dung."""
    sub_html = f'<p class="ph-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="ph-wrap">
        <h1 class="ph-title">{title}</h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# User management (dùng trong trang Cài đặt)
# ────────────────────────────────────────────────────────────

def get_all_users() -> list[dict]:
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
                business_role: str, system_role: str) -> tuple[bool, str]:
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


def toggle_user_active(user_id: int, is_active: bool) -> tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE users SET is_active = :a WHERE id = :id"
            ), {"a": is_active, "id": user_id})
            conn.commit()
        status = "kích hoạt" if is_active else "vô hiệu hóa"
        return True, f"Đã {status} tài khoản."
    except Exception as e:
        return False, str(e)


def change_system_role(user_id: int, new_role: str) -> tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE users SET system_role = :r WHERE id = :id"
            ), {"r": new_role, "id": user_id})
            conn.commit()
        return True, f"Đã cập nhật quyền thành {new_role}."
    except Exception as e:
        return False, str(e)


def transfer_admin(current_admin_id: int, new_admin_id: int) -> tuple[bool, str]:
    """
    Chuyển quyền ADMIN sang user khác. Admin hiện tại trở thành MEMBER.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE users SET system_role = 'MEMBER' WHERE id = :id"
            ), {"id": current_admin_id})
            conn.execute(text(
                "UPDATE users SET system_role = 'ADMIN' WHERE id = :id"
            ), {"id": new_admin_id})
            conn.commit()
        return True, "Đã chuyển quyền Admin thành công."
    except Exception as e:
        return False, str(e)


def reset_user_password(user_id: int, new_plain: str) -> tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE users SET password_hash = :h WHERE id = :id"
            ), {"h": hash_password(new_plain), "id": user_id})
            conn.commit()
        return True, "Đã đặt lại mật khẩu."
    except Exception as e:
        return False, str(e)


def change_own_password(user_id: int, old_plain: str, new_plain: str) -> tuple[bool, str]:
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
                         business_role: str = "DP") -> tuple[bool, str]:
    """Tạo tài khoản ADMIN đầu tiên trong lần khởi tạo hệ thống"""
    return create_user(email, full_name, plain_password, business_role, "ADMIN")
