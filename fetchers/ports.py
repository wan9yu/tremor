"""IMF PortWatch — global port calls (trade tension watchlist, tier 2).

Guarded equilibrium: ports, shippers, and the economies behind them keep cargo
moving (idle berths and unworked cargo burn money). The leaking hand: a sustained
drop in global port calls leaks a strike, lockdown, blockade, war damage,
sanctions, or a demand collapse. This is the PORT side of PortWatch — 2065 ports
from satellite AIS — distinct from the chokepoint (canal/strait) line.

Reading: total port calls worldwide on the latest available day. A drop is the
alarming move.

Source: IMF PortWatch `Daily_Ports_Data` ArcGIS feature service. Keyless.
"""
from core import clock, portwatch

LINE = "port_throughput"
LABEL = "Global port calls (PortWatch)"
UNIT = "port calls"
ANOMALY_DIRECTION = "down"
TIER = 2
# Cargo breathes with the week: measured over 211 observations, Sundays run 8.0%
# below the line's level and Mondays 7.2% above — a span of 2.50x its own pooled
# scale at a permutation p of 0.0001, the strongest weekly rhythm in the repo.
# Left unremoved it biased every verdict by which weekday the observation fell
# on (mean z from +1.52 on Mondays to -1.18 on Sundays) and it was MASKING real
# alarm-direction days: the July 2026 dip reads as one tremble pooled and three
# consecutive ones once the rhythm is removed.
WEEKLY_CYCLE = True

# Named here so the archive seeder in tools/ addresses exactly the same service,
# field and note prefix the daily fetch does.
SERVICE = "Daily_Ports_Data"
FIELD = "portcalls"
NOTE = "IMF PortWatch global port calls"


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
