"""One-off: recover the per-strait breakdown this instrument threw away.

`chokepoint_breadth` has recorded 210 observations as a single 28-strait SUM.
The breakdown arrived in every one of those responses and was discarded. That is
why a 65% collapse at the Strait of Hormuz moved the recorded line by under 2%
and left nothing to go back to — the aggregation happened at capture, so no
later analysis could undo it.

For this line the loss is not yet permanent: IMF PortWatch still serves the
complete daily series back to 2019, so the resolution can be recovered by asking
again. That is not true of the other lines and will not be true of this one
forever, which is the argument for capturing components from now on rather than
relying on a source's goodwill.

Written to `data/components/chokepoint_breadth.csv`, keyed by the OBSERVATION
date (the day the transits happened), not the collection date. Diagnostic only:
no scoring code reads it, it is not mirrored to the dashboard, it changes no
verdict, and `tools/replay.py --check` must still pass after it runs.

    python tools/backfill_components.py            # recover and write
    python tools/backfill_components.py --dry-run  # report what it would fetch
"""
import csv
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect
from core import portwatch
from fetchers import chokepoint

# The service caps a response at 1000 features (maxRecordCount) and DOES support
# pagination — asking for more just truncates, silently. A 40-day chunk of 28
# straits is 1120 rows, so the first attempt at this lost 120 rows per chunk and
# produced days carrying 25 straits instead of 28. The tests caught it. Page
# explicitly and verify the panel is whole per date rather than trusting a count.
_CHUNK_DAYS = 30
_PAGE = 1000


def observation_dates(line):
    path = os.path.join(collect.DATA, line + ".csv")
    with open(path, newline="") as f:
        return sorted({r["obs_date"] for r in csv.DictReader(f)
                       if r.get("obs_date") and r["raw_value"]})


def fetch_range(service, field, name_field, start, end):
    """{obs_date: {strait: value}} for a date range, in one request."""
    import json

    import requests
    out, offset = {}, 0
    while True:
        params = {
            "where": f"date >= DATE '{start}' AND date <= DATE '{end}'",
            "outFields": f"date,{name_field},{field}",
            "resultRecordCount": _PAGE,
            "resultOffset": offset,
            "orderByFields": f"date,{name_field}",
            "f": "json",
        }
        r = requests.get(portwatch._BASE.format(svc=service), params=params,
                         headers=portwatch._HEADERS, timeout=60)
        if r.status_code != 200:
            break
        payload = r.json()
        features = payload.get("features") or []
        for feature in features:
            attrs = feature.get("attributes", {})
            day = portwatch._parse_date(attrs.get("date"))
            name, value = attrs.get(name_field), attrs.get(field)
            if day and name is not None and value is not None:
                out.setdefault(day.isoformat(), {})[str(name)] = float(value)
        if not payload.get("exceededTransferLimit") and len(features) < _PAGE:
            break
        offset += len(features)
        if not features:
            break
    return out


def main(argv):
    dry = "--dry-run" in argv
    dates = observation_dates(chokepoint.LINE)
    print(f"{chokepoint.LINE}: {len(dates)} observations to recover, "
          f"{dates[0]} .. {dates[-1]}")
    if dry:
        return 0

    start = datetime.date.fromisoformat(dates[0])
    end = datetime.date.fromisoformat(dates[-1])
    recovered, day = {}, start
    while day <= end:
        chunk_end = min(day + datetime.timedelta(days=_CHUNK_DAYS - 1), end)
        got = fetch_range(chokepoint.SERVICE, chokepoint.FIELD, "portname",
                          day.isoformat(), chunk_end.isoformat())
        recovered.update(got)
        print(f"  {day} .. {chunk_end}: {len(got)} days")
        day = chunk_end + datetime.timedelta(days=1)

    wanted = {d: recovered[d] for d in dates if d in recovered}
    missing = [d for d in dates if d not in recovered]
    rows = [{"date": obs, "component": name, "value": collect._fmt(value)}
            for obs, comps in wanted.items() for name, value in sorted(comps.items())]
    rows.sort(key=lambda r: (r["date"], r["component"]))
    collect._write_rows(os.path.join(collect.COMPONENTS, chokepoint.LINE + ".csv"),
                        collect.COMPONENT_HEADER, rows)

    straits = {r["component"] for r in rows}
    sizes = {len(c) for c in wanted.values()}
    print(f"\nrecovered {len(wanted)}/{len(dates)} observations, "
          f"{len(straits)} distinct straits, {len(rows)} rows")
    if len(sizes) > 1:
        print(f"  WARNING: observations carry differing panel sizes {sorted(sizes)} — "
              f"either the source changed its panel or a page was lost. "
              f"Do not use until resolved.")
    if missing:
        print(f"  not served by the source: {missing}")
    print(f"written to data/components/{chokepoint.LINE}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
