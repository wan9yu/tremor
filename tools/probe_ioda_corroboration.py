"""Round-time diagnostic (P0-1): is a CORROBORATED net_outages sibling line
buildable? Its labeled output gates that sibling line's construction and the
registry wording that describes net_outages' blind spot.

CORRECTING A FALSE PREMISE. It is tempting to read "IODA activated bgp/merit-nt
on 2026-07-05" (fetchers/net_outages.py's module docstring) as "corroboration
is only knowable from that date forward" -- it is not. That date is only when
the LIVE v1 capture first recorded those datasources; RE-QUERYING the summary
and events endpoints today returns bgp/merit-nt country scores far back
(2024-10, 2026-03-06 both answer). There is also a genuine era HOLE (2026-06-15
re-queries ping-only). So corroboration seedability is an ERA-COVERAGE TABLE,
computed per month from what a re-query actually returns, not a single cutoff
date with a "not seedable before X" branch -- this tool never coded such a
branch, and Step 2 below builds the table instead.

THE LABELING PROBLEM. The record's ~59 net_outages "real" alarm days
(trembling=="1") were confirmed by RATE (R11 -- a tremble rate the null model
would not produce by chance), never individually adjudicated real-vs-artifact
by a human. So there is no ground-truth key to test "does corroboration
separate real from artifact" against. This tool does not pretend to one: it
LABELS every alarm day with what a re-query actually shows (raw ping count,
corroborated count, tools/reconcile_net_outages.classify_common_mode's lean)
and reports the resulting picture, including the deflation risk -- an
ok-lean, high-raw alarm day a corroborated line would count as near-zero.

REUSE, NOT REIMPLEMENT. Every live call here is
tools/reconcile_net_outages.requery (summary endpoint) or
tools/reconcile_net_outages._fetch_events (events endpoint, per-country
datasource attribution) -- which already own the SSL context, the User-Agent
(core.useragent, via that module), and the one settled-window boundary
(fetchers/net_outages.window_for_day, T1). classify_common_mode is the same
pure, unit-tested classifier reconcile_net_outages.py and tools/lean_panel.py
already share. This file adds nothing to that boundary; it only asks it more
questions.

Live network, so this is a ROUND-TIME diagnostic -- never a gate or a test.
IODA is intermittently flaky (SSLEOFError, URLError -- reconcile_net_outages.py's
own docstring), and an older settled window can take tens of seconds to
compute, so every per-window call here retries a few times through a short
backoff and DEGRADES that one window to "unavailable" on exhaustion rather
than raising -- one bad window must never abort a run that is re-querying
close to a hundred of them.

    python tools/probe_ioda_corroboration.py
"""
import csv
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # tools/, for reconcile_net_outages
sys.path.insert(0, ROOT)    # repo root, for data/

import reconcile_net_outages as R

_ROWS = os.path.join(ROOT, "data", "net_outages.csv")
# A genuinely down window degrades to "unavailable" rather than blocking a
# run that re-queries close to a hundred windows; base latency on an older
# window already runs tens of seconds (measured), so the backoff itself stays
# short -- it is here to ride out a transient SSLEOFError/URLError, not to
# wait out a real outage the way an overnight sweep (tools/seed_ioda.py) does.
_BACKOFF_S = (5, 15)
_PAUSE_S = 0.5  # between live calls -- polite, not a rate-limit dance

# Step 0's independent sample: spread across the full alarm history (2022-2026)
# plus the two dates validation hand-checked against a known corroboration
# count (2026-03-06, 2026-04-08).
_REPRO_SAMPLE = ("2022-02-23", "2023-06-22", "2024-03-15", "2025-03-01",
                  "2026-03-06", "2026-04-08", "2026-08-24", "2026-09-05")
# Landmark calm days validation already hand-checked (a corroboration-blind
# era and a heavily-corroborated month) -- pinned into the ~30-day calm
# sample so the era picture is not left to stride-alignment luck.
_CALM_PINS = ("2024-10-15", "2026-06-15")
_CALM_SAMPLE_N = 30
# "High raw" for the killer question (Step 3 / answer 4): tied to the
# classifier's own sync_min (R._CM_SYNC_MIN) -- a batch this size is already
# what classify_common_mode treats as big enough to weigh, not an
# independently chosen number.
_HIGH_RAW = R._CM_SYNC_MIN


def _with_retry(fn, *args, backoff=_BACKOFF_S):
    """Call ``fn(*args)``, retrying through IODA's intermittent SSLEOFError /
    URLError. Raises the last error once ``backoff`` is exhausted; the caller
    decides how the window degrades -- this never itself prints or hides the
    failure."""
    last = None
    for attempt in range(len(backoff) + 1):
        try:
            return fn(*args)
        except Exception as e:
            last = e
            if attempt < len(backoff):
                time.sleep(backoff[attempt])
    raise last


def _all_rows():
    return list(csv.DictReader(open(_ROWS)))


def _label_window(row, want_era=False):
    """Fetch, retry, and classify one settled window -- the per-row body
    step1_label_all and step3_bands's calm-day loop each ran inline before
    this was factored out. Degrades to ``status: "unavailable"`` on exhausted
    retries rather than raising (``_with_retry``'s contract); each caller
    still does its own printing from the returned dict, since step1's table
    carries two more columns (lean, era) than step3's calm-day table.

    ``want_era`` additionally records whether ANY bgp/merit-nt event appeared
    anywhere in the window (``era_covered``) -- step1's own extra field, which
    step2_era_profile derives the era table from. The calm-day loop has no
    use for it, so the key is simply absent from its dicts.
    """
    d = row["date"]
    end = R.window_end(row)
    try:
        events = _with_retry(R._fetch_events, end)
    except Exception as e:
        label = {"date": d, "window_end": end, "raw": None, "corrob": None,
                 "lean": None, "status": "unavailable", "error": type(e).__name__}
        if want_era:
            label["era_covered"] = None
        return label
    cm = R.classify_common_mode(events)
    label = {"date": d, "window_end": end, "raw": cm["ping_countries"],
             "corrob": cm["corroborated"], "lean": cm["verdict"], "status": "ok"}
    if want_era:
        label["era_covered"] = any(
            str(e.get("datasource") or "").startswith(("bgp", "merit-nt"))
            for e in events)
    return label


def step0_reproduce(rows_by_date, sample=_REPRO_SAMPLE):
    """Step 0 -- REPRODUCE. Does re-querying the summary endpoint's
    ping-slash24 country count for a settled window still match the row's
    stored ``raw_value``? Sanity that a re-query is faithful before Step 1
    trusts ~59 more of them."""
    print(f"{'date':12s} {'win-end':12s} {'stored':>6} {'requeried':>9}")
    out = []
    mismatches = 0
    for d in sample:
        row = rows_by_date.get(d)
        if row is None:
            print(f"{d:12s}  -- not in the record, skipped")
            continue
        end = R.window_end(row)
        stored = int(float(row["raw_value"]))
        try:
            got = _with_retry(R.requery, end)
        except Exception as e:
            print(f"{d:12s} {end:12s} {stored:>6}   unavailable ({type(e).__name__})")
            out.append({"date": d, "window_end": end, "stored": stored, "got": None})
            time.sleep(_PAUSE_S)
            continue
        flag = "  <-- MISMATCH" if got != stored else ""
        print(f"{d:12s} {end:12s} {stored:>6} {got:>9}{flag}")
        if got != stored:
            mismatches += 1
        out.append({"date": d, "window_end": end, "stored": stored, "got": got})
        time.sleep(_PAUSE_S)
    print(f"{len(out)} window(s) reproduced, {mismatches} mismatch(es)")
    return out


def step1_label_all(alarm_rows):
    """Step 1 -- LABEL ALL ALARM WINDOWS. For every trembling=='1' row,
    re-query its settled window's per-country events ONCE and derive both the
    raw ping-slash24 country count and the corroborated count (ping AND (bgp
    OR merit-nt)) from that single fetch -- classify_common_mode already
    counts both (``ping_countries``, ``corroborated``) from the events it is
    given, so this never double-fetches the same window through the summary
    endpoint too (Step 0 spot-checks that the two endpoints agree). Also
    records whether ANY bgp/merit-nt event appeared anywhere in the window
    (``era_covered``), independent of whether it landed on a pinged country --
    that is what separates a genuine corroboration MISS from a window IODA
    simply cannot corroborate yet (Step 2).

    This is the core deliverable: what a corroborated line would have counted
    on every historical alarm, without a real/artifact key the record does
    not have (see module docstring)."""
    print(f"{'date':12s} {'win-end':12s} {'raw':>4} {'corrob':>6} {'lean':11} "
          f"{'bgp/mnt':7} {'avail'}")
    out = []
    for row in alarm_rows:
        label = _label_window(row, want_era=True)
        if label["status"] == "ok":
            print(f"{label['date']:12s} {label['window_end']:12s} {label['raw']:>4} "
                  f"{label['corrob']:>6} {label['lean']:11} "
                  f"{'yes' if label['era_covered'] else 'no':7} yes")
        else:
            print(f"{label['date']:12s} {label['window_end']:12s} {'':>4} {'':>6} "
                  f"{'':11} {'':7} unavailable ({label['error']})")
        out.append(label)
        time.sleep(_PAUSE_S)
    unavailable = sum(1 for r in out if r["status"] != "ok")
    print(f"{len(out)} alarm window(s) labeled, {unavailable} unavailable")
    return out


def step2_era_profile(labels):
    """Step 2 -- ERA PROFILE. Monthly across the alarm history, is bgp/merit-nt
    present on re-query that month? Derived from Step 1's own per-window
    ``era_covered`` flags, not a separate sweep -- the ~59 alarm windows
    already span 2022-02 through the live tail, so no extra live calls are
    needed to see the shape of the hole. A month reads "none" only when every
    alarm window inside it came back with zero bgp/merit-nt events anywhere;
    "partial" when a month with more than one alarm window saw both; a
    calendar month with no alarm in it is not a row here -- there is nothing
    in the alarm history to derive it from."""
    by_month = {}
    for r in labels:
        if r["status"] != "ok":
            continue
        month = r["window_end"][:7]
        by_month.setdefault(month, []).append(r["era_covered"])
    print(f"{'month':8s} {'coverage':9} {'alarm days'}")
    out = {}
    for month in sorted(by_month):
        flags = by_month[month]
        if all(flags):
            cov = "yes"
        elif not any(flags):
            cov = "none"
        else:
            cov = "partial"
        out[month] = cov
        print(f"{month:8s} {cov:9} {len(flags)}")
    blind = [m for m, c in out.items() if c in ("none", "partial")]
    print(f"{len(out)} month(s) with an alarm; {len(blind)} corroboration-blind "
          f"or partial: {blind}")
    return out


def _calm_sample(rows, n=_CALM_SAMPLE_N, pins=_CALM_PINS):
    """~n calm (trembling=='0') days, stride-sampled across the full record's
    date range plus the landmark dates validation already hand-checked, so
    the sample is not left to stride-alignment luck alone."""
    calm = [r for r in rows
            if r.get("trembling") == "0" and r.get("raw_value") not in ("", "None")]
    calm.sort(key=lambda r: r["date"])
    picked = {r["date"]: r for r in calm if r["date"] in pins}
    remaining = n - len(picked)
    if remaining > 0 and calm:
        stride = max(1, len(calm) // remaining)
        for r in calm[::stride]:
            if len(picked) >= n:
                break
            picked.setdefault(r["date"], r)
    return sorted(picked.values(), key=lambda r: r["date"])


def step3_bands(labels, calm_rows):
    """Step 3 -- TWO BANDS.

    (a) Does corroboration separate the alarm days classify_common_mode
    leans "common-mode" from the ones it leans "ok"? Compares each band's
    average raw count against its average corroborated count.

    (b) ~30 calm (non-alarm) days, each re-queried the same way as an alarm
    window: does the corroborated definition survive the chronic-but-real
    background, or does it collapse to noise on an ordinary day?
    """
    ok = [r for r in labels if r["status"] == "ok"]
    cm_days = [r for r in ok if r["lean"] == "common-mode"]
    ok_days = [r for r in ok if r["lean"] == "ok"]

    def _avg(rows, key):
        vals = [r[key] for r in rows]
        return sum(vals) / len(vals) if vals else float("nan")

    print("(a) alarm days by lean:")
    print(f"  common-mode-lean: {len(cm_days):>3} day(s), avg raw {_avg(cm_days, 'raw'):5.1f}, "
          f"avg corroborated {_avg(cm_days, 'corrob'):5.2f}")
    print(f"  ok-lean:          {len(ok_days):>3} day(s), avg raw {_avg(ok_days, 'raw'):5.1f}, "
          f"avg corroborated {_avg(ok_days, 'corrob'):5.2f}")

    print("\n(b) calm-day corroboration survival:")
    print(f"{'date':12s} {'win-end':12s} {'raw':>4} {'corrob':>6} {'lean'}")
    calm_labels = []
    for row in calm_rows:
        label = _label_window(row)
        if label["status"] == "ok":
            print(f"{label['date']:12s} {label['window_end']:12s} {label['raw']:>4} "
                  f"{label['corrob']:>6} {label['lean']}")
        else:
            print(f"{label['date']:12s} {label['window_end']:12s} {'':>4} {'':>6} "
                  f"unavailable ({label['error']})")
        calm_labels.append(label)
        time.sleep(_PAUSE_S)
    ok_calm = [r for r in calm_labels if r["status"] == "ok"]
    with_outage = [r for r in ok_calm if r["raw"]]
    survives = [r for r in with_outage if r["corrob"]]
    print(f"{len(ok_calm)} calm day(s) sampled, {len(with_outage)} carried any raw "
          f"outage, {len(survives)} of those kept corroboration (corroborated > 0)")
    return {"cm_days": cm_days, "ok_days": ok_days, "calm": calm_labels}


def killer_question(labels):
    """Answer 4 -- REAL-looking alarm days a corroborated line would MISS:
    ok-lean (not classified as the active-probing common-mode artifact), a
    raw count at or above the classifier's own sync_min (not a one-off
    blip), yet corroborated_count <= 1 (near-zero). These are the deflation
    risk a corroborated sibling line would introduce -- a real-looking
    tremble it would report as almost nothing."""
    ok = [r for r in labels
          if r["status"] == "ok" and r["lean"] == "ok" and (r["raw"] or 0) >= _HIGH_RAW]
    missed = [r for r in ok if (r["corrob"] or 0) <= 1]
    missed.sort(key=lambda r: -(r["raw"] or 0))
    print(f"{'date':12s} {'win-end':12s} {'raw':>4} {'corrob':>6} {'bgp/mnt era'}")
    for r in missed:
        print(f"{r['date']:12s} {r['window_end']:12s} {r['raw']:>4} {r['corrob']:>6} "
              f"{'yes' if r['era_covered'] else 'no'}")
    print(f"{len(missed)} of {len(ok)} ok-lean/high-raw alarm day(s) would be missed "
          f"(corroborated <= 1)")
    return missed


def main():
    t0 = time.time()
    rows = _all_rows()
    rows_by_date = {r["date"]: r for r in rows}
    alarm_rows = [r for r in rows if r.get("trembling") == "1"]

    print("=== step 0: reproduce (summary endpoint vs stored raw_value) ===")
    step0_reproduce(rows_by_date)

    print("\n=== step 1: label every alarm window ===")
    labels = step1_label_all(alarm_rows)

    print("\n=== step 2: era profile ===")
    step2_era_profile(labels)

    print("\n=== step 3: two bands ===")
    calm_rows = _calm_sample(rows)
    step3_bands(labels, calm_rows)

    print("\n=== answer 4: real-looking alarm days a corroborated line would miss ===")
    killer_question(labels)

    print(f"\ndone in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
