"""
Enterprise ERP Design System — Industrial Light theme.
Sidebar tối tương phản cao, nội dung chính sáng chuyên nghiệp.
Không có dark mode toggle — một giao diện duy nhất, ổn định.
"""
import io
from typing import List

import pandas as pd
import streamlit as st

# ════════════════════════════════════════════════════════════
# PALETTE — Industrial Enterprise Light
# ════════════════════════════════════════════════════════════

_P = {
    # Backgrounds
    "bg":            "#F4F6F9",   # Main canvas
    "surface":       "#FFFFFF",   # Cards / tables
    "surface_2":     "#F8FAFC",   # Nested / input bg
    # Borders
    "border":        "#E2E8F0",   # Standard (SAP-style gridlines)
    "border_strong": "#CBD5E1",   # Stronger border
    # Text
    "text":          "#1E293B",   # Primary (Slate 800)
    "text_dim":      "#64748B",   # Secondary (Slate 500)
    "text_faint":    "#94A3B8",   # Placeholder / faint (Slate 400)
    # Brand / actions
    "brand":         "#0284C7",   # Industrial Blue
    "brand_deep":    "#0369A1",
    "brand_soft":    "#E0F2FE",   # Light tint
    "accent":        "#0EA5E9",
    # Status
    "pos":           "#059669",
    "pos_soft":      "#D1FAE5",
    "neg":           "#DC2626",
    "neg_soft":      "#FEE2E2",
    "warn":          "#D97706",
    "warn_soft":     "#FEF3C7",
    # Chart
    "grid":          "#E2E8F0",
    # Shadows (ERP — cực nhẹ, không dày)
    "shadow":        "0 1px 3px rgba(15,23,42,.07), 0 1px 2px rgba(15,23,42,.04)",
    "shadow_hover":  "0 4px 12px rgba(2,132,199,.10), 0 2px 4px rgba(2,132,199,.06)",
}


def get_theme() -> str:
    return "light"


def palette() -> dict:
    return _P


# ════════════════════════════════════════════════════════════
# GLOBAL CSS
# ════════════════════════════════════════════════════════════

def inject_global_css() -> None:
    p = _P
    vars_block = "\n".join(f"    --{k.replace('_','-')}: {v};" for k, v in p.items())

    st.markdown(f"""<style>
:root {{
{vars_block}
    --background-color:           {p['bg']};
    --secondary-background-color: {p['surface']};
    --text-color:                 {p['text']};
    --primary-color:              {p['brand']};
}}

html, body, [class*="css"] {{
    font-family: 'Inter', 'Roboto', 'Segoe UI', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
}}

.stApp {{ background: {p['bg']} !important; color: {p['text']} !important; }}
.main .block-container {{
    padding: 1.2rem 2rem 2.5rem !important;
    max-width: 1520px !important;
}}

.stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
    color: {p['text']} !important;
}}

.stApp [data-testid="stMetric"] {{
    background: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 5px !important;
    padding: .8rem 1rem !important;
}}

.stApp .stButton > button, .stApp .stDownloadButton > button {{
    border-radius: 5px !important;
    border: 1px solid {p['border_strong']} !important;
    background: {p['surface']} !important;
    color: {p['text']} !important;
    padding: .32rem .85rem !important;
}}
.stApp .stButton > button[kind="primary"] {{
    background: {p['brand']} !important;
    color: #fff !important;
    border: none !important;
}}
.stApp .stButton > button:hover {{
    border-color: {p['brand']} !important;
    color: {p['brand']} !important;
    background: {p['brand_soft']} !important;
}}

.ph-wrap {{
    display:flex; align-items:flex-end; justify-content:space-between;
    margin-bottom:1rem; padding-bottom:.75rem; border-bottom:2px solid {p['border']};
}}
.ph-title {{ font-size:1.25rem; font-weight:700; color:{p['text']}; margin:0;
    letter-spacing:-.3px; line-height:1.2; }}
.ph-sub {{ font-size:.78rem; color:{p['text_dim']}; margin:.2rem 0 0; }}

.sec-head {{ display:flex; align-items:center; gap:.5rem; margin:1.1rem 0 .65rem; }}
.sec-title {{ font-size:.93rem; font-weight:600; color:{p['text']}; letter-spacing:-.1px; }}
.sec-sub {{ font-size:.74rem; color:{p['text_faint']}; margin-left:.3rem; }}

.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:.55rem; margin:.15rem 0 .5rem; }}
.kpi {{ background:{p['surface']}; border:1px solid {p['border']}; border-radius:5px; padding:.8rem .95rem; box-shadow:{p['shadow']}; }}
.kpi-ico {{ width:24px; height:24px; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:12px; background:{p['brand_soft']}; flex-shrink:0; }}
.kpi-label {{ font-size:.63rem; font-weight:700; color:{p['text_dim']}; text-transform:uppercase; letter-spacing:.7px; }}
.kpi-value {{ font-size:1.42rem; font-weight:700; color:{p['text']}; line-height:1.05; letter-spacing:-.4px; }}
.kpi-delta {{ font-size:.68rem; font-weight:600; margin-top:.25rem; display:flex; align-items:center; gap:.25rem; }}
.kpi-delta.pos {{ color:{p['pos']}; }}
.kpi-delta.neg {{ color:{p['neg']}; }}
.kpi-delta.neutral {{ color:{p['text_faint']}; }}
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# COMPONENTS
# ════════════════════════════════════════════════════════════

def section(title: str, sub: str = "") -> None:
    sub_html = f'<span class="sec-sub">{sub}</span>' if sub else ""
    st.markdown(f'<div class="sec-head"><span class="sec-title">{title}</span>{sub_html}</div>',
                unsafe_allow_html=True)


def kpi_cards(cards: List[dict]) -> None:
    """cards: list of dict(label, value, icon='', delta='', tone='neutral'|'pos'|'neg', foot='')"""
    items = []
    for c in cards:
        ico = f'<span class="kpi-ico">{c.get("icon","")}</span>' if c.get("icon") else ""
        tone = c.get("tone", "neutral")
        arrow = "▲" if tone == "pos" else "▼" if tone == "neg" else "•"
        delta = ""
        if c.get("delta"):
            foot = f'<span class="kpi-foot">· {c["foot"]}</span>' if c.get("foot") else ""
            delta = f'<div class="kpi-delta {tone}">{arrow} {c["delta"]} {foot}</div>'
        elif c.get("foot"):
            delta = f'<div class="kpi-delta neutral"><span class="kpi-foot">{c["foot"]}</span></div>'
        items.append(
            f'<div class="kpi"><div class="kpi-top">{ico}'
            f'<span class="kpi-label">{c["label"]}</span></div>'
            f'<div class="kpi-value">{c["value"]}</div>{delta}</div>'
        )
    st.markdown(f'<div class="kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CHART THEME (Altair)
# ════════════════════════════════════════════════════════════

def chart_colors() -> dict:
    p = _P
    return {
        "brand": p["brand"], "accent": p["accent"],
        "pos": p["pos"], "neg": p["neg"], "warn": p["warn"],
        "grid": p["grid"], "axis": p["text_dim"], "text": p["text"],
    }


def page_header(title: str, subtitle: str = "") -> None:
    """Tiêu đề trang chuẩn — dùng ở đầu mỗi trang nội dung."""
    sub_html = f'<p class="ph-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="ph-wrap">
        <h1 class="ph-title">{title}</h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def style_chart(ch):
    """Áp ERP theme thống nhất cho mọi biểu đồ Altair."""
    c = chart_colors()
    return (
        ch.configure(background="transparent")
          .configure_view(strokeWidth=0, fill="transparent")
          .configure_axis(
              labelColor=c["axis"], titleColor=c["axis"],
              gridColor=c["grid"], domainColor=c["grid"], tickColor=c["grid"],
              labelFontSize=11, titleFontSize=11, titleFontWeight=600, grid=True)
          .configure_legend(labelColor=c["text"], titleColor=c["text"],
                            labelFontSize=11, titleFontSize=11, orient="top")
          .configure_title(color=c["text"], fontSize=13, anchor="start", fontWeight=700)
    )


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()
