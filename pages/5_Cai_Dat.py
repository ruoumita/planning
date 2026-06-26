import streamlit as st
import pandas as pd
from utils.auth import (
    page_header, is_admin,
    change_own_password, get_all_users, create_user,
    toggle_user_active, change_system_role, transfer_admin,
    reset_user_password,
)
from utils.database import (
    get_database_url, save_database_url,
    test_connection, create_all_tables, build_mysql_url, get_engine,
)
from sqlalchemy import text

user = st.session_state["user"]
page_header("⚙️ Cài đặt", "Quản lý người dùng, phân quyền và kết nối database")

_BR_OPTIONS = ["DP", "SP", "DP+SP"]

# ── Tab layout ────────────────────────────────────────────────
if is_admin(user):
    tabs = st.tabs(["👥 Người dùng", "🔐 Mật khẩu", "🗄️ Database"])
else:
    tabs = st.tabs(["🔐 Mật khẩu"])

# ══════════════════════════════════════════════════════════════
# Tab: Quản lý người dùng (chỉ ADMIN)
# ══════════════════════════════════════════════════════════════
if is_admin(user):
    with tabs[0]:
        try:
            all_users = get_all_users()
        except Exception as e:
            st.error(f"Không tải được danh sách: {e}")
            st.stop()

        st.markdown("#### Danh sách người dùng")
        df_u = pd.DataFrame(all_users)[
            ["email", "full_name", "business_role", "system_role", "is_active", "created_at"]
        ]
        df_u.columns = ["Email", "Họ tên", "BR", "SR", "Active", "Ngày tạo"]
        df_u["Ngày tạo"] = df_u["Ngày tạo"].astype(str).str[:10]
        df_u["Active"] = df_u["Active"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df_u, use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("#### Thao tác người dùng")

        badge = {"ADMIN": "🔴", "MEMBER": "🟡", "VIEWER": "🟢"}
        other_users = [u for u in all_users if u["id"] != user["id"]]

        for u in other_users:
            icon = badge.get(u["system_role"], "⚪")
            act  = "✅" if u["is_active"] else "❌"
            with st.expander(f"{icon} {act}  {u['full_name'] or u['email']}  ·  `{u['email']}`  ·  {u['system_role']} / {u['business_role']}", expanded=False):
                ca, cb, cc, cd = st.columns([2, 2, 2, 1])

                with ca:
                    new_sr = st.selectbox("System Role", ["ADMIN", "MEMBER", "VIEWER"],
                                          index=["ADMIN", "MEMBER", "VIEWER"].index(u["system_role"]),
                                          key=f"sr_{u['id']}")
                    if st.button("Đổi SR", key=f"b_sr_{u['id']}", use_container_width=True):
                        if new_sr == "ADMIN":
                            ok, msg = transfer_admin(user["id"], u["id"])
                            if ok:
                                st.session_state["user"]["system_role"] = "MEMBER"
                        else:
                            ok, msg = change_system_role(u["id"], new_sr)
                        st.toast(msg, icon="✅" if ok else "❌")
                        st.rerun()

                with cb:
                    br_idx = _BR_OPTIONS.index(u["business_role"]) if u["business_role"] in _BR_OPTIONS else 0
                    new_br = st.selectbox("Business Role", _BR_OPTIONS,
                                          index=br_idx, key=f"br_{u['id']}")
                    if st.button("Đổi BR", key=f"b_br_{u['id']}", use_container_width=True):
                        try:
                            eng = get_engine()
                            with eng.connect() as conn:
                                conn.execute(text("UPDATE users SET business_role=:br WHERE id=:id"),
                                             {"br": new_br, "id": u["id"]})
                                conn.commit()
                            st.toast("Đã cập nhật BR.", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.toast(str(e), icon="❌")

                with cc:
                    lbl = "Vô hiệu hóa" if u["is_active"] else "Kích hoạt"
                    if st.button(lbl, key=f"b_tog_{u['id']}", use_container_width=True):
                        ok, msg = toggle_user_active(u["id"], not u["is_active"])
                        st.toast(msg, icon="✅" if ok else "❌")
                        st.rerun()

                with cd:
                    with st.popover("🔑 Reset PW"):
                        np2 = st.text_input("Mật khẩu mới", type="password", key=f"rpw_{u['id']}")
                        if st.button("Xác nhận", key=f"b_rpw_{u['id']}"):
                            if np2:
                                ok, msg = reset_user_password(u["id"], np2)
                                st.toast(msg, icon="✅" if ok else "❌")

        st.divider()
        st.markdown("#### Tạo người dùng mới")
        with st.form("create_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_email = c1.text_input("Email *")
            new_name  = c2.text_input("Họ tên")
            c3, c4, c5 = st.columns(3)
            new_pw = c3.text_input("Mật khẩu *", type="password")
            new_br = c4.selectbox("Business Role", _BR_OPTIONS)
            new_sr = c5.selectbox("System Role", ["VIEWER", "MEMBER", "ADMIN"])
            if st.form_submit_button("➕ Tạo tài khoản", type="primary", use_container_width=True):
                if not new_email or not new_pw:
                    st.error("Email và mật khẩu là bắt buộc.")
                else:
                    ok, msg = create_user(new_email.strip().lower(), new_name, new_pw, new_br, new_sr)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# ══════════════════════════════════════════════════════════════
# Tab: Đổi mật khẩu cá nhân
# ══════════════════════════════════════════════════════════════
pw_tab = tabs[1] if is_admin(user) else tabs[0]
with pw_tab:
    st.markdown("#### Thông tin tài khoản")
    _badge = {"ADMIN": "#EF4444", "MEMBER": "#F59E0B", "VIEWER": "#10B981"}.get(user["system_role"], "#64748B")
    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin:.4rem 0 1rem;">
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.8rem 1rem;">
    <div style="font-size:.68rem;font-weight:700;color:var(--text-dim);text-transform:uppercase;letter-spacing:.8px;margin-bottom:.3rem;">Email</div>
    <div style="font-size:.88rem;font-weight:600;color:var(--text);word-break:break-all;">{user["email"]}</div>
  </div>
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.8rem 1rem;">
    <div style="font-size:.68rem;font-weight:700;color:var(--text-dim);text-transform:uppercase;letter-spacing:.8px;margin-bottom:.3rem;">Họ tên</div>
    <div style="font-size:.88rem;font-weight:600;color:var(--text);">{user["full_name"] or "—"}</div>
  </div>
  <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:.8rem 1rem;">
    <div style="font-size:.68rem;font-weight:700;color:var(--text-dim);text-transform:uppercase;letter-spacing:.8px;margin-bottom:.3rem;">Phân quyền</div>
    <div style="font-size:.88rem;font-weight:600;color:{_badge};">{user["system_role"]}</div>
    <div style="font-size:.76rem;color:var(--text-dim);margin-top:.15rem;">{user["business_role"]}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Đổi mật khẩu")
    with st.form("change_pw_form", clear_on_submit=True):
        old_pw = st.text_input("Mật khẩu hiện tại", type="password")
        new_pw = st.text_input("Mật khẩu mới",      type="password")
        cfm_pw = st.text_input("Xác nhận mật khẩu mới", type="password")
        if st.form_submit_button("💾 Lưu mật khẩu mới", type="primary"):
            if not old_pw or not new_pw:
                st.error("Vui lòng điền đầy đủ.")
            elif new_pw != cfm_pw:
                st.error("Mật khẩu xác nhận không khớp.")
            elif len(new_pw) < 6:
                st.error("Mật khẩu tối thiểu 6 ký tự.")
            else:
                ok, msg = change_own_password(user["id"], old_pw, new_pw)
                st.success(msg) if ok else st.error(msg)

# ══════════════════════════════════════════════════════════════
# Tab: Database (chỉ ADMIN)
# ══════════════════════════════════════════════════════════════
if is_admin(user):
    with tabs[2]:
        st.markdown("#### Kết nối cơ sở dữ liệu")
        current_url = get_database_url() or ""
        if current_url:
            masked = current_url[:35] + "…" if len(current_url) > 35 else current_url
            st.info(f"URL hiện tại: `{masked}`")
        else:
            st.warning("Chưa cấu hình Database URL.")

        with st.expander("🔧 Thay đổi kết nối MariaDB", expanded=not current_url):
            with st.form("db_conn_form"):
                c1, c2 = st.columns([3, 1])
                db_host = c1.text_input("Host", value="192.168.1.113")
                db_port = c2.number_input("Port", value=3307, min_value=1, max_value=65535, step=1)
                db_name = st.text_input("Database", value="planningmml")
                c3, c4 = st.columns(2)
                db_user = c3.text_input("Username", value="planning_scd")
                db_pass = c4.text_input("Password", type="password")
                if st.form_submit_button("🔗 Kiểm tra & Lưu", type="primary", use_container_width=True):
                    if not all([db_host, db_user, db_pass, db_name]):
                        st.warning("Điền đầy đủ thông tin kết nối.")
                    else:
                        new_url = build_mysql_url(db_host, int(db_port), db_name, db_user, db_pass)
                        with st.spinner("Đang kết nối..."):
                            ok, msg = test_connection(new_url)
                        if ok:
                            save_database_url(new_url)
                            st.success(f"✅ {msg} — Đã lưu cấu hình mới.")
                        else:
                            st.error(f"❌ {msg}")

        st.divider()
        st.markdown("#### Khởi tạo cấu trúc bảng")
        st.caption("Dùng `IF NOT EXISTS` — dữ liệu cũ không bị xóa. Chạy sau khi thay đổi kết nối.")
        if st.button("🗄️ Tạo / kiểm tra toàn bộ bảng", use_container_width=True):
            with st.spinner("Đang chạy DDL..."):
                ok, msg = create_all_tables()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

