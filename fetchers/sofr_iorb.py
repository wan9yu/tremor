"""SOFR minus IORB — US dollar-funding stress (financial-plumbing watchlist, tier 2).

Guarded equilibrium: the Fed pins overnight secured rates inside its administered
corridor (the IORB ceiling, the ON-RRP floor, the standing repo backstop). The
leaking hand: when SOFR pushes above the IORB ceiling the Fed defends, reserves
have grown scarce and the repo market is seizing — dollar-funding stress the
guardrails can no longer absorb (cf. the Sept-2019 repo spike). Differencing
against the defended ceiling isolates the guard deviation, not the rate level.

Reading: SOFR − IORB in basis points. A rising positive gap is the alarming move.
Source: FRED keyless CSV for SOFR and IORB.
"""
from core import fred

LINE = "sofr_iorb_spread"
LABEL = "SOFR − IORB spread (bps)"
UNIT = "bps"
ANOMALY_DIRECTION = "up"
TIER = 2


def fetch_daily():
    sofr_date, sofr = fred.latest_value("SOFR")
    iorb_date, iorb = fred.latest_value("IORB")
    missing = []
    if sofr is None:
        missing.append("SOFR")
    if iorb is None:
        missing.append("IORB")
    if missing:
        return {"raw_value": None, "source_note": "FRED unavailable: " + ", ".join(missing)}
    bps = (sofr - iorb) * 100.0
    return {
        "raw_value": round(bps, 1),
        "source_note": f"FRED SOFR {sofr} ({sofr_date}) − IORB {iorb}",
        "obs_date": sofr_date,
    }
