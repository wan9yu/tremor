"""Reconciliation check for the net_outages settle (R23.1 Pending-review tripwire).

Settling to a completed D-1 window rests the artifact fix on one live data point
(2026-08-24 re-queried to 4). "~24h" is IODA's TYPICAL detection latency, not a
bound: on a slow-pipeline day a window read ~24.4h after its end could still be
inflating (a smaller 08-24 sibling) or, worse, UNDER-counting a real onset. So this
re-queries IODA's settled window for recorded rows and compares to the stored raw.
A mismatch large enough to flip a verdict reopens the D-2 question with data.

Live network, so it is a ROUND-TIME / weekly tool — never a gate or a test.

    python tools/reconcile_net_outages.py          # the last ~7 settled rows
    python tools/reconcile_net_outages.py --seam    # first-run: the 2026-07-10->08-25
                                                    # unsettled seam + one day of each multi-day run
"""
import csv
import datetime
import json
import os
import ssl
import sys
import urllib.request

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/summary"
_DS = "ping-slash24"
_ROWS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "net_outages.csv")
# interior day of each of the 6 multi-day runs (a settle phase-shift cannot erase a
# sustained episode, only move its onset row — these must reproduce)
_RUN_DAYS = ("2022-11-14", "2022-11-19", "2022-11-24", "2022-11-29", "2023-06-22", "2024-03-15")
_FLIP = 3  # a count delta this large would meaningfully move the z; the operator
           # confirms whether it actually flips the tremble verdict for that row


def _window(end_date):
    """The settled 24h window ending 22:00Z on ``end_date`` -> (from, until) unix."""
    end = datetime.datetime.combine(datetime.date.fromisoformat(end_date),
                                    datetime.time(22, 0), tzinfo=datetime.timezone.utc)
    ts = int(end.timestamp())
    return ts - 86400, ts


def requery(end_date):
    """Count ping-slash24 countries in ``end_date``'s settled window, live from IODA."""
    frm, until = _window(end_date)
    q = f"{_URL}?from={frm}&until={until}&entityType=country&limit=400"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # IODA's chain trips some sandboxes; read-only GET
    req = urllib.request.Request(q, headers={"User-Agent": "tremor/1.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=45, context=ctx).read())["data"]
    return sum(1 for e in data
               if any(str(k).startswith(_DS) for k in (e.get("scores") or {})))


def _scored_rows():
    return [r for r in csv.DictReader(open(_ROWS)) if r["raw_value"] not in ("", "None")]


def main(argv):
    rows = _scored_rows()
    if "--seam" in argv:
        targets = [r for r in rows if "2026-07-10" <= r["date"] <= "2026-08-25"]
        targets += [r for r in rows if r["date"] in _RUN_DAYS]
    else:
        targets = [r for r in rows if r.get("obs_date")][-7:]
    if not targets:
        print("no settled rows yet — the tool has nothing to reconcile until CI writes "
              "settled rows. Re-run after the first post-switch daily runs, or use --seam.")
        return 0
    print(f"{'row':12s} {'win-end':12s} {'stored':>6} {'settled':>7}")
    flips = 0
    for r in targets:
        end = r.get("obs_date") or r["date"]  # settled rows carry the window-end date
        try:
            got = requery(end)
        except Exception as e:
            print(f"{r['date']:12s} {end:12s}   ERR {type(e).__name__}")
            continue
        stored = int(float(r["raw_value"]))
        flag = "  <-- MISMATCH (check if it flips the verdict)" if abs(got - stored) >= _FLIP else ""
        print(f"{r['date']:12s} {end:12s} {stored:>6} {got:>7}{flag}")
        if flag:
            flips += 1
    print(f"\n{len(targets)} rows checked, {flips} mismatch(es) >= {_FLIP} countries.")
    return 1 if flips else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
