"""One-off: restore the published rows the first FRED seed dropped.

The 2026-08-02 seed rebuilt credit_spread, em_corp_oas and euro_hy_spread as
one-row-per-observation series. In doing so it deleted 26 previously committed
rows across the three lines — every dark day (including credit_spread's
2026-07-16, which data/summary.csv still counts, leaving the summary
irreconcilable with the line files), every stale republish after the first, and
it let an archive observation collide with a published row at 2026-07-14. The
mistake is recorded in annotations.csv (2026-08-03 correction row); this tool
is the repair.

ENTIRELY OFFLINE — it must not, and does not, touch FRED. The full observation
series is reconstructed from the seeded file itself (every observation appears
in it exactly once) and the published live rows come from the _preseed archives
plus any rows collected since the seed. The corrected merge rule lives in
seedlib.merge, which the seeders themselves now use, so this class of loss
cannot recur on the queued polar_temp and gnss seeds.

Protocol as ever: the current (broken) files are archived as
``<line>_seed1.csv`` before being replaced; nothing is silently rewritten.

    python tools/repair_fred_seed.py --dry-run
    python tools/repair_fred_seed.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect
import seedlib

from fetchers import credit_spread, em_oas, euro_hy_spread

LINES = [
    (credit_spread, "BAMLH0A0HYM2", "OAS"),
    (em_oas, "BAMLEMCBPIOAS", "OAS"),
    (euro_hy_spread, "BAMLHE00EHYIOAS", "OAS"),
]


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def repair(mod, series_id, label, dry):
    line = mod.LINE
    current = _read(os.path.join(collect.DATA, line + ".csv"))
    preseed = _read(os.path.join(collect.DATA, "archive", f"{line}_preseed.csv"))
    if not current or not preseed:
        print(f"  {line}: missing current or preseed file — SKIPPED")
        return False

    # The observation series, reconstructed offline: first occurrence per
    # observation across the seeded file, in observation order.
    series = {}
    for r in current:
        obs = r.get("obs_date")
        if obs and r.get("raw_value") and obs not in series:
            series[obs] = float(r["raw_value"])
    history = sorted(series.items())

    # The published live rows: everything in the preseed archive, plus rows
    # collected after the seed ran (their notes carry no import mark).
    last_preseed = max(r["date"] for r in preseed)
    live = preseed + [r for r in current
                      if r["date"] > last_preseed
                      and seedlib.IMPORT_MARK not in r.get("source_note", "")]

    def import_note(obs, value):
        return f"FRED {series_id} {label} {obs}{seedlib.IMPORT_MARK}"

    plan, dropped = seedlib.merge(history, live, import_note)
    print(f"  {line}: {len(history)} observations, {len(live)} published live "
          f"rows -> {len(plan)} merged rows ({len(current)} before)")
    for d in dropped:
        print(f"    note: {d}")
    if dry:
        return True

    seedlib.archive_current(line, "seed1")
    out = seedlib.score_series(plan, mod)
    collect.write_line(line, out)

    dates = [r["date"] for r in out]
    assert len(dates) == len(set(dates)), "duplicate dates survived the merge"
    restored = {r["date"] for r in live} - {r["date"] for r in current}
    print(f"    -> restored dates: {sorted(restored)}")
    print(f"    -> {sum(1 for r in out if r['z_score'])} scored, "
          f"{sum(int(r['trembling']) for r in out)} trembles, "
          f"{sum(1 for r in out if r['status'] == 'dark')} dark, "
          f"{sum(1 for r in out if r['status'] == 'stale')} stale")
    return True


def main(argv):
    dry = "--dry-run" in argv
    print("repairing the FRED seed collateral" + (" (dry run)" if dry else "") + "\n")
    ok = all([repair(mod, sid, label, dry) for mod, sid, label in LINES])
    print("\ndone" if ok else "\nFAILED for at least one line")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
