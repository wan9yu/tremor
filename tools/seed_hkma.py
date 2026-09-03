"""One-off: give hkma_aggr_balance the baseline it launched without.

The line went live cold on 2026-07-23 and holds 20 unique observations against a
``normalize.WINDOW`` of 90. Its siblings were all seeded; this one never was. The
cost is measured, not stylistic: on 2026-08-09 the cold window put Qn at 32.20
where the seeded window puts it at 112.99, so the same reading scored 19.223
instead of 6.186 — a real move, judged by a scale 3.5x too narrow to know what
this series normally does.

Honest by construction, the same four ways ``seed_portwatch.py`` is:
  * Only real published observations are written. Nothing is interpolated.
  * Each seeded row is judged by the SAME ``normalize.judge`` the live collector
    uses, replayed strictly in order against only the rows already emitted, so
    no row is ever judged against readings from its own future.
  * Row dates follow the live rule, via the source's own
    ``hkma_aggr_balance.PUBLICATION_LAG_DAYS``, so a seeded row and a live row
    mean the same thing.
  * Every seeded row says so in ``source_note``. These were computed
    retroactively; they were never live detections.

THE RANGE STOPS AT THE DAY BEFORE THE LINE LAUNCHED, and that boundary is the
whole safety argument. ``seedlib.merge`` rule 3 drops an import that lands on a
published first-occurrence or dark row, but an import landing on a published
STALE-REPUBLISH row wins the date and rewrites it. Ending at 2026-07-22 means no
import can reach either branch: every seeded row lands on a date no live row
holds, and the one observation a live row does hold (2026-07-22, carried by row
2026-07-23) is skipped by rule 2. The published record is therefore untouchable
by this tool by construction, not by care.

EVERY observation lost to a dark day since launch is left lost. No count is given
here because the outage is ongoing and any number rots overnight; the rule is
what holds. Recovering them would mean importing onto dates the published record
already occupies. Under the lag mapping this tool installs they all land on
published DARK rows and are dropped, overwriting nothing — measured, 0 rows
changed. Under seedlib's DEFAULT identity mapping three of them (08-10, 08-17,
08-24) would instead land on stale-republish rows and REWRITE them — measured, 3
rows changed. That is the hazard this tool's ``row_date`` avoids, and it is why
the mapping is a safety control and not a cosmetic one.

THE PAYLOAD IS COMMITTED, NOT FETCHED. ``data/archive/hkma_seed_fetch.csv`` holds
the 96 observations this seed was built from, and the tool reads them rather than
calling the API. That is not a cache: the HKMA closing balance is a settled
official statistic that has never been observed to revise (checked across 20
observation dates), so re-fetching could only ever return the same numbers, while
the endpoint itself fails in phases of tens of minutes. The committed payload IS
the provenance. It was obtained once with a single request, recorded here so it
can be reproduced by hand:

    GET .../daily-figures-interbank-liquidity
        ?choose=end_of_date&from=2026-03-01&to=2026-07-22
        &fields=end_of_date,closing_balance
        &sortby=end_of_date&sortorder=asc&pagesize=200
    -> HTTP 200, 9.16s, 5,197 bytes, 96 records

Run from the repo root:
    python tools/seed_hkma.py --dry-run   # report what it would write
    python tools/seed_hkma.py             # archive, seed, re-judge
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import seedlib
import collect
from fetchers import hkma_aggr_balance as hkma

# The day before the line's first published row. See the module docstring: this
# single number is what keeps the seed off the published record.
SEED_TO = "2026-07-22"

_PAYLOAD = os.path.join(collect.DATA, "archive", "hkma_seed_fetch.csv")


def _row_date(obs):
    """The row an observation would have been collected on."""
    return (datetime.date.fromisoformat(obs)
            + datetime.timedelta(days=hkma.PUBLICATION_LAG_DAYS)).isoformat()


def history():
    """[(obs_date, value)] oldest-first, from the payload committed with this tool."""
    rows = [(r["obs_date"], float(r["closing_balance"]))
            for r in collect._read_rows(_PAYLOAD)]
    if not rows:
        print(f"  FAILED — no observations in {os.path.relpath(_PAYLOAD)}")
        return None
    print(f"  payload: {len(rows)} observations {rows[0][0]}..{rows[-1][0]}")
    return rows


def _note(obs, value):
    """The live fetcher's own wording, marked as an import."""
    return f"{hkma.NOTE} {value:.0f} HK$m ({obs}){seedlib.IMPORT_MARK}"


def main(argv):
    dry = "--dry-run" in argv
    print(f"seeding {hkma.LINE} through {SEED_TO}" + (" (dry run)" if dry else ""))
    rows = history()
    if rows is None:
        return 1
    late = [obs for obs, _ in rows if obs > SEED_TO]
    if late:
        print(f"  REFUSED — {len(late)} observations after {SEED_TO}; the boundary "
              f"is what keeps this seed off the published record.")
        return 1
    seedlib.run_seed(hkma, rows, _note, dry=dry, row_date=_row_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
