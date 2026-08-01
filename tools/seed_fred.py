"""One-off: give the FRED-backed lines the history they could always have had.

Three lines read a FRED series that the keyless endpoint serves three years of,
and all three have been scoring against a few weeks of their own collection
instead. `euro_hy_spread` is the sharpest case: every one of its rows is
`warming-up` with an empty z, so the line has never produced a verdict at all.

The reason it went unseeded for six weeks was a wrong sentence in this repo —
`fetchers/credit_spread.py` asserted that fredgraph "serves a short rolling
window, so it cannot be used to rebuild history". It serves 787 observations back
to 2023-08-01: three years, six times the 180-day MAX_AGE_DAYS the baseline
actually uses. The docstring is corrected; this tool is the consequence.

Method, following the `vix` and PortWatch precedents:
  * every row is scored by ``collect.score_row`` — the same builder the daily
    collector uses — replayed strictly oldest-first against only the rows already
    emitted, so no row is ever judged against readings from its own future;
  * rows are dated by OBSERVATION, and seeded rows say so in ``source_note``:
    they were computed retroactively and were never live detections;
  * the existing live rows are re-scored into the new series and the old file is
    archived, exactly as the PortWatch v2 rebuild did. Nothing is silently
    rewritten in place.

RATE LIMITS ARE NOT ADVISORY HERE. fredgraph.csv sits behind bot management;
ten requests in twenty seconds black-holed a probing IP for over an hour and the
block spread across the FRED estate. This fetches each series ONCE and sleeps
between series. Do not run it from CI — locking out the runner stops collection.

    python tools/seed_fred.py --dry-run   # report what it would write
    python tools/seed_fred.py             # archive, seed, rescore
"""
import csv
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import collect
from core import fred

# One request per series, generously spaced. The probe that discovered the block
# was making roughly one request every two seconds.
_PAUSE_S = 30

SEEDS = [
    ("euro_hy_spread", "BAMLHE00EHYIOAS", "OAS"),
    ("em_corp_oas", "BAMLEMCBPIOAS", "OAS"),
    ("credit_spread", "BAMLH0A0HYM2", "OAS"),
]

IMPORT_MARK = " [archive import: scored retroactively, not a live reading]"


def series_history(series_id):
    """[(obs_date, value)] oldest-first from the keyless CSV, or None."""
    try:
        r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                         params={"id": series_id},
                         headers={"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"},
                         timeout=60)
    except requests.RequestException as e:
        print(f"    request failed: {type(e).__name__}")
        return None
    if r.status_code != 200 or not r.text.strip():
        print(f"    HTTP {r.status_code}, {len(r.text)} bytes — treating as blocked")
        return None
    out = []
    for row in r.text.strip().splitlines()[1:]:
        parts = row.split(",")
        if len(parts) >= 2 and parts[1] not in ("", ".", "NaN"):
            try:
                out.append((parts[0], float(parts[1])))
            except ValueError:
                continue
    return out


def live_rows(line):
    """Existing rows keyed by observation date, so the seed can absorb them."""
    path = os.path.join(collect.DATA, line + ".csv")
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {r["obs_date"]: r for r in csv.DictReader(f)
                if r.get("obs_date") and r["raw_value"]}


def seed(line, series_id, label, dry):
    history = series_history(series_id)
    if not history:
        print(f"  {line}: no history returned — SKIPPED, nothing written")
        return False
    existing = live_rows(line)
    print(f"  {line}: {len(history)} archived observations "
          f"{history[0][0]}..{history[-1][0]}; {len(existing)} live rows on file")
    if dry:
        return True

    src = os.path.join(collect.DATA, line + ".csv")
    archive = os.path.join(collect.DATA, "archive")
    os.makedirs(archive, exist_ok=True)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(archive, f"{line}_preseed.csv"))

    out = []
    for obs_date, value in history:
        # A day the instrument actually collected keeps its own row date and its
        # own note; the rest are archive imports. Either way the VERDICT is
        # recomputed here against the deeper baseline, which is the point.
        live = existing.get(obs_date)
        row_date = live["date"] if live else obs_date
        note = (live["source_note"] if live
                else f"FRED {series_id} {label} {obs_date}{IMPORT_MARK}")
        out.append(collect.score_row(row_date, value, note, obs_date, out))
    collect.write_line(line, out)

    scored = sum(1 for r in out if r["z_score"])
    trembles = sum(int(r["trembling"]) for r in out)
    print(f"    -> {len(out)} rows, {scored} scored, {trembles} trembles, "
          f"last status={out[-1]['status']}")
    return True


def main(argv):
    dry = "--dry-run" in argv
    print("seeding the FRED-backed lines"
          + (" (dry run)" if dry else "")
          + f"\n  one request per series, {_PAUSE_S}s apart — fredgraph is bot-managed\n")
    ok = True
    for i, (line, series_id, label) in enumerate(SEEDS):
        if i and not dry:
            time.sleep(_PAUSE_S)
        ok = seed(line, series_id, label, dry) and ok
    print("\ndone" if ok else "\nFAILED for at least one line — check before committing")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
