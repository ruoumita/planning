"""
Enterprise ERP Design System — Industrial Light theme.
Sidebar tối tương phản cao, nội dung chính sáng chuyên nghiệp.
Không có dark mode toggle — một giao diện duy nhất, ổn định.
"""
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

/* ── Typography ──────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Inter', 'Roboto', 'Segoe UI', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
}}

/* ── App canvas ──────────────────────────────────────────── */
.stApp {{ background: {p['bg']} !important; color: {p['text']} !important; }}
.main .block-container {{
    padding: 1.2rem 2rem 2.5rem !important;
    max-width: 1520px !important;
}}

/* ── Text normalization ──────────────────────────────────── */
.stApp p, .stApp li {{ color: {p['text']} !important; }}
.stApp [data-testid="stMarkdownContainer"] p  {{ color: {p['text']} !important; }}
.stApp [data-testid="stMarkdownContainer"] li {{ color: {p['text']} !important; }}
.stApp [data-testid="stMarkdownContainer"] span {{ color: {p['text']}; }}
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] * {{
    color: {p['text_faint']} !important; font-size:.77rem !important; }}
.stApp h1, .stApp h2, .stApp h3 {{ color: {p['text']} !important; font-weight:700 !important; }}
.stApp h4, .stApp h5 {{
    color: {p['text_dim']} !important; font-size:.76rem !important;
    text-transform: uppercase; letter-spacing:.9px !important; font-weight:700 !important; }}
.stApp .main h3 {{
    font-size: 1rem !important; font-weight:700 !important;
    color: {p['text']} !important; margin: 1.2rem 0 .5rem !important; }}

/* ── Page header ─────────────────────────────────────────── */
.ph-wrap {{
    display:flex; align-items:flex-end; justify-content:space-between;
    margin-bottom:1rem; padding-bottom:.75rem;
    border-bottom:2px solid {p['border']};
}}
.ph-title {{ font-size:1.25rem; font-weight:700; color:{p['text']}; margin:0;
    letter-spacing:-.3px; line-height:1.2; }}
.ph-sub {{ font-size:.78rem; color:{p['text_dim']}; margin:.2rem 0 0; }}

/* ── Section header ──────────────────────────────────────── */
.sec-head {{ display:flex; align-items:center; gap:.5rem; margin:1.1rem 0 .65rem; }}
.sec-head::before {{ content:""; width:3px; height:15px; border-radius:2px;
    background:{p['brand']}; }}
.sec-title {{ font-size:.93rem; font-weight:600; color:{p['text']}; letter-spacing:-.1px; }}
.sec-sub {{ font-size:.74rem; color:{p['text_faint']}; margin-left:.3rem; }}

/* ── KPI cards — compact ERP ─────────────────────────────── */
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr));
    gap:.55rem; margin:.15rem 0 .5rem; }}
.kpi {{
    position:relative; background:{p['surface']};
    border:1px solid {p['border']}; border-radius:5px;
    padding:.8rem .95rem; box-shadow:{p['shadow']};
    transition:box-shadow .12s ease; overflow:hidden;
}}
.kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px;
    background:{p['brand']}; }}
.kpi:hover {{ box-shadow:{p['shadow_hover']}; }}
.kpi-top {{ display:flex; align-items:center; gap:.4rem; margin-bottom:.35rem; }}
.kpi-ico {{ width:24px; height:24px; border-radius:4px; display:flex; align-items:center;
    justify-content:center; font-size:12px; background:{p['brand_soft']}; flex-shrink:0; }}
.kpi-label {{ font-size:.63rem; font-weight:700; color:{p['text_dim']};
    text-transform:uppercase; letter-spacing:.7px; line-height:1.1; }}
.kpi-value {{ font-size:1.42rem; font-weight:700; color:{p['text']}; line-height:1.05;
    letter-spacing:-.4px; }}
.kpi-delta {{ font-size:.68rem; font-weight:600; margin-top:.25rem; display:flex;
    align-items:center; gap:.25rem; }}
.kpi-delta.pos {{ color:{p['pos']}; }}
.kpi-delta.neg {{ color:{p['neg']}; }}
.kpi-delta.neutral {{ color:{p['text_faint']}; }}
.kpi-foot {{ color:{p['text_faint']}; font-weight:500; }}

/* ── Metric (native) ─────────────────────────────────────── */
div[data-testid="stMetric"], div[data-testid="metric-container"] {{
    background:{p['surface']} !important; border:1px solid {p['border']} !important;
    border-radius:5px !important; padding:.8rem 1rem !important;
    box-shadow:{p['shadow']} !important; }}
[data-testid="stMetricLabel"] p {{ color:{p['text_dim']} !important; font-weight:600 !important;
    font-size:.67rem !important; text-transform:uppercase; letter-spacing:.6px; }}
[data-testid="stMetricValue"] {{ color:{p['text']} !important; font-weight:700 !important; }}

/* ── Buttons — ERP flat ──────────────────────────────────── */
.stApp .stButton > button, .stApp .stDownloadButton > button {{
    border-radius:5px !important; font-weight:500 !important; font-size:.83rem !important;
    transition:all .12s !important; border:1px solid {p['border_strong']} !important;
    background:{p['surface']} !important; color:{p['text']} !important;
    padding:.32rem .85rem !important; box-shadow:none !important; }}
.stApp .stButton > button:hover, .stApp .stDownloadButton > button:hover {{
    border-color:{p['brand']} !important; color:{p['brand']} !important;
    background:{p['brand_soft']} !important; }}
.stApp .stButton > button[kind="primary"] {{
    background:{p['brand']} !important; color:#fff !important;
    border:none !important; box-shadow:none !important; }}
.stApp .stButton > button[kind="primary"]:hover {{
    background:{p['brand_deep']} !important; color:#fff !important; }}

/* ── Tabs — ERP underline style ──────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap:0 !important; border-bottom:1px solid {p['border']} !important;
    background:{p['surface']} !important; }}
.stTabs [data-baseweb="tab"] {{
    font-size:.81rem !important; font-weight:500 !important;
    color:{p['text_dim']} !important; padding:.52rem .85rem !important;
    border-radius:0 !important; border-bottom:2px solid transparent !important; }}
.stTabs [aria-selected="true"] {{
    color:{p['brand']} !important; border-bottom:2px solid {p['brand']} !important;
    font-weight:600 !important; background:{p['brand_soft']} !important; }}

/* ── Inline code ─────────────────────────────────────────── */
code {{ background:{p['brand_soft']} !important; color:{p['brand']} !important;
    border:1px solid {p['border']} !important; border-radius:3px !important;
    padding:1px 5px !important; font-size:.82em !important; }}

/* ── Labels ──────────────────────────────────────────────── */
.stApp label {{ color:{p['text_dim']} !important; font-size:.79rem !important;
    font-weight:600 !important; letter-spacing:.1px !important; }}

/* ── Inputs / textarea ───────────────────────────────────── */
.stApp [data-baseweb="input"],
.stApp [data-baseweb="base-input"],
.stApp [data-baseweb="input"] > div,
.stApp [data-baseweb="textarea"],
.stApp .stTextInput > div > div,
.stApp .stPasswordInput > div > div,
.stApp .stNumberInput > div > div {{
    background:{p['surface']} !important;
    border-color:{p['border_strong']} !important; border-radius:5px !important; }}
.stApp [data-baseweb="input"]:focus-within,
.stApp [data-baseweb="textarea"]:focus-within {{
    border-color:{p['brand']} !important;
    box-shadow:0 0 0 2px rgba(2,132,199,.14) !important; }}
.stApp [data-baseweb="input"] input {{ color:{p['text']} !important; }}
.stApp [data-baseweb="input"] input::placeholder {{ color:{p['text_faint']} !important; }}
.stApp [data-baseweb="textarea"] textarea {{ color:{p['text']} !important; }}
.stApp [data-baseweb="textarea"] textarea::placeholder {{ color:{p['text_faint']} !important; }}

/* ── Selectbox ───────────────────────────────────────────── */
.stApp [data-baseweb="select"],
.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="select"] > div > div,
.stApp .stSelectbox > div > div {{
    background:{p['surface']} !important;
    border-color:{p['border_strong']} !important; border-radius:5px !important; }}
.stApp [data-baseweb="select"] [data-value],
.stApp [data-baseweb="select"] input,
.stApp [data-baseweb="select"] span {{ color:{p['text']} !important; }}
.stApp [data-baseweb="select"] svg path {{ fill:{p['text_dim']} !important; }}
.stApp [data-baseweb="popover"],
.stApp [data-baseweb="menu"] {{
    background:{p['surface']} !important; border:1px solid {p['border']} !important;
    box-shadow:{p['shadow_hover']} !important; border-radius:5px !important; }}
.stApp [data-baseweb="option"] {{
    background:{p['surface']} !important; color:{p['text']} !important;
    font-size:.83rem !important; }}
.stApp [data-baseweb="option"]:hover,
.stApp [data-baseweb="option"][aria-selected="true"] {{
    background:{p['brand_soft']} !important; color:{p['brand']} !important; }}

/* ── File uploader ───────────────────────────────────────── */
.stApp [data-testid="stFileUploadDropzone"],
.stApp .stFileUploader section,
.stApp .stFileUploader > div > div {{
    background:{p['surface_2']} !important;
    border:1px dashed {p['border_strong']} !important; border-radius:6px !important; }}
.stApp [data-testid="stFileUploadDropzone"] p,
.stApp [data-testid="stFileUploadDropzone"] span,
.stApp [data-testid="stFileUploadDropzone"] small {{ color:{p['text_dim']} !important; font-size:.82rem !important; }}
.stApp [data-testid="stFileUploadDropzone"] button,
.stApp .stFileUploader button {{
    background:{p['surface']} !important; color:{p['brand']} !important;
    border:1px solid {p['brand']} !important; border-radius:5px !important;
    font-size:.82rem !important; font-weight:500 !important; }}
.stApp [data-testid="stFileUploaderFile"] {{
    background:{p['surface']} !important; border:1px solid {p['border']} !important;
    border-radius:5px !important; }}
.stApp [data-testid="stFileUploaderFile"] * {{ color:{p['text_dim']} !important; }}

/* ── Form container ──────────────────────────────────────── */
.stApp [data-testid="stForm"],
.stApp .stForm,
.stApp [data-testid="stForm"] > div {{
    background:{p['surface']} !important; border:1px solid {p['border']} !important;
    border-radius:6px !important; padding:1rem 1.2rem !important; }}

/* ── Expander ────────────────────────────────────────────── */
.stApp [data-testid="stExpander"] {{
    border:1px solid {p['border']} !important; border-radius:6px !important;
    background:{p['surface']} !important; }}
.stApp [data-testid="stExpander"] summary {{
    color:{p['text']} !important; font-weight:600 !important;
    font-size:.84rem !important; padding:.55rem .85rem !important; }}
.stApp [data-testid="stExpander"] summary:hover {{ background:{p['surface_2']} !important; }}
.stApp [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{
    color:{p['text']} !important; }}

/* ── DataFrame ───────────────────────────────────────────── */
.stApp [data-testid="stDataFrame"] {{
    border:1px solid {p['border']} !important; border-radius:5px !important;
    overflow:hidden !important; box-shadow:{p['shadow']} !important; }}

/* ── Alerts ──────────────────────────────────────────────── */
.stApp .stAlert {{ border-radius:5px !important; border-left-width:3px !important; }}
.stApp [data-testid="stAlert"] {{ border-radius:5px !important; }}

/* ── Divider ─────────────────────────────────────────────── */
hr {{ border-color:{p['border']} !important; margin:1rem 0 !important; }}

/* ── Popover ─────────────────────────────────────────────── */
.stApp [data-testid="stPopover"],
.stApp [data-testid="stPopover"] > div {{
    background:{p['surface']} !important; border:1px solid {p['border']} !important;
    border-radius:6px !important; box-shadow:{p['shadow_hover']} !important; }}
.stApp [data-testid="stPopover"] p {{ color:{p['text']} !important; }}

/* ── Number input ────────────────────────────────────────── */
.stApp [data-testid="stNumberInput"] button {{
    background:{p['surface_2']} !important; color:{p['text_dim']} !important;
    border-color:{p['border']} !important; border-radius:4px !important; }}

/* ── Chart card ──────────────────────────────────────────── */
[data-testid="stVegaLiteChart"], .stVegaLiteChart {{
    background:{p['surface']}; border:1px solid {p['border']}; border-radius:5px;
    padding:.45rem .3rem .1rem; box-shadow:{p['shadow']}; }}
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# COMPONENTS
# ════════════════════════════════════════════════════════════

def section(title: str, sub: str = "") -> None:
    sub_html = f'<span class="sec-sub">{sub}</span>' if sub else ""
    st.markdown(f'<div class="sec-head"><span class="sec-title">{title}</span>{sub_html}</div>',
                unsafe_allow_html=True)


def kpi_cards(cards: list[dict]) -> None:
    """cards: list of dict(label, value, icon='', delta='', tone='neutral'|'pos'|'neg', foot='')"""
    p = _P
    items = []
    for c in cards:
        ico = f'<span class="kpi-ico">{c.get("icon","")}</span>' if c.get("icon") else ""
        delta = ""
        if c.get("delta"):
            tone = c.get("tone", "neutral")
            arrow = "▲" if tone == "pos" else "▼" if tone == "neg" else "•"
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
