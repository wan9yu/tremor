"""Fingrid — infrastructure tension line (grid frequency).

Guarded equilibrium: grid operators defend 50 Hz second by second — one of the
most fiercely guarded balances humans maintain. The leaking hand: any deviation
means supply/demand was overwhelmed — a blackout precursor, a fuel shortage, a
system under shock.

Reading: the day's maximum absolute deviation from 50 Hz, in millihertz. A
larger deviation is the alarming direction. (Max deviation captures "stress"
far better than a daily average, which washes the spikes out.)

Source: Fingrid Open Data (Finland, Nordic synchronous grid), dataset 177
(real-time frequency). Needs a free api key in env FINGRID_API_KEY (sent as the
x-api-key header).
"""
import os
from datetime import datetime, timedelta, timezone

import requests

LINE = "grid_frequency"
LABEL = "Grid freq. max |dev| from 50Hz (mHz)"
UNIT = "mHz"
ANOMALY_DIRECTION = "up"  # a larger deviation is the alarming move

_DATASET = 177
_URL = f"https://data.fingrid.fi/api/datasets/{_DATASET}/data"


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    key = os.environ.get("FINGRID_API_KEY")
    if not key:
        return {"raw_value": None, "source_note": "missing FINGRID_API_KEY"}
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        r = requests.get(
            _URL,
            timeout=20,
            headers={"x-api-key": key, "Accept": "application/json"},
            params={
                "startTime": start.strftime(fmt),
                "endTime": end.strftime(fmt),
                "pageSize": 20000,
            },
        )
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"Fingrid request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"Fingrid HTTP {r.status_code}"}
    try:
        body = r.json()
    except ValueError:
        return {"raw_value": None, "source_note": "Fingrid returned a non-JSON body"}

    rows = body.get("data", []) if isinstance(body, dict) else body
    deviations = []
    for row in rows or []:
        value = row.get("value") if isinstance(row, dict) else None
        if value is None:
            continue
        try:
            deviations.append(abs(float(value) - 50.0) * 1000.0)  # Hz -> mHz
        except (TypeError, ValueError):
            continue
    if not deviations:
        return {"raw_value": None, "source_note": "Fingrid dataset 177 returned no points"}
    return {
        "raw_value": round(max(deviations), 2),
        "source_note": f"Fingrid dataset 177 max |dev| over {len(deviations)} points",
    }
