"""
market_hours.py
-----------------
Approximate local trading-session status per index, used for the
"market pulse" strip in the Streamlit app. Deliberately simple:
regular weekday open/close window per exchange, no public-holiday
calendar. Good enough for an at-a-glance signal, not for trading.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

# ticker -> (exchange label, IANA tz, open time, close time)
EXCHANGE_INFO: dict[str, tuple[str, str, time, time]] = {
    "^GSPC":     ("NYSE",     "America/New_York",   time(9, 30),  time(16, 0)),
    "^NDX":      ("NASDAQ",   "America/New_York",   time(9, 30),  time(16, 0)),
    "^DJI":      ("NYSE",     "America/New_York",   time(9, 30),  time(16, 0)),
    "^GSPTSE":   ("TSX",      "America/Toronto",    time(9, 30),  time(16, 0)),
    "^BVSP":     ("B3",       "America/Sao_Paulo",  time(10, 0),  time(17, 0)),
    "^FTSE":     ("LSE",      "Europe/London",      time(8, 0),   time(16, 30)),
    "^GDAXI":    ("Xetra",    "Europe/Berlin",      time(9, 0),   time(17, 30)),
    "^FCHI":     ("Euronext", "Europe/Paris",       time(9, 0),   time(17, 30)),
    "^STOXX50E": ("Euronext", "Europe/Paris",       time(9, 0),   time(17, 30)),
    "^N225":     ("TSE",      "Asia/Tokyo",         time(9, 0),   time(15, 0)),
    "^HSI":      ("HKEX",     "Asia/Hong_Kong",     time(9, 30),  time(16, 0)),
    "000001.SS": ("SSE",      "Asia/Shanghai",      time(9, 30),  time(15, 0)),
    "^NSEI":     ("NSE",      "Asia/Kolkata",       time(9, 15),  time(15, 30)),
    "^AXJO":     ("ASX",      "Australia/Sydney",   time(10, 0),  time(16, 0)),
    "^KS11":     ("KRX",      "Asia/Seoul",         time(9, 0),   time(15, 30)),
}


@dataclass
class MarketStatus:
    ticker: str
    exchange: str
    local_time: str
    is_open: bool
    label: str  # "Open" or "Closed"


def get_market_status(ticker: str) -> MarketStatus | None:
    info = EXCHANGE_INFO.get(ticker)
    if info is None:
        return None
    exchange, tz_name, open_t, close_t = info
    now = datetime.now(ZoneInfo(tz_name))
    is_weekday = now.weekday() < 5  # Mon-Fri
    is_open = is_weekday and open_t <= now.time() <= close_t
    return MarketStatus(
        ticker=ticker,
        exchange=exchange,
        local_time=now.strftime("%H:%M"),
        is_open=is_open,
        label="Open" if is_open else "Closed",
    )
