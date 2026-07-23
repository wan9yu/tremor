"""Keyless FRED access via the public fredgraph.csv endpoint (no API key).

FRED serves any series as CSV at fredgraph.csv?id=<series>, which needs no key —
handy for the lighter watchlist lines. (The primary credit-spread line uses the
keyed JSON API; this is the keyless path for additional FRED-based candidates.)
"""
import requests

_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def latest_value(series_id):
    """Latest non-empty (date, value) for a FRED series, or (None, None)."""
    try:
        r = requests.get(_URL, params={"id": series_id}, headers=_HEADERS, timeout=15)
    except requests.RequestException:
        return None, None
    if r.status_code != 200:
        return None, None
    rows = r.text.strip().splitlines()
    # rows are "observation_date,VALUE"; "." marks a missing observation.
    for row in reversed(rows[1:]):
        parts = row.split(",")
        if len(parts) >= 2 and parts[1] not in ("", ".", "NaN"):
            try:
                return parts[0], float(parts[1])
            except ValueError:
                continue
    return None, None


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
