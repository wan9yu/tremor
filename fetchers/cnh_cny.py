"""Offshore vs onshore yuan (CNH − CNY) — China capital-control tension line.

Guarded equilibrium: the PBOC manages the onshore yuan (CNY) inside a tight daily
band, burning FX reserves to defend it. The freely-traded offshore yuan (CNH) has
no such guard. The leaking hand: when CNH trades persistently weaker than CNY, the
market is pricing depreciation the onshore peg won't yet admit — capital-flight
pressure, tightening controls, a managed devaluation building.

Reading: the CNH − CNY spread in pips (1 pip = 0.0001 yuan per USD). A widening
POSITIVE spread (offshore yuan weaker) is the alarming direction.

Source: Yahoo Finance daily quotes for USDCNH=X (offshore) and USDCNY=X (onshore).
Free and keyless. Both legs must be present, or the day is written empty.
"""
import requests

LINE = "cnh_cny"
LABEL = "Offshore−onshore yuan spread (pips)"
UNIT = "pips"
ANOMALY_DIRECTION = "up"  # offshore yuan weakening past onshore is the alarming move
TIER = 1  # primary indicator

_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (tremor; +https://github.com/wan9yu/tremor)"}


def _yahoo_price(symbol):
    """Latest price for a Yahoo Finance symbol, or None."""
    try:
        r = requests.get(
            _CHART.format(sym=symbol),
            headers=_HEADERS,
            timeout=12,
            params={"interval": "1d", "range": "5d"},
        )
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    try:
        meta = r.json()["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        return float(price) if price is not None else None
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    cnh = _yahoo_price("USDCNH=X")
    cny = _yahoo_price("USDCNY=X")
    missing = []
    if cnh is None or cnh <= 0:
        missing.append("USDCNH")
    if cny is None or cny <= 0:
        missing.append("USDCNY")
    if missing:
        return {
            "raw_value": None,
            "source_note": "yuan spread unavailable, missing: " + ", ".join(missing),
        }
    pips = (cnh - cny) * 10000.0
    return {
        "raw_value": round(pips, 1),
        "source_note": f"Yahoo USDCNH {cnh:.4f} − USDCNY {cny:.4f} (pips)",
    }
