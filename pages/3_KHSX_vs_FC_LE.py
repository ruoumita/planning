import io
import streamlit as st
import pandas as pd
import altair as alt
from utils.auth import page_header
from utils.ui import section, kpi_cards, style_chart, chart_colors
from utils.database import (
    get_versions, get_khsx_data_by_version,
    get_fc_data_by_version, get_khsx_version_refs, fmt_ver,
)

user = st.session_state["user"]
page_header("📈 KHSX vs FC LE", "Đối chiếu kế hoạch sản xuất với dự báo Latest Estimate cùng phiên bản")


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


# ══ SLICER BAND ══════════════════════════════════════════════
khsx_vers = get_versions("khsx")
if not khsx_vers:
    st.info("Chưa có dữ liệu KHSX. Vui lòng upload trước.")
    st.stop()

ver_opts = {
    f"{fmt_ver(v['version_id'], v['uploaded_at'])}  ·  {v['uploaded_by']}": v["version_id"]
    for v in khsx_vers
}

col_sel, col_unit = st.columns([3, 1])
with col_sel:
    sel = st.selectbox("Chọn phiên bản KHSX", list(ver_opts.keys()))
with col_unit:
    unit_sel = st.radio("Đơn vị", ["Unit 1", "Unit 2"], horizontal=True, key="unit_sel_3")

khsx_ver = ver_opts[sel]
khsx_lbl = fmt_ver(khsx_ver, next(v["uploaded_at"] for v in khsx_vers if v["version_id"] == khsx_ver))
qty_col  = "qty_1" if unit_sel == "Unit 1" else "qty_2"
unit_tag = "U1" if qty_col == "qty_1" else "U2"

refs = get_khsx_version_refs(khsx_ver)
ref_gt    = refs.get("gt_ambient")
ref_mt_a  = refs.get("mt_ambient")
ref_mt_cf = refs.get("mt_chillfrozen")

def _ref_lbl(tbl, ver_id):
    vl = get_versions(tbl)
    v = next((v for v in vl if v["version_id"] == ver_id), None)
    return fmt_ver(ver_id, v["uploaded_at"]) if v else f"v{ver_id}"

c1, c2, c3 = st.columns(3)
c1.info(f"GT Ambient: **{_ref_lbl('fc_le_gt_ambient', ref_gt)}**"   if ref_gt   else "GT Ambient: _Không dùng_")
c2.info(f"MT Ambient: **{_ref_lbl('fc_le_mt_ambient', ref_mt_a)}**" if ref_mt_a else "MT Ambient: _Không dùng_")
c3.info(f"MT ChillFrozen: **{_ref_lbl('fc_le_mt_chillfrozen', ref_mt_cf)}**" if ref_mt_cf else "MT ChillFrozen: _Không dùng_")

if not any([ref_gt, ref_mt_a, ref_mt_cf]):
    st.warning("Phiên bản KHSX này không tham chiếu nhóm FC LE nào.")
    st.stop()

with st.spinner("Đang tải dữ liệu..."):
    df_khsx = get_khsx_data_by_version(khsx_ver)

if df_khsx.empty:
    st.warning("Không có dữ liệu KHSX cho phiên bản này.")
    st.stop()

df_khsx["date_nhap"] = pd.to_datetime(df_khsx["date_nhap"], errors="coerce")

all_items = sorted(df_khsx["item_code"].dropna().unique().tolist())
sel_items = st.multiselect("Lọc Item Code", all_items, placeholder="Tất cả SKU — chọn để thu hẹp")
if sel_items:
    df_khsx = df_khsx[df_khsx["item_code"].isin(sel_items)]

CC = chart_colors()


def color_diff(val):
    if pd.isna(val) or val == 0: return ""
    return "background-color:#D1FAE5;color:#065F46" if val > 0 else "background-color:#FEE2E2;color:#991B1B"


def show_comparison(df_k, fc_table, fc_version, time_unit, section_title, qc, utag):
    section(section_title)
    fc_lbl = _ref_lbl(fc_table, fc_version)
    dk = df_k.copy()
    if time_unit == "week":
        iso = dk["date_nhap"].dt.isocalendar()
        dk["period"] = iso["year"].astype(str) + "-T" + iso["week"].astype(str).str.zfill(2)
    else:
        dk["period"] = dk["date_nhap"].dt.to_period("M").astype(str)

    khsx_qty = qc if qc in dk.columns else "qty_1"
    k_agg = dk.groupby(["item_code", "period"])[khsx_qty].sum().reset_index().rename(columns={khsx_qty: "khsx"})

    df_fc = get_fc_data_by_version(fc_table, fc_version)
    if df_fc.empty:
        st.warning(f"Không có dữ liệu {fc_table} phiên bản {fc_lbl}.")
        return
    if sel_items:
        df_fc = df_fc[df_fc["item_code"].isin(sel_items)]

    df_fc["from_date"] = pd.to_datetime(df_fc["from_date"], errors="coerce")
    if time_unit == "week":
        iso2 = df_fc["from_date"].dt.isocalendar()
        df_fc["period"] = iso2["year"].astype(str) + "-T" + iso2["week"].astype(str).str.zfill(2)
    else:
        df_fc["period"] = df_fc["from_date"].dt.to_period("M").astype(str)

    fc_qty = qc if qc in df_fc.columns else "qty_1"
    fc_agg = df_fc.groupby(["item_code", "period"])[fc_qty].sum().reset_index().rename(columns={fc_qty: "fc_le"})

    merged = pd.merge(k_agg, fc_agg, on=["item_code", "period"], how="outer").fillna(0)
    merged["Chênh lệch"] = merged["khsx"] - merged["fc_le"]
    merged["Chênh lệch %"] = merged.apply(
        lambda r: r["Chênh lệch"] / r["fc_le"] * 100 if r["fc_le"] != 0 else None, axis=1)

    tot_k = merged["khsx"].sum()
    tot_f = merged["fc_le"].sum()
    gap   = tot_k - tot_f
    fill  = (tot_k / tot_f * 100) if tot_f else 0

    kpi_cards([
        {"label": f"KHSX {khsx_lbl}", "value": f"{tot_k:,.0f}", "icon": "🏭", "foot": "kế hoạch sản xuất"},
        {"label": f"FC LE {fc_lbl}",  "value": f"{tot_f:,.0f}", "icon": "🎯", "foot": "dự báo Latest Est."},
        {"label": "Chênh lệch", "value": f"{gap:+,.0f}", "icon": "⚖️",
         "delta": f"{gap:+,.0f}", "tone": "pos" if gap >= 0 else "neg", "foot": "KHSX − FC LE"},
        {"label": "Tỷ lệ đáp ứng", "value": f"{fill:.0f}%", "icon": "📊",
         "delta": "đạt" if fill >= 100 else "thiếu", "tone": "pos" if fill >= 100 else "neg",
         "foot": "KHSX / FC LE"},
    ])

    # period totals for combo chart
    per = merged.groupby("period", as_index=False).agg(KHSX=("khsx", "sum"), FC_LE=("fc_le", "sum"))
    per["Δ"] = per["KHSX"] - per["FC_LE"]
    per = per.sort_values("period")

    cL, cR = st.columns([1.4, 1])
    with cL:
        long = per.melt(id_vars=["period"], value_vars=["KHSX", "FC_LE"], var_name="loai", value_name="val")
        long["loai"] = long["loai"].map({"KHSX": "KHSX", "FC_LE": "FC LE"})
        x_enc = alt.X("period:N", title=None, axis=alt.Axis(labelAngle=-40))
        bars = alt.Chart(long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=x_enc, xOffset="loai:N",
            y=alt.Y("val:Q", title="Sản lượng"),
            color=alt.Color("loai:N", title=None,
                            scale=alt.Scale(domain=["KHSX", "FC LE"], range=[CC["brand"], CC["accent"]])),
            tooltip=["period:N", "loai:N", alt.Tooltip("val:Q", format=",.0f")],
        )
        line = alt.Chart(per).mark_line(point=True, strokeWidth=2.5, color=CC["warn"]).encode(
            x=x_enc, y=alt.Y("Δ:Q", title="Chênh lệch"),
            tooltip=["period:N", alt.Tooltip("Δ:Q", title="Chênh lệch", format="+,.0f")],
        )
        combo = alt.layer(bars, line).resolve_scale(y="independent").properties(height=300)
        st.altair_chart(style_chart(combo), use_container_width=True)

    with cR:
        mv = merged.groupby("item_code", as_index=False)["Chênh lệch"].sum()
        mv = mv[mv["Chênh lệch"] != 0]
        if not mv.empty:
            top = pd.concat([mv.nlargest(6, "Chênh lệch"), mv.nsmallest(6, "Chênh lệch")]).drop_duplicates("item_code")
            top["Xu hướng"] = top["Chênh lệch"].apply(lambda x: "KHSX cao" if x >= 0 else "FC LE cao")
            mvc = alt.Chart(top).mark_bar(cornerRadius=3).encode(
                y=alt.Y("item_code:N", sort="-x", title=None),
                x=alt.X("Chênh lệch:Q", title="KHSX − FC LE"),
                color=alt.Color("Xu hướng:N", legend=None,
                                scale=alt.Scale(domain=["KHSX cao", "FC LE cao"], range=[CC["pos"], CC["neg"]])),
                tooltip=["item_code:N", alt.Tooltip("Chênh lệch:Q", format="+,.0f")],
            ).properties(height=300)
            st.altair_chart(style_chart(mvc), use_container_width=True)
        else:
            st.caption("Không có SKU lệch.")

    col_khsx = f"KHSX {khsx_lbl} [{utag}]"
    col_fc   = f"FC LE {fc_lbl} [{utag}]"
    disp = merged.rename(columns={
        "item_code": "Item Code", "period": "Kỳ",
        "khsx": col_khsx, "fc_le": col_fc,
    }).sort_values(["Item Code", "Kỳ"])

    styled = (
        disp.style.map(color_diff, subset=["Chênh lệch", "Chênh lệch %"])
        .format({
            col_khsx: "{:,.2f}", col_fc: "{:,.2f}",
            "Chênh lệch": "{:+,.2f}",
            "Chênh lệch %": lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
        })
    )
    st.dataframe(styled, use_container_width=True, height=340)

    xlsx = _to_excel(disp)
    st.download_button(
        "⬇️  Xuất Excel", xlsx,
        f"cmp_{fc_table}_{fc_lbl}_khsx_{khsx_lbl}_{utag}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_{fc_table}",
    )


if ref_gt:
    show_comparison(df_khsx, "fc_le_gt_ambient", ref_gt, "week",
                    "🟢 KHSX vs FC LE GT Ambient · theo TUẦN ISO", qty_col, unit_tag)
else:
    st.info("📌 Phiên bản KHSX này không tham chiếu FC LE GT Ambient.")

if ref_mt_a:
    show_comparison(df_khsx, "fc_le_mt_ambient", ref_mt_a, "month",
                    "🔵 KHSX vs FC LE MT Ambient · theo THÁNG", qty_col, unit_tag)
else:
    st.info("📌 Phiên bản KHSX này không tham chiếu FC LE MT Ambient.")

if ref_mt_cf:
    show_comparison(df_khsx, "fc_le_mt_chillfrozen", ref_mt_cf, "week",
                    "🟠 KHSX vs FC LE MT ChillFrozen · theo TUẦN ISO", qty_col, unit_tag)
else:
    st.info("📌 Phiên bản KHSX này không tham chiếu FC LE MT ChillFrozen.")
