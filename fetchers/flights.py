"""Community ADS-B — airspace tension line (flight-volume proxy). The origin line.

Guarded equilibrium: airlines' profit motive keeps planes flying on schedule.
The leaking hand: a sharp drop in airborne volume betrays a larger force that
overwhelmed that motive — closed airspace, severe weather, pandemics, control
lockdowns. Military airspace closures are not announced; they leave a shadow
only in how many aircraft are actually in the air. Flights become a side channel
for the otherwise invisible.

Reading: number of aircraft airborne across a FIXED set of busy, densely-fed
airspaces, sampled at the same time each day. A sudden DROP is the alarming move.

Source: keyless community ADS-B aggregators (airplanes.live / adsb.fi / adsb.lol),
which — unlike OpenSky's anonymous endpoint — respond reliably from shared cloud
IPs and need no key or registration. Each region is tried against the providers
in order, so counts normally come from one provider and stay comparable. Coverage
is volunteer-based, so this is a regional proxy, not a global census; that's fine
because the z-score reacts to a line's deviation from its own baseline, not its
absolute level. The region set is fixed: if any region has no data, the day is
written empty (a partial sum would look like a flight drop).
"""
from core import adsb

LINE = "flights"
LABEL = "Aircraft airborne (major airspaces)"
UNIT = "aircraft"
ANOMALY_DIRECTION = "down"  # a drop in flight volume is the alarming move
WEEKLY_CYCLE = True  # flight volume has a strong weekday rhythm; de-cycle by weekday

# A concurrent-snapshot line is only comparable day to day if sampled at a FIXED
# hour: aircraft aloft swing ~150/hour (~0.9z) around the target, so a mistimed
# sample measures the diurnal cycle, not the world — the 2026-08-28 z=-3.05 false
# tremble was a run delayed into the 05:54Z trough (R25). daily.yml now schedules
# early and SLEEPS to 22:30Z so the sample lands on target; on the rare run delayed
# PAST the sleep window, collect.py's guard refuses the off-hour reading (dark)
# rather than score a trough as a flight drop. 22:30Z is the historical effective
# hour (the record's samples cluster there); these are COLLECTION-time attrs, read
# only by collect(), never scoring attrs (replay/seeders have no sample time).
SAMPLE_TARGET_UTC_H = 22.5  # target sample hour (22:30Z); the baseline is built here
SAMPLE_TOL_H = 1.5          # a reading more than this from the target is not comparable

# Fixed, non-overlapping regions with dense community ADS-B coverage.
_REGIONS = [
    ("W/C Europe", 48.5, 9.0),
    ("US East", 39.0, -77.0),
    ("US West", 36.0, -116.0),
    ("E Asia/Japan", 35.0, 137.0),
]


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str}."""
    return adsb.airborne_over(_REGIONS, "regions")
