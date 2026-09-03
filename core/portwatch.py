"""IMF PortWatch helper — daily sums over a feature layer (keyless).

Shared by the trade lines (chokepoint transits and port calls) so the ArcGIS
query, the sum-by-date statistics, and the observation selection live in one
place.

WHY THE FIXED LAG. PortWatch is a COMPLETE DAILY series — every one of the 28
chokepoints on every date back to 2019, no gaps — that is PUBLISHED WEEKLY, in
batches of seven days. This helper used to ask for the newest available day and
keep exactly one row, so on six days out of seven it re-recorded a reading it
already held: it downloaded the whole week and threw away six sevenths of it.
That, not the publication lag, is why these lines never accumulated enough
distinct observations to score. When the Strait of Hormuz closed, the transit
collapse was sitting inside a response the instrument had already received and
discarded.

Asking instead for the observation exactly ``LAG_DAYS`` back yields one NEW
observation per collection day, which is the cadence the data actually has. The
lag has to clear the worst case: a release lands mid-week covering through the
prior Sunday, so the newest available reading ages from about 3 days just after
a release to about 9 days just before the next one. Ten buys a day of margin. If
the target is still unpublished, the newest available day is used and the
shortfall is stated in the note rather than hidden.

THE PRICE, recorded here so it is visible from the code and not only from
radar.md: a fixed lag makes these lines permanently ~10 days stale, which puts
them permanently outside the freshness rule for a displayed tier-1 instrument
(≤ ~2 days). This trades liveness for the ability to score at all, and it is the
right trade only because these are watchlist lines. Reading the newest available
day instead would be fresher and would still be unable to judge itself.
"""
import datetime
import json

import requests

from core import useragent

_BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
         "{svc}/FeatureServer/0/query")
_HEADERS = useragent.HEADERS

LAG_DAYS = 10
_FETCH_DAYS = 40  # one request comfortably covers a publication cycle


def _parse_date(value):
    """PortWatch dates arrive as ISO strings or as epoch milliseconds."""
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value[:10])
        except ValueError:
            return None
    try:
        return datetime.datetime.utcfromtimestamp(value / 1000).date()
    except (TypeError, ValueError, OSError):
        return None


def daily_totals(service, field, count=_FETCH_DAYS):
    """``([(date, total)] newest-first, "")`` or ``(None, reason)``."""
    stats = json.dumps([
        {"statisticType": "sum", "onStatisticField": field, "outStatisticFieldName": "total"}
    ])
    params = {
        "where": "1=1",
        "groupByFieldsForStatistics": "date",
        "outStatistics": stats,
        "orderByFields": "date DESC",
        "resultRecordCount": count,
        "f": "json",
    }
    try:
        r = requests.get(_BASE.format(svc=service), params=params, headers=_HEADERS, timeout=30)
    except requests.RequestException as e:
        return None, f"PortWatch request failed: {type(e).__name__}"
    if r.status_code != 200:
        return None, f"PortWatch HTTP {r.status_code}"
    try:
        features = r.json().get("features") or []
    except ValueError:
        return None, "PortWatch returned a non-JSON body"
    rows = []
    for feature in features:
        attrs = feature.get("attributes", {})
        day, total = _parse_date(attrs.get("date")), attrs.get("total")
        if day is not None and total is not None:
            rows.append((day, float(total)))
    if not rows:
        return None, "PortWatch returned no usable daily rows"
    rows.sort(reverse=True)
    return rows, ""


def daily_sum_at_lag(service, field, today, lag_days=LAG_DAYS):
    """Sum ``field`` on the day ``lag_days`` before ``today``.

    Returns ``(total, obs_date, note)``; note carries the failure reason when
    total is None, or a "[behind]" marker when the target day was not yet
    published and an older one was used.
    """
    rows, reason = daily_totals(service, field)
    if rows is None:
        return None, None, reason
    try:
        target = datetime.date.fromisoformat(today) - datetime.timedelta(days=lag_days)
    except (ValueError, TypeError):
        return None, None, "bad collection date"
    for day, total in rows:  # newest-first, so the first match is the closest
        if day <= target:
            behind = (target - day).days
            note = (f" [behind: wanted {target}, newest available {day}]"
                    if behind else "")
            return total, day.isoformat(), note
    return None, None, f"PortWatch has nothing at or before {target}"


def components_at(service, field, name_field, obs_date):
    """``{name: value}`` for every feature on ``obs_date``, or ``{}``.

    The sum this module normally returns throws away the thing that actually
    matters. PortWatch answers with all 28 chokepoints every day and the line
    stores one scalar, so a strait collapsing 65% moves the recorded number by
    under 2% and is unrecoverable afterwards — that is not a scoring problem,
    it is a CAPTURE problem, and no later analysis can undo it. This returns the
    breakdown so it can be written down beside the sum. Nothing scores it.
    """
    params = {
        "where": f"date = DATE '{obs_date}'",
        "outFields": f"{name_field},{field}",
        "resultRecordCount": 200,
        "f": "json",
    }
    try:
        r = requests.get(_BASE.format(svc=service), params=params,
                         headers=_HEADERS, timeout=30)
        features = r.json().get("features") or [] if r.status_code == 200 else []
    except (requests.RequestException, ValueError):
        return {}
    out = {}
    for feature in features:
        attrs = feature.get("attributes", {})
        name, value = attrs.get(name_field), attrs.get(field)
        if name is not None and value is not None:
            out[str(name)] = float(value)
    return out
