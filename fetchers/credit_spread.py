"""FRED — financial-system trust line (the cleanest one).

Guarded equilibrium: banks want to lend to each other to earn, and central
banks press credit spreads down. The leaking hand: when banks suddenly will not
lend to each other, systemic fear has overpowered greed — the 2008 fuse.

Reading: ICE BofA US High Yield OAS (BAMLH0A0HYM2), in percentage points — one
number that compresses the whole high-yield market's fear. A SPIKE up is the
alarming direction.

Source: FRED API. Needs a free api key in env FRED_API_KEY. The classic TED
spread (TEDRATE) was discontinued with LIBOR's retirement; this is the modern
replacement. FRED now serves only a rolling ~3-year window, which is plenty for
a forward probe.
"""
import os

import requests

LINE = "credit_spread"
LABEL = "US HY credit spread OAS (pp)"
UNIT = "pp"
ANOMALY_DIRECTION = "up"  # a spike in the spread is the alarming move

_SERIES = "BAMLH0A0HYM2"
_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str, "obs_date": str}."""
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return {"raw_value": None, "source_note": "missing FRED_API_KEY"}
    try:
        r = requests.get(
            _URL,
            timeout=15,
            params={
                "series_id": _SERIES,
                "api_key": key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 5,
            },
        )
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"FRED request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"FRED HTTP {r.status_code}"}
    try:
        observations = r.json().get("observations") or []
    except ValueError:
        return {"raw_value": None, "source_note": "FRED returned a non-JSON body"}
    # Observations are newest-first; "." marks a missing value (non-trading day).
    for obs in observations:
        value = obs.get("value")
        if value not in (None, "", "."):
            try:
                return {
                    "raw_value": float(value),
                    "source_note": f"FRED {_SERIES} OAS {obs.get('date')}",
                    "obs_date": obs.get("date"),
                }
            except ValueError:
                continue
    return {"raw_value": None, "source_note": "FRED returned no usable recent value"}
