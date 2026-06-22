"""Grid frequency — infrastructure tension line.

Guarded equilibrium: grid operators defend 50 Hz second by second — one of the
most fiercely guarded balances humans maintain. The leaking hand: any deviation
means supply/demand was overwhelmed — a blackout precursor, a fuel shortage, a
system under shock.

Reading: the maximum absolute deviation from 50 Hz, in millihertz. A larger
deviation is the alarming direction. (Max deviation captures "stress" far better
than an average, which washes the spikes out.)

Source: Fingrid Open Data (Finland), dataset 177 (real-time frequency), over a
24-hour window — a richer signal than a momentary snapshot. Needs a free key in
env FINGRID_API_KEY (sent as the x-api-key header). If the key is missing or
Fingrid fails, this falls back to Statnett (Norway) — the SAME Nordic 50 Hz
synchronous grid — whose real-time endpoint is keyless, so the line keeps
running. Both measure one physical equilibrium; Fingrid is preferred only for
its wider window.
"""
import os
from datetime import datetime, timedelta, timezone

import requests


def _now_utc():
    return datetime.now(timezone.utc)


LINE = "grid_frequency"
LABEL = "Grid freq. max |dev| from 50Hz (mHz)"
UNIT = "mHz"
ANOMALY_DIRECTION = "up"  # a larger deviation is the alarming move

_FINGRID_URL = "https://data.fingrid.fi/api/datasets/177/data"
_STATNETT_URL = "https://driftsdata.statnett.no/restapi/Frequency/BySecond"


def _max_dev_mhz(values):
    """Max |value - 50 Hz| over an iterable of Hz readings, in mHz; or None."""
    deviations = []
    for value in values:
        try:
            deviations.append(abs(float(value) - 50.0) * 1000.0)  # Hz -> mHz
        except (TypeError, ValueError):
            continue
    return max(deviations) if deviations else None


def _fingrid():
    """Fingrid dataset 177 over 24h -> (raw_value, note) or (None, reason)."""
    key = os.environ.get("FINGRID_API_KEY")
    if not key:
        return None, "missing FINGRID_API_KEY"
    end = _now_utc()
    start = end - timedelta(hours=24)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        r = requests.get(
            _FINGRID_URL,
            timeout=20,
            headers={"x-api-key": key, "Accept": "application/json"},
            params={"startTime": start.strftime(fmt), "endTime": end.strftime(fmt),
                    "pageSize": 20000, "sortBy": "startTime", "sortOrder": "desc"},
        )
    except requests.RequestException as e:
        return None, f"Fingrid request failed: {type(e).__name__}"
    if r.status_code != 200:
        return None, f"Fingrid HTTP {r.status_code}"
    try:
        body = r.json()
    except ValueError:
        return None, "Fingrid returned a non-JSON body"
    rows = body.get("data", []) if isinstance(body, dict) else body
    values = [row.get("value") for row in (rows or []) if isinstance(row, dict)]
    dev = _max_dev_mhz(values)
    if dev is None:
        return None, "Fingrid dataset 177 returned no usable points"
    return round(dev, 2), f"Fingrid dataset 177 max |dev| over {len(values)} points (24h)"


def _statnett():
    """Statnett keyless ~60s snapshot -> (raw_value, note) or (None, reason)."""
    try:
        r = requests.get(_STATNETT_URL, timeout=15, headers={"Accept": "application/json"})
    except requests.RequestException as e:
        return None, f"Statnett request failed: {type(e).__name__}"
    if r.status_code != 200:
        return None, f"Statnett HTTP {r.status_code}"
    try:
        measurements = r.json().get("Measurements") or []
    except ValueError:
        return None, "Statnett returned a non-JSON body"
    dev = _max_dev_mhz(measurements)
    if dev is None:
        return None, "Statnett frequency window was empty"
    return round(dev, 2), f"Statnett Nordic grid max |dev|, ~60s snapshot, {len(measurements)} points"


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}.

    Prefer Fingrid (24h window); fall back to keyless Statnett on any failure.
    """
    value, note = _fingrid()
    if value is not None:
        return {"raw_value": value, "source_note": note}

    fallback_value, fallback_note = _statnett()
    if fallback_value is not None:
        return {
            "raw_value": fallback_value,
            "source_note": f"{fallback_note} [Fingrid unavailable: {note}]",
        }
    return {
        "raw_value": None,
        "source_note": f"grid frequency unavailable (Fingrid: {note}; Statnett: {fallback_note})",
    }
