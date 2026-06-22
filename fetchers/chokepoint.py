"""IMF PortWatch — maritime chokepoint transits (trade tension watchlist, tier 2).

Guarded equilibrium: trade economics and the littoral states keep ships flowing
through each of 28 maritime chokepoints (idle routes burn money). The leaking
hand: a drop in transits leaks a blockade, war, drought, or attack specific to
that strait — the live data already shows Hormuz collapsed to a couple of
transits a day under blockade while the Red Sea cut Suez well below normal.

Reading: total vessel transits across all chokepoints on the latest available day.
A drop is the alarming move. (The dataset lags a few days; we take the latest
record, which is honest at daily cadence since a closure persists.)

Source: IMF PortWatch `Daily_Chokepoints_Data` ArcGIS feature service. Keyless.
"""
import json

import requests

LINE = "chokepoint_breadth"
LABEL = "Chokepoint vessel transits (28 straits)"
UNIT = "vessels"
ANOMALY_DIRECTION = "down"
TIER = 2

_URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/"
        "Daily_Chokepoints_Data/FeatureServer/0/query")
_STATS = json.dumps([
    {"statisticType": "sum", "onStatisticField": "n_total", "outStatisticFieldName": "total"}
])
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def fetch_daily():
    params = {
        "where": "1=1",
        "groupByFieldsForStatistics": "date",
        "outStatistics": _STATS,
        "orderByFields": "date DESC",
        "resultRecordCount": 1,
        "f": "json",
    }
    try:
        r = requests.get(_URL, params=params, headers=_HEADERS, timeout=25)
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"PortWatch request failed: {type(e).__name__}"}
    if r.status_code != 200:
        return {"raw_value": None, "source_note": f"PortWatch HTTP {r.status_code}"}
    try:
        features = r.json().get("features") or []
    except ValueError:
        return {"raw_value": None, "source_note": "PortWatch returned a non-JSON body"}
    if not features:
        return {"raw_value": None, "source_note": "PortWatch returned no chokepoint data"}
    attrs = features[0].get("attributes", {})
    total = attrs.get("total")
    date = attrs.get("date")
    if total is None:
        return {"raw_value": None, "source_note": "PortWatch returned no transit total"}
    return {
        "raw_value": float(total),
        "source_note": f"IMF PortWatch 28 chokepoints, total transits {date}",
    }
