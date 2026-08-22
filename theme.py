"""
theme.py
---------
Visual identity for the Global Market Correlation Explorer.

Palette — "trading floor at dawn": deep ink background, signal teal for
rising/positive correlation, ember rose for falling/negative, amber for
headline numbers. Chosen to echo real market up/down conventions without
reaching for literal red/green, and to read as one coherent system across
Streamlit's native widgets, the matplotlib heatmap, and the Plotly Sankey.

Type — Space Grotesk for headlines (geometric, a little unusual, still
legible), Inter for body copy, IBM Plex Mono for every number and ticker
(so prices, correlations and exchange clocks all read like a data feed).
"""

BG = "#0E1420"
PANEL = "#161D2C"
PANEL_BORDER = "#232B3D"
TEXT = "#EDEFF4"
MUTED = "#8B93A7"
TEAL = "#2DD4BF"     # positive / open / primary actions
ROSE = "#FB7A6B"     # negative / closed / warnings
AMBER = "#F0B429"    # headline numbers, highlights

FONT_DISPLAY = "'Space Grotesk', sans-serif"
FONT_BODY = "'Inter', sans-serif"
FONT_MONO = "'IBM Plex Mono', monospace"

HEATMAP_THEME = {
    "panel": PANEL,
    "text": TEXT,
    "muted": MUTED,
    # matplotlib can't load web fonts like the browser does, so the figure
    # itself uses matplotlib's default font — only colors are themed here.
    "cmap": None,  # filled in by build_dark_cmap() in app.py (needs matplotlib)
}

SANKEY_THEME = {
    "panel": PANEL,
    "text": TEXT,
    "font": "Inter",
    "node_color": "#3A445C",
    "node_line": PANEL_BORDER,
    "link_colors": {
        "strong": f"rgba(45,212,191,0.75)",   # teal
        "moderate": f"rgba(240,180,41,0.6)",  # amber
        "weak": f"rgba(139,147,167,0.45)",    # muted slate
        "negative": f"rgba(251,122,107,0.5)", # rose
    },
}

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: {FONT_BODY};
}}

.stApp {{
    background: {BG};
}}

h1, h2, h3, h4 {{
    font-family: {FONT_DISPLAY} !important;
    color: {TEXT} !important;
    letter-spacing: -0.01em;
}}

p, span, label, .stMarkdown {{
    color: {TEXT};
}}

/* Hero header */
.hero {{
    padding: 0.25rem 0 1.25rem 0;
    border-bottom: 1px solid {PANEL_BORDER};
    margin-bottom: 1.5rem;
}}
.hero-eyebrow {{
    font-family: {FONT_MONO};
    color: {TEAL};
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}}
.hero-title {{
    font-family: {FONT_DISPLAY};
    font-weight: 700;
    font-size: 2.1rem;
    color: {TEXT};
    margin: 0 0 0.4rem 0;
    line-height: 1.15;
}}
.hero-sub {{
    color: {MUTED};
    font-size: 0.98rem;
    max-width: 60ch;
    margin: 0;
}}

/* Market pulse strip (signature element) */
.pulse-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin: 0.9rem 0 1.6rem 0;
}}
.pulse-chip {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: {PANEL};
    border: 1px solid {PANEL_BORDER};
    border-radius: 999px;
    padding: 0.35rem 0.85rem 0.35rem 0.6rem;
}}
.pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}}
.pulse-name {{
    font-size: 0.82rem;
    color: {TEXT};
    font-weight: 500;
}}
.pulse-meta {{
    font-family: {FONT_MONO};
    font-size: 0.76rem;
    color: {MUTED};
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {PANEL};
    border-right: 1px solid {PANEL_BORDER};
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    font-family: {FONT_DISPLAY} !important;
}}

/* Buttons */
.stButton > button {{
    font-family: {FONT_BODY};
    font-weight: 600;
    border-radius: 8px;
}}
.stButton > button[kind="primary"] {{
    background: {TEAL};
    color: {BG};
    border: none;
}}
.stButton > button[kind="primary"]:hover {{
    background: #26b8a4;
    color: {BG};
}}

/* Metrics */
[data-testid="stMetric"] {{
    background: {PANEL};
    border: 1px solid {PANEL_BORDER};
    border-radius: 10px;
    padding: 0.9rem 1rem 0.7rem 1rem;
}}
[data-testid="stMetricValue"] {{
    font-family: {FONT_MONO} !important;
    color: {AMBER} !important;
}}
[data-testid="stMetricLabel"] {{
    color: {MUTED} !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* Tabs */
[data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {PANEL_BORDER};
}}
[data-baseweb="tab"] {{
    font-family: {FONT_BODY};
    font-weight: 500;
    color: {MUTED};
}}
[aria-selected="true"] {{
    color: {TEAL} !important;
}}

/* Dataframes / captions */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {MUTED} !important;
}}

/* Hide the default "Made with Streamlit" footer (cosmetic only) */
footer {{ visibility: hidden; }}
</style>
"""
