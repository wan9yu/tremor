"""FRED — financial-system trust line (the cleanest one).

Guarded equilibrium: banks want to lend to each other to earn, and central
banks press credit spreads down. The leaking hand: when banks suddenly will not
lend to each other, systemic fear has overpowered greed — the 2008 fuse.

Reading: ICE BofA US High Yield OAS (BAMLH0A0HYM2), in percentage points — one
number that compresses the whole high-yield market's fear. A SPIKE up is the
alarming direction.

Source: FRED API, with a KEYLESS fallback. The keyed JSON API is primary; if the
key is absent or the call fails, the public fredgraph.csv endpoint serves the
same series without any key. That fallback covers the failure this line is most
exposed to — a rotated or expired key silently blinding a tier-1 instrument. It
is a LIVENESS fallback only: fredgraph ignores a start-date parameter and serves
a short rolling window, so it cannot be used to rebuild history.

The classic TED spread (TEDRATE) was discontinued with LIBOR's retirement; this
is the modern replacement. FRED serves only a rolling ~3-year window, which is
plenty for a forward probe.
"""
import os

import requests

from core import fred

LINE = "credit_spread"
LABEL = "US HY credit spread OAS (pp)"
UNIT = "pp"
ANOMALY_DIRECTION = "up"  # a spike in the spread is the alarming move

_SERIES = "BAMLH0A0HYM2"
_URL = "https://api.stlouisfed.org/fred/series/observations"


def _keyless(reason):
    """Public fredgraph.csv path — no key. Used when the keyed API cannot answer."""
    result = fred.reading(_SERIES)
    if result["raw_value"] is None:
        return {"raw_value": None,
                "source_note": f"{reason}; keyless fallback also failed"}
    result["source_note"] += f" [keyless fallback: {reason}]"
    return result


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str, "obs_date": str}."""
    key = os.environ.get("FRED_API_KEY")
    if not key:
        return _keyless("missing FRED_API_KEY")
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
        return _keyless(f"FRED request failed: {type(e).__name__}")
    if r.status_code != 200:
        return _keyless(f"FRED HTTP {r.status_code}")
    try:
        observations = r.json().get("observations") or []
    except ValueError:
        return _keyless("FRED returned a non-JSON body")
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
    return _keyless("FRED returned no usable recent value")
