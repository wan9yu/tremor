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

from core import dates, useragent

_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_HEADERS = useragent.HEADERS

_MIN_GAP_S = 5.0
_last_request = 0.0

# A served row must START with a date. fredgraph answers a bot block with an
# HTML page, and an HTML line splits at a comma too: on 2026-10-22 the Google
# Fonts <link> split into ("    <link href=…Open+Sans:300", "400"), which the
# old parse returned as a reading of 400 dated with half a URL. Only the value
# column was ever checked, so five lines committed it as an observation, and
# the malformed obs_date later crashed the nightly derive step.
#
# The test is the record's one shared date predicate (``core.dates``), the same
# one the collector's obs_date gate and the derive step's guard use, so what is
# accepted here is exactly what those layers will accept downstream. It is total
# over any input, so a caller can pass a parsed field without a type check.
_is_iso_date = dates.is_strict_date


def _spaced_get(params, timeout=15):
    """GET fredgraph.csv, at most one request per ``_MIN_GAP_S`` per process."""
    global _last_request
    wait = _MIN_GAP_S - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()
    return requests.get(_URL, params=params, headers=_HEADERS, timeout=timeout)


def series(series_id, timeout=15):
    """[(date, value)] for a FRED series, oldest-first, or None.

    Rows are "observation_date,VALUE"; "." marks a missing observation. A row
    whose first field is not a strict date is dropped (see ``_is_iso_date``),
    and a body with no surviving row is ``None`` — the same unavailable answer
    every caller already handles.

    The seeder passes a longer timeout; EVERY caller goes through the pacing
    above — this module is the only sanctioned path to fredgraph.
    """
    try:
        r = _spaced_get({"id": series_id}, timeout=timeout)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    out = []
    for row in r.text.strip().splitlines()[1:]:
        parts = row.split(",")
        if len(parts) < 2 or not _is_iso_date(parts[0]):
            continue
        if parts[1] in ("", ".", "NaN"):
            continue
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


def common_pair(series_a, series_b):
    """``(date, value_a, value_b, missing)`` on the newest date BOTH report.

    For a spread of two series this is the only honest pairing: the two need
    not publish on the same schedule (SOFR posts T+1, IORB same-day), so
    "latest of each" can subtract values from different days — across an FOMC
    move that manufactures a spread jump the size of the policy step itself.

    ``missing`` lists the ids whose fetch came back empty. A caller that only
    wants the pair should use ``latest_common``; a caller that must describe
    the failure needs the difference between "one leg is down" and "both legs
    are healthy but share no date", which a bare ``None`` date erases.
    """
    rows_a, rows_b = series(series_a), series(series_b)
    if not rows_a or not rows_b:
        return None, None, None, [sid for sid, rows in
                                  ((series_a, rows_a), (series_b, rows_b))
                                  if not rows]
    by_date_b = dict(rows_b)
    for obs, value_a in reversed(rows_a):
        if obs in by_date_b:
            return obs, value_a, by_date_b[obs], []
    return None, None, None, []


def latest_common(series_a, series_b):
    """``(date, value_a, value_b)`` on the newest date BOTH series report.

    Returns ``(None, None, None)`` if either series is unavailable or they
    share no date; ``common_pair`` is the same lookup with the cause kept.
    """
    obs, value_a, value_b, _ = common_pair(series_a, series_b)
    return obs, value_a, value_b


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
