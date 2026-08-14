"""Serve the level layer's open-state count as a dashboard panel.

The scored ``chokepoint_breadth`` line is a SUM over 28 straits, and a sum cannot
see one or two small straits go silent: a full simultaneous closure of the Strait
of Hormuz and Kerch Strait moves the 28-strait total ~1 z, about a third of the
way to its own -3z alarm (radar.md round 12). The level layer already detects what
the sum cannot -- it holds a per-strait state open against a pinned pre-event
reference -- but its output is diagnostic, unscored, and DELIBERATELY firewalled
from the scoring path (tests/test_level.py, tests/test_side_channel.py): the moment
the scorer reads it, a diagnostic file becomes an input to a verdict.

This reporter is the OTHER side of that firewall. It reads the derived
``data/levels.csv`` and writes ``docs/data/stuck.csv``, a presentation view served
to the GitHub Pages dashboard. It lives outside the scoring path -- collect.py and
core/normalize.py never name it -- and, like the rendered charts, it is recomputed
from scratch every run, so it carries no forward-only protocol of its own; the
record it derives from has one. It never writes a scored line, the summary, or a
verdict, and it is served BY THE REPORTER, never through collect.MIRRORED.

    python tools/stuck_panel.py    # rebuild docs/data/stuck.csv from data/levels.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import level_layer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = os.path.join(ROOT, "data", "levels.csv")
OUT = os.path.join(ROOT, "docs", "data", "stuck.csv")
HEADER = ["date", "component", "since", "pct", "stale"]
OPEN_EVENTS = ("open", "hold")


def build_panel(level_rows, stale_now=frozenset()):
    """Timeline rows for the stuck-strait panel, oldest-first.

    ``level_rows`` are ``data/levels.csv`` rows (date, component, event, ...,
    ratio). One output row per (date, strait) for every day a strait is OPEN,
    carrying the date its state opened and its trailing traffic as a whole-number
    percentage of the pinned reference. Grouping the output by date gives the
    daily count of straits stuck quiet -- the number the 28-strait sum cannot
    show. ``stale_now`` is the set of components whose source stopped arriving
    while their state was open; the flag is set only on the most recent date, the
    one day it actually describes.
    """
    rows = sorted(level_rows, key=lambda r: (r["date"], r["component"]))
    latest = rows[-1]["date"] if rows else None
    opened = {}
    out = []
    for r in rows:
        comp, event, date = r["component"], r["event"], r["date"]
        if event == "open":
            opened[comp] = date
        elif event == "clear":
            opened.pop(comp, None)
            continue
        if event not in OPEN_EVENTS:
            continue
        stale = "1" if (date == latest and comp in stale_now) else ""
        out.append({"date": date, "component": comp,
                    "since": opened.get(comp, date),
                    "pct": round(float(r["ratio"]) * 100), "stale": stale})
    return out


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    level_rows = _read(LEVELS)
    # Staleness: which currently-open straits stopped being served (dropped out of
    # PortWatch's panel while their state was open, as Hormuz did on 2026-07-24).
    # Reuses the level layer's own last-seen bookkeeping so the two cannot disagree.
    stale_now = set()
    if level_rows:
        newest, seen = level_layer.last_seen()
        open_now, _ = level_layer.open_states(level_rows, "component")
        for comp in open_now:
            if level_layer.stale_note(newest, seen.get(comp, newest)):
                stale_now.add(comp)
    rows = build_panel(level_rows, stale_now)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    latest = rows[-1]["date"] if rows else None
    n_now = sum(1 for r in rows if r["date"] == latest)
    print(f"stuck panel: {len(rows)} rows, {n_now} strait(s) open now -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
