"""The level layer: is any strait STUCK in a broken state right now?

The scored lines answer a CHANGE question — "is today unusual against the
recent past?" — and a rolling baseline absorbs any persistent state: when the
Strait of Hormuz closed, a Hormuz-only change line read z=-0.47 on the closure
day, and by summer the closure WAS the baseline. The founding question ("is the
world actually more disordered?") is partly a LEVEL question, and this is the
smallest honest answer to it this repo has found.

THE RULE (five parameters, no free lunch hidden in them):
  * reference: the median of a strait's transits over days t-365..t-60,
    requiring >=30 observations and a median of >=5/day — small straits whose
    normal traffic is a handful of ships cannot produce a meaningful ratio;
  * breach: the 14-day trailing median at or below 0.5x the reference;
  * OPEN after 14 consecutive breach days — persistence is what separates a
    closure from a storm week; the reference is PINNED at the open, so the
    broken state cannot argue itself normal by becoming the baseline;
  * CLEAR when the trailing median recovers to 0.8x the PINNED reference.

Replayed against the full component record this opens three states across two
straits: Hormuz (2026-04-06, still open, running ~7% of its pinned 72/day) and
Kerch (2026-05-14, self-cleared 05-19; RE-opened 2026-07-26, still open at ~0%
of its pinned 12/day). Two states are open at once as of the latest served obs.
The other 26 straits produce zero breach days, including Taiwan through its July
AIS-gap artifact -- which was a gap-then-backfill in VALUES (present at 277->28
->401), never a missing row, so it opens no state.

WHAT THIS IS NOT. It is not a scored line: it has no z, no trembling flag, it
is counted in no summary, and nothing in the scoring path reads its output
(enforced by tests). It reads only the diagnostic component record and writes
``data/levels.csv``, which is DERIVED — recomputed from scratch on every run,
so it needs no forward-only protocol of its own; the record it derives from
has one. It is not mirrored to the dashboard.

    python tools/level_layer.py            # recompute data/levels.csv
    python tools/level_layer.py --report   # print the states currently open
"""
import os
import statistics
import sys
from bisect import bisect_left
import datetime
from datetime import date as _date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect

REF_WINDOW = (365, 60)   # reference: median over days t-365..t-60
REF_MIN_OBS = 30         # ...requiring at least this many observations
REF_MIN_RATE = 5.0       # ...and a median of at least this many transits/day
TRAIL_DAYS = 14          # trailing median window
OPEN_RATIO = 0.5         # breach: trailing median <= this share of reference
OPEN_PERSIST = 14        # consecutive breach days before a state opens
CLEAR_RATIO = 0.8        # clear: trailing median back to this share of PINNED
STALE_DAYS = 1           # an open state whose component stopped arriving says so

SOURCE = os.path.join(collect.COMPONENTS, "chokepoint_breadth.csv")
OUT = os.path.join(collect.DATA, "levels.csv")
HEADER = ["date", "component", "event", "trail_median", "reference", "ratio"]


def walk(series):
    """Level events for one component: [(date, event, trail, ref, ratio)].

    ``series`` is [(date, value)] oldest-first. Events are ``open``/``hold``/
    ``clear``; ``hold`` is emitted daily while a state stays open, so the file
    answers "what is broken TODAY" with a row, not with an absence.

    Dates are unique and sorted, so every calendar window is a contiguous
    slice found by bisect over the ordinals — this runs daily in CI and must
    not grow quadratically with the record.
    """
    ords = [_date.fromisoformat(d).toordinal() for d, _ in series]
    values = [v for _, v in series]
    out = []
    breach_run = 0
    pinned = None
    for i, (date, _) in enumerate(series):
        ord_today = ords[i]
        trail = values[bisect_left(ords, ord_today - TRAIL_DAYS + 1):i + 1]
        trail_median = statistics.median(trail)

        if pinned is None:
            ref_vals = values[bisect_left(ords, ord_today - REF_WINDOW[0]):
                              bisect_left(ords, ord_today - REF_WINDOW[1] + 1)]
            if len(ref_vals) < REF_MIN_OBS:
                breach_run = 0
                continue
            ref = statistics.median(ref_vals)
            if ref < REF_MIN_RATE:
                breach_run = 0
                continue
            if trail_median <= OPEN_RATIO * ref:
                breach_run += 1
                if breach_run >= OPEN_PERSIST:
                    pinned = ref
                    out.append((date, "open", trail_median, pinned,
                                trail_median / pinned))
            else:
                breach_run = 0
        else:
            if trail_median >= CLEAR_RATIO * pinned:
                out.append((date, "clear", trail_median, pinned,
                            trail_median / pinned))
                pinned = None
                breach_run = 0
            else:
                out.append((date, "hold", trail_median, pinned,
                            trail_median / pinned))
    return out


def compute():
    """All level events across every component, sorted by (date, component)."""
    by_component = {}
    for r in collect._read_rows(SOURCE):
        by_component.setdefault(r["component"], []).append(
            (r["date"], float(r["value"])))
    rows = []
    for component, series in by_component.items():
        series.sort()
        for date, event, trail, ref, ratio in walk(series):
            rows.append({"date": date, "component": component, "event": event,
                         "trail_median": f"{trail:g}", "reference": f"{ref:g}",
                         "ratio": f"{ratio:.3f}"})
    rows.sort(key=lambda r: (r["date"], r["component"]))
    return rows


def open_states(rows, key):
    """``(open_now, opened)`` — replay open/hold/clear rows into current states.

    Shared with the drift layer: the two detectors calibrate differently and
    deliberately keep separate ``walk`` functions, but replaying their event
    rows into "what is open right now" is one mechanism, and the day it was
    two, only one of them learned to disclose staleness.
    """
    open_now, opened = {}, {}
    for r in rows:
        if r["event"] == "open":
            opened[r[key]] = r["date"]
            open_now[r[key]] = r
        elif r["event"] == "hold":
            open_now[r[key]] = r
        else:
            open_now.pop(r[key], None)
    return open_now, opened


def stale_note(newest, last, gone_days=None):
    """The NO LONGER SERVED banner, or "" while the input is still arriving.

    A state cannot clear if the thing it watches stops being served, and a
    frozen open state reads exactly like one still being observed. Hormuz left
    PortWatch's panel on 2026-07-24 with its state open; the same exposure
    exists for any drifted line whose source dies.
    """
    if not last:
        return ""
    gone = (datetime.date.fromisoformat(newest)
            - datetime.date.fromisoformat(last)).days
    if gone <= STALE_DAYS:
        return ""
    return (f"  [NO LONGER SERVED: last seen {last}, {gone} observation days ago "
            f"— this state cannot clear because nothing is watching it]")


def last_seen():
    """``(newest_date_in_file, {component: its own newest date})``.

    A state cannot clear if its component stops being served, and a stale open
    state reads exactly like a state still being watched. The Strait of Hormuz
    stopped appearing in PortWatch's panel on 2026-07-24 while its state was
    open — so the report has to distinguish "still observed broken" from "we
    stopped being able to look".
    """
    newest, per_component = "", {}
    for r in collect._read_rows(SOURCE):
        newest = max(newest, r["date"])
        name = r["component"]
        per_component[name] = max(per_component.get(name, ""), r["date"])
    return newest, per_component


def main(argv):
    rows = compute()
    if "--report" in argv:
        newest, seen = last_seen()
        open_now, opened = open_states(rows, "component")
        if not open_now:
            print("no state is open")
        for component, r in sorted(open_now.items()):
            stale = stale_note(newest, seen.get(component, newest))
            print(f"OPEN {component}: since {opened[component]}, "
                  f"trailing {r['trail_median']} vs pinned {r['reference']} "
                  f"({float(r['ratio']) * 100:.0f}%), as of {r['date']}{stale}")
        return 0
    collect._write_rows(OUT, HEADER, rows)
    events = sum(1 for r in rows if r["event"] != "hold")
    print(f"levels: {len(rows)} rows ({events} open/clear events) -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
