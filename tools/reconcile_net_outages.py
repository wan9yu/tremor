"""Reconciliation check for the net_outages settle (R23.1 Pending-review tripwire).

Two checks, both against live IODA, run on the recent settled rows:

1. COUNT vs SETTLE. Settling to a completed D-1 window rests the artifact fix on
   one live data point (2026-08-24 re-queried to 4). "~24h" is IODA's TYPICAL
   detection latency, not a bound: on a slow-pipeline day a window read ~24.4h
   after its end could still be inflating (a smaller 08-24 sibling) or, worse,
   UNDER-counting a real onset. So this re-queries the settled window and compares
   to the stored raw; a mismatch large enough to flip a verdict reopens it.

2. COMMON-MODE signature (added 2026-09-04, R27). The settle rule makes the count
   STABLE but does not filter a synchronized-onset active-probing artifact: such a
   cluster lives in its own settled window and trembles there (see the 2026-08-26
   annotation, and the 2026-09-04 case — 15 countries, z=6.098, that re-queried to
   a stable 15 yet was an artifact). monitor_swept only catches the catastrophic
   >=100-country / >=80%-share sweep; a ~15-country cluster falls below it and no
   COUNT check flags it. So for every trembling row this also pulls IODA's
   per-country events and asks the R23 question mechanically: is the tremble a
   synchronized batch of countries that fired on ping-slash24 ALONE — no BGP, no
   network-telescope corroboration? A real multi-country event withdraws routes or
   shifts telescope traffic for at least some members and its onsets stagger; a
   measurement common-mode fires ping-only and onsets together. A hit is a LEAN,
   not a verdict — it says "run the R23 adjudication", it does not dark anything
   (auto-darking a sub-100 cluster would one day refuse a genuine catastrophe,
   the same reason monitor_swept stays a narrow conjunction).

Live network, so it is a ROUND-TIME / weekly tool — never a gate or a test. The
COMMON-MODE classifier itself is pure and unit-tested (tests/test_reconcile_common_mode.py);
only the fetch is network.

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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import useragent
from fetchers import net_outages

_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/summary"
_EVENTS_URL = "https://api.ioda.inetintel.cc.gatech.edu/v2/outages/events"
_DS = "ping-slash24"
_ROWS = os.path.join(ROOT, "data", "net_outages.csv")
# COMMON-MODE thresholds. A synchronized batch of this many countries (their first
# ping onset inside one window), almost all firing ping-slash24 with no BGP or
# network-telescope corroboration, is the active-probing common-mode signature.
# Deliberately conservative — a real regional event corroborates on BGP for some
# members and staggers its onsets, so it fails one of the three tests. Calibrated
# against 2026-09-04 (12 ping-only countries, a 7-country batch inside 15 min).
_CM_SYNC_WINDOW_S = 900   # 15 min: "onset together"
_CM_SYNC_MIN = 5          # at least this many countries in the synchronized batch
_CM_PING_ONLY_SHARE = 0.8  # of that batch, this share must be ping-slash24-only
# interior day of each of the 6 multi-day runs (a settle phase-shift cannot erase a
# sustained episode, only move its onset row — these must reproduce)
_RUN_DAYS = ("2022-11-14", "2022-11-19", "2022-11-24", "2022-11-29", "2023-06-22", "2024-03-15")
_FLIP = 3  # a count delta this large would meaningfully move the z; the operator
           # confirms whether it actually flips the tremble verdict for that row


def requery(end_date):
    """Count ping-slash24 countries in ``end_date``'s settled window, live from IODA."""
    frm, until = net_outages.window_for_day(datetime.date.fromisoformat(end_date))
    q = f"{_URL}?from={frm}&until={until}&entityType=country&limit=400"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # IODA's chain trips some sandboxes; read-only GET
    req = urllib.request.Request(q, headers=useragent.HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=45, context=ctx).read())["data"]
    return sum(1 for e in data
               if any(str(k).startswith(_DS) for k in (e.get("scores") or {})))


def classify_common_mode(events, sync_window_s=_CM_SYNC_WINDOW_S,
                         sync_min=_CM_SYNC_MIN, ping_only_share=_CM_PING_ONLY_SHARE):
    """Decide whether one window's outage events are a common-mode active-probing
    artifact. ``events`` is ``[{"country", "datasource", "start"}]``. Pure — no
    network — so the live fetch (``_fetch_events``) stays out of the unit test.

    A country is ping-only when it has a ping-slash24 event and NO bgp / merit-nt
    event; corroborated when it has ping-slash24 AND one of those. The signal is a
    synchronized batch (>= ``sync_min`` countries whose first ping onset falls in one
    ``sync_window_s`` window) that is >= ``ping_only_share`` ping-only. Chronic
    always-on outages (Cape Verde, Tunisia) are ping-only too but do not fall in a
    tight synchronized batch, so the synchrony test excludes them without a hand list.
    Returns a summary dict; ``verdict`` is "common-mode" or "ok"."""
    by_country = {}
    for e in events:
        ds = str(e.get("datasource") or "")
        rec = by_country.setdefault(e.get("country"), {"ping": [], "corrob": False})
        if ds.startswith("ping-slash24"):
            if e.get("start") is not None:
                rec["ping"].append(int(e["start"]))
        elif ds.startswith("bgp") or ds.startswith("merit-nt"):
            rec["corrob"] = True
    ping = {c: v for c, v in by_country.items() if v["ping"]}
    onsets = sorted((min(v["ping"]), c) for c, v in ping.items())
    best = []
    for t0, _ in onsets:
        batch = [c for t, c in onsets if t0 <= t <= t0 + sync_window_s]
        if len(batch) > len(best):
            best = batch
    ping_only_in_batch = [c for c in best if not ping[c]["corrob"]]
    share = len(ping_only_in_batch) / len(best) if best else 0.0
    common_mode = len(best) >= sync_min and share >= ping_only_share
    return {
        "verdict": "common-mode" if common_mode else "ok",
        "ping_countries": len(ping),
        "corroborated": sum(1 for v in ping.values() if v["corrob"]),
        "sync_batch": len(best),
        "sync_ping_only": len(ping_only_in_batch),
        "batch_countries": sorted(best),
    }


def _fetch_events(end_date):
    """IODA per-country outage events for ``end_date``'s settled window, live."""
    frm, until = net_outages.window_for_day(datetime.date.fromisoformat(end_date))
    q = f"{_EVENTS_URL}?from={frm}&until={until}&entityType=country&limit=1000"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # IODA's chain trips some sandboxes; read-only GET
    req = urllib.request.Request(q, headers=useragent.HEADERS)
    data = json.loads(urllib.request.urlopen(req, timeout=45, context=ctx).read())["data"]
    return [{"country": e.get("location_name") or e.get("location"),
             "datasource": e.get("datasource"), "start": e.get("start")} for e in data]


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
    cm_hits = 0
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
        # A trembling row is the one that needs adjudication: a stable count is not
        # proof of a real event (2026-09-04). Ask the common-mode question of it.
        if r.get("trembling") == "1":
            pad = f"{'':12s} {'':12s}"
            try:
                cm = classify_common_mode(_fetch_events(end))
            except Exception as e:
                print(f"{pad}   common-mode: ERR {type(e).__name__}")
            else:
                if cm["verdict"] == "common-mode":
                    cm_hits += 1
                    print(f"{pad}   <-- COMMON-MODE LEAN: {cm['sync_ping_only']}/{cm['sync_batch']} "
                          f"synchronized countries ping-slash24-only "
                          f"({cm['corroborated']}/{cm['ping_countries']} corroborated) — run the R23 adjudication")
                else:
                    print(f"{pad}   common-mode: ok (batch {cm['sync_batch']}, "
                          f"{cm['corroborated']}/{cm['ping_countries']} corroborated)")
    print(f"\n{len(targets)} rows checked, {flips} count mismatch(es) >= {_FLIP}, "
          f"{cm_hits} common-mode lean(s).")
    return 1 if (flips or cm_hits) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
