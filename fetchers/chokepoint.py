"""IMF PortWatch — maritime chokepoint transits (trade tension watchlist, tier 2).

Guarded equilibrium: trade economics and the littoral states keep ships flowing
through each of 28 maritime chokepoints (idle routes burn money). The leaking
hand: a drop in transits leaks a blockade, war, drought, or attack specific to
that strait — the live data already shows Hormuz collapsed to a couple of
transits a day under blockade while the Red Sea cut Suez well below normal.

Reading: total vessel transits across all chokepoints on the latest available day.
A drop is the alarming move.

Source: IMF PortWatch `Daily_Chokepoints_Data` ArcGIS feature service. Keyless.
"""
from core import portwatch

LINE = "chokepoint_breadth"
LABEL = "Chokepoint vessel transits (28 straits)"
UNIT = "vessels"
ANOMALY_DIRECTION = "down"
TIER = 2  # watchlist: strong signal but PortWatch lags ~8 days — too stale to display live


def fetch_daily():
    total, date, note = portwatch.latest_daily_sum("Daily_Chokepoints_Data", "n_total")
    if total is None:
        return {"raw_value": None, "source_note": note}
    return {
        "raw_value": total,
        "source_note": f"IMF PortWatch 28 chokepoints, total transits {date}",
        "obs_date": date,
    }
