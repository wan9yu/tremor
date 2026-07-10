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
from core import portwatch

LINE = "port_throughput"
LABEL = "Global port calls (PortWatch)"
UNIT = "port calls"
ANOMALY_DIRECTION = "down"
TIER = 2


def fetch_daily():
    total, date, note = portwatch.latest_daily_sum("Daily_Ports_Data", "portcalls")
    if total is None:
        return {"raw_value": None, "source_note": note}
    return {
        "raw_value": total,
        "source_note": f"IMF PortWatch global port calls {date}",
        "obs_date": date,
    }
