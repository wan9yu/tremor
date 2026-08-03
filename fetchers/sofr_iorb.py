"""SOFR minus IORB — US dollar-funding stress (financial-plumbing watchlist, tier 2).

Guarded equilibrium: the Fed pins overnight secured rates inside its administered
corridor (the IORB ceiling, the ON-RRP floor, the standing repo backstop). The
leaking hand: when SOFR pushes above the IORB ceiling the Fed defends, reserves
have grown scarce and the repo market is seizing — dollar-funding stress the
guardrails can no longer absorb (cf. the Sept-2019 repo spike). Differencing
against the defended ceiling isolates the guard deviation, not the rate level.

Reading: SOFR − IORB in basis points. A rising positive gap is the alarming move.
Source: FRED keyless CSV for SOFR and IORB.

BOTH LEGS MUST DESCRIBE THE SAME DAY. The two series publish on different
schedules — SOFR posts next-morning, IORB updates the day it changes — so
"latest of each" can pair a pre-FOMC SOFR with a post-FOMC IORB: across a 25bp
policy step that manufactures a ~25bp spread jump, a z of ~12 against this
line's measured Qn of ~2bp, out of nothing but leg misalignment. The spread is
therefore computed on the newest date BOTH series report, and that date is the
observation.
"""
from core import fred

LINE = "sofr_iorb_spread"
LABEL = "SOFR − IORB spread (bps)"
UNIT = "bps"
ANOMALY_DIRECTION = "up"
TIER = 2


def fetch_daily():
    date, sofr, iorb = fred.latest_common("SOFR", "IORB")
    if date is None:
        return {"raw_value": None,
                "source_note": "FRED SOFR/IORB share no reported date"}
    bps = (sofr - iorb) * 100.0
    return {
        "raw_value": round(bps, 1),
        "source_note": f"FRED SOFR {sofr} − IORB {iorb} (both {date})",
        "obs_date": date,
    }
