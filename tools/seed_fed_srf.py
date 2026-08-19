"""Seed fed_srf_takeup from the NY Fed markets API full history (keyless).

The Standing Repo Facility began operating 2021-07-28; one search call returns
every repo operation since. The seeded reading is the per-day TOTAL amount
accepted across that day's SRF ops, in $m — the exact measure the live fetcher
writes forward off the same endpoint, so history and the live tail are one series.
Every business day is kept, INCLUDING the ~61% that print exactly $0: a $0 day is
a real observation of the defended equilibrium (the facility operated, nobody
borrowed), and in anchored scale-mode it scores an honest z=0. Re-runnable and
idempotent (see tools/seedlib.rerun_is_safe); never restore the pre-seed archive
by hand.

    python tools/seed_fed_srf.py [--dry]
"""
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # repo root, for collect / fetchers
sys.path.insert(0, _HERE)                    # tools/, for seedlib

import seedlib
from fetchers import fed_srf_takeup as srf

_START = "2021-07-28"   # SRF inception


def history():
    """``[(operation_date, total-accepted-$m)]`` oldest-first, all complete days.

    Uses ``srf.settled_takeup`` — the SAME settle rule the live fetcher applies —
    so the seed never records a partial current day and the live tail picks up
    where the seed stops, one series. ``today`` is computed once (explicit UTC) and
    used for both the query bound and the settle boundary so they cannot diverge.
    """
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    takeup = srf.settled_takeup(srf.search(_START, today), today)
    return [(day, round(amt, 1)) for day, amt in sorted(takeup.items())]


def import_note(obs, value):
    return (f"NY Fed SRF total accepted {value:,.1f}$m on {obs}"
            + seedlib.IMPORT_MARK)


def main(argv):
    hist = history()
    print(f"fed_srf_takeup: pulled {len(hist)} operation days "
          f"{hist[0][0]}..{hist[-1][0]} from the NY Fed markets API")
    seedlib.run_seed(srf, hist, import_note, dry="--dry" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
