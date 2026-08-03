"""One-off: seed polar_temp from DMI's own per-year archive files.

The live fetcher reads the last row of meanT{year}_running.txt; the same
directory serves the same product for every year since 2019 — and this seeder
parses those files with the FETCHER'S OWN ``parse_rows``/``anomaly_c``, so the
seeded values are identical to what the live fetcher would have recorded by
construction, not by copy-paste. (That mattered immediately: DMI's 2023 file
is comma-separated where every other year is whitespace-separated, and a
format quirk now needs exactly one fix, not two.)

WHY IT STOPS AT 2019: that is simply all the source serves today (checked, not
assumed — an earlier probe reported files back to 2017, and the directory now
lists 2019..2026 only). Deeper history exists elsewhere in other product
lineages with real discontinuities (the T511->T799 step alone shifts the mean
0.67K), so even if it reappears, one lineage is the honest cut. 2019 onward is
~2,700 observations — fifteen times the age cap the baseline actually uses.

Eight requests, one per year, politely spaced; then ``seedlib.run_seed`` end
to end: published rows preserved, everything re-scored oldest-first, pre-seed
file archived.

    python tools/seed_polar.py --dry-run
    python tools/seed_polar.py
"""
import datetime
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import seedlib
from fetchers import polar_temp

_FIRST_YEAR = 2019
_PAUSE_S = 2


def year_rows(year):
    """[(obs_date, doy, temp_k)] for one DMI year file, or None on failure."""
    try:
        r = requests.get(polar_temp._URL.format(year=year),
                         headers=polar_temp._HEADERS, timeout=30)
    except requests.RequestException as e:
        print(f"    {year}: request failed ({type(e).__name__})")
        return None
    if r.status_code != 200 or len(r.text) < 40:
        print(f"    {year}: HTTP {r.status_code}, {len(r.text)} bytes")
        return None
    return polar_temp.parse_rows(r.text)


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
        for obs, doy, temp_k in rows:
            history.append((obs, polar_temp.anomaly_c(doy, temp_k)))
            temps[obs] = temp_k
        time.sleep(_PAUSE_S)
    history.sort()

    def import_note(obs, anomaly):
        return (f"DMI +80N {obs}: {temps[obs] - 273.15:.2f}°C, {anomaly:+.2f}°C vs "
                f"1958-2002 normal (context line, never counted)"
                + seedlib.IMPORT_MARK)

    seedlib.run_seed(polar_temp, history, import_note, dry=dry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
