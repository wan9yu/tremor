"""GDELT global news tone — "felt vs real" contrast line (tier 2).

The average emotional tone of the entire previous UTC day's global news-coded
events (GDELT AvgTone, aggregated in core/gdeltday.py alongside the conflict
share). More negative = the world's coverage reads grimmer. This is the spec's
own first suggestion for the feel proxy (news negativity): it measures the
VALENCE of coverage where the conflict share measures the event mix.

NOT a tension indicator (no guard) — never counted, contrast only.

Reading: average tone (typically -10..+10; recent global averages sit around
-2 to -4). FALLING tone is the "feels worse" direction.
"""
from core import gdeltday

LINE = "gdelt_tone"
LABEL = "Global news tone (GDELT)"
UNIT = "tone"
ANOMALY_DIRECTION = "down"
WEEKLY_CYCLE = True  # news volume has a strong weekday rhythm: weekends carry
# ~62k events against ~108k on weekdays, and the thinner weekend mix reads as
# more conflict and grimmer tone. De-cycling keys off obs_date, not the row date.
TIER = 2


def fetch_daily():
    stats, note = gdeltday.day_stats()
    if stats is None:
        return {"raw_value": None, "source_note": note}
    return {
        "raw_value": stats["tone"],
        "source_note": (f"GDELT full-day average tone, {stats['events']} events "
                        f"({stats['obs_date']})"),
        "obs_date": stats["obs_date"],
    }
