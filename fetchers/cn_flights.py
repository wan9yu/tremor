"""China airborne aircraft — RETIRED 2026-07-23 (radar round 8), not collected.

Scoped the main flights idea to China's three busiest metros (Beijing, Shanghai,
Guangzhou). Removed from collect.LINES because it is structurally confounded, not
merely weak: the alarm direction is down, and a community ADS-B feeder dropping
offline drives the count down too, so the sensor is collinear with its own
failure and cannot separate a real grounding from a rebooted receiver (2026-07-20
read Beijing=0, impossible for a metro). Free community ADS-B over mainland China
is too sparse and feeder-dependent (~30-60 aircraft per metro vs ~800 over Europe)
for the count to mean real traffic.

Kept on disk for the record and the re-activation condition: re-add to LINES only
with a per-metro same-frame denominator that breaks the collinearity. Data
archived at data/archive/cn_flights_retired.csv; full rationale in
data/annotations.csv 2026-07-23 and radar.md round 8.
"""
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
