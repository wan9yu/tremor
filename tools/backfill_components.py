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

ADDING A DATE THE RECORD NEVER CAPTURED. The default path recovers the dates the
LINE recorded, and can therefore only fill a gap under an existing observation.
When the capture missed a day outright — the 2026-10-28..10-31 outage left
2026-10-18..10-21 with no line row at all — no line row exists to derive the day
from, so it has to be named:

    python tools/backfill_components.py --dates 2026-10-18,2026-10-25

That path MERGES: the days already in the file are read verbatim and only the
named dates are added, and the tool refuses to proceed if a named date is
already present (a backfill must never rewrite a captured day) or if any
existing date would change. Every other day stays byte-identical.
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
    if not os.path.exists(path):
        # loud and stated, not a bare traceback: the default path recovers the
        # days a line RECORDED, so a missing line file is a wrong invocation
        raise SystemExit(f"no line record at {path} — this path recovers the days "
                         f"a line recorded; name absent days with --dates=")
    try:
        with open(path, newline="") as f:
            return sorted({r["obs_date"] for r in csv.DictReader(f)
                           if r.get("obs_date") and r["raw_value"]})
    except OSError as e:
        raise SystemExit(f"cannot read {path}: {e}") from None


def fetch_range(service, field, name_field, start, end):
    """{obs_date: {strait: value}} for a date range, one page at a time.

    Goes through ``portwatch._query`` rather than calling ``requests`` directly,
    so a quota breach (the host answers HTTP 200 with an error body) is named and
    waited out instead of arriving as a feature list that happens to be empty —
    the failure mode that would otherwise look like "the source has no data for
    these days" and silently recover nothing.
    """
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
        payload, reason = portwatch._query(service, params)
        if payload is None:
            raise SystemExit(f"PortWatch: {reason} — nothing written")
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


def _components_path():
    return os.path.join(collect.COMPONENTS, chokepoint.LINE + ".csv")


def _existing_by_date():
    path = _components_path()
    if not os.path.exists(path):
        return {}
    out = {}
    for r in collect._read_rows(path):
        out.setdefault(r["date"], {})[r["component"]] = r["value"]
    return out


def add_dates(wanted_dates, dry):
    """Merge the named dates into the file; never touch a day already there.

    Returns a process exit code: 0 when the file was written (or ``--dry-run``),
    2 when the request was refused for a reason the operator must read.
    """
    existing = _existing_by_date()
    already = sorted(d for d in wanted_dates if d in existing)
    if already:
        print(f"REFUSED: {', '.join(already)} already in "
              f"data/components/{chokepoint.LINE}.csv — a capture is never rewritten")
        return 2
    print(f"backfilling {len(wanted_dates)} named date(s): {', '.join(wanted_dates)}")
    if dry:
        return 0
    got = fetch_range(chokepoint.SERVICE, chokepoint.FIELD, "portname",
                      wanted_dates[0], wanted_dates[-1])
    recovered = {d: got[d] for d in wanted_dates if d in got}
    missing = [d for d in wanted_dates if d not in got]
    if missing:
        print(f"REFUSED: the source served nothing for {', '.join(missing)} — "
              f"nothing written")
        return 2
    sizes = {len(c) for c in recovered.values()}
    if len(sizes) > 1:
        print(f"REFUSED: the recovered panel sizes differ {sorted(sizes)} — "
              f"a page was lost; nothing written")
        return 2
    rows = [{"date": obs, "component": name, "value": collect._fmt(value)}
            for obs, comps in recovered.items()
            for name, value in sorted(comps.items())]
    rows += [{"date": d, "component": c, "value": v}
             for d, comps in existing.items() for c, v in comps.items()]
    rows.sort(key=lambda r: (r["date"], r["component"]))
    # the merge must not move a single existing row (same date, same component,
    # same rendered value); only new dates may appear
    after = {}
    for r in rows:
        after.setdefault(r["date"], {})[r["component"]] = r["value"]
    for day, comps in existing.items():
        if after.get(day) != comps:
            print(f"REFUSED: the merge would change {day}; nothing written")
            return 2
    collect._write_rows(_components_path(), collect.COMPONENT_HEADER, rows)
    added = len(rows) - sum(len(c) for c in existing.values())
    print(f"added {len(recovered)} observation(s), {added} row(s); "
          f"{len(existing)} existing day(s) unchanged")
    return 0


def main(argv):
    dry = "--dry-run" in argv
    named = [a.partition("=")[2] for a in argv if a.startswith("--dates=")]
    if named and named[0]:
        wanted = [d.strip() for d in named[0].split(",") if d.strip()]
        for d in wanted:
            if not collect.is_strict_date(d):
                print(f"REFUSED: {d!r} is not YYYY-MM-DD")
                return 2
        return add_dates(sorted(wanted), dry)
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
