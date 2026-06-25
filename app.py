"""
Demand & Supply Planning System — Masan Meat Life
Entry point: authentication, design-system CSS, sidebar, navigation.
"""
import base64
from pathlib import Path
import streamlit as st
from utils.database import (
    get_database_url, save_database_url, test_connection,
    create_all_tables, is_db_initialized, build_mysql_url,
)
from utils.auth import authenticate, create_initial_admin
from utils.ui import inject_global_css

_LOGO_PATH = Path(__file__).parent / "logo MML.png"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""
_LOGO_SRC  = f"data:image/png;base64,{_LOGO_B64}" if _LOGO_B64 else ""

st.set_page_config(
    page_title="Demand & Supply Planning System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global design-system CSS (themable, sync light/dark) ─────
inject_global_css()

# ── Sidebar — theme-aware (sáng theo giao diện sáng, tối theo tối) ─
st.markdown("""<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--surface) 0%, var(--surface-2) 100%) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    display:flex !important; flex-direction:column !important; height:100vh !important;
    padding:0 !important; overflow-x:hidden !important; overflow-y:auto !important;
}
[data-testid="stSidebarNav"] { display:none !important; }
[data-testid="stSidebar"] .stPageLink { margin:0 !important; }
[data-testid="stSidebar"] .stPageLink a {
    display:flex !important; align-items:center !important; gap:.6rem !important;
    padding:.58rem .9rem !important; margin:2px .65rem !important; border-radius:9px !important;
    color:var(--text-dim) !important; font-size:.85rem !important; font-weight:500 !important;
    text-decoration:none !important; transition:all .15s ease !important;
    border-left:3px solid transparent !important;
}
[data-testid="stSidebar"] .stPageLink a p,
[data-testid="stSidebar"] .stPageLink a span { color:inherit !important; }
[data-testid="stSidebar"] .stPageLink a:hover {
    background:var(--brand-soft) !important; color:var(--text) !important; }
[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background:var(--brand-soft) !important; color:var(--brand) !important;
    border-left:3px solid var(--brand) !important; font-weight:600 !important; }
[data-testid="stSidebar"] .stButton > button {
    font-size:.8rem !important; font-weight:600 !important; border-radius:9px !important;
    width:100% !important; background:rgba(239,68,68,0.1) !important; color:#DC2626 !important;
    border:1px solid rgba(239,68,68,0.3) !important; transition:all .15s !important; }
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(239,68,68,0.18) !important; color:#B91C1C !important; }
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SIDEBAR BUILDER
# ════════════════════════════════════════════════════════════

def _sidebar_header():
    logo_html = (
        f'<img src="{_LOGO_SRC}" style="width:42px;height:42px;border-radius:9px;'
        f'object-fit:contain;background:#FFFFFF;padding:3px;flex-shrink:0;" alt="MML">'
        if _LOGO_SRC else
        '<div style="width:42px;height:42px;background:linear-gradient(135deg,#3B82F6,#1D4ED8);'
        'border-radius:10px;display:flex;align-items:center;justify-content:center;'
        'font-size:22px;flex-shrink:0;">📦</div>'
    )
    st.sidebar.markdown(f"""
    <div style="padding:1.1rem 1rem .9rem; border-bottom:1px solid var(--border);">
        <div style="display:flex; align-items:center; gap:.75rem;">
            {logo_html}
            <div>
                <div style="color:var(--text);font-weight:700;font-size:.88rem;
                            line-height:1.15;letter-spacing:-.2px;">Demand &amp; Supply</div>
                <div style="color:var(--text-faint);font-size:.66rem;letter-spacing:.9px;
                            text-transform:uppercase;margin-top:1px;">Planning System</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _sidebar_nav(user: dict):
    st.sidebar.markdown(
        '<p style="color:var(--text-faint);font-size:.62rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1.5px;padding:.85rem 1rem .3rem;margin:0;">MENU CHÍNH</p>',
        unsafe_allow_html=True,
    )
    nav = [
        ("pages/1_Dashboard.py",         "📊  Dashboard"),
        ("pages/2_So_Sanh_Phien_Ban.py", "🔄  So sánh phiên bản"),
        ("pages/3_KHSX_vs_FC_LE.py",     "📈  KHSX vs FC LE"),
        ("pages/6_Lich_Su_Phien_Ban.py", "📋  Lịch sử & Xu hướng"),
    ]
    if user["system_role"] in ("ADMIN", "MEMBER"):
        nav.append(("pages/4_Upload.py", "📤  Upload dữ liệu"))
    nav.append(("pages/5_Cai_Dat.py", "⚙️  Cài đặt"))
    for path, label in nav:
        st.sidebar.page_link(path, label=label)


def _sidebar_footer(user: dict):
    st.sidebar.markdown('<div style="flex:1;min-height:1.5rem;"></div>', unsafe_allow_html=True)

    badge_cfg = {
        "ADMIN":  ("#EF4444", "#FEE2E2"), "MEMBER": ("#F59E0B", "#FEF3C7"),
        "VIEWER": ("#10B981", "#D1FAE5"),
    }
    sr = user["system_role"]
    bc, bg = badge_cfg.get(sr, ("#64748B", "#F1F5F9"))
    initials = "".join(w[0].upper() for w in (user["full_name"] or user["email"]).split()[:2])

    st.sidebar.markdown(f"""
    <div style="border-top:1px solid var(--border);padding:.85rem 1rem .7rem;">
        <div style="display:flex;align-items:center;gap:.65rem;margin-bottom:.6rem;">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#3B82F6,#6366F1);
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        color:#FFF;font-weight:700;font-size:.78rem;flex-shrink:0;">{initials}</div>
            <div style="min-width:0;flex:1;">
                <div style="color:var(--text);font-weight:600;font-size:.82rem;overflow:hidden;
                            text-overflow:ellipsis;white-space:nowrap;">{user["full_name"]}</div>
                <div style="color:var(--text-faint);font-size:.69rem;overflow:hidden;
                            text-overflow:ellipsis;white-space:nowrap;">{user["email"]}</div>
            </div>
        </div>
        <div style="display:flex;gap:.3rem;flex-wrap:wrap;">
            <span style="background:{bg}20;color:{bc};border:1px solid {bc}40;font-size:.6rem;
                         font-weight:700;padding:2px 7px;border-radius:999px;text-transform:uppercase;
                         letter-spacing:.6px;">{sr}</span>
            <span style="background:rgba(91,141,239,0.16);color:#7FA8FF;border:1px solid rgba(91,141,239,0.28);
                         font-size:.6rem;font-weight:700;padding:2px 7px;border-radius:999px;
                         text-transform:uppercase;letter-spacing:.6px;">{user["business_role"]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪  Đăng xuất", use_container_width=True, key="logout_btn"):
        st.session_state.clear()
        st.rerun()
    st.sidebar.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# STATE
# ════════════════════════════════════════════════════════════
user     = st.session_state.get("user")
db_url   = get_database_url()
db_ready = is_db_initialized() if db_url else False

_BR_OPTIONS = ["DP", "SP", "DP+SP"]

# ════════════════════════════════════════════════════════════
# NOT LOGGED IN
# ════════════════════════════════════════════════════════════
if not user:
    st.markdown("""<style>
        section[data-testid="stSidebar"] { display:none !important; }
        .stApp, .main .block-container {
            background: radial-gradient(1200px 600px at 50% -10%, #16294B 0%, #0B1528 55%, #070D1A 100%) !important;
            min-height: 100vh !important; padding: 3rem 1rem !important;
        }
    </style>""", unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        _login_logo = (
            f'<img src="{_LOGO_SRC}" style="width:80px;height:80px;border-radius:18px;'
            f'object-fit:contain;background:#FFFFFF;padding:8px;margin-bottom:1rem;'
            f'box-shadow:0 12px 36px rgba(91,141,239,0.28);" alt="MML">'
            if _LOGO_SRC else
            '<div style="width:64px;height:64px;background:linear-gradient(135deg,#3B82F6,#1D4ED8);'
            'border-radius:18px;display:inline-flex;align-items:center;justify-content:center;'
            'font-size:32px;margin-bottom:1rem;box-shadow:0 10px 30px rgba(29,78,216,0.5);">📦</div>'
        )
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:2rem;">
            {_login_logo}
            <h1 style="color:#F8FAFC;font-size:1.62rem;font-weight:800;margin:0;
                       letter-spacing:-.5px;line-height:1.25;">Demand &amp; Supply<br>Planning System</h1>
            <p style="color:#5E7196;font-size:.71rem;margin-top:.5rem;letter-spacing:1.5px;
                      text-transform:uppercase;">Masan Group Corporation</p>
        </div>
        """, unsafe_allow_html=True)

        # ── WIZARD ──
        if not db_url or not db_ready:
            st.markdown("""
            <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
                        border-radius:12px;padding:.75rem 1rem;margin-bottom:1rem;text-align:center;">
                <span style="color:#FCD34D;font-size:.85rem;font-weight:600;">
                    ⚙️  Hệ thống chưa khởi tạo — hoàn thành thiết lập bên dưới</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("**Bước 1 — Kết nối Database**", expanded=not db_url):
                c1, c2 = st.columns([3, 1])
                db_host = c1.text_input("Host", value="192.168.1.113", key="w_host")
                db_port = c2.number_input("Port", value=3307, min_value=1, max_value=65535, step=1, key="w_port")
                c3, c4 = st.columns(2)
                db_user = c3.text_input("Username", value="planning_scd", key="w_user")
                db_pass = c4.text_input("Password", type="password", key="w_pass")
                db_name = st.text_input("Database name", value="planningmml", key="w_db")
                if st.button("🔌  Kiểm tra & lưu kết nối", type="primary", use_container_width=True, key="w_test"):
                    if not all([db_host, db_user, db_pass, db_name]):
                        st.warning("Điền đầy đủ thông tin.")
                    else:
                        new_url = build_mysql_url(db_host, int(db_port), db_name, db_user, db_pass)
                        ok, msg = test_connection(new_url)
                        if ok:
                            save_database_url(new_url)
                            st.success(msg + " — Đã lưu!")
                            st.rerun()
                        else:
                            st.error(msg)

            if db_url:
                with st.expander("**Bước 2 — Tạo bảng Database**", expanded=not db_ready):
                    st.info("Tạo toàn bộ bảng nghiệp vụ (idempotent — an toàn khi chạy lại).")
                    if st.button("🗄️  Tạo tất cả bảng", type="primary", use_container_width=True, key="w_create"):
                        with st.spinner("Đang tạo bảng..."):
                            ok, msg = create_all_tables()
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()

            if db_ready:
                with st.expander("**Bước 3 — Tạo tài khoản Admin đầu tiên**", expanded=True):
                    with st.form("setup_admin_form"):
                        a_email = st.text_input("Email Admin *")
                        a_name  = st.text_input("Họ tên")
                        a_br    = st.selectbox("Business Role", _BR_OPTIONS)
                        a_pw    = st.text_input("Mật khẩu *", type="password")
                        a_pw2   = st.text_input("Xác nhận mật khẩu", type="password")
                        if st.form_submit_button("✅  Hoàn tất thiết lập", type="primary", use_container_width=True):
                            if not a_email or not a_pw:
                                st.error("Email và mật khẩu là bắt buộc.")
                            elif a_pw != a_pw2:
                                st.error("Mật khẩu xác nhận không khớp.")
                            else:
                                ok, msg = create_initial_admin(a_email.strip().lower(), a_name, a_pw, a_br)
                                if ok:
                                    st.success("✅  Hệ thống sẵn sàng — vui lòng đăng nhập.")
                                    st.rerun()
                                else:
                                    st.error(msg)
            st.stop()

        # ── LOGIN ──
        st.markdown("""
        <div style="background:rgba(255,255,255,0.04);backdrop-filter:blur(8px);
                    border:1px solid rgba(255,255,255,0.08);border-radius:16px;
                    padding:1.75rem 1.75rem .5rem;">
            <p style="color:#6B7E9E;font-size:.7rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:1.5px;text-align:center;margin:0 0 1.25rem;">ĐĂNG NHẬP HỆ THỐNG</p>
        </div>
        """, unsafe_allow_html=True)

        email_in    = st.text_input("Email", placeholder="your.name@masangroup.com",
                                    label_visibility="collapsed", key="l_email")
        password_in = st.text_input("Mật khẩu", type="password", placeholder="Mật khẩu",
                                    label_visibility="collapsed", key="l_pw")

        if st.button("Đăng nhập  →", type="primary", use_container_width=True, key="l_btn"):
            if not email_in or not password_in:
                st.error("Vui lòng nhập đầy đủ thông tin.")
            else:
                u = authenticate(email_in.strip().lower(), password_in)
                if u:
                    st.session_state["user"] = u
                    st.rerun()
                else:
                    st.error("Email hoặc mật khẩu không đúng, hoặc tài khoản bị vô hiệu hóa.")

        st.markdown('<p style="color:#3C4D6B;font-size:.71rem;text-align:center;margin-top:.85rem;">'
                    'Liên hệ quản trị viên nếu quên mật khẩu</p>', unsafe_allow_html=True)

    st.stop()


# ════════════════════════════════════════════════════════════
# LOGGED IN — Navigation + Sidebar
# ════════════════════════════════════════════════════════════
_pages = [
    st.Page("pages/1_Dashboard.py",         title="Dashboard",          icon="📊", default=True),
    st.Page("pages/2_So_Sanh_Phien_Ban.py", title="So sánh phiên bản", icon="🔄"),
    st.Page("pages/3_KHSX_vs_FC_LE.py",     title="KHSX vs FC LE",      icon="📈"),
    st.Page("pages/6_Lich_Su_Phien_Ban.py", title="Lịch sử & Xu hướng", icon="📋"),
]
if user["system_role"] in ("ADMIN", "MEMBER"):
    _pages.append(st.Page("pages/4_Upload.py", title="Upload dữ liệu", icon="📤"))
_pages.append(st.Page("pages/5_Cai_Dat.py", title="Cài đặt", icon="⚙️"))

pg = st.navigation(_pages, position="hidden")

_sidebar_header()
_sidebar_nav(user)
_sidebar_footer(user)

pg.run()
