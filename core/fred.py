"""Keyless FRED access via the public fredgraph.csv endpoint (no API key).

FRED serves any series as CSV at fredgraph.csv?id=<series>, which needs no key —
handy for the lighter watchlist lines. (The primary credit-spread line uses the
keyed JSON API; this is the keyless path for additional FRED-based candidates.)

PACING IS NOT OPTIONAL. fredgraph sits behind bot management: ten requests in
twenty seconds black-holed a probing IP for over an hour, and the block spread
across the FRED estate. The daily run makes five keyless hits back to back
(SOFR, IORB, em_corp_oas, euro_hy_spread, VIXCLS — six if the credit-spread
fallback engages), which without spacing runs at half the measured lockout rate
from a CI address this project cannot afford to burn. Every request through
this module therefore waits out a minimum gap from the previous one.
"""
import time

import requests

_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}

_MIN_GAP_S = 5.0
_last_request = 0.0


def _spaced_get(params):
    """GET fredgraph.csv, at most one request per ``_MIN_GAP_S`` per process."""
    global _last_request
    wait = _MIN_GAP_S - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()
    return requests.get(_URL, params=params, headers=_HEADERS, timeout=15)


def series(series_id):
    """[(date, value)] for a FRED series, oldest-first, or None.

    Rows are "observation_date,VALUE"; "." marks a missing observation.
    """
    try:
        r = _spaced_get({"id": series_id})
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    out = []
    for row in r.text.strip().splitlines()[1:]:
        parts = row.split(",")
        if len(parts) >= 2 and parts[1] not in ("", ".", "NaN"):
            try:
                out.append((parts[0], float(parts[1])))
            except ValueError:
                continue
    return out or None


def latest_value(series_id):
    """Latest non-empty (date, value) for a FRED series, or (None, None)."""
    rows = series(series_id)
    if not rows:
        return None, None
    return rows[-1]


def latest_common(series_a, series_b):
    """``(date, value_a, value_b)`` on the newest date BOTH series report.

    For a spread of two series this is the only honest pairing: the two need
    not publish on the same schedule (SOFR posts T+1, IORB same-day), so
    "latest of each" can subtract values from different days — across an FOMC
    move that manufactures a spread jump the size of the policy step itself.
    Returns ``(None, None, None)`` if either series is unavailable or they
    share no date.
    """
    rows_a, rows_b = series(series_a), series(series_b)
    if not rows_a or not rows_b:
        return None, None, None
    by_date_b = dict(rows_b)
    for date, value_a in reversed(rows_a):
        if date in by_date_b:
            return date, value_a, by_date_b[date]
    return None, None, None


def reading(series_id, label="OAS"):
    """A keyless FRED series as the fetcher contract dict.

    The shared shape for the one-line watchlist lines (em_corp_oas,
    euro_hy_spread, …) so the "unavailable" note and the value-to-dict wrapping
    live in one place. ``label`` names the quantity in the note (e.g. "OAS").
    """
    date, value = latest_value(series_id)
    if value is None:
        return {"raw_value": None, "source_note": f"FRED {series_id} unavailable"}
    return {"raw_value": value, "source_note": f"FRED {series_id} {label} {date}",
            "obs_date": date}
