"""Seed stablecoin_peg from Bitstamp's full daily history (keyless).

USDC/USD reaches the 2023-03 SVB depeg (settled close $0.9685) and USDT/USD the
2022-05 UST/Luna sag; both run on Bitstamp back to ~2021. The seeded reading is
the per-day worst deviation-from-$1 across the two pairs, in bp — the exact
measure the live fetcher writes forward, off the same endpoint, so history and the
live tail are one series. Re-runnable and idempotent (see
tools/seedlib.rerun_is_safe); never restore the pre-seed archive by hand.

    python tools/seed_stablecoin.py [--dry]
"""
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # repo root, for collect / fetchers
sys.path.insert(0, _HERE)                    # tools/, for seedlib

import seedlib
from fetchers import stablecoin_peg as sp

_START = int(datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc).timestamp())


def _full_history(pair):
    """Every daily ``date -> close`` for a pair, paged forward from 2020."""
    by_date = {}
    cursor = _START
    while True:
        page = sp.candles(pair, limit=1000, start=cursor)
        if not page:
            break
        for day, close, _low in page:
            by_date[day] = close
        nxt = int(datetime.datetime.fromisoformat(page[-1][0])
                  .replace(tzinfo=datetime.timezone.utc).timestamp()) + 86400
        if nxt <= cursor:   # no forward progress -> reached the present
            break
        cursor = nxt
    return by_date


def history():
    """``[(date, worst-dev-bp)]`` oldest-first across USDC + USDT."""
    closes = {name: _full_history(pair) for name, pair in sp.PAIRS.items()}
    days = sorted(set().union(*(c.keys() for c in closes.values())))
    out = []
    for day in days:
        devs = [sp.dev_bp(closes[name][day]) for name in sp.PAIRS if day in closes[name]]
        if devs:
            out.append((day, round(max(devs), 1)))
    return out


def import_note(obs, value):
    return (f"Bitstamp settled daily close, worst {value:.1f}bp from $1"
            + seedlib.IMPORT_MARK)


def main(argv):
    hist = history()
    print(f"stablecoin_peg: pulled {len(hist)} daily observations "
          f"{hist[0][0]}..{hist[-1][0]} from Bitstamp")
    seedlib.run_seed(sp, hist, import_note, dry="--dry" in argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
