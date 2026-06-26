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
from utils.auth import (
    authenticate, create_initial_admin,
    create_session, get_session, delete_session,
    write_session_cookie, clear_session_cookie, read_session_cookie,
)
from utils.ui import inject_global_css

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
[data-testid="stSidebar"] .stButton > button{
    width:100% !important;
    font-size:.79rem !important;
    font-weight:700 !important;
    border-radius:4px !important;
    background:rgba(255,255,255,.10) !important;
    color:#FFFFFF !important;
    border:1px solid rgba(255,255,255,.24) !important;
}

[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span{
    color:#FFFFFF !important;
    font-weight:700 !important;
}

[data-testid="stSidebar"] .stButton > button:hover{
    background:rgba(255,255,255,.18) !important;
    color:#FFFFFF !important;
}
</style>""", unsafe_allow_html=True)
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
                <div style="color:#EF4444;font-weight:700;font-size:.86rem;
                            line-height:1.15;letter-spacing:-.1px;">F2A System</div>
                <div style="color:#38BDF8;font-size:.63rem;letter-spacing:1px;
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
        ("pages/dashboard.py", "📊  Dashboard"),
        ("pages/version_comparison.py", "🔄  Version Comparison"),
        ("pages/forecast_vs_le.py", "📈  Forecast vs FC LE"),
        ("pages/version_history.py", "📋  Version History"),
    ]
    if user["system_role"] in ("ADMIN", "MEMBER"):
        nav.append(("pages/data_upload.py", "📤  Data Upload"))
    nav.append(("pages/master_data.py", "📁  Master Data"))
    nav.append(("pages/settings.py", "⚙️  Settings"))
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


def _login_logo_html():
    if _LOGO_SRC:
        return (
            f'<img src="{_LOGO_SRC}" style="width:239px;height:120px;border-radius:10px;'
            f'object-fit:contain;background:#FFFFFF;padding:10px;margin-bottom:1.1rem;'
            f'box-shadow:0 8px 32px rgba(0,0,0,0.4);" alt="MML">'
        )
    return (
        '<div style="width:120px;height:60px;background:#0EA5E9;'
        'border-radius:10px;display:inline-flex;align-items:center;justify-content:center;'
        'font-size:40px;margin-bottom:1.1rem;box-shadow:0 8px 24px rgba(14,165,233,.4);">🏭</div>'
    )


def _render_prelogin_css():
    st.markdown("""
    <style>
        /* ===== Hide sidebar ===== */
        section[data-testid="stSidebar"] {
            display:none !important;
        }

        /* ===== Background ===== */
        .stApp,
        .main .block-container{
            background:linear-gradient(135deg,#0F172A 0%,#111827 100%) !important;
            min-height:100vh !important;
            padding:2.2rem 1rem 2rem !important;
            color:#E2E8F0 !important;
        }

        .stApp .main{
            background:transparent !important;
        }

        /* ==========================================================
           LABELS / TEXT
        ========================================================== */

        .stApp label,
        .stApp .stMarkdown,
        .stApp .stMarkdown p,
        .stApp .stExpander summary,
        .stApp [data-testid="stExpander"] summary{
            color:#F8FAFC !important;
        }

        .stApp .stExpander summary{
            font-weight:700 !important;
            font-size:.96rem !important;
        }

        /* ==========================================================
           TEXT INPUT
        ========================================================== */

        .stApp .stTextInput > div > div,
        .stApp .stPasswordInput > div > div{
            background:#FFFFFF !important;
            border:1px solid #CBD5E1 !important;
            border-radius:10px !important;
            box-shadow:none !important;
        }

        .stApp .stTextInput input,
        .stApp .stPasswordInput input{
            background:#FFFFFF !important;
            color:#111827 !important;
            caret-color:#111827 !important;
        }

        .stApp .stTextInput input::placeholder,
        .stApp .stPasswordInput input::placeholder{
            color:#94A3B8 !important;
        }

        .stApp .stTextInput > div > div:focus-within,
        .stApp .stPasswordInput > div > div:focus-within{
            border:1px solid #38BDF8 !important;
            box-shadow:0 0 0 3px rgba(56,189,248,.18) !important;
        }

        /* ==========================================================
           NUMBER INPUT (PORT)
        ========================================================== */

        .stApp .stNumberInput > div > div{
            background:#FFFFFF !important;
            border:1px solid #CBD5E1 !important;
            border-radius:10px !important;
        }

        .stApp .stNumberInput input{
            background:#FFFFFF !important;
            color:#111827 !important;
            caret-color:#111827 !important;
        }

        /* ==========================================================
           BUTTON
        ========================================================== */

        .stApp .stButton > button{
            background:#0284C7 !important;
            color:#FFFFFF !important;
            border:none !important;
            font-weight:700 !important;
            border-radius:10px !important;
            min-height:46px !important;
            transition:.2s;
        }

        .stApp .stButton > button:hover{
            background:#38BDF8 !important;
        }

        /* ==========================================================
           FORM / ALERT
        ========================================================== */

        .stApp .stAlert,
        .stApp .stExpander,
        .stApp .stForm{
            background:rgba(15,23,42,.90) !important;
            border:1px solid #334155 !important;
            color:#E2E8F0 !important;
        }

        /* ==========================================================
           SELECTBOX (Business Role)
        ========================================================== */

        .stApp .stSelectbox > div > div{
            background:#FFFFFF !important;
            border:1px solid #CBD5E1 !important;
            border-radius:10px !important;
        }

        .stApp .stSelectbox div[data-baseweb="select"]{
            background:#FFFFFF !important;
            color:#111827 !important;
        }

        /* ==========================================================
           INPUT LABELS
        ========================================================== */

        .stTextInput label,
        .stPasswordInput label,
        .stNumberInput label,
        .stSelectbox label{
            color:#F8FAFC !important;
            font-weight:600 !important;
        }

    </style>
    """, unsafe_allow_html=True)

def _render_prelogin_branding():
    st.markdown(f"""
        <div style="text-align:center;margin-bottom:1rem;">
            {_login_logo_html()}
            <div style="font-size:3.2rem;font-weight:800;margin:.15rem 0 0;
                       letter-spacing:-.4px;line-height:1.02;text-transform:uppercase;color:#EF4444;">
                F2A SYSTEM
            </div>
            <div style="font-size:.82rem;font-weight:700;letter-spacing:1.2px;
                        text-transform:uppercase;margin-top:.25rem;color:#CBD5E1;">
                FORECAST TO AVAILABLE SYSTEM
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_setup_banner():
    st.markdown("""
        <div style="margin-bottom:.9rem;text-align:center;">
            <span style="color:#38BDF8;font-size:.86rem;font-weight:600;text-transform:uppercase;
                          letter-spacing:.7px;">⚙️ Hệ thống chưa khởi tạo — hoàn thành thiết lập bên dưới</span>
        </div>
        """, unsafe_allow_html=True)


def _render_db_wizard(db_url, db_ready):
    if db_url and db_ready:
        return False

    _render_setup_banner()

    with st.expander("**Bước 1 — Kết nối Database**", expanded=not db_url):
        c1, c2 = st.columns([3, 1])
        db_host = c1.text_input("Host", value="192.168.1.113", key="w_host")
        db_port = c2.text_input("Port", value="3307", key="w_port")
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

    return True


# ════════════════════════════════════════════════════════════
# STATE — restore session từ cookie nếu chưa đăng nhập
# ════════════════════════════════════════════════════
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
    _render_prelogin_css()

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
        _render_prelogin_branding()

        # ── WIZARD ──
        if _render_db_wizard(db_url, db_ready):
            st.stop()

        # ── LOGIN ──
        st.markdown("""
        <div style="margin-bottom:1rem;text-align:center;">
            <div style="font-size:.95rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:1.2px;margin:0;color:#60A5FA;">
                ĐĂNG NHẬP
            </div>
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
    st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
    st.Page("pages/version_comparison.py", title="Version Comparison", icon="🔄"),
    st.Page("pages/forecast_vs_le.py", title="Forecast vs FC LE", icon="📈"),
    st.Page("pages/version_history.py", title="Version History", icon="📋"),
]
if user["system_role"] in ("ADMIN", "MEMBER"):
    _pages.append(st.Page("pages/data_upload.py", title="Data Upload", icon="📤"))
_pages.append(st.Page("pages/master_data.py", title="Master Data", icon="📁"))
_pages.append(st.Page("pages/settings.py", title="Settings", icon="⚙️"))

pg = st.navigation(_pages, position="hidden")

_sidebar_header()
_sidebar_nav(user)
_sidebar_footer(user)

pg.run()

# Ghi cookie sau khi page render xong (chỉ sau lần đăng nhập đầu tiên)
if _wc := st.session_state.pop("_write_cookie", None):
    write_session_cookie(_wc)
