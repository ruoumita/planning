import io
import streamlit as st
import pandas as pd
import altair as alt
from sqlalchemy import text
from utils.auth import page_header
from utils.ui import section, kpi_cards, style_chart, chart_colors
from utils.database import get_engine, get_table_stats, get_versions, get_version_totals, fmt_ver

user = st.session_state["user"]
page_header("📊 Dashboard", "Bức tranh tổng thể chuỗi cung ứng — Demand & Supply Planning")


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


TABLES = {
    "fc_muf":               ("FC Monthly (MUF)",    "🗓️"),
    "fc_target":            ("FC Target",           "🎯"),
    "fc_le_gt_ambient":     ("FC LE GT Ambient",    "🏪"),
    "fc_le_mt_ambient":     ("FC LE MT Ambient",    "🏬"),
    "fc_le_mt_chillfrozen": ("FC LE MT ChillFrozen","❄️"),
    "khsx":                 ("KHSX (Prd Weekly)",   "🏭"),
}
CC = chart_colors()

# ══ EXECUTIVE KPI BAND ═══════════════════════════════════════
stats = {tbl: get_table_stats(tbl) for tbl in TABLES}
total_versions = sum(s["version_count"] for s in stats.values())
total_rows     = sum(s["total_rows"] for s in stats.values())
tables_ready   = sum(1 for s in stats.values() if s["version_count"] > 0)
latest_overall = max(
    [(s["latest_at"], k) for k, s in stats.items() if s["latest_at"]],
    default=(None, None)
)
last_lbl = "—"
if latest_overall[0]:
    k = latest_overall[1]
    last_lbl = f"{TABLES[k][0]} · {fmt_ver(stats[k]['latest_version'], stats[k]['latest_at'])}"

section("Chỉ số tổng hợp")
kpi_cards([
    {"label": "Bảng có dữ liệu", "value": f"{tables_ready}/{len(TABLES)}", "icon": "🗂️",
     "foot": "nguồn dữ liệu đang hoạt động"},
    {"label": "Tổng phiên bản", "value": f"{total_versions:,}", "icon": "🔢", "foot": "trên toàn hệ thống"},
    {"label": "Tổng bản ghi", "value": f"{total_rows:,}", "icon": "🧾", "foot": "dòng dữ liệu"},
    {"label": "Cập nhật gần nhất", "value": last_lbl.split(' · ')[-1] if last_lbl != "—" else "—",
     "icon": "🕒", "foot": last_lbl.split(' · ')[0] if last_lbl != "—" else "chưa có dữ liệu"},
])

# ══ PER-TABLE STATUS CARDS ═══════════════════════════════════
section("Trạng thái theo bảng dữ liệu")
cards = []
for tbl, (label, icon) in TABLES.items():
    s = stats[tbl]
    if s["latest_version"] and s["latest_at"]:
        ver_lbl = fmt_ver(s["latest_version"], s["latest_at"])
        cards.append({
            "label": label, "icon": icon, "value": f"{s['version_count']} phiên bản",
            "delta": ver_lbl, "tone": "neutral",
            "foot": f"{s['total_rows']:,} dòng · {s['uploaded_by'] or '—'}",
        })
    else:
        cards.append({"label": label, "icon": icon, "value": "—", "foot": "chưa có dữ liệu"})
kpi_cards(cards)

st.divider()

# ══ UPLOAD ACTIVITY ══════════════════════════════════════════
try:
    engine = get_engine()
    history = []
    with engine.connect() as conn:
        for tbl, (label, _) in TABLES.items():
            rows = conn.execute(text(f"""
                SELECT MIN(`uploaded_at`) AS d, `version_id`
                FROM `{tbl}` GROUP BY `version_id`
            """)).fetchall()
            for r in rows:
                if r[0]:
                    history.append({"Bảng": label, "Ngày": pd.to_datetime(str(r[0])).date()})

    cL, cR = st.columns([1.5, 1])
    with cL:
        section("Hoạt động upload", "số phiên bản theo ngày")
        if history:
            df_h = pd.DataFrame(history)
            agg = df_h.groupby(["Ngày", "Bảng"]).size().reset_index(name="count")
            chart = alt.Chart(agg).mark_bar(cornerRadius=2).encode(
                x=alt.X("Ngày:T", title=None, axis=alt.Axis(format="%d/%m")),
                y=alt.Y("count:Q", title="Số phiên bản"),
                color=alt.Color("Bảng:N", title=None,
                                scale=alt.Scale(scheme="blues")),
                tooltip=["Ngày:T", "Bảng:N", "count:Q"],
            ).properties(height=300)
            st.altair_chart(style_chart(chart), use_container_width=True)
        else:
            st.info("Chưa có lịch sử upload.")

    with cR:
        section("Phiên bản hiện tại")
        cur = []
        for tbl, (label, _) in TABLES.items():
            s = stats[tbl]
            cur.append({"Bảng": label,
                        "Phiên bản": fmt_ver(s["latest_version"], s["latest_at"]) if s["latest_version"] else "—"})
        st.dataframe(pd.DataFrame(cur), use_container_width=True, hide_index=True, height=300)
except Exception:
    st.info("Không thể tải hoạt động upload.")

st.divider()

# ══ KHSX SPOTLIGHT ═══════════════════════════════════════════
section("KHSX — Sản lượng phiên bản mới nhất", "Top SKU theo kế hoạch sản xuất")
try:
    versions = get_versions("khsx")
    if versions:
        lv = versions[0]["version_id"]
        ver_lbl = fmt_ver(lv, versions[0]["uploaded_at"])
        engine = get_engine()
        with engine.connect() as conn:
            df_k = pd.read_sql(text("""
                SELECT `item_code`, SUM(`qty_1`) AS u1, SUM(`qty_2`) AS u2
                FROM `khsx` WHERE `version_id` = :v
                GROUP BY `item_code` ORDER BY u1 DESC LIMIT 50
            """), conn, params={"v": lv})

        for c in ("u1", "u2"):
            if c in df_k.columns:
                df_k[c] = pd.to_numeric(df_k[c], errors="coerce").fillna(0.0)

        if not df_k.empty:
            f1, f2 = st.columns([3, 1])
            with f1:
                items = sorted(df_k["item_code"].dropna().unique().tolist())
                sel_items = st.multiselect("Lọc Item Code", items,
                                           placeholder="Top 50 SKU — chọn để thu hẹp", key="db_item")
            with f2:
                u_sel = st.radio("Đơn vị", ["Unit 1", "Unit 2"], horizontal=True, key="db_unit")
            qcol = "u1" if u_sel == "Unit 1" else "u2"
            d = df_k[df_k["item_code"].isin(sel_items)] if sel_items else df_k

            kpi_cards([
                {"label": "Tổng sản lượng", "value": f"{d[qcol].sum():,.0f}", "icon": "📦", "foot": ver_lbl},
                {"label": "Số SKU", "value": f"{len(d):,}", "icon": "🔖", "foot": f"đơn vị {u_sel}"},
                {"label": "SKU lớn nhất", "value": f"{d[qcol].max():,.0f}" if len(d) else "—",
                 "icon": "🏆", "foot": (d.iloc[0]['item_code'] if len(d) else "—")},
            ])

            top = d.nlargest(20, qcol)
            chart = alt.Chart(top).mark_bar(cornerRadius=3, color=CC["brand"]).encode(
                y=alt.Y("item_code:N", sort="-x", title=None),
                x=alt.X(f"{qcol}:Q", title=f"Sản lượng ({u_sel})"),
                tooltip=["item_code:N", alt.Tooltip(f"{qcol}:Q", format=",.0f")],
            ).properties(height=420)
            st.altair_chart(style_chart(chart), use_container_width=True)

            xlsx = _to_excel(d.rename(columns={"item_code": "Item Code", "u1": "Unit 1", "u2": "Unit 2"}))
            st.download_button(f"⬇️  Xuất Excel — {ver_lbl}", xlsx,
                               f"khsx_dashboard_{ver_lbl}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Chưa có dữ liệu KHSX.")
except Exception:
    st.info("Không thể tải dữ liệu KHSX.")
