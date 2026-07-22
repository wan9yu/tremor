"""IMF PortWatch — maritime chokepoint transits (trade tension watchlist, tier 2).

Guarded equilibrium: trade economics and the littoral states keep ships flowing
through each of 28 maritime chokepoints (idle routes burn money). The leaking
hand: a drop in transits leaks a blockade, war, drought, or attack specific to
that strait.

Reading: total vessel transits across all 28 chokepoints on the observation
exactly ``LAG_DAYS`` back. A drop is the alarming move.

Two limits worth stating plainly. The reading is a 28-point TOTAL, so a single
strait closing moves it only a percent or two and can be lost in the sum — a
per-strait breadth count would see what this cannot. And the fixed lag keeps it
permanently about ten days stale, which is why it stays on the watchlist: the
freshness rule reserves tier-1 for instruments that can answer within ~2 days.

Source: IMF PortWatch `Daily_Chokepoints_Data` ArcGIS feature service. Keyless.
"""
from core import clock, portwatch

LINE = "chokepoint_breadth"
LABEL = "Chokepoint vessel transits (28 straits)"
UNIT = "vessels"
ANOMALY_DIRECTION = "down"
TIER = 2  # watchlist: PortWatch is ~10 days behind — too stale to display live

# Named here so the archive seeder in tools/ addresses exactly the same service,
# field and note prefix the daily fetch does.
SERVICE = "Daily_Chokepoints_Data"
FIELD = "n_total"
NOTE = "IMF PortWatch 28 chokepoints, total transits"


def fetch_daily():
    total, date, note = portwatch.daily_sum_at_lag(
        SERVICE, FIELD, clock.china_today())
    if total is None:
        return {"raw_value": None, "source_note": note}
    return {
        "raw_value": total,
        "source_note": f"{NOTE} {date}{note}",
        "obs_date": date,
    }
