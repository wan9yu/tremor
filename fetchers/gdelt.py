"""GDELT global crisis-coverage share — airspace-of-attention WATCHLIST (tier 2).

NOT a tension indicator, by the project's own rule: news coverage has no guard,
spikes are cheap, and raw counts inflate as media densifies. So it is kept on the
watchlist — scraped daily to build history and observed, never counted in the
trembling resonance. Its natural eventual role is the "felt vs real" contrast:
how disordered the world is *reported* to be, set against the objective lines.

Reading: the share of all global news coverage matching a fixed crisis/conflict
query, in percent (GDELT timelinevol — a fraction, which partly resists the
raw-count inflation trap). A rising share is the notable direction.

Source: GDELT DOC 2.0 API. Free, keyless, but rate-limited (~1 request / 5s),
which is fine for a once-daily scrape.
"""
import requests

LINE = "gdelt"
LABEL = "Global crisis-coverage share (GDELT)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
TIER = 2  # watchlist — collected daily, not displayed, not counted

_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_QUERY = "(crisis OR war OR conflict OR protest OR sanctions OR collapse)"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    try:
        r = requests.get(
            _URL,
            timeout=30,
            headers=_HEADERS,
            params={"query": _QUERY, "mode": "timelinevol",
                    "timespan": "5d", "format": "json"},
        )
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"GDELT request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"GDELT HTTP {r.status_code}"}
    try:
        timeline = r.json().get("timeline") or []
    except ValueError:
        return {"raw_value": None, "source_note": "GDELT returned a non-JSON body"}
    if not timeline:
        return {"raw_value": None, "source_note": "GDELT returned no timeline"}
    points = timeline[0].get("data") or []
    # Most recent daily point with a usable value.
    for point in reversed(points):
        value = point.get("value")
        if value is not None:
            try:
                return {
                    "raw_value": round(float(value), 4),
                    "source_note": f"GDELT crisis-coverage share {point.get('date')}",
                }
            except (TypeError, ValueError):
                continue
    return {"raw_value": None, "source_note": "GDELT returned no usable point"}
