"""Statnett — infrastructure tension line (grid frequency).

Guarded equilibrium: grid operators defend 50 Hz second by second — one of the
most fiercely guarded balances humans maintain. The leaking hand: any deviation
means supply/demand was overwhelmed — a blackout precursor, a fuel shortage, a
system under shock.

Reading: the maximum absolute deviation from 50 Hz in the latest ~60-second
window, in millihertz. A larger deviation is the alarming direction. (Max
deviation captures "stress" far better than an average, which washes the spikes
out.)

Source: Statnett (Norway TSO) real-time frequency REST API. Statnett sits on the
Nordic synchronous grid — the same 50 Hz balance Finland's Fingrid measures — but
its endpoint is fully public: no key, no login, no registration. That keeps this
line running out of the box. (Fingrid dataset 177 is an equivalent alternative
if a key is ever preferred.)
"""
import requests

LINE = "grid_frequency"
LABEL = "Grid freq. max |dev| from 50Hz (mHz)"
UNIT = "mHz"
ANOMALY_DIRECTION = "up"  # a larger deviation is the alarming move

_URL = "https://driftsdata.statnett.no/restapi/Frequency/BySecond"


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    try:
        r = requests.get(_URL, timeout=15, headers={"Accept": "application/json"})
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"Statnett request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"Statnett HTTP {r.status_code}"}
    try:
        measurements = r.json().get("Measurements") or []
    except ValueError:
        return {"raw_value": None, "source_note": "Statnett returned a non-JSON body"}

    deviations = []
    for value in measurements:
        try:
            deviations.append(abs(float(value) - 50.0) * 1000.0)  # Hz -> mHz
        except (TypeError, ValueError):
            continue
    if not deviations:
        return {"raw_value": None, "source_note": "Statnett frequency window was empty"}
    return {
        "raw_value": round(max(deviations), 2),
        "source_note": f"Statnett Nordic grid max |dev|, ~60s snapshot, {len(deviations)} points",
    }
