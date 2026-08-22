"""
correlation_utils.py
---------------------
Shared, testable logic for the global market correlation analysis.
No API keys required anywhere in this module — yfinance pulls public
data straight from Yahoo Finance.

Both `market_correlation_script.py` (plain CLI script) and
`app.py` (Streamlit app) import from here, so there is exactly one
copy of the analysis logic to maintain.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# ── Universe of global indices ───────────────────────────────────────
# ticker -> human readable name. The Streamlit app lets the user pick
# any subset of these (2 or more) instead of always using all 15.
INDICES: dict[str, str] = {
    "^GSPC":     "S&P 500 (US)",
    "^NDX":      "Nasdaq 100 (US)",
    "^DJI":      "Dow Jones (US)",
    "^GSPTSE":   "TSX Composite (Canada)",
    "^BVSP":     "Bovespa (Brazil)",
    "^FTSE":     "FTSE 100 (UK)",
    "^GDAXI":    "DAX (Germany)",
    "^FCHI":     "CAC 40 (France)",
    "^STOXX50E": "Euro Stoxx 50 (EU)",
    "^N225":     "Nikkei 225 (Japan)",
    "^HSI":      "Hang Seng (Hong Kong)",
    "000001.SS": "Shanghai Composite (China)",
    "^NSEI":     "Nifty 50 (India)",
    "^AXJO":     "ASX 200 (Australia)",
    "^KS11":     "KOSPI (South Korea)",
}

PERIOD_CHOICES = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]


class NoDataError(RuntimeError):
    """Raised when yfinance returns nothing usable for the requested tickers."""


# ── 1. Download + clean close prices ─────────────────────────────────
def fetch_close_prices(
    tickers: list[str],
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Download daily Close prices for `tickers` and return a clean,
    aligned DataFrame (columns = tickers, no gaps).

    Raises NoDataError if nothing came back for any ticker.
    """
    if len(tickers) < 2:
        raise ValueError("Need at least 2 tickers to build a correlation matrix.")

    raw = yf.download(
        tickers,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )

    if raw is None or raw.empty:
        raise NoDataError(
            "Yahoo Finance returned no data at all for this request. "
            "Check your internet connection or try a different period."
        )

    # yf.download returns a MultiIndex column frame when multiple tickers
    # are requested. Safely extract the 'Close' level regardless of layout.
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"]
        else:
            close = raw.xs("Close", axis=1, level=-1)
    else:
        # Single-ticker fallback: columns are just ['Open','High',...]
        close = raw[["Close"]]
        close.columns = tickers[:1]

    # Keep only tickers that actually returned a column at all
    close = close.reindex(columns=[t for t in tickers if t in close.columns])

    # Clean missing values (cross-border holiday gaps)
    close = close.ffill().bfill()
    close = close.dropna(axis=1, how="all")  # drop any ticker still fully empty

    # NOTE: "missing" must be computed AFTER the all-NaN drop above, not
    # before it. A ticker can come back from yfinance as a real column that
    # is nonetheless entirely NaN (a common real-world Yahoo Finance hiccup,
    # not just an absent ticker) — checking column presence alone would miss
    # that case and silently include a dead column downstream.
    missing = sorted(set(tickers) - set(close.columns))

    if close.shape[1] < 2:
        raise NoDataError(
            "Fewer than 2 selected markets returned usable data — "
            "pick a different combination or period."
        )

    close.attrs["missing"] = missing
    return close


# ── 2. Log returns ────────────────────────────────────────────────────
def compute_log_returns(close: pd.DataFrame, name_map: dict[str, str] | None = None) -> pd.DataFrame:
    log_returns = np.log(close / close.shift(1)).dropna(how="all")
    if name_map:
        log_returns = log_returns.rename(columns=name_map)
    return log_returns


# ── 3. Correlation matrix ─────────────────────────────────────────────
def compute_correlation(log_returns: pd.DataFrame) -> pd.DataFrame:
    corr = log_returns.corr(method="pearson").round(2)
    corr.index.name = None
    corr.columns.name = None
    return corr


# ── 4. Pairwise table (sorted, unique pairs only) ─────────────────────
def pairwise_correlations(corr: pd.DataFrame) -> pd.DataFrame:
    mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    # NOTE: pandas >= 2.1 changed .stack()'s default behaviour so it no
    # longer auto-drops NaN rows (the old dropna=True default is gone).
    # The upper-triangle mask above still puts NaN everywhere we don't
    # want a pair, so we must drop those explicitly or every pair gets
    # duplicated (both A-B and B-A, plus the NaN diagonal).
    pairs = corr.where(mask).stack().dropna().reset_index()
    pairs.columns = ["Index A", "Index B", "Correlation"]
    return pairs.sort_values("Correlation", ascending=False).reset_index(drop=True)


# ── 5. Heatmap (matplotlib/seaborn figure, for st.pyplot or savefig) ──
# `theme=None` keeps the script's original light coolwarm look untouched.
# The Streamlit app passes a dict to match its dark palette instead.
def build_heatmap_figure(corr: pd.DataFrame, title: str = "Correlation Matrix", theme: dict | None = None):
    import matplotlib.pyplot as plt
    import seaborn as sns

    n = corr.shape[0]
    fig, ax = plt.subplots(figsize=(max(6, n * 0.9), max(5, n * 0.75)))

    cmap = theme["cmap"] if theme else "coolwarm"
    if theme:
        fig.patch.set_facecolor(theme["panel"])
        ax.set_facecolor(theme["panel"])

    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        vmin=-0.2,
        vmax=1.0,
        square=True,
        linewidths=0.5,
        linecolor=theme["panel"] if theme else "white",
        cbar_kws={"label": "Pearson correlation", "shrink": 0.8},
        annot_kws={"fontsize": 8, "color": theme["text"] if theme else "black"},
        ax=ax,
    )
    # NOTE: deliberately NOT passing a custom fontfamily here. "Space Grotesk"
    # etc. are web fonts the browser downloads for the Streamlit chrome around
    # this figure — matplotlib can't fetch them the same way, and asking for a
    # font it doesn't have installed just prints a "findfont" warning per draw
    # and falls back anyway. Matplotlib's default keeps this figure clean.
    text_color = theme["text"] if theme else "black"
    muted_color = theme["muted"] if theme else "black"
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14, color=text_color)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9, color=muted_color)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=9, color=muted_color)
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color(muted_color)
    cbar.ax.tick_params(colors=muted_color)
    if theme:
        cbar.outline.set_edgecolor(theme["panel"])
    fig.tight_layout()
    return fig


# ── 6. Sankey diagram ──────────────────────────────────────────────────
# Default palette matches the original script (red/orange/blue on white).
_DEFAULT_LINK_COLORS = {"strong": "rgba(178,24,43,0.75)", "moderate": "rgba(239,138,98,0.75)",
                         "weak": "rgba(103,169,207,0.75)", "negative": "rgba(120,120,120,0.55)"}


def _link_color(v: float, palette: dict[str, str]) -> str:
    if v >= 0.7:
        return palette["strong"]
    elif v >= 0.4:
        return palette["moderate"]
    elif v >= 0:
        return palette["weak"]
    else:
        return palette["negative"]


def build_sankey_figure(
    pairs: pd.DataFrame,
    title: str = "Correlation Flow",
    top_n: int | None = None,
    theme: dict | None = None,
):
    """
    Build a Sankey diagram from a pairs table (Index A, Index B, Correlation).
    If top_n is given, only the strongest `top_n` pairs are shown; otherwise
    ALL pairs in the table are shown (used when the user hand-picks a small
    set of markets and wants every pairwise relationship visualised).

    `theme=None` keeps the script's original light look (steelblue nodes on
    white). The Streamlit app passes a dict to match its dark palette.
    """
    data = pairs.copy()
    if top_n is not None:
        data = data.head(top_n)

    nodes = list(pd.unique(data[["Index A", "Index B"]].values.ravel()))
    node_idx = {name: i for i, name in enumerate(nodes)}

    # Sankey link widths must be > 0; negative/zero correlations get a thin
    # nominal width so they still render as a (visually weak) flow.
    values = data["Correlation"].apply(lambda v: max(v, 0.02))

    link_palette = theme["link_colors"] if theme else _DEFAULT_LINK_COLORS
    node_color = theme["node_color"] if theme else "steelblue"
    node_line_color = theme["node_line"] if theme else "black"

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=18,
            line=dict(color=node_line_color, width=0.5),
            label=nodes,
            color=node_color,
        ),
        link=dict(
            source=[node_idx[a] for a in data["Index A"]],
            target=[node_idx[b] for b in data["Index B"]],
            value=values,
            color=[_link_color(v, link_palette) for v in data["Correlation"]],
            label=[f"r={v:.2f}" for v in data["Correlation"]],
        ),
    )])

    layout_kwargs = dict(title_text=title, font_size=11, height=550)
    if theme:
        layout_kwargs.update(
            paper_bgcolor=theme["panel"],
            plot_bgcolor=theme["panel"],
            font_color=theme["text"],
            font_family=theme.get("font"),
            title_font_color=theme["text"],
        )
    fig.update_layout(**layout_kwargs)
    return fig


# ── 7. One-shot convenience wrapper used by both the script and the app ─
def run_full_analysis(tickers: list[str], period: str = "1y", interval: str = "1d"):
    """
    Runs the whole pipeline and returns everything the UI/script needs:
    (close_prices, log_returns, corr_matrix, pairs_table, missing_tickers)
    """
    name_map = {t: INDICES.get(t, t) for t in tickers}
    close = fetch_close_prices(tickers, period=period, interval=interval)
    missing = close.attrs.get("missing", [])
    log_returns = compute_log_returns(close, name_map=name_map)
    corr = compute_correlation(log_returns)
    pairs = pairwise_correlations(corr)
    return close, log_returns, corr, pairs, missing
