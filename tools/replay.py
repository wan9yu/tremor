"""Recompute the whole record under today's rules and report where it diverges.

tremor never rewrites history: a methodology change applies forward only, so a
row keeps whatever verdict the code of its day produced. That is the right rule —
it is what stops the record from being quietly improved after the fact — but it
has a consequence that bit once already. ``data/summary.csv`` is not a time
series of one measurement; it is an append-only log of what several successive
algorithms said on the day each ran. Any statistic of the form "over N days, X
happened M times" therefore mixes methodologies and is not a statement about the
world.

The fix is not to rewrite. It is to make the record RE-DERIVABLE, so both
questions can be answered separately and honestly:

  * what did we say at the time?  -> the committed CSVs, untouched
  * what would we say now?        -> this tool

Run it and it replays every line through ``normalize.judge`` exactly as
``collect.score_row`` does, using only the rows that preceded each row, and
prints every date where today's rules disagree with what was published.

    python tools/replay.py            # summary of divergences
    python tools/replay.py --verbose  # every diverging row
    python tools/replay.py --check    # exit 1 if divergence exceeds the bound

The ``--check`` bound is deliberately loose: divergence is EXPECTED after a
forward-only change and is not a failure. It exists to catch the other thing —
a replay that diverges on rows written since the last methodology change, which
would mean the collector and the scorer have drifted apart.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect

# Rows written on or after this date should replay exactly: it is the date of the
# most recent change to scoring semantics (Qn + the no-RMS-fallback rule).
# Bump it when normalize.py's verdicts change, and say so in annotations.csv.
STABLE_SINCE = "2026-07-23"


def replay_line(mod):
    """[(date, published_row, replayed_row)] for one line, oldest first."""
    path = os.path.join(collect.DATA, mod.LINE + ".csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, published in enumerate(rows):
        raw = published.get("raw_value")
        replayed = collect.score_row(
            published["date"],
            float(raw) if raw not in (None, "") else None,
            "",                      # the note is not part of the verdict
            published.get("obs_date") or "",
            rows[:i],
            weekly_cycle=getattr(mod, "WEEKLY_CYCLE", False),
        )
        out.append((published["date"], published, replayed))
    return out


def _differs(published, replayed):
    """Only verdict fields count; source_note is prose and is not replayed."""
    for field in ("z_score", "trembling", "direction", "status"):
        if (published.get(field) or "") != (replayed.get(field) or ""):
            return True
    return False


def main(argv):
    verbose = "--verbose" in argv
    check = "--check" in argv

    total = diverged = recent_diverged = 0
    per_line = []
    counts_now = {}

    for mod in collect.LINES:
        rows = replay_line(mod)
        if not rows:
            continue
        bad = [(d, p, r) for d, p, r in rows if _differs(p, r)]
        recent = [d for d, _, _ in bad if d >= STABLE_SINCE]
        total += len(rows)
        diverged += len(bad)
        recent_diverged += len(recent)
        per_line.append((mod.LINE, len(rows), len(bad), len(recent)))
        for date, _, replayed in rows:
            if replayed["trembling"] == "1" and replayed["direction"] == mod.ANOMALY_DIRECTION \
                    and getattr(mod, "TIER", 1) == 1:
                counts_now.setdefault(date, []).append(mod.LINE)
        if verbose:
            for date, p, r in bad:
                print(f"  {mod.LINE:22} {date}  published z={p['z_score'] or '—':>7} "
                      f"t={p['trembling']} {p.get('status') or '—':<11}"
                      f"  ->  now z={r['z_score'] or '—':>7} t={r['trembling']} {r['status']}")

    print(f"{'line':22} {'rows':>6} {'diverge':>8} {'since ' + STABLE_SINCE:>18}")
    for line, n, bad, recent in per_line:
        flag = "  <-- DRIFT" if recent else ""
        print(f"{line:22} {n:>6} {bad:>8} {recent:>18}{flag}")
    print(f"{'TOTAL':22} {total:>6} {diverged:>8} {recent_diverged:>18}")

    with open(os.path.join(collect.DATA, "summary.csv"), newline="") as f:
        published = {r["date"]: int(r["trembling_count"] or 0)
                     for r in csv.DictReader(f)}
    disagree = [d for d in sorted(published)
                if published[d] != len(counts_now.get(d, []))]
    print(f"\nheadline: published reported a tremble on "
          f"{sorted(d for d in published if published[d] > 0)}")
    print(f"          today's rules give {sorted(counts_now)}")
    if disagree:
        print(f"          they disagree on {len(disagree)} of {len(published)} days: {disagree}")
        for d in disagree:
            print(f"            {d}: published {published[d]}, "
                  f"now {len(counts_now.get(d, []))} {counts_now.get(d, [])}")

    print(f"\nDivergence before {STABLE_SINCE} is EXPECTED — it is the forward-only rule "
          f"showing its seams,\nnot an error. Divergence AFTER it means the collector and "
          f"the scorer have drifted apart.")

    if check and recent_diverged:
        print(f"\nFAIL: {recent_diverged} rows written since {STABLE_SINCE} do not replay.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
