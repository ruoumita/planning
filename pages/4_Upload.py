import streamlit as st
import pandas as pd
from utils.auth import page_header, can_upload
from utils.database import (
    get_versions, upload_fc_data, upload_khsx_data,
    validate_fc_le_version_exists, fmt_ver,
)
from utils.validators import validate_fc_file, validate_khsx_file

user = st.session_state["user"]
page_header("📤 Upload dữ liệu", "Mỗi lần upload tạo phiên bản mới — dữ liệu cũ không bị xóa")

if not can_upload(user):
    st.error("🚫 Chỉ ADMIN và MEMBER mới có quyền upload dữ liệu.")
    st.stop()

br, sr = user["business_role"], user["system_role"]
show_dp = (sr == "ADMIN") or (br in ("DP", "DP+SP"))
show_sp = (sr == "ADMIN") or (br in ("SP", "DP+SP"))

tab_labels = []
if show_dp:
    tab_labels += ["FC Monthly", "FC Target", "FC LE · GT Ambient",
                   "FC LE · MT Ambient", "FC LE · MT ChillFrozen"]
if show_sp:
    tab_labels += ["KHSX (Prd Weekly)"]

tabs = st.tabs(tab_labels)
ti = 0

FC_COLS_HINT = (
    "`From_date · To_date · Factory · Region · Channel · "
    "Group_Customer · Customer · Item_Code · Item_Des · "
    "Qty_1 · Unit_1 · Qty_2 · Unit_2`"
)


def fc_tab(tab, db_table: str, display: str, key: str):
    with tab:
        st.markdown(f"**Cột chuẩn:** {FC_COLS_HINT}")
        up = st.file_uploader(f"Chọn file Excel (.xlsx)", type=["xlsx"], key=f"fu_{key}")
        if up:
            try:
                df_raw = pd.read_excel(up, engine="openpyxl")
            except Exception as e:
                st.error(f"Không đọc được file: {e}")
                return
            ok, msg, df = validate_fc_file(df_raw)
            if not ok:
                st.error(f"❌ {msg}")
                return
            st.success(msg)

            with st.expander("Xem trước dữ liệu (10 dòng đầu)", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            ci, cb = st.columns([3, 1])
            ci.caption(f"**{len(df):,}** dòng  ·  bảng `{db_table}`")
            clicked = cb.button("✅  Xác nhận upload", key=f"btn_{key}", type="primary", use_container_width=True)
            if clicked:
                with st.spinner("Đang insert..."):
                    try:
                        nv = upload_fc_data(df, db_table, user["email"])
                        st.success(f"🎉 Upload thành công!  Phiên bản mới: **v{nv}**")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Lỗi insert: {e}")


if show_dp:
    fc_tab(tabs[ti], "fc_muf",               "FC Monthly",       "muf");      ti += 1
    fc_tab(tabs[ti], "fc_target",            "FC Target",        "target");   ti += 1
    fc_tab(tabs[ti], "fc_le_gt_ambient",     "FC LE GT Ambient", "le_gt");    ti += 1
    fc_tab(tabs[ti], "fc_le_mt_ambient",     "FC LE MT Ambient", "le_mt_a");  ti += 1
    fc_tab(tabs[ti], "fc_le_mt_chillfrozen", "FC LE MT CF",      "le_mt_cf"); ti += 1

if show_sp:
    with tabs[ti]:
        st.markdown(f"**Cột chuẩn:** `Date_nhap · Factory · Region · Channel · Group_Customer · Customer · Item_Code · Item_Des · Qty_1 · Unit_1 · Qty_2 · Unit_2`")
        st.divider()
        st.markdown("#### Tham chiếu phiên bản FC LE")
        st.caption("Chọn version FC LE đã dùng làm cơ sở. Có thể để 'Không dùng'.")

        def _opts(tbl):
            vl = get_versions(tbl)
            d = {"Không dùng": None}
            for v in vl:
                d[f"{fmt_ver(v['version_id'], v['uploaded_at'])}  ·  {v['uploaded_by']}"] = v["version_id"]
            return d

        c1, c2, c3 = st.columns(3)
        with c1:
            og = _opts("fc_le_gt_ambient")
            sg = st.selectbox("FC LE GT Ambient", list(og.keys()), key="sp_gt")
            rg = og[sg]
        with c2:
            oa = _opts("fc_le_mt_ambient")
            sa = st.selectbox("FC LE MT Ambient", list(oa.keys()), key="sp_mt_a")
            ra = oa[sa]
        with c3:
            oc = _opts("fc_le_mt_chillfrozen")
            sc = st.selectbox("FC LE MT ChillFrozen", list(oc.keys()), key="sp_mt_cf")
            rc = oc[sc]

        st.divider()
        up = st.file_uploader("Chọn file Excel (.xlsx) — KHSX", type=["xlsx"], key="fu_khsx")
        if up:
            try:
                df_raw = pd.read_excel(up, engine="openpyxl")
            except Exception as e:
                st.error(f"Không đọc được file: {e}")
                st.stop()
            ok, msg, df = validate_khsx_file(df_raw)
            if not ok:
                st.error(f"❌ {msg}")
                st.stop()
            st.success(msg)

            with st.expander("Xem trước dữ liệu (10 dòng đầu)", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            refs_desc = [x for x in [rg and f"GT v{rg}", ra and f"MT Amb v{ra}", rc and f"MT CF v{rc}"] if x]
            ci, cb = st.columns([3, 1])
            ci.caption(f"**{len(df):,}** dòng  ·  Tham chiếu: {', '.join(refs_desc) or '_Không có_'}")
            khsx_clicked = cb.button("✅  Xác nhận upload", key="btn_khsx", type="primary", use_container_width=True)
            if khsx_clicked:
                errs = []
                if rg and not validate_fc_le_version_exists("fc_le_gt_ambient", rg):
                    errs.append(f"GT Ambient v{rg} không tồn tại trong DB!")
                if ra and not validate_fc_le_version_exists("fc_le_mt_ambient", ra):
                    errs.append(f"MT Ambient v{ra} không tồn tại trong DB!")
                if rc and not validate_fc_le_version_exists("fc_le_mt_chillfrozen", rc):
                    errs.append(f"MT ChillFrozen v{rc} không tồn tại trong DB!")
                if errs:
                    for e in errs: st.error(f"❌ {e}")
                else:
                    with st.spinner("Đang insert..."):
                        try:
                            nv = upload_khsx_data(df, user["email"], rg, ra, rc)
                            st.success(f"🎉 Upload thành công!  Phiên bản KHSX mới: **v{nv}**")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Lỗi insert: {e}")
