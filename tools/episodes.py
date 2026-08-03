"""Count EPISODES, not tremble days — the seeded lines are nothing like iid.

Every rate this project has quoted has been per-day: "this line trembles X% of
the time". For the fast lines that is honest. For the slow financial and
physical ones it is not, and the measurement is stark: credit_spread's raw
lag-1 autocorrelation is 0.987, which leaves its ninety-observation baseline
carrying about ONE AND A HALF independent readings. On such a line one event
prints as a run of tremble days, and the day count overstates the number of
independent alarms by roughly eight times — credit_spread's 66 alarm-direction
tremble days are 8 episodes in three years, em_corp_oas' 48 are 7, polar_temp's
384 are 34.

Nothing here changes a verdict; the trembles are not wrong, and they cluster
inside the credit episodes already on the record. What is wrong is reading "66"
as sixty-six pieces of evidence. So the record grows a second column rather
than a different rule: this tool reports both counts, and the per-day rate
should never again be quoted for a line without its episode count beside it.

An episode is a maximal run of alarm-direction tremble days, allowing a gap of
``GAP`` non-trembling days inside it. The tolerance is not free-chosen: at
gap=1 an audit of the bridged days found 16 of 17 were same-direction readings
sitting just under the bar — the same event still underway, not a new one.

    python tools/episodes.py           # every line, days vs episodes
    python tools/episodes.py --json    # machine-readable
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect

GAP = 1  # non-trembling days tolerated inside one episode


def _lag1(values):
    """Lag-1 autocorrelation of a value list, or None if it cannot be formed."""
    clean = [v for v in values if v is not None]
    if len(clean) < 3:
        return None
    mean = sum(clean) / len(clean)
    var = sum((v - mean) ** 2 for v in clean)
    if var <= 0:
        return None
    cov = sum((clean[i] - mean) * (clean[i + 1] - mean) for i in range(len(clean) - 1))
    return cov / var


def episodes(observed, alarms, gap=GAP):
    """Group alarm days into episodes; returns [(start, end, days)].

    The gap is counted in the line's OWN OBSERVATIONS, not in calendar days.
    A calendar rule silently splits every episode at every weekend on a
    business-day line — credit_spread's eight real episodes came out as
    twenty-one that way, which would have overstated its independent alarms by
    the very factor this tool exists to correct.
    """
    index = {date: i for i, date in enumerate(observed)}
    out = []
    for date in alarms:
        i = index.get(date)
        if i is None:
            continue
        if out and i - out[-1][3] <= gap + 1:
            out[-1] = (out[-1][0], date, out[-1][2] + 1, i)
        else:
            out.append((date, date, 1, i))
    return [(s, e, n) for s, e, n, _ in out]


def report_line(mod):
    rows = collect._read_rows(os.path.join(collect.DATA, mod.LINE + ".csv"))
    if not rows:
        return None
    scored = [r for r in rows if r["z_score"]]
    observed = [r["obs_date"] or r["date"] for r in scored]
    alarm = [r["obs_date"] or r["date"] for r in rows
             if r["trembling"] == "1" and r["direction"] == mod.ANOMALY_DIRECTION]
    eps = episodes(observed, sorted(alarm))
    values = [float(r["raw_value"]) for r in rows if r["raw_value"]]
    rho = _lag1(values)
    span_days = 0
    if scored:
        span_days = (datetime.date.fromisoformat(rows[-1]["date"])
                     - datetime.date.fromisoformat(rows[0]["date"])).days
    return {
        "line": mod.LINE,
        "tier": getattr(mod, "TIER", 1),
        "scored_days": len(scored),
        "span_years": round(span_days / 365.25, 2),
        "alarm_days": len(alarm),
        "episodes": len(eps),
        "longest_run": max((n for _, _, n in eps), default=0),
        "lag1": None if rho is None else round(rho, 3),
        "episode_dates": [(s, e, n) for s, e, n in eps],
    }


def main(argv):
    out = [r for r in (report_line(mod) for mod in collect.LINES) if r]
    if "--json" in argv:
        print(json.dumps(out, indent=2))
        return 0
    print(f"{'line':22} {'t':>1} {'scored':>7} {'yrs':>5} {'alarm days':>11} "
          f"{'episodes':>9} {'longest':>8} {'lag-1':>6}")
    for r in out:
        print(f"{r['line']:22} {r['tier']:>1} {r['scored_days']:>7} {r['span_years']:>5} "
              f"{r['alarm_days']:>11} {r['episodes']:>9} {r['longest_run']:>8} "
              f"{'—' if r['lag1'] is None else format(r['lag1'], '.3f'):>6}")
    print("\nA day count is not an evidence count. On a line whose lag-1 runs above ~0.9,\n"
          "one event prints as a run of days: quote the episode count beside any rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
