import streamlit as st
import pandas as pd
import altair as alt
from utils.ui import page_header, section, kpi_cards, style_chart, chart_colors, to_excel_bytes
from utils.database import get_versions, get_fc_data_by_version, get_khsx_data_by_version, fmt_ver, get_md_items_by_version, get_md_items_slicers

user = st.session_state["user"]
page_header("🔄 So sánh phiên bản", "Đo lường thay đổi dự báo giữa hai phiên bản theo SKU và thời gian")


TABLES = {
    "fc_muf":               "FC Monthly (MUF)",
    "fc_target":            "FC Target",
    "fc_le_gt_ambient":     "FC LE GT Ambient",
    "fc_le_mt_ambient":     "FC LE MT Ambient",
    "fc_le_mt_chillfrozen": "FC LE MT ChillFrozen",
    "khsx":                 "KHSX (Prd Weekly)",
}

# ══ SLICER BAND ══════════════════════════════════════════════
col1, col2, col3 = st.columns([2, 1.5, 1.5])
with col1:
    tbl_label = st.selectbox("Bảng dữ liệu", list(TABLES.values()))
    tbl = [k for k, v in TABLES.items() if v == tbl_label][0]

versions = get_versions(tbl)
if not versions:
    st.info("Bảng này chưa có dữ liệu.")
    st.stop()

# Product attribute slicers (from latest md_items)
md_df = get_md_items_by_version()
md_slicers = get_md_items_slicers()
if not md_df.empty:
    s1, s2, s3, s4 = st.columns([1, 1, 1, 1])
    cat_sel = s1.multiselect("Category", md_slicers.get("category_desc", []), key="vc_cat")
    sub_sel = s2.multiselect("Sub Category", md_slicers.get("sub_category_desc", []), key="vc_sub")
    brand_sel = s3.multiselect("Brand", md_slicers.get("brand_desc", []), key="vc_brand")
    brandy_sel = s4.multiselect("Brandy", md_slicers.get("brandy_desc", []), key="vc_brandy")
    mask = pd.Series([True] * len(md_df))
    if cat_sel:
        mask &= md_df["category_desc"].isin(cat_sel)
    if sub_sel:
        mask &= md_df["sub_category_desc"].isin(sub_sel)
    if brand_sel:
        mask &= md_df["brand_desc"].isin(brand_sel)
    if brandy_sel:
        mask &= md_df["brandy_desc"].isin(brandy_sel)
    md_allowed = md_df.loc[mask, "item_code"].dropna().unique().tolist()
else:
    md_allowed = None

ver_opts = {
    f"{fmt_ver(v['version_id'], v['uploaded_at'])}  ·  {v['uploaded_by']}": v["version_id"]
    for v in versions
}
labels = list(ver_opts.keys())

with col2:
    la = st.selectbox("Phiên bản A (cũ)", labels, index=min(1, len(labels) - 1))
with col3:
    lb = st.selectbox("Phiên bản B (mới)", labels, index=0)

va, vb = ver_opts[la], ver_opts[lb]
if va == vb:
    st.warning("Chọn 2 phiên bản khác nhau.")
    st.stop()

c_unit, c_item = st.columns([1.2, 2.8])
with c_unit:
    unit_sel = st.radio("Đơn vị", ["Unit 1 (qty_1)", "Unit 2 (qty_2)"], horizontal=True, key="unit_sel_2")
qty_col = "qty_1" if unit_sel.startswith("Unit 1") else "qty_2"
unit_tag = "U1" if qty_col == "qty_1" else "U2"

# ── Load ─────────────────────────────────────────────────────
with st.spinner("Đang tải dữ liệu..."):
    try:
        time_col = "date_nhap" if tbl == "khsx" else "from_date"
        load = get_khsx_data_by_version if tbl == "khsx" else lambda v: get_fc_data_by_version(tbl, v)
        df_a, df_b = load(va), load(vb)
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        st.stop()

all_items = sorted(set(
    df_a["item_code"].dropna().unique().tolist() +
    df_b["item_code"].dropna().unique().tolist()
))
with c_item:
    sel_items = st.multiselect("Lọc Item Code", all_items, placeholder="Tất cả SKU — chọn để thu hẹp")
if sel_items:
    df_a = df_a[df_a["item_code"].isin(sel_items)]
    df_b = df_b[df_b["item_code"].isin(sel_items)]


def agg(df, tc, qc):
    if df.empty or qc not in df.columns:
        return pd.DataFrame(columns=["item_code", tc, "qty"])
    return (df.groupby(["item_code", tc], dropna=False)[qc]
              .sum().reset_index().rename(columns={qc: "qty"}))

# apply md_items attribute filter if present (already computed above)
if md_allowed is not None:
    if not df_a.empty:
        df_a = df_a[df_a["item_code"].isin(md_allowed)]
    if not df_b.empty:
        df_b = df_b[df_b["item_code"].isin(md_allowed)]


agg_a = agg(df_a, time_col, qty_col)
agg_b = agg(df_b, time_col, qty_col)


merged = pd.merge(
    agg_a.rename(columns={"qty": "ver_A"}),
    agg_b.rename(columns={"qty": "ver_B"}),
    on=["item_code", time_col], how="outer",
).fillna(0)
merged["Chênh lệch"]   = merged["ver_B"] - merged["ver_A"]
merged["Chênh lệch %"] = merged.apply(
    lambda r: r["Chênh lệch"] / r["ver_A"] * 100 if r["ver_A"] != 0 else None, axis=1)

lbl_a = next((fmt_ver(v["version_id"], v["uploaded_at"]) for v in versions if v["version_id"] == va), f"v{va}")
lbl_b = next((fmt_ver(v["version_id"], v["uploaded_at"]) for v in versions if v["version_id"] == vb), f"v{vb}")

col_a = f"{lbl_a} [{unit_tag}]"
col_b = f"{lbl_b} [{unit_tag}]"
merged = merged.rename(columns={
    "item_code": "Item Code", time_col: "Kỳ",
    "ver_A": col_a, "ver_B": col_b,
})
merged["Kỳ"] = merged["Kỳ"].astype(str).str[:10]
merged = merged.sort_values(["Item Code", "Kỳ"])

if merged.empty:
    st.info("Không có dữ liệu để so sánh.")
    st.stop()

cc = chart_colors()
tot_a, tot_b = merged[col_a].sum(), merged[col_b].sum()
diff = tot_b - tot_a
pct  = (diff / tot_a * 100) if tot_a else 0
sku_delta = merged.groupby("Item Code")["Chênh lệch"].sum()
sku_up = int((sku_delta > 0).sum())
sku_dn = int((sku_delta < 0).sum())

# ══ KPI BAND ═════════════════════════════════════════════════
section("Tổng quan thay đổi", f"{lbl_a} → {lbl_b} · {unit_sel}")
kpi_cards([
    {"label": f"Tổng {lbl_a}", "value": f"{tot_a:,.0f}", "icon": "📦", "foot": "phiên bản gốc"},
    {"label": f"Tổng {lbl_b}", "value": f"{tot_b:,.0f}", "icon": "🎯",
     "delta": f"{diff:+,.0f} ({pct:+.1f}%)", "tone": "pos" if diff >= 0 else "neg", "foot": "so với A"},
    {"label": "SKU tăng", "value": f"{sku_up:,}", "icon": "🟢", "tone": "pos",
     "delta": "tăng", "foot": "mã so với A"},
    {"label": "SKU giảm", "value": f"{sku_dn:,}", "icon": "🔴", "tone": "neg",
     "delta": "giảm", "foot": "mã so với A"},
    {"label": "Tổng SKU", "value": f"{merged['Item Code'].nunique():,}", "icon": "🧾",
     "foot": f"{len(merged):,} dòng"},
])

# ══ CHARTS ═══════════════════════════════════════════════════
ch = merged.copy()
ch["_d"] = pd.to_datetime(ch["Kỳ"], errors="coerce")
ch = ch.dropna(subset=["_d"])

cL, cR = st.columns([1.35, 1])

with cL:
    section("Diễn biến theo thời gian", "cột = sản lượng · đường = chênh lệch B−A")
    if ch.empty:
        st.caption("Không đủ dữ liệu thời gian để vẽ biểu đồ.")
    else:
        ch["Tháng"] = ch["_d"].dt.to_period("M").dt.to_timestamp()
        g = ch.groupby("Tháng", as_index=False).agg(A=(col_a, "sum"), B=(col_b, "sum"))
        g["Δ"] = g["B"] - g["A"]
        long = g.melt(id_vars=["Tháng"], value_vars=["A", "B"], var_name="pb", value_name="val")
        long["pb"] = long["pb"].map({"A": lbl_a, "B": lbl_b})

        x_enc = alt.X("yearmonth(Tháng):T", title=None, axis=alt.Axis(format="%m/%Y", labelAngle=0))
        bars = alt.Chart(long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=x_enc, xOffset=alt.XOffset("pb:N"),
            y=alt.Y("val:Q", title="Sản lượng"),
            color=alt.Color("pb:N", title="Phiên bản",
                            scale=alt.Scale(domain=[lbl_a, lbl_b], range=[cc["brand"], cc["accent"]])),
            tooltip=[alt.Tooltip("yearmonth(Tháng):T", title="Tháng", format="%m/%Y"),
                     "pb:N", alt.Tooltip("val:Q", title="SL", format=",.0f")],
        )
        line = alt.Chart(g).mark_line(point=True, strokeWidth=2.5, color=cc["warn"]).encode(
            x=x_enc, y=alt.Y("Δ:Q", title="Chênh lệch (B−A)"),
            tooltip=[alt.Tooltip("yearmonth(Tháng):T", title="Tháng", format="%m/%Y"),
                     alt.Tooltip("Δ:Q", title="Chênh lệch", format="+,.0f")],
        )
        combo = alt.layer(bars, line).resolve_scale(y="independent").properties(height=320)
        st.altair_chart(style_chart(combo), use_container_width=True)

with cR:
    section("Top biến động SKU", "tăng / giảm mạnh nhất")
    mv = sku_delta.reset_index()
    mv = mv[mv["Chênh lệch"] != 0]
    if mv.empty:
        st.caption("Không có SKU thay đổi.")
    else:
        top = pd.concat([mv.nlargest(7, "Chênh lệch"), mv.nsmallest(7, "Chênh lệch")]).drop_duplicates("Item Code")
        top["Xu hướng"] = top["Chênh lệch"].apply(lambda x: "Tăng" if x >= 0 else "Giảm")
        mvc = alt.Chart(top).mark_bar(cornerRadius=3).encode(
            y=alt.Y("Item Code:N", sort="-x", title=None),
            x=alt.X("Chênh lệch:Q", title="Chênh lệch B−A"),
            color=alt.Color("Xu hướng:N", legend=None,
                            scale=alt.Scale(domain=["Tăng", "Giảm"], range=[cc["pos"], cc["neg"]])),
            tooltip=["Item Code:N", alt.Tooltip("Chênh lệch:Q", format="+,.0f")],
        ).properties(height=320)
        st.altair_chart(style_chart(mvc), use_container_width=True)

# ══ DETAIL TABLE ═════════════════════════════════════════════
section("Chi tiết theo SKU & kỳ")
st.caption("🟢 xanh = B tăng so với A  ·  🔴 đỏ = B giảm so với A")

def color_diff(val):
    if pd.isna(val) or val == 0: return ""
    return "background-color:#D1FAE5;color:#065F46" if val > 0 else "background-color:#FEE2E2;color:#991B1B"

styled = (
    merged.style
    .map(color_diff, subset=["Chênh lệch", "Chênh lệch %"])
    .format({
        col_a: "{:,.2f}", col_b: "{:,.2f}",
        "Chênh lệch": "{:+,.2f}",
        "Chênh lệch %": lambda x: f"{x:+.1f}%" if pd.notna(x) else "—",
    })
)
st.dataframe(styled, use_container_width=True, height=440)

xlsx = to_excel_bytes(merged)
st.download_button(
    "⬇️  Xuất Excel",
    xlsx,
    f"compare_{tbl}_{lbl_a}_vs_{lbl_b}_{unit_tag}.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
