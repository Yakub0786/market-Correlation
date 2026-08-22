"""
market_correlation_script.py
-----------------------------
Standalone command-line version of the global index correlation analysis.
No API key needed — yfinance reads public Yahoo Finance data directly.

Run:
    python market_correlation_script.py

Produces:
    global_market_correlation.png   (heatmap)
    correlation_sankey.html         (interactive sankey, top 20 pairs)
"""

import correlation_utils as cu

TICKERS = list(cu.INDICES.keys())
TOP_N = 20  # how many strongest pairs to show in the Sankey diagram


def main():
    print(f"Downloading data for {len(TICKERS)} indices...")
    close, log_returns, corr, pairs_sorted, missing = cu.run_full_analysis(
        TICKERS, period="1y", interval="1d"
    )
    if missing:
        print(f"Warning: no data returned for {missing}")

    # ── Heatmap ──────────────────────────────────────────────────────
    fig = cu.build_heatmap_figure(
        corr, title="Global Stock Market Correlation Matrix\n(Daily Log Returns, Trailing 1 Year)"
    )
    fig.savefig("global_market_correlation.png", dpi=200, bbox_inches="tight")
    print("Heatmap saved to global_market_correlation.png")

    # ── Strongest / weakest pairs ────────────────────────────────────
    print("\n=== Top 10 Strongest Correlated Pairs ===")
    print(pairs_sorted.head(10).to_string(index=False))

    print("\n=== Top 10 Weakest / Most Negatively Correlated Pairs ===")
    print(pairs_sorted.tail(10).sort_values("Correlation").to_string(index=False))

    print(f"\nFull pair table shape: {pairs_sorted.shape[0]} pairs across {corr.shape[0]} indices")

    # ── Sankey diagram of strongest correlations ─────────────────────
    sankey_fig = cu.build_sankey_figure(
        pairs_sorted, title=f"Top {TOP_N} Strongest Index Correlations (Sankey Flow)", top_n=TOP_N
    )
    sankey_fig.write_html("correlation_sankey.html")
    print("\nSankey diagram saved to correlation_sankey.html")


if __name__ == "__main__":
    main()
