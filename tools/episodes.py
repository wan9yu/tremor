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

    python tools/episodes.py             # every line, days vs episodes
    python tools/episodes.py --json      # machine-readable
    python tools/episodes.py --markdown  # radar-metrics.md table
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect
import seedlib

GAP = 1  # non-trembling days tolerated inside one episode
MATURE = 60  # scored readings a tier-2 line needs before promotion is even
             # adjudicable (radar.md: "a tier-2 line earns a primary slot over
             # ≥60 scored readings"; the same bar tools/pending.py checks with
             # distinct_scored(...) >= 60). A line under this is not lacking
             # data by accident — it just has not banked enough evidence yet.


def _lag1(clean):
    """Lag-1 autocorrelation of a value list, or None if it cannot be formed."""
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
    out, last_i = [], None
    for date in alarms:
        i = index.get(date)
        if i is None:
            continue
        if out and i - last_i <= gap + 1:
            start, _, n = out[-1]
            out[-1] = (start, date, n + 1)
        else:
            out.append((date, date, 1))
        last_i = i
    return out


def report_line(mod):
    rows = seedlib.read_line(mod.LINE)
    if not rows:
        return None
    scored = [r for r in rows if r["z_score"]]
    observed = [r["obs_date"] or r["date"] for r in scored]
    # One pass, one counts_as_tremble call per row: alarm and benign are
    # mutually exclusive (a row is one or the other, never both), so a
    # second full scan re-evaluating the predicate is redundant. Benign is
    # trembling in the OTHER direction — statistically live, but not the
    # line's declared alarm; cnh_cny's four down-trembles are the canonical
    # case (radar.md: "0 alarms (4 benign down-trembles)"). Calling
    # ``counts_as_tremble`` (rather than re-comparing direction here) keeps
    # the ANOMALY_DIRECTION check itself living only in collect.py
    # (lint_ssot.py's TestTrembleCountPredicateIsOneHome).
    alarm, benign = [], []
    for r in rows:
        d = r["obs_date"] or r["date"]
        if collect.counts_as_tremble(r, mod):
            alarm.append(d)
        elif r["trembling"] == "1":
            benign.append(d)
    dark = sum(1 for r in rows if r["status"] == collect.normalize.STATUS_DARK)
    eps = episodes(observed, sorted(alarm))
    values = [float(r["raw_value"]) for r in rows if r["raw_value"]]
    rho = _lag1(values)
    # The span the RATES describe, so it means what its name says: a line
    # with rows but nothing scored has no span, not a span of everything.
    span_days = ((datetime.date.fromisoformat(scored[-1]["date"])
                  - datetime.date.fromisoformat(scored[0]["date"])).days
                 if scored else 0)
    return {
        "line": mod.LINE,
        "tier": getattr(mod, "TIER", 1),
        "rows": len(rows),
        "dark": dark,
        "read": len(rows) - dark,
        "scored_days": len(scored),
        "span_years": round(span_days / 365.25, 2),
        "alarm_days": len(alarm),
        "benign_trembles": len(benign),
        "episodes": len(eps),
        "longest_run": max((n for _, _, n in eps), default=0),
        "lag1": None if rho is None else round(rho, 3),
        "mature": len(scored) >= MATURE,
        # Rows stay sorted by collection ``date`` (collect._upsert), so the
        # last row is the freshest; obs_date wins over date for the same
        # reason ``observed``/``alarm`` above prefer it — a lagged source's
        # own observation date, not the day it was fetched.
        "last_obs": rows[-1]["obs_date"] or rows[-1]["date"],
        "episode_dates": eps,
    }


def render_markdown(out):
    """Render ``out`` (report_line dicts, in collect.LINES order) as a table.

    A pure function of ``out`` — no clock, no filesystem, no set/dict-iteration
    beyond the order ``out`` already fixes — so calling it twice on the same
    record byte-equals: what tests/audit_registry.py's freshness check relies
    on. This replaces the hand-copied ``Reliab``/``Respons`` cells radar.md
    used to carry (D6): four of those cells were caught measured stale, and a
    hand-copied metric drifts the day after it is fixed.
    """
    lines = [
        "# radar metrics",
        "",
        "Generated by `python tools/episodes.py --markdown` — do not hand-edit. Regenerate",
        "and commit instead; a cell drifting from the record here is exactly what replacing",
        "radar.md's hand-copied `Reliab`/`Respons` columns (D6) exists to end.",
        "",
        "`read` = rows minus `dark` (a fetch that returned nothing to judge) — the",
        "reliability count. `benign` = trembling days in the OTHER direction from the",
        "line's declared alarm (statistically live, not counted — cnh_cny's benign",
        "down-trembles are the canonical case). `episodes`/`longest_run` group alarm",
        "days into runs (module docstring). `mature` marks scored >= "
        f"{MATURE} — the tier-1 promotion bar.",
        "",
        "| line | tier | rows | read | dark | scored | span (yrs) | alarm days | benign "
        "| episodes | longest run | lag-1 | mature | last obs |",
        "|---|:--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--:|---|",
    ]
    for r in out:
        lag1 = "—" if r["lag1"] is None else format(r["lag1"], ".3f")
        lines.append(
            f"| {r['line']} | {r['tier']} | {r['rows']} | {r['read']} | {r['dark']} | "
            f"{r['scored_days']} | {r['span_years']} | {r['alarm_days']} | "
            f"{r['benign_trembles']} | {r['episodes']} | {r['longest_run']} | {lag1} | "
            f"{'yes' if r['mature'] else 'no'} | {r['last_obs']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv):
    out = [r for r in (report_line(mod) for mod in collect.LINES) if r]
    if "--markdown" in argv:
        sys.stdout.write(render_markdown(out))
        return 0
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
