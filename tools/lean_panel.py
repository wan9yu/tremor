"""Serve a same-day machine lean for a firing tier-1 line.

A tier-1 line that trembles in its own alarm direction is shown on the
dashboard as a bare resonance=1 -- correct, but silent on the one question an
operator asks next: is this a real event, or a measurement artifact? For
net_outages, tools/reconcile_net_outages.py already answers a version of that
question live against IODA (the common-mode signature, R23/R27) -- but it is a
ROUND-TIME reconciliation tool, run by a human, never wired to the dashboard.

This reporter is the served version of that answer. It reads the tier-1 line
CSVs and data/summary.csv and writes docs/data/leans.csv, a presentation view
for the GitHub Pages dashboard (task 2, separate, renders it). Like
tools/stuck_panel.py, it lives outside the scoring path -- collect.py and
core/normalize.py never name it -- and it is recomputed from scratch every
run, so it carries no forward-only protocol of its own; the record it derives
from has one. It never writes a scored line, the summary, or a verdict, and
it is served BY THE REPORTER, never through collect.MIRRORED.

Collection-Day-Risk: NONE. This runs in daily.yml's post-commit derive step,
after the day is already safely pushed, and it must never be able to redden
that step: reconcile_net_outages.py's own docstring already logs URLError /
SSLEOFError as an intermittent IODA symptom, so every network call here is
wrapped to degrade to lean="unavailable" on ANY exception, and main() itself
never raises -- see _classify and main() below.

    python tools/lean_panel.py    # rebuild docs/data/leans.csv
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # tools/, for reconcile_net_outages
sys.path.insert(0, ROOT)    # repo root, for collect's shared CSV helpers
import collect
import reconcile_net_outages

SUMMARY = os.path.join(ROOT, "data", "summary.csv")
OUT = os.path.join(ROOT, "docs", "data", "leans.csv")
HEADER = ["date", "line", "lean", "evidence"]

# Tier-1 lines, read off collect.LINES the same way collect.py itself decides
# tier (TIER absent means 1) -- so a future promotion or demotion is picked
# up here without a second list to keep in sync.
TIER1 = [mod for mod in collect.LINES if getattr(mod, "TIER", 1) == 1]


def build_panel(summary_rows, line_rows_by_id, tier1, classify):
    """Timeline rows for the machine-lean panel, oldest-first.

    ``summary_rows`` are ``data/summary.csv`` rows -- only their ``date``
    column is used, as the set of committed collection days to walk. That is
    what keeps the walk to the live daily record: a tier-1 line's own CSV
    also carries an archive-imported backfill (years of history scored
    retroactively to seed its baseline) that predates summary.csv and has no
    committed day of its own, so a row whose date summary.csv never recorded
    is never even looked up. ``line_rows_by_id`` maps each tier-1 line's id
    to its own ``data/<line>.csv`` rows. ``tier1`` is the tier-1 modules
    (each carrying ``.LINE`` and ``.ANOMALY_DIRECTION``) -- a line the caller
    leaves out of this list is never consulted, tier-1 or not.

    For every committed day, for every line in ``tier1`` trembling that day
    IN ITS OWN alarm direction (``collect.counts_as_tremble`` -- the one home
    for that predicate; see its docstring), one row is emitted by calling
    ``classify(line, obs_date)``. ``obs_date`` is the row's own settled-window
    date, falling back to the collection date when the row carries none.

    ``classify`` never touches the network here -- this is the pure,
    gate-tested half of the reporter; the live IODA fetch lives only in
    ``main()``'s ``_classify``, so this stays testable with synthetic rows
    and a stub.
    """
    rows_by_date = {
        mod.LINE: {r["date"]: r for r in line_rows_by_id.get(mod.LINE, [])}
        for mod in tier1
    }
    out = []
    for date in sorted({r["date"] for r in summary_rows}):
        for mod in tier1:
            row = rows_by_date[mod.LINE].get(date)
            if row is None or not collect.counts_as_tremble(row, mod):
                continue
            obs_date = row.get("obs_date") or date
            lean, evidence = classify(mod.LINE, obs_date)
            out.append({"date": date, "line": mod.LINE, "lean": lean, "evidence": evidence})
    return out


def _classify(line_id, obs_date):
    """The real classify(): only net_outages has a machine classifier.

    tools/reconcile_net_outages.py's common-mode signature (R23/R27) is pure
    and unit-tested (tests/test_reconcile_common_mode.py); only the fetch
    that feeds it is network. IODA is intermittently flaky (URLError,
    SSLEOFError -- reconcile_net_outages.py's own docstring), so the fetch
    and the classification are both wrapped: ANY exception here degrades to
    "unavailable" rather than propagating, because a network flake must
    never be mistaken for a verdict, and must never reach main() as a raise.
    """
    if line_id != "net_outages":
        return "unavailable", "no machine classifier for this line"
    try:
        events = reconcile_net_outages._fetch_events(obs_date)
        cm = reconcile_net_outages.classify_common_mode(events)
    except Exception as e:
        return "unavailable", type(e).__name__
    if cm["verdict"] == "common-mode":
        evidence = (f"{cm['sync_ping_only']}/{cm['sync_batch']} synchronized "
                    f"ping-slash24-only, {cm['corroborated']}/{cm['ping_countries']} corroborated")
        return "common-mode", evidence
    evidence = (f"batch {cm['sync_batch']}, "
                f"{cm['corroborated']}/{cm['ping_countries']} corroborated")
    return "ok", evidence


def main():
    try:
        summary_rows = collect._read_rows(SUMMARY)
        line_rows_by_id = {
            mod.LINE: collect._read_rows(os.path.join(collect.DATA, mod.LINE + ".csv"))
            for mod in TIER1
        }
        rows = build_panel(summary_rows, line_rows_by_id, TIER1, _classify)
        collect._write_rows(OUT, HEADER, rows)
        latest = rows[-1]["date"] if rows else None
        n_now = sum(1 for r in rows if r["date"] == latest) if latest else 0
        print(f"lean panel: {len(rows)} row(s), {n_now} firing tier-1 line(s) on {latest} -> {OUT}")
    except Exception as e:
        # NEVER-FAIL: this is the post-commit derive step; the day is already
        # safely pushed, and nothing presentational may cost it a red run.
        # Whatever OUT already held (or nothing, on a first run) is left in
        # place rather than risk writing a half-built file.
        print(f"lean panel: FAILED ({type(e).__name__}: {e}) -- leaving prior {OUT} in place")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
