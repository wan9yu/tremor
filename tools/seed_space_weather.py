"""Seed space_weather from the GFZ Potsdam definitive Kp archive (keyless).

GFZ Potsdam (the index's official issuer) distributes every 3-hourly Kp since
1932-01-01 as one keyless text file, CC BY 4.0. Each line is one day carrying its
eight 3-hourly Kp values (columns 8-15); the seeded reading is that day's MAXIMUM,
the exact measure the live SWPC fetcher writes forward — history and the live tail
are one series, aggregated by this same module's daily_max / settled.

The seed starts at 2022-07-27 to ALIGN with gnss_interference's own history start:
this line's whole purpose is to disambiguate gnss (and grid_frequency), and a
shared window makes that day-for-day comparison possible from the first scored row
rather than after a fresh warm-up. The full 1932-> archive is available if a deeper
baseline is ever wanted; 2022-> is ~1,490 days, plenty for a mature 90-day window.

Re-runnable and idempotent (see tools/seedlib.rerun_is_safe); never restore the
pre-seed archive by hand.

    python tools/seed_space_weather.py [--dry]
"""
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # repo root, for collect / fetchers
sys.path.insert(0, _HERE)                    # tools/, for seedlib

import requests

import seedlib
from core import useragent
from fetchers import space_weather as sw

_START = "2022-07-27"  # align with gnss_interference's in-repo history start
_ARCHIVE = "https://www-app3.gfz-potsdam.de/kp_index/Kp_ap_Ap_SN_F107_since_1932.txt"


def parse_archive(text):
    """[(date, kp)] 3-hourly pairs from the GFZ since-1932 file.

    Comment lines start with '#'. A data row is whitespace-separated:
    ``YYYY MM DD days days_m Bsr dB Kp1..Kp8 ap1..ap8 Ap SN F10.7obs F10.7adj D``
    — the eight Kp columns are fields 7..14 (zero-based). Each is emitted as a
    (date, kp) pair, so the shared ``sw.daily_max`` reduces them exactly as it
    reduces the live SWPC 3-hourly stream. Rows before _START are skipped cheaply.
    A field that will not parse is skipped, never fabricated.
    """
    pairs = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 15 or not (f[0].isdigit() and f[1].isdigit() and f[2].isdigit()):
            continue
        date = f"{f[0]}-{f[1]}-{f[2]}"
        if date < _START:
            continue
        for kp in f[7:15]:
            try:
                pairs.append((date, float(kp)))
            except ValueError:
                continue
    return pairs


def history():
    """``[(date, daily-max-Kp)]`` oldest-first, every complete UTC day since _START.

    Uses ``sw.settled(sw.daily_max(...))`` — the SAME aggregation and settle rule
    the live fetcher applies — so the seed never records a still-forming day and
    the live tail picks up where the seed stops, one series.
    """
    text = requests.get(_ARCHIVE, headers=useragent.HEADERS, timeout=60).text
    days = sw.settled(sw.daily_max(parse_archive(text)))
    return [(day, round(kp, 3)) for day, kp in sorted(days.items())]


def import_note(obs, value):
    return f"GFZ Potsdam planetary Kp daily max {value:g} on {obs}" + seedlib.IMPORT_MARK


def main(argv):
    hist = history()
    print(f"space_weather: pulled {len(hist)} days {hist[0][0]}..{hist[-1][0]} "
          f"from the GFZ Potsdam Kp archive")
    seedlib.run_seed(sw, hist, import_note, dry="--dry" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
