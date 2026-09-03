"""Geomagnetic storms — a space-weather CONTEXT line (never counted).

NOT a tension indicator. There is no guard: nobody defends the state of the
magnetosphere at a set point that a hidden human force overpowers — the Sun IS
the force, an exogenous driver, the same category as the Arctic temperature or a
seismic energy the guard gate excludes. So this line can never be counted in the
resonance and can never be promoted to tier-1, exactly like the vix / polar_temp
context lines.

Its job is auxiliary interpretation — specifically, it is a CONFOUNDER-SUBTRACTOR
for two lines already in the registry. When `gnss_interference` or
`grid_frequency` trembles, the reading alone cannot say whether a human hand
(GPS jamming, an electronic-warfare campaign, a grid under attack) or a
geomagnetic storm drove it — a severe storm degrades GNSS accuracy worldwide and
induces currents that stress power grids. Read beside this line the ambiguity
resolves: GNSS/grid tremble + a calm Kp = a real terrestrial disturbance; both
elevated together = the Sun, not a hidden hand. That sharpens two existing
instruments rather than adding a decorative third.

Reading: the day's MAXIMUM planetary Kp index (0-9, in thirds). Kp is the
canonical 3-hourly global geomagnetic-disturbance index; the daily MAX captures a
storm far better than an average, which washes the spikes out — the same choice
`grid_frequency` makes for its max-deviation. UP (a stronger storm) is the
noteworthy direction. Scored on the ordinary rolling z, so "storm" means unusual
against the last ~90 days, which is exactly the confounder question: was today
geomagnetically disturbed relative to the recent baseline the other lines also
sit against?

Source: NOAA SWPC planetary K-index (keyless JSON, 3-hourly, ~real time). The
seeder pulls the full definitive history from GFZ Potsdam (keyless, since 1932)
through this module's OWN daily_max / settled aggregation, so history and the
live tail are one measure. A settled read: obs_date is the latest COMPLETE UTC
day (< today), so a re-read of the still-forming day — whose Kp is a nowcast that
will revise — is never recorded, and a re-read of a completed day is a stale
republish (obs-dedup), not a second observation.
"""
import datetime

import requests

from core import useragent

LINE = "space_weather"
LABEL = "Geomagnetic storm — daily max planetary Kp"
UNIT = "Kp"
ANOMALY_DIRECTION = "up"  # a stronger storm is the noteworthy move
TIER = 2  # context line — fails the guard gate, never counted, never promotable
QUANTUM = 1.0 / 3.0  # Kp is reported in thirds (the 0, 0+, 1-, 1 ... scale); this
                     # floors the robust scale so a solar-quiet stretch of nearly
                     # identical daily maxima cannot leave the line unable to judge
                     # the storm that follows — the net_outages lesson.

_LIVE = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
_HEADERS = useragent.HEADERS


def parse_live(payload):
    """[(utc_date, kp)] from the SWPC planetary-K JSON (a list of 3-hourly dicts).

    Each record carries a ``time_tag`` (UTC) and ``Kp``; the date is the first
    ten characters of the tag. A record whose Kp will not parse is skipped rather
    than fabricated. Raises ValueError on a shape that is not the list of dicts
    the endpoint documents, so a changed/empty body degrades to a stated-empty
    row upstream instead of a silent zero.
    """
    if not isinstance(payload, list):
        raise ValueError("unexpected response shape")
    pairs = []
    for rec in payload:
        if not isinstance(rec, dict):
            raise ValueError("unexpected response shape")
        tag = rec.get("time_tag")
        if not tag:
            continue
        try:
            pairs.append((tag[:10], float(rec.get("Kp"))))
        except (TypeError, ValueError):
            continue
    return pairs


def daily_max(pairs):
    """Collapse 3-hourly ``[(date, kp)]`` to ``{date: max Kp that day}``.

    The ONE aggregation, shared by the live fetcher and the GFZ seeder (which
    emits the same (date, kp) pairs from its eight per-day columns), so the
    seeded history and the live tail are one measure of the same daily maximum.
    """
    by_day = {}
    for day, kp in pairs:
        if day and (day not in by_day or kp > by_day[day]):
            by_day[day] = kp
    return by_day


def settled(daily, today=None):
    """``{date: max Kp}`` for every COMPLETE UTC day — those strictly before
    ``today`` (an explicit UTC date, defaulted here).

    The still-forming current day is dropped: its Kp is a nowcast that revises,
    and the boundary is UTC, not a naive local date, so it never depends on the
    runner's timezone.
    """
    if today is None:
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    return {day: kp for day, kp in daily.items() if day < today}


def fetch_daily():
    try:
        r = requests.get(_LIVE, headers=_HEADERS, timeout=30)
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        days = settled(daily_max(parse_live(r.json())))
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        return {"raw_value": None,
                "source_note": f"NOAA SWPC planetary-K unavailable: {type(e).__name__}"}

    obs = max(days, default=None)
    if obs is None:
        return {"raw_value": None,
                "source_note": "NOAA SWPC: no settled Kp day found"}
    val = round(days[obs], 3)
    return {
        "raw_value": val,
        "source_note": f"NOAA SWPC planetary Kp daily max {val:g} on {obs}",
        "obs_date": obs,
    }
