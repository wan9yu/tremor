"""The drift layer: has a line's whole level moved and stayed moved?

The scored lines answer a CHANGE question and the level layer answers a
COLLAPSE question about one strait. Neither sees the third shape, and the
instrument has now measured two of them: GPS interference stepped up in mid-2023
from about 0.25% of aircraft to about 0.44% and never came back — a 1.64x rise
over four years in which NO SINGLE DAY was ever unusual against its own trailing
ninety — and the Arctic anomaly runs warm on 75% of its 2,739 days. A rolling
baseline absorbs anything that arrives slowly enough, and "slowly enough" is
only three months here.

THE RULE, a two-sided clone of the level layer so there is one idea to learn and
not two: a line is in a DRIFTED state when its two-week median has run at least
half again above (or a third below) its own year-ago median for 28 straight
days. The year-ago reference is FROZEN the moment the state opens, so a drift
cannot become its own baseline — the same pin that keeps the Hormuz closure
visible five months in. It clears when the two-week median comes back within
20% of the pinned reference.

WHY THOSE NUMBERS, measured over 3,882 judged line-days across every line with
enough history: at 1.5x/28 days the entire multi-year record produces exactly
ONE state — gnss_interference from 2023-07-09 to 2023-11-19, the real mid-2023
jamming escalation — and zero false ones. Shortening the persistence to 7 or 14
days makes vix's 2026-03 episode open a redundant state the z-layer already
reported. Raising the ratio to 1.75x or 2x delays the true detection by six
weeks or loses it. The nearest non-gnss ratio anywhere in the record is credit's
1.396, which is a comfortable margin below the bar.

WHAT IT CANNOT DO, stated because a detector's blind spots are part of its
reading: it is a RATIO, so it is undefined on a line that crosses zero
(polar_temp's anomaly is meaningless divided by a median near zero), and it
cannot see a ratchet slow enough for the trailing reference to absorb — gnss's
own post-2023 creep from 0.294 to 0.419 never trips it. The yearly-median table
in radar-log.md (Round 10) is what covers those, moved there in the round-19
registry/log split; this covers the step.

Diagnostic only, under the same rule as the level layer and the intraday
sampler: no scoring code reads it, it is not mirrored to the dashboard, it
changes no verdict, and it is recomputed from scratch on every run.

    python tools/drift_layer.py            # recompute data/drifts.csv
    python tools/drift_layer.py --report   # print the states currently open
"""
import os
import statistics
import sys
from bisect import bisect_left
from datetime import date as _date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect
import level_layer
import seedlib

# The window geometry is the sibling's, imported rather than restated so the
# two detectors cannot drift apart on the parts that are deliberately identical.
# What differs — the ratios, the persistence, the two-sidedness — is below.
REF_WINDOW = level_layer.REF_WINDOW
REF_MIN_OBS = level_layer.REF_MIN_OBS
TRAIL_DAYS = level_layer.TRAIL_DAYS
HIGH_RATIO = 1.5         # open-high: trailing median >= this share of reference
LOW_RATIO = 1 / 1.5      # open-low: trailing median <= this share of reference
PERSIST = 28             # consecutive breach days before a state opens
CLEAR_BAND = 0.2         # clear when back within this fraction of PINNED

OUT = os.path.join(collect.DATA, "drifts.csv")
HEADER = ["date", "line", "event", "direction", "trail_median", "reference", "ratio"]


def walk(series):
    """Drift events for one series of (date, value): [(date, event, dir, trail, ref, ratio)].

    ``hold`` is emitted daily while a state stays open, so the file answers
    "what is drifted TODAY" with a row rather than with an absence.
    """
    ords = [_date.fromisoformat(d).toordinal() for d, _ in series]
    values = [v for _, v in series]
    if any(v <= 0 for v in values):
        return []  # a ratio to a median is meaningless on a series crossing zero
    out = []
    # One counter, not two: HIGH_RATIO is above LOW_RATIO, so a day cannot
    # breach in both directions and the side is already known when the run
    # is extended.
    side, run = "", 0
    pinned = None
    pinned_dir = ""
    for i, (date, _) in enumerate(series):
        ord_today = ords[i]
        trail = values[bisect_left(ords, ord_today - TRAIL_DAYS + 1):i + 1]
        trail_median = statistics.median(trail)

        if pinned is None:
            ref_vals = values[bisect_left(ords, ord_today - REF_WINDOW[0]):
                              bisect_left(ords, ord_today - REF_WINDOW[1] + 1)]
            if len(ref_vals) < REF_MIN_OBS:
                side, run = "", 0
                continue
            ref = statistics.median(ref_vals)
            ratio = trail_median / ref
            today_side = ("high" if ratio >= HIGH_RATIO
                          else "low" if ratio <= LOW_RATIO else "")
            run = run + 1 if today_side and today_side == side else bool(today_side)
            side = today_side
            if run >= PERSIST:
                pinned, pinned_dir = ref, side
                out.append((date, "open", pinned_dir, trail_median, pinned, ratio))
        else:
            ratio = trail_median / pinned
            back = abs(ratio - 1.0) <= CLEAR_BAND
            out.append((date, "clear" if back else "hold", pinned_dir,
                        trail_median, pinned, ratio))
            if back:
                pinned, pinned_dir = None, ""
                side, run = "", 0
    return out


def series_for(line):
    """[(obs_date, value)] for a scored line, oldest first, deduplicated."""
    rows = seedlib.read_line(line)
    seen = {}
    for r in rows:
        if not r["raw_value"]:
            continue
        seen.setdefault(r["obs_date"] or r["date"], float(r["raw_value"]))
    return sorted(seen.items())


def compute():
    rows = []
    for mod in collect.LINES:
        series = series_for(mod.LINE)
        if len(series) < REF_MIN_OBS:
            continue
        for date, event, direction, trail, ref, ratio in walk(series):
            rows.append({"date": date, "line": mod.LINE, "event": event,
                         "direction": direction, "trail_median": f"{trail:g}",
                         "reference": f"{ref:g}", "ratio": f"{ratio:.3f}"})
    rows.sort(key=lambda r: (r["date"], r["line"]))
    return rows


def main(argv):
    rows = compute()
    if "--report" in argv:
        open_now, opened = level_layer.open_states(rows, "line")
        # The same disclosure the level layer carries: a drifted state whose
        # line stops being served freezes at its last evidence and reads
        # exactly like one still being watched.
        newest = max((r["date"] for r in rows), default="")
        last = {}
        for mod in collect.LINES:
            series = series_for(mod.LINE)
            if series:
                last[mod.LINE] = series[-1][0]
        if not open_now:
            print("no line is in a drifted state")
        for line, r in sorted(open_now.items()):
            stale = level_layer.stale_note(max(newest, last.get(line, "")),
                                           last.get(line))
            print(f"DRIFTED {r['direction'].upper()} {line}: since {opened[line]}, "
                  f"two-week median {r['trail_median']} vs pinned {r['reference']} "
                  f"({float(r['ratio']) * 100:.0f}%), as of {r['date']}{stale}")
        closed = [r for r in rows if r["event"] in ("open", "clear")]
        if closed:
            print("\nevery state the record has ever held:")
            for r in closed:
                print(f"  {r['date']}  {r['line']:22} {r['event']:5} {r['direction']:4} "
                      f"ratio {r['ratio']}")
        return 0
    collect._write_rows(OUT, HEADER, rows)
    events = sum(1 for r in rows if r["event"] != "hold")
    print(f"drifts: {len(rows)} rows ({events} open/clear events) -> {OUT}")
    return 0



if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
