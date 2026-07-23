"""China airborne aircraft — airspace WATCHLIST line (tier 2).

Same idea as the main flights line, scoped to China's three busiest metros
(Beijing, Shanghai, Guangzhou). This is a TIER-2 / watchlist indicator: scraped
every day so history and z-score accumulate, but NOT displayed and NOT counted
toward the trembling resonance — a candidate being observed for promotion.

Why watchlist, not primary: free community ADS-B coverage over mainland China is
sparse and feeder-dependent (measured ~30-60 aircraft over each metro vs ~800
over Europe), so the count partly reflects receiver availability, not real air
traffic. Keeping it tier-2 lets us watch whether it becomes a usable signal
without letting that noise into the live instrument. Promote by setting TIER = 1.
"""
# RETIRED 2026-07-23 (radar round 8): removed from collect.LINES. The alarm
# direction is down and a community ADS-B feeder dropping offline drives the
# count down too, so the sensor is collinear with its own failure and cannot
# separate a real grounding from a rebooted receiver. Kept on disk for the
# record; re-add to LINES only with a per-metro same-frame denominator that
# breaks that collinearity. See data/annotations.csv 2026-07-23.

from core import adsb

LINE = "cn_flights"
LABEL = "China aircraft airborne (watchlist)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"
TIER = 2  # watchlist — collected daily, not displayed, not counted
WEEKLY_CYCLE = True

_REGIONS = [("Beijing", 39.9, 116.4), ("Shanghai", 31.2, 121.5), ("Guangzhou", 23.0, 113.5)]


def fetch_daily():
    return adsb.airborne_over(_REGIONS, "China metros")
