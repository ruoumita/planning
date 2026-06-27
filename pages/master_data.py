import streamlit as st
import pandas as pd
from utils.ui import page_header
from utils.auth import is_admin
from utils.database import (
    get_md_versions, get_md_preview, upload_md_data, delete_md_version,
    MD_COL_HINTS, fmt_ver,
)

user = st.session_state.get("user")
if not user:
    st.warning("⚠️ Vui lòng đăng nhập trước.")
    st.switch_page("app.py")
    st.stop()

page_header(
    "📁 Dữ liệu nền",
    "Quản lý upload dữ liệu tham chiếu — chỉ ADMIN mới được upload và xóa",
)

_admin = is_admin(user)

MD_TABLES = [
    ("md_items",    "🗂️ Items",    "Items (Danh mục sản phẩm)"),
    ("md_org",      "🏢 Org",      "Org (Đơn vị tổ chức / kho)"),
    ("md_price",    "💰 Price",    "Price (Bảng giá)"),
    ("md_uom",      "📐 UOM",      "UOM (Đơn vị đo)"),
    ("md_whmatrix", "🔀 WH Matrix","WH Matrix (Ma trận kho)"),
]


def _render_md_tab(tbl: str, admin: bool):
    versions = get_md_versions(tbl)
    latest   = versions[0] if versions else None

    # ── Phiên bản đang dùng ─────────────────────────────────
    st.markdown("#### 📌 Phiên bản đang dùng")
    if not latest:
        st.info("Chưa có dữ liệu — chưa upload phiên bản nào.")
    else:
        vid  = latest["version_id"]
        lbl  = fmt_ver(vid, latest["uploaded_at"])
        date = str(latest["uploaded_at"])[:10] if latest["uploaded_at"] else "—"
        rows = f'{latest["row_count"]:,}'
        by   = latest["uploaded_by"] or "—"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(99,102,241,0.06));
                    border:1px solid rgba(99,102,241,0.28);border-radius:12px;
                    padding:.85rem 1.2rem;margin-bottom:.75rem;">
            <span style="font-size:1.05rem;font-weight:700;color:var(--brand);">{lbl}</span>
            &nbsp;&nbsp;
            <span style="font-size:.8rem;color:var(--text-dim);">
                📅 {date} &nbsp;·&nbsp; 👤 {by} &nbsp;·&nbsp; 🗃️ {rows} dòng
            </span>
            &nbsp;&nbsp;
            <span style="background:#10B981;color:#fff;font-size:.65rem;font-weight:700;
                         padding:2px 8px;border-radius:999px;text-transform:uppercase;">ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Xem trước dữ liệu (10 dòng đầu)", expanded=False):
            df_pre = get_md_preview(tbl, vid, 10)
            if df_pre.empty:
                st.caption("Không có dữ liệu để hiển thị.")
            else:
                st.dataframe(df_pre, use_container_width=True)

    st.divider()

    # ── Upload phiên bản mới (Admin only) ───────────────────
    if admin:
        st.markdown("#### 📤 Upload phiên bản mới")
        hint = MD_COL_HINTS.get(tbl, "")
        st.markdown(
            f'<p style="font-size:.8rem;color:var(--text-dim);margin-bottom:.5rem;">'
            f'<b>Cột chuẩn:</b> <code>{hint}</code></p>',
            unsafe_allow_html=True,
        )

        up = st.file_uploader(
            "Chọn file Excel (.xlsx)",
            type=["xlsx"],
            key=f"fu_{tbl}",
            label_visibility="collapsed",
        )
        if up:
            try:
                df_raw = pd.read_excel(up, engine="openpyxl")
            except Exception as e:
                st.error(f"Không đọc được file: {e}")
                return

            if df_raw.empty:
                st.warning("File không có dữ liệu.")
                return

            st.success(f"✅ Đọc được **{len(df_raw):,}** dòng · {len(df_raw.columns)} cột")

            with st.expander("Xem trước dữ liệu (10 dòng đầu)", expanded=True):
                st.dataframe(df_raw.head(10), use_container_width=True)

            ci, cb = st.columns([3, 1])
            ci.caption(f"**{len(df_raw):,}** dòng sẽ được insert vào `{tbl}`")
            if cb.button(
                "✅  Xác nhận upload",
                key=f"btn_{tbl}",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Đang insert..."):
                    try:
                        nv = upload_md_data(df_raw, tbl, user["email"])
                        st.success(f"🎉 Upload thành công!  Phiên bản mới: **v{nv}**")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi insert: {e}")

        st.divider()

    # ── Lịch sử phiên bản ───────────────────────────────────
    st.markdown("#### 📋 Lịch sử phiên bản")
    if not versions:
        st.caption("Chưa có phiên bản nào.")
        return

    for idx, v in enumerate(versions):
        vid      = v["version_id"]
        lbl      = fmt_ver(vid, v["uploaded_at"])
        date     = str(v["uploaded_at"])[:16].replace("T", " ") if v["uploaded_at"] else "—"
        by       = v["uploaded_by"] or "—"
        rows_str = f'{v["row_count"]:,}'
        is_first = (idx == 0)

        badge = (
            '<span style="background:#10B981;color:#fff;font-size:.6rem;font-weight:700;'
            'padding:1px 7px;border-radius:999px;">ACTIVE</span> '
            if is_first else ""
        )

        c_info, c_del = st.columns([6, 1])
        with c_info:
            st.markdown(
                f'<div style="padding:.4rem 0;">'
                f'<span style="font-weight:600;color:var(--text);">{lbl}</span> {badge}'
                f'<span style="font-size:.78rem;color:var(--text-dim);">'
                f'&nbsp;&nbsp;📅 {date} &nbsp;·&nbsp; 👤 {by}'
                f' &nbsp;·&nbsp; 🗃️ {rows_str} dòng</span></div>',
                unsafe_allow_html=True,
            )

        if admin:
            with c_del:
                confirm_key = f"confirm_del_{tbl}_{vid}"
                if st.session_state.get(confirm_key):
                    if st.button(
                        "⚠️ Xác nhận",
                        key=f"yes_{tbl}_{vid}",
                        type="primary",
                        use_container_width=True,
                    ):
                        ok, msg = delete_md_version(tbl, vid)
                        st.session_state.pop(confirm_key, None)
                        st.success(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()
                else:
                    if st.button(
                        "🗑️",
                        key=f"del_{tbl}_{vid}",
                        use_container_width=True,
                        help=f"Xóa phiên bản {lbl}",
                    ):
                        st.session_state[confirm_key] = True
                        st.rerun()


# ── Render tabs ──────────────────────────────────────────────
tab_labels = [label for _, label, _ in MD_TABLES]
tabs = st.tabs(tab_labels)

for tab, (tbl, _, _title) in zip(tabs, MD_TABLES):
    with tab:
        _render_md_tab(tbl, _admin)
