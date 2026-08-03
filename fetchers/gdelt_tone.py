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
# NOT flagged as a weekly-cycle line. The volume rhythm is real — weekends carry
# ~62k events against ~108k on weekdays — but the TONE it produces does not
# measurably follow it: the weekday-median span is 1.61x this line's own pooled
# scale at a permutation p of 0.58 (n=24), which is no evidence of a rhythm at
# all. The sister line gdelt (conflict SHARE) does carry the flag, on a measured
# effect. Flagging a rhythm that is not there costs real sensitivity, so it is
# claimed only where it was measured.
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
