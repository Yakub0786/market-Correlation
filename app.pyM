"""
Global Market Correlation Explorer — Streamlit app
-----------------------------------------------------
Pick 2+ global stock indices from the sidebar, click "Run analysis",
and get a correlation heatmap, a Sankey diagram of how strongly the
selected markets move together, and the underlying data tables.

No API keys needed anywhere — yfinance reads free public data
straight from Yahoo Finance.

Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import io

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import streamlit as st

import correlation_utils as cu
import market_hours as mh
import theme as th

st.set_page_config(
    page_title="Global Market Correlation Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(th.CUSTOM_CSS, unsafe_allow_html=True)


def build_dark_cmap():
    # vmin=-0.2, vmax=1.0 -> rose at the low end, slate around zero, teal at the high end
    zero_pos = 0.2 / 1.2
    return LinearSegmentedColormap.from_list(
        "trading_floor",
        [(0.0, th.ROSE), (zero_pos, "#3A445C"), (1.0, th.TEAL)],
    )


HEATMAP_THEME = {**th.HEATMAP_THEME, "cmap": build_dark_cmap()}

# ── Cached data fetch (the expensive, network-bound step) ────────────
@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch(tickers: tuple[str, ...], period: str):
    close = cu.fetch_close_prices(list(tickers), period=period)
    return close, close.attrs.get("missing", [])


def run_analysis(tickers: list[str], period: str):
    close, missing = cached_fetch(tuple(sorted(tickers)), period)
    name_map = {t: cu.INDICES.get(t, t) for t in tickers}
    log_returns = cu.compute_log_returns(close, name_map=name_map)
    corr = cu.compute_correlation(log_returns)
    pairs = cu.pairwise_correlations(corr)
    return {
        "close": close, "log_returns": log_returns, "corr": corr, "pairs": pairs,
        "missing": missing, "tickers": tickers, "period": period,
    }


def render_pulse_strip(tickers: list[str]):
    """Signature element: real open/closed status per selected exchange."""
    chips = []
    for t in tickers:
        status = mh.get_market_status(t)
        if status is None:
            continue
        dot_color = th.TEAL if status.is_open else th.ROSE
        chips.append(
            f'<div class="pulse-chip">'
            f'<span class="pulse-dot" style="background:{dot_color}"></span>'
            f'<span class="pulse-name">{cu.INDICES.get(t, t)}</span>'
            f'<span class="pulse-meta">{status.exchange} · {status.local_time} · {status.label}</span>'
            f'</div>'
        )
    if chips:
        st.markdown(f'<div class="pulse-row">{"".join(chips)}</div>', unsafe_allow_html=True)
        st.caption("Local exchange time and regular session hours — approximate, ignores public holidays.")


# ── Sidebar: market + period selection ────────────────────────────────
st.sidebar.markdown(
    f'<div style="font-family:{th.FONT_DISPLAY};font-weight:700;font-size:1.1rem;'
    f'color:{th.TEXT};margin-bottom:0.2rem;">Build your view</div>',
    unsafe_allow_html=True,
)
st.sidebar.caption("No API key needed — reads free, public Yahoo Finance data.")

DEFAULT_TICKERS = ["^GSPC", "^NDX", "^FTSE", "^N225", "^NSEI"]

selected_tickers = st.sidebar.multiselect(
    "Global indices (pick 2 or more)",
    options=list(cu.INDICES.keys()),
    default=DEFAULT_TICKERS,
    format_func=lambda t: cu.INDICES.get(t, t),
)

period = st.sidebar.selectbox(
    "History window",
    options=cu.PERIOD_CHOICES,
    index=cu.PERIOD_CHOICES.index("1y"),
    help="How much trailing daily price history to pull for each index.",
)

run_clicked = st.sidebar.button("Run analysis", type="primary", width="stretch")

if "results" not in st.session_state:
    st.session_state.results = None

if run_clicked:
    if len(selected_tickers) < 2:
        st.sidebar.error("Select at least 2 markets to compare.")
    else:
        with st.spinner(f"Downloading {len(selected_tickers)} markets and computing correlations..."):
            try:
                st.session_state.results = run_analysis(selected_tickers, period)
            except (cu.NoDataError, ValueError) as e:
                st.sidebar.error(str(e))
            except Exception as e:
                st.sidebar.error(f"Something went wrong fetching data: {e}")

# ── Hero ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">Cross-market correlation</div>
        <h1 class="hero-title">Global Market Correlation Explorer</h1>
        <p class="hero-sub">Daily log-return Pearson correlation between the indices you pick —
        how much they tend to move together, not whether one causes the other.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

results = st.session_state.results

if results is None:
    render_pulse_strip(selected_tickers)
    st.info("Select 2 or more markets in the sidebar, then click **Run analysis**.")
    st.stop()

close, log_returns, corr, pairs, missing, tickers, used_period = (
    results["close"], results["log_returns"], results["corr"], results["pairs"],
    results["missing"], results["tickers"], results["period"],
)
live_tickers = [t for t in tickers if t not in missing]

render_pulse_strip(live_tickers)

if missing:
    st.warning(
        f"No data came back for: {', '.join(cu.INDICES.get(t, t) for t in missing)}. "
        "Showing results for the remaining markets."
    )

# ── Overview strip ────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Markets analysed", corr.shape[0])
c2.metric("Trading days", log_returns.shape[0])
c3.metric("History window", used_period)
st.caption(f"Date range: {close.index.min().date()} → {close.index.max().date()}")

tab_heatmap, tab_sankey, tab_pairs, tab_data = st.tabs(
    ["Heatmap", "Sankey flow", "Pairs table", "Raw data"]
)

# ── Heatmap tab ────────────────────────────────────────────────────────
with tab_heatmap:
    fig = cu.build_heatmap_figure(
        corr, title=f"Correlation matrix · Trailing {used_period}", theme=HEATMAP_THEME
    )
    st.pyplot(fig, width="stretch")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    st.download_button(
        "Download heatmap as PNG", data=buf.getvalue(),
        file_name="market_correlation_heatmap.png", mime="image/png",
    )
    plt.close(fig)

# ── Sankey tab ─────────────────────────────────────────────────────────
with tab_sankey:
    total_pairs = len(pairs)
    if total_pairs > 12:
        top_n = st.slider(
            "Show strongest N pairs", min_value=5, max_value=total_pairs,
            value=min(20, total_pairs),
            help="Flow width shows correlation strength. Limiting to the strongest "
                 "pairs keeps the diagram readable when many markets are selected.",
        )
    else:
        top_n = total_pairs
        st.caption(f"Showing all {total_pairs} pairs between your {len(live_tickers)} selected markets.")

    sankey_fig = cu.build_sankey_figure(
        pairs, title=f"Correlation flow · {len(live_tickers)} selected markets",
        top_n=top_n, theme=th.SANKEY_THEME,
    )
    st.plotly_chart(sankey_fig, width="stretch")
    st.caption(
        "Teal = strong positive correlation (≥0.7) · Amber = moderate (0.4–0.7) · "
        "Slate = weak positive · Rose = zero or negative correlation."
    )

    html_bytes = sankey_fig.to_html(include_plotlyjs="cdn").encode("utf-8")
    st.download_button(
        "Download Sankey as HTML", data=html_bytes,
        file_name="correlation_sankey.html", mime="text/html",
    )

# ── Pairs table tab ─────────────────────────────────────────────────────
with tab_pairs:
    left, right = st.columns(2)
    with left:
        st.subheader("Strongest pairs")
        st.dataframe(pairs.head(10), hide_index=True, width="stretch")
    with right:
        st.subheader("Weakest / most negative pairs")
        st.dataframe(
            pairs.tail(10).sort_values("Correlation"), hide_index=True, width="stretch"
        )
    st.subheader("Full correlation matrix")
    st.dataframe(
        corr.style.background_gradient(cmap=HEATMAP_THEME["cmap"], vmin=-0.2, vmax=1.0).format("{:.2f}"),
        width="stretch",
    )

# ── Raw data tab ─────────────────────────────────────────────────────────
with tab_data:
    st.subheader("Close prices")
    st.dataframe(close, width="stretch")
    st.subheader("Daily log returns")
    st.dataframe(log_returns, width="stretch")
    st.download_button(
        "Download close prices as CSV", data=close.to_csv().encode("utf-8"),
        file_name="close_prices.csv", mime="text/csv",
    )
