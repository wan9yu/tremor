"""Emerging-market corporate credit spread — EM dollar-funding watchlist (tier 2).

Guarded equilibrium: emerging-market sovereigns defend access to dollar funding
(reserves, IMF lines, rate hikes to retain capital). The leaking hand: a spike in
the ICE BofA EM corporate option-adjusted spread leaks a systemic loss of dollar
access across the developing world — capital flight and dollar shortage the local
guards cannot offset. Orthogonal to US high-yield: a different population of
borrowers, a different guard.

Reading: EM corporate OAS in percentage points. A spike is the alarming move.
Source: FRED keyless CSV (BAMLEMCBPIOAS).
"""
from core import fred

LINE = "em_corp_oas"
LABEL = "EM corporate credit spread OAS (pp)"
UNIT = "pp"
ANOMALY_DIRECTION = "up"
TIER = 2

_SERIES = "BAMLEMCBPIOAS"


def fetch_daily():
    date, value = fred.latest_value(_SERIES)
    if value is None:
        return {"raw_value": None, "source_note": f"FRED {_SERIES} unavailable"}
    return {"raw_value": value, "source_note": f"FRED {_SERIES} OAS {date}"}
