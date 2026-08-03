"""One-off: give the FRED-backed lines the history they could always have had.

Three lines read a FRED series that the keyless endpoint serves three years of,
and all three had been scoring against a few weeks of their own collection
instead. `euro_hy_spread` was the sharpest case: every one of its rows was
`warming-up` with an empty z, so the line had never produced a verdict at all.

The reason it went unseeded for six weeks was a wrong sentence in this repo —
`fetchers/credit_spread.py` asserted that fredgraph "serves a short rolling
window, so it cannot be used to rebuild history". It serves 787 observations back
to 2023-08-01: three years, six times the 180-day MAX_AGE_DAYS the baseline
actually uses. The docstring is corrected; this tool is the consequence.

Method: ``seedlib.run_seed`` end to end — the merge preserves every published
row (the first version of this tool keyed live rows by observation and
silently deleted 26 of them; annotations 2026-08-03 records the mistake,
tools/repair_fred_seed.py repaired it), and every row is re-scored strictly
oldest-first, so no row is ever judged against readings from its own future.
The pre-seed file is archived, never rewritten.

RATE LIMITS ARE NOT ADVISORY HERE. fredgraph.csv sits behind bot management;
ten requests in twenty seconds black-holed a probing IP for over an hour and
the block spread across the FRED estate. History comes through ``fred.series``
— the module's pacing applies — with a further long sleep between series. Do
not run this from CI; locking out the runner stops collection.

    python tools/seed_fred.py --dry-run   # report what it would write
    python tools/seed_fred.py             # archive, seed, rescore
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seedlib
from core import fred
from fetchers import credit_spread, em_oas, euro_hy_spread

# One request per series, generously spaced on top of core/fred.py's own
# per-request floor. The probe that discovered the block was making roughly
# one request every two seconds.
_PAUSE_S = 30

SEEDS = [
    (euro_hy_spread, "BAMLHE00EHYIOAS", "OAS"),
    (em_oas, "BAMLEMCBPIOAS", "OAS"),
    (credit_spread, "BAMLH0A0HYM2", "OAS"),
]


def seed(mod, series_id, label, dry):
    history = fred.series(series_id, timeout=60)
    if not history:
        print(f"  {mod.LINE}: no history returned — SKIPPED, nothing written")
        return False

    def import_note(obs, value):
        return f"FRED {series_id} {label} {obs}{seedlib.IMPORT_MARK}"

    seedlib.run_seed(mod, history, import_note, dry=dry)
    return True


def main(argv):
    dry = "--dry-run" in argv
    print("seeding the FRED-backed lines"
          + (" (dry run)" if dry else "")
          + f"\n  one request per series, {_PAUSE_S}s apart — fredgraph is bot-managed\n")
    ok = True
    for i, (mod, series_id, label) in enumerate(SEEDS):
        if i:
            time.sleep(_PAUSE_S)
        ok = seed(mod, series_id, label, dry) and ok
    print("\ndone" if ok else "\nFAILED for at least one line — check before committing")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
