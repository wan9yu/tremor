"""Euro high-yield credit spread — European financial-stress watchlist (tier 2).

Guarded equilibrium: the ECB and European banks press credit spreads down (rate
policy, bond purchases, the profit motive to lend). The leaking hand: a spike in
the ICE BofA Euro High Yield option-adjusted spread leaks European credit fear —
banking stress, fragmentation, a growth scare — that the guards could not hold
down. Orthogonal to the US high-yield line: a different borrower population and a
different central bank, so EU-specific stress can move while US spreads sit calm.

Reading: Euro HY OAS in percentage points. A spike is the alarming move.
Source: FRED keyless CSV (BAMLHE00EHYIOAS).
"""
from core import fred

LINE = "euro_hy_spread"
LABEL = "Euro HY credit spread OAS (pp)"
UNIT = "pp"
ANOMALY_DIRECTION = "up"
TIER = 2

_SERIES = "BAMLHE00EHYIOAS"


def fetch_daily():
    date, value = fred.latest_value(_SERIES)
    if value is None:
        return {"raw_value": None, "source_note": f"FRED {_SERIES} unavailable"}
    return {"raw_value": value, "source_note": f"FRED {_SERIES} OAS {date}",
            "obs_date": date}
