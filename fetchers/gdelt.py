"""GDELT global conflict-event share — "felt vs real" contrast line (tier 2).

NOT a tension indicator, by the project's own rule: event tallies have no guard
and inflate as media coverage densifies. It rides the watchlist as one half of
the "felt vs real" contrast — how much conflict the world's news is coding, set
against the objective lines; the gap is the anxiety premium of the age.

Measurement definition (v2, fixed 2026-07-10): the share of MATERIAL-CONFLICT
events (QuadClass 4) across the ENTIRE previous UTC day (~96 15-minute files,
aggregated once in core/gdeltday.py). The v1 series sampled a single 15-minute
file and was noise-dominated (8→23% inside a week); v1 is archived at
data/archive/gdelt_v1.csv and this series starts fresh.

Reading: percent of the day's events coded as material conflict. Rising = the
world's news is reporting more conflict.
"""
from core import gdeltday

LINE = "gdelt"
LABEL = "Global conflict-event share (GDELT)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
WEEKLY_CYCLE = True  # news volume has a strong weekday rhythm: weekends carry
# ~62k events against ~108k on weekdays, and the thinner weekend mix reads as
# more conflict and grimmer tone. De-cycling keys off obs_date, not the row date.
TIER = 2


def fetch_daily():
    stats, note = gdeltday.day_stats()
    if stats is None:
        return {"raw_value": None, "source_note": note}
    return {
        "raw_value": stats["share"],
        "source_note": (f"GDELT full-day conflict share, {stats['events']} events "
                        f"across {stats['files']} files ({stats['obs_date']})"),
        "obs_date": stats["obs_date"],
    }
