"""VIX — fear as PRICED by markets; "felt vs real" contrast line (tier 2).

The spec excluded VIX as a tension indicator (a passive read, no guard) — and
that exclusion stands. But the contrast line is exempt from the guard gate by
design: it exists to measure how disordered the world FEELS, and implied equity
volatility is the cleanest daily price on collective fear. Together with the
GDELT lines it gives the feel side two independent modalities: what the news
reports, and what hedgers pay.

Reading: CBOE VIX daily close. Rising = fear is being priced higher. Never
counted in the resonance. Series seeded from FRED's public archive at creation
(2026-07-10) so its baseline needed no warm-up; seed rows are dated by their
observation date and noted as archive imports.

Source: FRED keyless CSV, series VIXCLS.
"""
from core import fred

LINE = "vix"
LABEL = "VIX (fear priced)"
UNIT = "index"
ANOMALY_DIRECTION = "up"
TIER = 2

_SERIES = "VIXCLS"


def fetch_daily():
    date, value = fred.latest_value(_SERIES)
    if value is None:
        return {"raw_value": None, "source_note": f"FRED {_SERIES} unavailable"}
    return {"raw_value": value, "source_note": f"FRED {_SERIES} close {date}",
            "obs_date": date}
