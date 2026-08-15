"""Stablecoin depeg — the dollar-shadow peg under stress (tier 2).

Guarded equilibrium: a fiat stablecoin issuer promises to redeem at par ($1) and
defends the peg with reserves + primary-market redemption + secondary-market
arbitrage. The leaking hand: a depeg leaks reserve stress, a redemption-queue
panic, or lost confidence in the backing. USDC printed a $0.9685 daily CLOSE on
2023-03-11 (a $0.805 intraday low) when ~$3.3bn of Circle's reserves were trapped
in the failing Silicon Valley Bank; USDT sagged in the May-2022 UST/Luna contagion
as Tether cleared >$10bn of redemptions. A real defended equilibrium with a
visible, reachable leak.

Reading: the day's DEVIATION FROM $1, in basis points, for the most-broken of the
two largest fiat stablecoins (USDC, USDT), taken from each pair's settled daily
CLOSE. UP (a wider deviation) is the alarming move. The close, not the intraday
low, is scored ON PURPOSE: a systemic depeg persists into the close (USDC held
below peg for ~3 days over the SVB weekend), while a flash-wick that recovers by
day's end is exactly the intraday-transient event a daily instrument should NOT
count — the cadence objection that kept this line rejected until the SVB
counter-example (a sustained, multi-day depeg) showed the objection was overstated.

Source: Bitstamp public OHLC (keyless), one settled daily candle per pair. A single
venue, but the measure is venue-robust: in calm every venue reads ~$1, and in a
real depeg the venue that shows it IS the signal. Both legs are read in one pass;
if either is missing the reading is EMPTY rather than half-computed. The line is
scored with a one-day settle lag (obs_date = the completed candle's date), so a
re-read of the same day is a stale republish, not a second observation.
"""
import datetime

import requests

LINE = "stablecoin_peg"
LABEL = "Stablecoin depeg — worst of USDC/USDT (bp from $1)"
UNIT = "bp"
ANOMALY_DIRECTION = "up"
TIER = 2
QUANTUM = 1  # 1 bp: below the peg's own resolution is noise, and it floors the
             # robust scale so a calm run of near-perfect pegs cannot zero it

PAIRS = {"USDC": "usdcusd", "USDT": "usdtusd"}
_OHLC = "https://www.bitstamp.net/api/v2/ohlc/{pair}/"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def candles(pair, limit, start=None, end=None):
    """Daily OHLC for a Bitstamp pair, oldest-first: ``[(date, close, low)]``.

    Shared with the seeder so the live line and its history are the same measure
    off the same endpoint. ``step`` is one day; values arrive as strings.
    """
    params = {"step": 86400, "limit": limit}
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end
    r = requests.get(_OHLC.format(pair=pair), params=params, headers=_HEADERS, timeout=20)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}")
    out = []
    for c in r.json()["data"]["ohlc"]:
        day = datetime.datetime.utcfromtimestamp(int(c["timestamp"])).date().isoformat()
        out.append((day, float(c["close"]), float(c["low"])))
    out.sort()
    return out


def dev_bp(close):
    """Deviation of a settled close from the $1 peg, in basis points (>= 0)."""
    return abs(close - 1.0) * 1e4


def _latest_settled(pair, today):
    """The most recent daily candle whose day is already complete (date < today)."""
    for day, close, low in reversed(candles(pair, limit=4)):
        if day < today:
            return day, close, low
    return None


def fetch_daily():
    today = datetime.date.today().isoformat()
    legs = {}
    try:
        for name, pair in PAIRS.items():
            latest = _latest_settled(pair, today)
            if latest is None:
                return {"raw_value": None,
                        "source_note": f"Bitstamp {pair}: no settled candle before {today}"}
            legs[name] = latest
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        return {"raw_value": None, "source_note": f"Bitstamp unavailable: {type(e).__name__}"}

    devs = {name: dev_bp(close) for name, (_, close, _) in legs.items()}
    worst = max(devs, key=devs.__getitem__)
    obs = max(day for day, _, _ in legs.values())
    parts = ", ".join(f"{n} {legs[n][1]:.4f} ({devs[n]:.1f}bp)" for n in PAIRS)
    return {
        "raw_value": round(devs[worst], 1),
        "source_note": f"Bitstamp settled close: {parts} -> worst {worst} {devs[worst]:.1f}bp from $1",
        "obs_date": obs,
        "components": {n: round(devs[n], 1) for n in PAIRS},
    }
