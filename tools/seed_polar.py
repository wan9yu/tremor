"""One-off: seed polar_temp from DMI's own per-year archive files.

The live fetcher reads the last row of meanT{year}_running.txt; the same
directory serves the same product for every year since 2019 — identical
format, identical climatology baseline, so the seeded anomaly is computed by
exactly the arithmetic the daily fetcher uses and the existing live rows
re-derive with zero delta.

WHY IT STOPS AT 2019: that is simply all the source serves today (checked, not
assumed — an earlier probe reported files back to 2017, and the directory now
lists 2019..2026 only). Deeper history exists elsewhere in other product
lineages with real discontinuities (the T511->T799 step alone shifts the mean
0.67K), so even if it reappears, one lineage is the honest cut. 2019 onward is
~2,700 observations — fifteen times the age cap the baseline actually uses.

Eight requests, one per year, politely spaced. Method as ever via seedlib:
published rows preserved, everything re-scored oldest-first, pre-seed file
archived.

    python tools/seed_polar.py --dry-run
    python tools/seed_polar.py
"""
import csv
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import collect
import seedlib
from core import arctic_clim
from fetchers import polar_temp

_FIRST_YEAR = 2019
_PAUSE_S = 2


def year_rows(year):
    """[(obs_date, anomaly)] for one DMI year file, or None on failure."""
    try:
        r = requests.get(polar_temp._URL.format(year=year),
                         headers=polar_temp._HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"    {year}: request failed ({type(e).__name__})")
        return None
    if r.status_code != 200 or len(r.text) < 40:
        print(f"    {year}: HTTP {r.status_code}, {len(r.text)} bytes")
        return None
    out = []
    for line in r.text.strip().splitlines():
        # 2023's file is comma-separated with a header; the rest are
        # whitespace-separated. Normalizing commas to spaces reads both.
        parts = line.replace(",", " ").split()
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
            try:
                obs = datetime.datetime.strptime(parts[0], "%Y%m%d").strftime("%Y-%m-%d")
                doy, temp_k = int(parts[1]), float(parts[2])
            except (ValueError, IndexError):
                continue
            out.append((obs, temp_k, round(temp_k - arctic_clim.normal_k(doy), 3)))
    return out


def main(argv):
    dry = "--dry-run" in argv
    this_year = datetime.datetime.now(datetime.timezone.utc).year
    print("seeding polar_temp from DMI per-year files"
          + (" (dry run)" if dry else "") + "\n")

    history, temps = [], {}
    for year in range(_FIRST_YEAR, this_year + 1):
        rows = year_rows(year)
        if not rows:  # a failed request AND an unparsed file both leave a hole
            print("  a year file failed or parsed empty — refusing a series "
                  "with a hole in it")
            return 1
        print(f"  {year}: {len(rows)} observations")
        for obs, temp_k, anomaly in rows:
            history.append((obs, anomaly))
            temps[obs] = temp_k
        time.sleep(_PAUSE_S)
    history.sort()

    path = os.path.join(collect.DATA, polar_temp.LINE + ".csv")
    live = []
    if os.path.exists(path):
        with open(path, newline="") as f:
            live = list(csv.DictReader(f))

    def import_note(obs, anomaly):
        return (f"DMI +80N {obs}: {temps[obs] - 273.15:.2f}°C, {anomaly:+.2f}°C vs "
                f"1958-2002 normal (context line, never counted)"
                + seedlib.IMPORT_MARK)

    plan, dropped = seedlib.merge(history, live, import_note)
    print(f"\n  {len(history)} archived observations {history[0][0]}..{history[-1][0]}; "
          f"{len(live)} live rows -> {len(plan)} merged rows")
    for d in dropped:
        print(f"    note: {d}")
    if dry:
        return 0

    seedlib.archive_current(polar_temp.LINE, "preseed")
    out = seedlib.score_series(plan)
    collect.write_line(polar_temp.LINE, out)
    print(f"  -> {len(out)} rows, {sum(1 for r in out if r['z_score'])} scored, "
          f"{sum(int(r['trembling']) for r in out)} trembles, "
          f"last status={out[-1]['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
