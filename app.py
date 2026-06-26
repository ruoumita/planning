"""
F2A System (Forecast to Available System) — Masan MeatDeli
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
from utils.session import (
    create_session, get_session, delete_session,
    write_session_cookie, clear_session_cookie, read_session_cookie,
)

_LOGO_PATH = Path(__file__).parent / "logo MML.png"
_LOGO_B64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode() if _LOGO_PATH.exists() else ""
_LOGO_SRC  = f"data:image/png;base64,{_LOGO_B64}" if _LOGO_B64 else ""

st.set_page_config(
    page_title="F2A System — Masan MeatDeli",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global design-system CSS (themable, sync light/dark) ─────
inject_global_css()

# ── Sidebar — Industrial Dark Steel ──────────────────────────
st.markdown("""<style>
section[data-testid="stSidebar"] {
    background: #1E2530 !important;
    border-right: 1px solid #2E3A4E !important;
}
section[data-testid="stSidebar"] > div:first-child {
    display:flex !important; flex-direction:column !important; height:100vh !important;
    padding:0 !important; overflow-x:hidden !important; overflow-y:auto !important;
}
[data-testid="stSidebarNav"] { display:none !important; }
[data-testid="stSidebar"] .stPageLink { margin:0 !important; }
[data-testid="stSidebar"] .stPageLink a {
    display:flex !important; align-items:center !important; gap:.55rem !important;
    padding:.52rem .85rem !important; margin:1px .5rem !important; border-radius:4px !important;
    color:#94A3B8 !important; font-size:.83rem !important; font-weight:400 !important;
    text-decoration:none !important; transition:all .12s ease !important;
    border-left:3px solid transparent !important;
}
[data-testid="stSidebar"] .stPageLink a p,
[data-testid="stSidebar"] .stPageLink a span { color:inherit !important; }
[data-testid="stSidebar"] .stPageLink a:hover {
    background:#2A3444 !important; color:#CBD5E1 !important;
    border-left-color:#38BDF8 !important; }
[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background:#2A3444 !important; color:#38BDF8 !important;
    border-left:3px solid #38BDF8 !important; font-weight:600 !important; }
[data-testid="stSidebar"] .stButton > button {
    font-size:.79rem !important; font-weight:500 !important; border-radius:4px !important;
    width:100% !important; background:rgba(239,68,68,.1) !important; color:#F87171 !important;
    border:1px solid rgba(239,68,68,.25) !important; transition:all .12s !important; }
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(239,68,68,.18) !important; color:#FCA5A5 !important; }
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
    <div style="padding:1rem .9rem .85rem; border-bottom:1px solid #2E3A4E;">
        <div style="display:flex; align-items:center; gap:.7rem;">
            {logo_html}
            <div>
                <div style="color:#E2E8F0;font-weight:700;font-size:.86rem;
                            line-height:1.15;letter-spacing:-.1px;">F2A System</div>
                <div style="color:#4A5E7A;font-size:.63rem;letter-spacing:1px;
                            text-transform:uppercase;margin-top:2px;">Supply Chain · MeatDeli</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _sidebar_nav(user: dict):
    st.sidebar.markdown(
        '<p style="color:#3E5170;font-size:.6rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1.6px;padding:.85rem 1rem .3rem;margin:0;">NAVIGATION</p>',
        unsafe_allow_html=True,
    )
    nav = [
        ("pages/1_Dashboard.py",         "📊  Dashboard"),
        ("pages/2_So_Sanh_Phien_Ban.py", "🔄  So sánh phiên bản"),
        ("pages/3_KHSX_vs_FC_LE.py",     "📈  KHSX vs FC LE"),
        ("pages/6_Lich_Su_Phien_Ban.py", "📋  Lịch sử & Xu hướng"),
    ]
    if user["system_role"] in ("ADMIN", "MEMBER"):
        nav.append(("pages/4_Upload.py", "📤  Upload FC & KHSX"))
    nav.append(("pages/7_Master_Data.py", "📁  Upload Master Data"))
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
    <div style="border-top:1px solid #2E3A4E;padding:.8rem .9rem .6rem;">
        <div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem;">
            <div style="width:30px;height:30px;background:#0284C7;
                        border-radius:3px;display:flex;align-items:center;justify-content:center;
                        color:#FFF;font-weight:700;font-size:.73rem;flex-shrink:0;">{initials}</div>
            <div style="min-width:0;flex:1;">
                <div style="color:#CBD5E1;font-weight:600;font-size:.8rem;overflow:hidden;
                            text-overflow:ellipsis;white-space:nowrap;">{user["full_name"]}</div>
                <div style="color:#4A5E7A;font-size:.67rem;overflow:hidden;
                            text-overflow:ellipsis;white-space:nowrap;">{user["email"]}</div>
            </div>
        </div>
        <div style="display:flex;gap:.3rem;flex-wrap:wrap;">
            <span style="background:{bc}1A;color:{bc};border:1px solid {bc}40;font-size:.59rem;
                         font-weight:700;padding:1px 6px;border-radius:3px;text-transform:uppercase;
                         letter-spacing:.5px;">{sr}</span>
            <span style="background:#0284C71A;color:#38BDF8;border:1px solid #0284C740;
                         font-size:.59rem;font-weight:700;padding:1px 6px;border-radius:3px;
                         text-transform:uppercase;letter-spacing:.5px;">{user["business_role"]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪  Đăng xuất", use_container_width=True, key="logout_btn"):
        token = st.session_state.get("_session_token")
        if token:
            delete_session(token)
        st.session_state.clear()
        st.session_state["_do_logout"] = True  # clear cookie ở main area
        st.rerun()
    st.sidebar.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# STATE — restore session từ cookie nếu chưa đăng nhập
# ════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    _ck_token = read_session_cookie()
    if _ck_token:
        _ck_user = get_session(_ck_token)
        if _ck_user:
            st.session_state["user"] = _ck_user
            st.session_state["_session_token"] = _ck_token

user     = st.session_state.get("user")
db_url   = get_database_url()
db_ready = is_db_initialized() if db_url else False

_BR_OPTIONS = ["DP", "SP", "DP+SP"]

# ════════════════════════════════════════════════════════════
# NOT LOGGED IN
# ════════════════════════════════════════════════════════════
if not user:
    # Xóa cookie khi logout (phải render ở main area, không phải sidebar)
    if st.session_state.pop("_do_logout", False):
        clear_session_cookie()
    st.markdown("""<style>
        section[data-testid="stSidebar"] { display:none !important; }
        .stApp, .main .block-container {
            background: linear-gradient(160deg, #0F172A 0%, #1E293B 60%, #0F172A 100%) !important;
            min-height: 100vh !important; padding: 3rem 1rem !important;
        }
        /* ── Login inputs: trắng rõ trên nền tối ── */
        .stApp .stTextInput > div > div,
        .stApp .stPasswordInput > div > div,
        .stApp [data-baseweb="input"],
        .stApp [data-baseweb="input"] > div {
            background: rgba(255,255,255,0.10) !important;
            border: 1px solid rgba(255,255,255,0.22) !important;
            border-radius: 10px !important;
        }
        .stApp [data-baseweb="input"] input {
            color: #F8FAFC !important;
        }
        .stApp [data-baseweb="input"] input::placeholder {
            color: #94A3B8 !important;
        }
        /* ── Login primary button: nổi bật trên nền tối ── */
        .stApp .stButton > button,
        .stApp .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0EA5E9 0%, #38BDF8 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: .92rem !important;
            letter-spacing: .35px !important;
            box-shadow: 0 16px 32px rgba(14,165,233,.22) !important;
            border-radius: 10px !important;
            min-height: 46px !important;
        }
        .stApp .stButton > button:hover,
        .stApp .stButton > button[kind="primary"]:hover {
            background: linear-gradient(90deg, #38BDF8 0%, #A5F3FC 100%) !important;
            box-shadow: 0 20px 36px rgba(56,189,248,.28) !important;
        }
    </style>""", unsafe_allow_html=True)

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        _login_logo = (
            f'<img src="{_LOGO_SRC}" style="width:152px;height:114px;border-radius:10px;'
            f'object-fit:contain;background:#FFFFFF;padding:10px;margin-bottom:1.1rem;'
            f'box-shadow:0 8px 32px rgba(0,0,0,0.4);" alt="MML">'
            if _LOGO_SRC else
            '<div style="width:80px;height:60px;background:#0EA5E9;'
            'border-radius:10px;display:inline-flex;align-items:center;justify-content:center;'
            'font-size:36px;margin-bottom:1.1rem;box-shadow:0 8px 24px rgba(14,165,233,.4);">🏭</div>'
        )
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:1.75rem;">
            {_login_logo}
            <div style="font-size:.62rem;font-weight:700;color:#38BDF8;letter-spacing:2.5px;
                        text-transform:uppercase;margin-bottom:.4rem;">Forecast to Available System</div>
            <h1 style="color:#F1F5F9;font-size:1.75rem;font-weight:800;margin:0;
                       letter-spacing:-.5px;line-height:1.2;">F2A System</h1>
            <p style="color:#475569;font-size:.68rem;margin-top:.45rem;letter-spacing:1.2px;
                      text-transform:uppercase;">Supply Chain Department &nbsp;·&nbsp; Masan MeatDeli</p>
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
        <div style="border:1px solid rgba(255,255,255,0.18);border-radius:14px;
                    padding:1rem 1.3rem 1rem;margin-bottom:1.2rem;background:rgba(15,23,42,.55);
                    backdrop-filter:blur(18px);">
            <p style="color:#E2E8F0;font-size:.72rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:2px;text-align:center;margin:0 0 .75rem;">
                ĐĂNG NHẬP HỆ THỐNG
            </p>
        </div>
        """, unsafe_allow_html=True)

        email_in    = st.text_input("Email", placeholder="your.name@masanmeatdeli.com",
                                    label_visibility="collapsed", key="l_email")
        password_in = st.text_input("Mật khẩu", type="password", placeholder="Mật khẩu",
                                    label_visibility="collapsed", key="l_pw")

        st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
        if st.button("Đăng nhập  →", type="primary", use_container_width=True, key="l_btn"):
            if not email_in or not password_in:
                st.error("Vui lòng nhập đầy đủ thông tin.")
            else:
                u = authenticate(email_in.strip().lower(), password_in)
                if u:
                    token = create_session(u)
                    st.session_state["user"] = u
                    st.session_state["_session_token"] = token
                    st.session_state["_write_cookie"] = token
                    st.rerun()
                else:
                    st.error("Email hoặc mật khẩu không đúng, hoặc tài khoản bị vô hiệu hóa.")

        st.markdown('<p style="color:#CBD5E1;font-size:.68rem;text-align:center;margin-top:.75rem;">'
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
    _pages.append(st.Page("pages/4_Upload.py", title="Upload FC & KHSX", icon="📤"))
_pages.append(st.Page("pages/7_Master_Data.py", title="Master Data",        icon="📁"))
_pages.append(st.Page("pages/5_Cai_Dat.py",     title="Cài đặt hệ thống",  icon="⚙️"))

pg = st.navigation(_pages, position="hidden")

_sidebar_header()
_sidebar_nav(user)
_sidebar_footer(user)

pg.run()

# Ghi cookie sau khi page render xong (chỉ sau lần đăng nhập đầu tiên)
if _wc := st.session_state.pop("_write_cookie", None):
    write_session_cookie(_wc)
