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
    # The 28 straits arrive in the same response the sum is built from.
    # Storing only the sum is why a 65% collapse at Hormuz moved this line
    # by under 2% and left nothing to go back to.
    components = portwatch.components_at(SERVICE, FIELD, "portname", date)
    # The sum is only comparable across days if it is a sum of the same
    # straits. The source CAN come up short — obs 2026-07-24 arrived with no
    # Hormuz row at all, day ~146 of the closure — and a short panel must be
    # said out loud: the recorded total is then a 27-strait number sitting in
    # a 28-strait series. Which strait is missing is in the components file.
    if components and len(components) != 28:
        note += f" [panel short: {len(components)} of 28 straits in the response]"
    return {
        "raw_value": total,
        "source_note": f"{NOTE} {date}{note}",
        "obs_date": date,
        "components": components,
    }
