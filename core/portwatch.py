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
import time

import requests

from core import useragent

_BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
         "{svc}/FeatureServer/0/query")
_HEADERS = useragent.HEADERS

LAG_DAYS = 10
_FETCH_DAYS = 40  # one request comfortably covers a publication cycle

# THE QUOTA. The ArcGIS host meters request units per minute (6000), and it
# answers a breach with HTTP 200 and an error body, not with a 429 status:
#
#     {"error": {"code": 429, "message": "Unable to perform query. Too many
#      requests.", "details": ["... maximum allowed request units (6000) per
#      Minute. Retry after 60 sec."]}}
#
# Read as a feature layer that body has no ``features``, which used to be
# reported as "returned no usable daily rows" -- indistinguishable from the
# series being empty -- and ``components_at`` returned ``{}`` with no reason.
# A breach is now named as one, and waited out ONCE per process: the body says
# "Retry after 60 sec", a collection run makes only a handful of calls, and an
# unbounded retry would hold up every line behind this one. The wait is a budget
# of the whole process, not of each request, so a run that breaches twice still
# loses at most ``QUOTA_WAIT_S``. Lines that declare a sample hour are collected
# before the PortWatch lines (``collect.LINES``), so the wait cannot push them
# out of tolerance.
QUOTA_WAIT_S = 60
_quota_waits_left = 1
_sleep = time.sleep


_NOTE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        "0123456789 .,;:/+_()#%-")


def _clean(value, limit):
    """``value`` as one short note-safe line: alphanumerics and neutral punctuation.

    The note lands in a committed CSV and reaches the dashboard, which renders a
    dark row's ``source_note`` as HTML. An allowlist (not a strip of
    non-printables) means nothing this function returns can open a tag, quote an
    attribute or start a scheme, whatever a proxy or the upstream sends back.
    """
    return "".join(ch for ch in str(value) if ch in _NOTE_CHARS)[:limit]


def _query(service, params):
    """``(body, "")`` for a usable JSON object, else ``(None, reason)``.

    One request, plus -- at most once per process -- one retry after the stated
    quota wait. Everything else (a transport failure, a non-200, a non-JSON or
    list body, an error body that is not the quota) is final on the first answer.
    """
    global _quota_waits_left
    while True:
        try:
            r = requests.get(_BASE.format(svc=service), params=params,
                             headers=_HEADERS, timeout=30)
        except requests.RequestException as e:
            return None, f"PortWatch request failed: {type(e).__name__}"
        if r.status_code != 200:
            return None, f"PortWatch HTTP {r.status_code}"
        try:
            body = r.json()
        except ValueError:
            return None, "PortWatch returned a non-JSON body"
        if not isinstance(body, dict):
            return None, "PortWatch returned an unexpected JSON shape"
        error = body.get("error")
        if error is None:
            return body, ""
        code = error.get("code") if isinstance(error, dict) else None
        if str(code).strip() != "429":
            return None, f"PortWatch error body (code {_clean(code, 20)})"
        if _quota_waits_left <= 0:
            return None, "PortWatch quota: HTTP 200 error 429"
        _quota_waits_left -= 1
        _sleep(QUOTA_WAIT_S)


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
    body, reason = _query(service, params)
    if body is None:
        return None, reason
    features = body.get("features") or []
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
    """``({name: value}, reason)`` for every feature on ``obs_date``.

    ``reason`` is ``""`` when the breakdown came back, else the sentence for why
    it did not (``{}`` alongside it): a quota breach, a non-200, an empty answer.
    The breakdown is diagnostic and never blocks a reading, but a scored total
    sitting beside a missing breakdown must say why in the record.

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
    body, reason = _query(service, params)
    if body is None:
        return {}, reason
    out = {}
    for feature in body.get("features") or []:
        attrs = feature.get("attributes", {})
        name, value = attrs.get(name_field), attrs.get(field)
        if name is not None and value is not None:
            out[str(name)] = float(value)
    if not out:
        return {}, f"PortWatch returned no features for {_clean(obs_date, 10)}"
    return out, ""
