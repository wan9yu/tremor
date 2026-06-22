"""IMF PortWatch helper — latest daily sum of a field over a feature layer (keyless).

Shared by the trade lines (chokepoint transits and port calls) so the ArcGIS
query, the sum-by-date statistics, and the latest-day selection live in one place.
The dataset lags a few days; taking the most recent available day is honest at
daily cadence because a disruption persists.
"""
import json

import requests

_BASE = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
         "{svc}/FeatureServer/0/query")
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def latest_daily_sum(service, field):
    """Sum ``field`` over all rows on the most recent date.

    Returns ``(total: float | None, date: str | None, note: str)``; note carries
    the failure reason when total is None.
    """
    stats = json.dumps([
        {"statisticType": "sum", "onStatisticField": field, "outStatisticFieldName": "total"}
    ])
    params = {
        "where": "1=1",
        "groupByFieldsForStatistics": "date",
        "outStatistics": stats,
        "orderByFields": "date DESC",
        "resultRecordCount": 1,
        "f": "json",
    }
    try:
        r = requests.get(_BASE.format(svc=service), params=params, headers=_HEADERS, timeout=30)
    except requests.RequestException as e:
        return None, None, f"PortWatch request failed: {type(e).__name__}"
    if r.status_code != 200:
        return None, None, f"PortWatch HTTP {r.status_code}"
    try:
        features = r.json().get("features") or []
    except ValueError:
        return None, None, "PortWatch returned a non-JSON body"
    if not features:
        return None, None, "PortWatch returned no data"
    attrs = features[0].get("attributes", {})
    if attrs.get("total") is None:
        return None, None, "PortWatch returned no total"
    return float(attrs["total"]), attrs.get("date"), ""
