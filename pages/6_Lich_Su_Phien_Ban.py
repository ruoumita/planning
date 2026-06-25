import io
import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import text
from utils.auth import page_header
from utils.ui import section, kpi_cards, style_chart, chart_colors
from utils.database import get_versions, get_version_rows, get_version_totals, get_engine, fmt_ver

user = st.session_state["user"]
page_header("📋 Lịch sử & Xu hướng phiên bản", "Theo dõi diễn biến dữ liệu qua từng lần upload và tải lại bất kỳ phiên bản nào")


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


TABLES = {
    "fc_muf":               "FC Monthly (MUF)",
    "fc_target":            "FC Target",
    "fc_le_gt_ambient":     "FC LE GT Ambient",
    "fc_le_mt_ambient":     "FC LE MT Ambient",
    "fc_le_mt_chillfrozen": "FC LE MT ChillFrozen",
    "khsx":                 "KHSX (Prd Weekly)",
}

# ══ SLICER BAND ══════════════════════════════════════════════
cT, cU = st.columns([3, 1])
with cT:
    tbl_label = st.selectbox("Chọn bảng", list(TABLES.values()))
    tbl = [k for k, v in TABLES.items() if v == tbl_label][0]
with cU:
    unit_sel = st.radio("Đơn vị", ["Unit 1", "Unit 2"], horizontal=True, key="unit_sel_6")
qty_field = "total_qty1" if unit_sel == "Unit 1" else "total_qty2"

versions = get_versions(tbl)
if not versions:
    st.info(f"Bảng **{tbl_label}** chưa có dữ liệu nào được tải lên.")
    st.stop()

# ══ trend / totals ═══════════════════════════════════════════
totals = get_version_totals(tbl)
totals["label"] = totals.apply(lambda r: fmt_ver(r["version_id"], r["uploaded_at"]), axis=1)
totals = totals.sort_values("version_id")
CC = chart_colors()

latest = totals.iloc[-1]
prev   = totals.iloc[-2] if len(totals) > 1 else None
qty_latest = float(latest[qty_field] or 0)
qty_prev   = float(prev[qty_field] or 0) if prev is not None else 0
qd   = qty_latest - qty_prev
qpct = (qd / qty_prev * 100) if qty_prev else 0

# ══ KPI BAND ═════════════════════════════════════════════════
section("Tổng quan", f"{tbl_label} · {unit_sel}")
kpi_cards([
    {"label": "Số phiên bản", "value": f"{len(totals):,}", "icon": "🗂️", "foot": "đã upload"},
    {"label": "Phiên bản mới nhất", "value": latest["label"], "icon": "🆕",
     "foot": f"{latest['uploaded_by'] or '—'}"},
    {"label": f"Sản lượng mới nhất", "value": f"{qty_latest:,.0f}", "icon": "📦",
     "delta": (f"{qd:+,.0f} ({qpct:+.1f}%)" if prev is not None else None),
     "tone": ("pos" if qd >= 0 else "neg") if prev is not None else "neutral",
     "foot": "so với phiên bản trước"},
    {"label": "Số dòng mới nhất", "value": f"{int(latest['row_count']):,}", "icon": "🧾", "foot": "bản ghi"},
])

# ══ TREND CHART ══════════════════════════════════════════════
section("Diễn biến qua các phiên bản", "cột = số dòng · đường = tổng sản lượng")
if len(totals) >= 1:
    t = totals.copy()
    t["qty"] = t[qty_field].astype(float)
    x_enc = alt.X("label:N", title=None, sort=list(t["label"]), axis=alt.Axis(labelAngle=-35))
    bars = alt.Chart(t).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, opacity=.55,
                                 color=CC["brand"]).encode(
        x=x_enc, y=alt.Y("row_count:Q", title="Số dòng"),
        tooltip=[alt.Tooltip("label:N", title="Phiên bản"),
                 alt.Tooltip("row_count:Q", title="Số dòng", format=",.0f"),
                 alt.Tooltip("uploaded_by:N", title="Người upload")],
    )
    line = alt.Chart(t).mark_line(point=True, strokeWidth=3, color=CC["accent"]).encode(
        x=x_enc, y=alt.Y("qty:Q", title="Tổng sản lượng"),
        tooltip=[alt.Tooltip("label:N", title="Phiên bản"),
                 alt.Tooltip("qty:Q", title="Sản lượng", format=",.0f")],
    )
    combo = alt.layer(bars, line).resolve_scale(y="independent").properties(height=320)
    st.altair_chart(style_chart(combo), use_container_width=True)

# ══ VERSION LIST ═════════════════════════════════════════════
section("Danh sách phiên bản")
engine = get_engine()
summary_rows = []
with engine.connect() as conn:
    for v in versions:
        rc = conn.execute(
            text(f"SELECT COUNT(*) FROM `{tbl}` WHERE `version_id` = :v"),
            {"v": v["version_id"]}
        ).scalar()
        summary_rows.append({
            "Phiên bản": fmt_ver(v["version_id"], v["uploaded_at"]),
            "Người upload": v["uploaded_by"] or "—",
            "Ngày upload": str(v["uploaded_at"])[:10],
            "Số dòng": rc,
        })
df_sum = pd.DataFrame(summary_rows)

def highlight_latest(s):
    return ["font-weight:700; background:#EFF6FF; color:#1E3A8B" if i == 0 else "" for i in range(len(s))]

st.dataframe(
    df_sum.style.apply(highlight_latest, axis=0).format({"Số dòng": "{:,}"}),
    use_container_width=True, hide_index=True,
)

# ══ DETAIL + EXPORT ══════════════════════════════════════════
section("Xem chi tiết & tải về")
ver_opts = {
    f"{fmt_ver(v['version_id'], v['uploaded_at'])}  ·  {v['uploaded_by']}": v["version_id"]
    for v in versions
}
sel = st.selectbox("Chọn phiên bản", list(ver_opts.keys()))
sel_ver = ver_opts[sel]
sel_lbl = fmt_ver(sel_ver, next(v["uploaded_at"] for v in versions if v["version_id"] == sel_ver))
sel_rc  = next(r["Số dòng"] for r in summary_rows if r["Phiên bản"] == sel_lbl)

with st.spinner("Đang tải dữ liệu..."):
    df_preview = get_version_rows(tbl, sel_ver, limit=500)

if "item_code" in df_preview.columns:
    all_items = sorted(df_preview["item_code"].dropna().unique().tolist())
    sel_items = st.multiselect("Lọc Item Code", all_items, placeholder="Tất cả SKU — chọn để thu hẹp")
    if sel_items:
        df_preview = df_preview[df_preview["item_code"].isin(sel_items)]
else:
    sel_items = []

m1, m2, m3 = st.columns(3)
m1.metric("Phiên bản", sel_lbl)
m2.metric("Tổng số dòng", f"{sel_rc:,}")
m3.metric("Đang hiển thị", f"{len(df_preview):,}" + (" (500 đầu)" if sel_rc > 500 else ""))

dl_col, _ = st.columns([1, 3])
with dl_col:
    with st.spinner("Chuẩn bị file..."):
        df_full = get_version_rows(tbl, sel_ver)
        if sel_items:
            df_full = df_full[df_full["item_code"].isin(sel_items)]
    xlsx = _to_excel(df_full)
    st.download_button(
        f"⬇️  Xuất Excel — {sel_lbl}  ({len(df_full):,} dòng)",
        xlsx, f"{tbl}_{sel_lbl}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.dataframe(df_preview, use_container_width=True, height=440)
