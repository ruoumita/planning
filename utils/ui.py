"""
Design system — bảng màu chuyên nghiệp, KPI card, section header, theme cho biểu đồ.
Tự động đồng bộ với chế độ Sáng/Tối của Streamlit (Settings → Theme).
"""
import streamlit as st

# ════════════════════════════════════════════════════════════
# THEME PALETTES
# ════════════════════════════════════════════════════════════

_LIGHT = {
    "bg":            "#F4F6FB",
    "surface":       "#FFFFFF",
    "surface_2":     "#F8FAFD",
    "border":        "#E4E9F2",
    "border_strong": "#CBD5E1",
    "text":          "#0D1A2B",
    "text_dim":      "#5C6B82",
    "text_faint":    "#8A98AD",
    "brand":         "#2B59E0",
    "brand_deep":    "#1E40C4",
    "brand_soft":    "#EAF0FF",
    "accent":        "#6366F1",
    "pos":           "#0E9F6E",
    "pos_soft":      "#DEF7EC",
    "neg":           "#E02424",
    "neg_soft":      "#FDE8E8",
    "warn":          "#C27803",
    "warn_soft":     "#FDF6B2",
    "grid":          "#E8EDF5",
    "shadow":        "0 1px 2px rgba(16,30,54,.05), 0 8px 28px rgba(16,30,54,.06)",
    "shadow_hover":  "0 2px 6px rgba(43,89,224,.12), 0 14px 34px rgba(43,89,224,.14)",
}

_DARK = {
    "bg":            "#0B1220",
    "surface":       "#141E30",
    "surface_2":     "#1B2840",
    "border":        "#243353",
    "border_strong": "#33476E",
    "text":          "#E8EEF8",
    "text_dim":      "#9FB0CC",
    "text_faint":    "#6B7C9B",
    "brand":         "#5B8DEF",
    "brand_deep":    "#4F7BE0",
    "brand_soft":    "#18243B",
    "accent":        "#818CF8",
    "pos":           "#34D399",
    "pos_soft":      "rgba(52,211,153,.14)",
    "neg":           "#F87171",
    "neg_soft":      "rgba(248,113,113,.14)",
    "warn":          "#FBBF24",
    "warn_soft":     "rgba(251,191,36,.14)",
    "grid":          "#22314E",
    "shadow":        "0 1px 2px rgba(0,0,0,.45), 0 10px 30px rgba(0,0,0,.4)",
    "shadow_hover":  "0 2px 8px rgba(0,0,0,.5), 0 16px 38px rgba(0,0,0,.5)",
}


def get_theme() -> str:
    """'light' | 'dark' — ưu tiên override từ sidebar toggle, fallback Streamlit native."""
    override = st.session_state.get("_theme_override")
    if override in ("light", "dark"):
        return override
    try:
        t = st.context.theme.type
        return t if t in ("light", "dark") else "light"
    except Exception:
        return "light"


def palette() -> dict:
    return _DARK if get_theme() == "dark" else _LIGHT


# ════════════════════════════════════════════════════════════
# GLOBAL CSS
# ════════════════════════════════════════════════════════════

def inject_global_css() -> None:
    p = palette()
    vars_block = "\n".join(f"    --{k.replace('_','-')}: {v};" for k, v in p.items())

    st.markdown(f"""<style>
:root {{
{vars_block}
}}

/* ── Typography ──────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
}}

/* ── App canvas ──────────────────────────────────────────── */
.stApp {{ background: var(--bg) !important; }}
.main .block-container {{
    padding: 1.6rem 2.4rem 3rem !important;
    max-width: 1480px !important;
}}
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] li {{ color: var(--text); }}
.main h1, .main h2, .main h3, .main h4 {{ color: var(--text); }}

/* ── Page header ─────────────────────────────────────────── */
.ph-wrap {{
    display:flex; align-items:flex-end; justify-content:space-between;
    margin-bottom: 1.4rem; padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}}
.ph-title {{ font-size: 1.5rem; font-weight: 800; color: var(--text); margin: 0; letter-spacing:-.4px; line-height:1.2; }}
.ph-sub {{ font-size: .85rem; color: var(--text-dim); margin: .3rem 0 0; }}

/* ── Section header ──────────────────────────────────────── */
.sec-head {{ display:flex; align-items:center; gap:.6rem; margin: 1.5rem 0 .9rem; }}
.sec-head::before {{ content:""; width:4px; height:18px; border-radius:3px;
    background: linear-gradient(180deg, var(--brand), var(--accent)); }}
.sec-title {{ font-size: 1.02rem; font-weight: 700; color: var(--text); letter-spacing:-.2px; }}
.sec-sub {{ font-size: .78rem; color: var(--text-faint); margin-left:.35rem; }}

/* ── KPI cards ───────────────────────────────────────────── */
.kpi-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
    gap: .85rem; margin: .25rem 0 .5rem; }}
.kpi {{
    position:relative; background: var(--surface);
    border: 1px solid var(--border); border-radius: 14px;
    padding: 1.05rem 1.15rem 1rem; box-shadow: var(--shadow);
    transition: transform .16s ease, box-shadow .16s ease; overflow:hidden;
}}
.kpi::before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px;
    background: linear-gradient(180deg, var(--brand), var(--accent)); opacity:.85; }}
.kpi:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-hover); }}
.kpi-top {{ display:flex; align-items:center; gap:.5rem; margin-bottom:.55rem; }}
.kpi-ico {{ width:30px; height:30px; border-radius:9px; display:flex; align-items:center;
    justify-content:center; font-size:15px; background: var(--brand-soft); flex-shrink:0; }}
.kpi-label {{ font-size:.685rem; font-weight:700; color: var(--text-dim);
    text-transform:uppercase; letter-spacing:.7px; line-height:1.1; }}
.kpi-value {{ font-size:1.62rem; font-weight:800; color: var(--text); line-height:1.05;
    letter-spacing:-.6px; }}
.kpi-delta {{ font-size:.74rem; font-weight:600; margin-top:.4rem; display:flex;
    align-items:center; gap:.3rem; }}
.kpi-delta.pos {{ color: var(--pos); }}
.kpi-delta.neg {{ color: var(--neg); }}
.kpi-delta.neutral {{ color: var(--text-faint); }}
.kpi-foot {{ color: var(--text-faint); font-weight:500; }}

/* ── Metric (native) ─────────────────────────────────────── */
div[data-testid="stMetric"], div[data-testid="metric-container"] {{
    background: var(--surface) !important; border:1px solid var(--border) !important;
    border-radius:14px !important; padding:1rem 1.25rem !important; box-shadow: var(--shadow) !important;
}}
[data-testid="stMetricLabel"] p {{ color: var(--text-dim) !important; font-weight:600 !important;
    font-size:.72rem !important; text-transform:uppercase; letter-spacing:.5px; }}
[data-testid="stMetricValue"] {{ color: var(--text) !important; font-weight:800 !important; }}

/* ── Buttons ─────────────────────────────────────────────── */
.main .stButton > button, .main .stDownloadButton > button {{
    border-radius:10px !important; font-weight:600 !important; font-size:.85rem !important;
    transition: all .16s !important; border:1px solid var(--border-strong) !important;
    background: var(--surface) !important; color: var(--text) !important;
}}
.main .stButton > button:hover, .main .stDownloadButton > button:hover {{
    border-color: var(--brand) !important; color: var(--brand) !important; }}
.main .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, var(--brand), var(--brand-deep)) !important;
    color:#fff !important; border:none !important;
    box-shadow: 0 2px 10px rgba(43,89,224,.32) !important; }}
.main .stButton > button[kind="primary"]:hover {{ transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(43,89,224,.42) !important; color:#fff !important; }}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{ gap:.25rem !important; border-bottom:1px solid var(--border) !important; }}
.stTabs [data-baseweb="tab"] {{ font-size:.84rem !important; font-weight:600 !important;
    color: var(--text-dim) !important; padding:.6rem .95rem !important;
    border-radius:9px 9px 0 0 !important; }}
.stTabs [aria-selected="true"] {{ color: var(--brand) !important;
    border-bottom:2px solid var(--brand) !important; }}

/* ── Section h3/h4 ───────────────────────────────────────── */
.main h3 {{ font-size:1.08rem !important; font-weight:700 !important; color:var(--text) !important;
    margin:1.4rem 0 .6rem !important; letter-spacing:-.2px !important; }}
.main h4 {{ font-size:.95rem !important; font-weight:700 !important; color:var(--text-dim) !important;
    margin:1.1rem 0 .5rem !important; letter-spacing:.1px !important;
    text-transform:uppercase; font-size:.75rem !important; letter-spacing:.8px !important; }}

/* ── Inline code ─────────────────────────────────────────── */
code {{ background: var(--brand-soft) !important; color: var(--brand) !important;
    border: 1px solid var(--border) !important; border-radius:5px !important;
    padding: 1px 6px !important; font-size:.82em !important; }}

/* ── Labels ──────────────────────────────────────────────── */
.stTextInput label, .stSelectbox label, .stNumberInput label,
.stPasswordInput label, .stTextArea label, .stFileUploader label {{
    color: var(--text-dim) !important; font-size:.8rem !important;
    font-weight:600 !important; letter-spacing:.15px !important; }}

/* ── Inputs / textarea ───────────────────────────────────── */
[data-baseweb="input"] {{
    background: var(--surface-2) !important;
    border-color: var(--border-strong) !important; border-radius:9px !important; }}
[data-baseweb="input"]:focus-within {{
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 2px rgba(91,141,239,.18) !important; }}
[data-baseweb="input"] input {{ color: var(--text) !important; background:transparent !important; }}
[data-baseweb="input"] input::placeholder {{ color: var(--text-faint) !important; }}
[data-baseweb="textarea"] {{
    background: var(--surface-2) !important; border-color: var(--border-strong) !important;
    border-radius:9px !important; }}
[data-baseweb="textarea"] textarea {{ color: var(--text) !important; background:transparent !important; }}

/* ── Selectbox ───────────────────────────────────────────── */
[data-baseweb="select"] > div:first-child {{
    background: var(--surface-2) !important; border-color: var(--border-strong) !important;
    border-radius:9px !important; }}
[data-baseweb="select"] [data-value], [data-baseweb="select"] span {{
    color: var(--text) !important; }}
[data-baseweb="popover"] {{ background: var(--surface) !important;
    border: 1px solid var(--border) !important; box-shadow: var(--shadow) !important;
    border-radius:10px !important; }}
[data-baseweb="menu"] {{ background: var(--surface) !important; border-radius:10px !important; }}
[data-baseweb="option"] {{ background: var(--surface) !important; color: var(--text) !important; }}
[data-baseweb="option"]:hover {{ background: var(--brand-soft) !important; color: var(--brand) !important; }}

/* ── File uploader ───────────────────────────────────────── */
[data-testid="stFileUploader"] {{ border-radius:12px !important; }}
[data-testid="stFileUploadDropzone"] {{
    background: var(--surface-2) !important;
    border: 2px dashed var(--border-strong) !important;
    border-radius:12px !important; }}
[data-testid="stFileUploadDropzone"]:hover {{
    border-color: var(--brand) !important;
    background: var(--brand-soft) !important; }}
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] small,
[data-testid="stFileUploadDropzone"] span {{ color: var(--text-dim) !important; }}
[data-testid="stFileUploadDropzone"] button {{
    background: var(--surface) !important; color: var(--brand) !important;
    border: 1px solid var(--border-strong) !important; border-radius:8px !important; }}

/* ── Form container ──────────────────────────────────────── */
[data-testid="stForm"] {{
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important; border-radius:14px !important;
    padding: 1.2rem 1.4rem 1rem !important; }}

/* ── Expander ────────────────────────────────────────────── */
[data-testid="stExpander"] {{ border:1px solid var(--border) !important;
    border-radius:12px !important; background: var(--surface) !important; overflow:hidden !important; }}
[data-testid="stExpander"] summary {{
    color: var(--text) !important; font-weight:600 !important; font-size:.88rem !important; }}
[data-testid="stExpander"] summary:hover {{ background: var(--brand-soft) !important; }}

/* ── DataFame ────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{ border:1px solid var(--border) !important; border-radius:12px !important;
    overflow:hidden !important; box-shadow: var(--shadow) !important; }}

/* ── Uploaded file badge ─────────────────────────────────── */
[data-testid="stFileUploaderFile"] {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius:8px !important; }}
[data-testid="stFileUploaderFile"] span {{ color: var(--text) !important; }}

/* ── Divider ─────────────────────────────────────────────── */
hr {{ border-color: var(--border) !important; margin:1.2rem 0 !important; }}

/* ── Chart card ──────────────────────────────────────────── */
[data-testid="stVegaLiteChart"], .stVegaLiteChart {{
    background: var(--surface); border:1px solid var(--border); border-radius:14px;
    padding:.65rem .4rem .2rem; box-shadow: var(--shadow); }}
</style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# COMPONENTS
# ════════════════════════════════════════════════════════════

def section(title: str, sub: str = "") -> None:
    sub_html = f'<span class="sec-sub">{sub}</span>' if sub else ""
    st.markdown(f'<div class="sec-head"><span class="sec-title">{title}</span>{sub_html}</div>',
                unsafe_allow_html=True)


def kpi_cards(cards: list[dict]) -> None:
    """
    cards: list of dict(label, value, icon='', delta='', tone='neutral'|'pos'|'neg', foot='')
    """
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
    p = palette()
    return {
        "brand": p["brand"], "accent": p["accent"],
        "pos": p["pos"], "neg": p["neg"], "warn": p["warn"],
        "grid": p["grid"], "axis": p["text_dim"], "text": p["text"],
    }


def style_chart(ch):
    """Áp theme thống nhất cho mọi biểu đồ Altair."""
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
