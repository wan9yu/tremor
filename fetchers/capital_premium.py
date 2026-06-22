"""Korea "kimchi premium" — capital-control tension line.

Guarded equilibrium: arbitrage should erase the price gap for the same asset
across borders. The leaking hand: a persistent local premium means capital is
trapped inside the country — capital flight, tightening controls, a devaluation
on the way. Korea's premium is the canonical example.

Reading: (local BTC price in USD-equivalent) / (global BTC price in USD) - 1,
as a percentage. A widening POSITIVE premium is the alarming direction.

Sources (all keyless / free):
  - Korean BTC price: Upbit KRW-BTC (fallback: Bithumb).
  - Global BTC price: Coinbase BTC-USD spot.
  - USD/KRW reference rate: open.er-api.com.
"""
import requests

LINE = "capital_premium"
LABEL = "Korea BTC premium (%)"
UNIT = "%"
ANOMALY_DIRECTION = "up"  # a widening premium is the alarming move


def _korea_btc_krw():
    """Korean BTC price in KRW, as (price, venue) or (None, None)."""
    try:
        r = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": "KRW-BTC"},
            timeout=10,
        )
        if r.status_code == 200:
            return float(r.json()[0]["trade_price"]), "Upbit"
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    try:
        r = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW", timeout=10)
        if r.status_code == 200:
            return float(r.json()["data"]["closing_price"]), "Bithumb"
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None, None


def _global_btc_usd():
    try:
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=10)
        if r.status_code == 200:
            return float(r.json()["data"]["amount"])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def _krw_per_usd():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        if r.status_code == 200:
            return float(r.json()["rates"]["KRW"])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    krw_price, venue = _korea_btc_krw()
    usd_price = _global_btc_usd()
    krw_per_usd = _krw_per_usd()

    # Treat non-positive values as missing too: a zeroed/degenerate API response
    # would otherwise divide-by-zero below and crash the run.
    missing = []
    if krw_price is None or krw_price <= 0:
        missing.append("Korea BTC price")
    if usd_price is None or usd_price <= 0:
        missing.append("global BTC price")
    if krw_per_usd is None or krw_per_usd <= 0:
        missing.append("USD/KRW rate")
    if missing:
        return {
            "raw_value": None,
            "source_note": "kimchi premium unavailable, missing: " + ", ".join(missing),
        }

    implied_usd = krw_price / krw_per_usd
    premium_pct = (implied_usd / usd_price - 1.0) * 100.0
    return {
        "raw_value": round(premium_pct, 4),
        "source_note": f"{venue} KRW-BTC vs Coinbase USD @ {krw_per_usd:.2f} KRW/USD",
    }
