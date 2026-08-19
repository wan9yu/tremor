"""tremor — daily collector (an indicator radar).

Calls every tension-line fetcher, appends today's reading to ``data/<line>.csv``
with a robust z-score and a trembling flag, then rewrites ``data/summary.csv``
with the day's trembling count.

Fetcher contract — each module in ``fetchers/`` provides:
  - ``fetch_daily() -> {"raw_value": float | None, "source_note": str,
    "obs_date": str (optional)}``. A LAGGED source (one that republishes the
    same reading until it updates: FRED, PortWatch, GPSJam) MUST set
    ``obs_date`` to the observation's own date, or duplicate readings will
    quietly shrink the robust-scale baseline — the pseudo-replication the obs-dedup
    rule exists to kill.
    A fetcher MAY also return ``components``: ``{name: value}``, the breakdown
    the reading was aggregated from (per-strait, per-region, per-provider).
    These are written to ``data/components/<line>.csv`` and are DIAGNOSTIC ONLY —
    nothing scores them, nothing displays them. See ``write_components``.
  - module attrs: ``LINE``, ``LABEL``, ``UNIT``, ``ANOMALY_DIRECTION``
    ("up"/"down" — the alarm direction; only trembles in this direction feed
    trembling_count), optional ``TIER`` (default 1), optional ``WEEKLY_CYCLE``
    (True for lines with a weekday rhythm, e.g. flights), optional ``QUANTUM``
    (the measurement resolution of a COUNTED reading — one country, one basis
    point — which floors the robust scale so a calm stretch of identical
    integers cannot leave the line unable to judge the spike that follows), and
    optional ``ANCHOR`` + ``MATERIALITY`` for an ANCHORED line whose normal is a
    DECLARED constant, not a rolling window (a $1 peg, a $0 facility take-up).
    When ``MATERIALITY`` is set the rolling scale is bypassed entirely — the
    verdict is ``z = (raw - ANCHOR) / MATERIALITY``, so ``3*MATERIALITY`` is the
    smallest material move — which is the only honest reading for a near-constant
    series (a tiny rolling Qn cries wolf on ordinary fuzz; a zero Qn goes blind).
    A line declares ``QUANTUM`` or ``MATERIALITY``, never both.

Two tiers (each fetcher sets ``TIER``; absent means 1):
  - TIER 1 — primary instruments: displayed, and counted in the trembling
    resonance and the dark-line count.
  - TIER 2 — watchlist: scraped every day so history and z-score accumulate, but
    NOT counted and NOT shown. Candidates under observation; promote by setting
    ``TIER = 1``. This lets the set of instruments diverge (add candidates) and
    converge (graduate the good ones) over time.

Honest by construction: a failed fetch writes an EMPTY value with a stated
reason — never a fabricated or forward-filled number. The only composite is the
trembling count; the lines are never multiplied into a single doom score.
"""
import csv
import os
import shutil
from datetime import datetime, timezone

from core import clock, normalize

from fetchers import (capital_premium, chokepoint, cnh_cny, control_daylength,
                      credit_spread, em_oas, euro_hy_spread, fed_srf_takeup, flights,
                      fx_parallel_premium, gdelt, gdelt_tone, gnss, grid_frequency,
                      hkma_aggr_balance, net_outages, polar_temp, ports, sofr_iorb,
                      stablecoin_peg, tga_days_cash, vix)

# Every fetcher, both tiers. The tier-1 lines each guard a DIFFERENT domain
# (airspace / financial system / capital controls / communications), so several
# trembling at once means more than any one moving alone. Tier-2 lines ride along
# to build history until they earn promotion. The grouping below is a reading
# aid; ``TIER`` on each module is what actually decides.
LINES = [flights, credit_spread, cnh_cny, net_outages,  # tier 1 (primary, displayed)
         gnss, capital_premium, grid_frequency,         # tier 2 (demoted)
         chokepoint, sofr_iorb, em_oas, ports,          # tier 2 (candidates)
         euro_hy_spread, fx_parallel_premium, hkma_aggr_balance,  # tier 2 (built round 8)
         tga_days_cash,                                 # tier 2 (built round 11)
         stablecoin_peg,                                # tier 2 (built round 14)
         fed_srf_takeup,                                # tier 2 (built round 20)
         gdelt, gdelt_tone, vix, polar_temp,             # tier 2 (context, never promotable)
         control_daylength]                             # tier 2 (CONTROL — no world in it)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DOCS_DATA = os.path.join(ROOT, "docs", "data")

LINE_HEADER = ["date", "raw_value", "z_score", "trembling", "direction", "source_note",
               "obs_date", "status"]
# Summary holds only the tier-1 aggregates; each line's own z lives in its CSV, so
# the schema stays stable as indicators are added, promoted, or demoted.
SUMMARY_HEADER = ["date", "trembling_count", "dark_count", "blind_count"]
# Only what the dashboard actually reads is mirrored into docs/: the line CSVs,
# the summary, and the annotations. Everything else under data/ — the intraday
# sampler, components, archives, derived layers — is a measurement ABOUT the
# instrument and stays unserved BY DEFAULT: an allow-list, because a deny-list
# lets the next diagnostic file leak onto the dashboard by being forgotten.
# Nothing in collect.py or core/normalize.py may read the side channels either —
# see tests/test_side_channel.py.
MIRRORED = frozenset({"summary.csv", "annotations.csv"}
                     | {mod.LINE + ".csv" for mod in LINES})

COMPONENTS = os.path.join(DATA, "components")
COMPONENT_HEADER = ["date", "component", "value"]


def _read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _write_rows(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        # ignore extra keys so shrinking a schema (e.g. dropping per-line columns
        # from the summary) never trips on rows written under an older header.
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _upsert(rows, new_row, date):
    """Replace any existing row for ``date`` (idempotent re-runs), keep sorted."""
    rows = [r for r in rows if r.get("date") != date]
    rows.append(new_row)
    rows.sort(key=lambda r: r["date"])
    return rows


def _history(rows, today):
    """Prior (values, dates, obs_dates) aligned, excluding today.

    Empty cells become None; observation dedup and every other scoring rule
    live in ``normalize.judge``, so this stays pure data access.
    """
    values, dates, obs_dates = [], [], []
    for r in rows:
        if r.get("date") == today:
            continue
        v = r.get("raw_value")
        values.append(float(v) if v not in (None, "") else None)
        dates.append(r.get("date"))
        obs_dates.append(r.get("obs_date") or "")
    return values, dates, obs_dates


def _fmt(value):
    """Render a raw value compactly; empty string for None."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def score_row(date, raw, note, obs_date, prior_rows, weekly_cycle=False,
              quantum=None, anchor=None, materiality=None, weekend_market=False):
    """Judge one reading against ``prior_rows`` and return the CSV row for it.

    The ONLY place a line row is built. The daily collector and the archive
    seeders in ``tools/`` both go through here, so a schema change, a change of
    z precision, or a new verdict field cannot leave seeded rows in an older
    shape than live ones — most of some lines' history is written by a seeder,
    and that path is not exercised by the daily run.
    """
    # Judge the value AS IT WILL BE STORED. The CSV keeps ``_fmt(raw)`` (four
    # decimals) and replay re-parses that string, so judging the unrounded
    # float would leave live-vs-replay equality resting on the coincidence that
    # every fetcher pre-rounds. The record must be judged from what the record
    # holds.
    if raw is not None:
        raw = float(_fmt(raw))
    history, hist_dates, hist_obs = _history(prior_rows, date)
    z, trembling, direction, verdict_note, status = normalize.judge(
        history, hist_dates, hist_obs, raw, obs_date, date,
        weekly_cycle=weekly_cycle, quantum=quantum,
        anchor=anchor, materiality=materiality, weekend_market=weekend_market,
    )
    if verdict_note:
        note += f" {verdict_note}"
    return {
        "date": date,
        "raw_value": _fmt(raw),
        "z_score": "" if z is None else f"{z:.3f}",
        "trembling": str(trembling),
        "direction": direction,
        "source_note": note,
        "obs_date": obs_date or "",
        "status": status,
    }


def scoring_attrs(mod):
    """The per-line options ``score_row`` needs, read off the fetcher module.

    THE ONE PLACE THAT KNOWS WHICH MODULE ATTRIBUTES AFFECT A VERDICT. Three
    callers score rows — the daily collector, ``tools/replay.py``, and the
    seeders via ``seedlib`` — and every one of them must read the same set, or
    a line is judged by different rules depending on who wrote the row.

    That is not hypothetical. ``WEEKLY_CYCLE`` was forwarded by hand in each
    caller; when ``QUANTUM`` arrived, two callers were updated and the seeder
    was not, and the 1,626-day net_outages seed came back with 34 rows reading
    `no-spread` — including the largest genuine reading in the whole record, a
    45-country day that the floor exists precisely to keep scoreable. Adding a
    fourth attribute must now be a one-line change here, not a three-file
    memory test.
    """
    return {"weekly_cycle": getattr(mod, "WEEKLY_CYCLE", False),
            "quantum": getattr(mod, "QUANTUM", None),
            "anchor": getattr(mod, "ANCHOR", None),
            "materiality": getattr(mod, "MATERIALITY", None),
            "weekend_market": getattr(mod, "WEEKEND_MARKET", False)}


def write_line(line, rows):
    """Write a line's full row list to ``data/<line>.csv``."""
    _write_rows(os.path.join(DATA, line + ".csv"), LINE_HEADER, rows)


def write_components(line, date, components):
    """Append one day's breakdown to ``data/components/<line>.csv`` under ``date``.

    THE SCALAR IS NOT WHAT WE FETCHED. Every day this instrument downloads 28
    straits, twelve provider counts, tens of thousands of grid cells — and writes
    down one number each. The aggregation happens at CAPTURE, so it cannot be
    undone later: a strait collapsing 65% moved the recorded chokepoint number by
    under 2%, and there is no going back to ask which strait, because the answer
    was never written down. PortWatch will not serve 2019 forever.

    So the breakdown is stored beside the reading. It is DIAGNOSTIC ONLY, under
    the same rule as the intraday sampler: no scoring code may read it, it is not
    mirrored to the dashboard, and it changes no verdict. Its job is to make the
    analyses this project has already wanted — a per-strait breadth count, a
    regional rebalancing of the airspace line, a level layer — possible later
    without a time machine.
    """
    if not components:
        return
    path = os.path.join(COMPONENTS, line + ".csv")
    rows = [r for r in _read_rows(path) if r.get("date") != date]
    rows += [{"date": date, "component": name, "value": _fmt(float(value))}
             for name, value in sorted(components.items())]
    rows.sort(key=lambda r: (r["date"], r["component"]))
    _write_rows(path, COMPONENT_HEADER, rows)


def collect():
    today = clock.china_today()
    summary = {"date": today}
    trembling_count = 0
    dark_count = 0
    blind_count = 0

    for mod in LINES:
        path = os.path.join(DATA, mod.LINE + ".csv")
        rows = _read_rows(path)

        # Stamp WHEN the fetch happened. For a snapshot line the reading is
        # whatever the world looked like at one instant, and this project has
        # measured that instant to matter: reconstructing cnh_cny's committed
        # revisions showed the same calendar date written at values 131 pips
        # apart by runs at different times — 3.6x the line's robust scale, more
        # than the 3.0 its own alarm requires. Without the stamp that is
        # invisible after the fact. It goes in source_note, which is prose and
        # is not part of the replayed verdict, so it adds no drift.
        sampled = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
        try:
            result = mod.fetch_daily()
        except Exception as e:  # one bad source must never abort the whole run
            result = {"raw_value": None,
                      "source_note": f"fetcher crashed: {type(e).__name__}"}
        # The same rule covers a fetcher that RETURNS garbage instead of raising:
        # reading a malformed shape outside this guard would abort the run and
        # cost every line its day, not just the broken one.
        if not isinstance(result, dict) or "raw_value" not in result \
                or "source_note" not in result:
            result = {"raw_value": None,
                      "source_note": "fetcher returned a malformed result"}
        raw = result["raw_value"]
        note = f"{result['source_note']} [sampled {sampled}]"
        obs_date = result.get("obs_date") or ""
        tier = getattr(mod, "TIER", 1)
        primary = tier == 1

        row = score_row(today, raw, note, obs_date, rows, **scoring_attrs(mod))
        status = row["status"]
        trembling = int(row["trembling"])
        # Only tier-1 instruments count, and only trembles in the line's declared
        # ALARM direction — a guard visibly reasserting itself is recorded but is
        # not disorder. A line HOLDING a reading it cannot judge is blind, not
        # calm: the headline's denominator has to say how many instruments were
        # actually able to answer. A stale row is neither, because the
        # observation was judged when it first arrived and that verdict stands.
        if primary:
            if trembling and row["direction"] == mod.ANOMALY_DIRECTION:
                trembling_count += 1
            if status == normalize.STATUS_DARK:
                dark_count += 1
            elif status in normalize.BLIND_STATUSES:
                blind_count += 1

        _write_rows(path, LINE_HEADER, _upsert(rows, row, today))
        # Components are keyed by the OBSERVATION date when the line declares
        # one: for a lagged source the breakdown describes the day the transits
        # happened, not the day we asked. Keying by collection date left the
        # chokepoint file with two date axes ten days apart at the backfill/live
        # seam. Snapshot lines have no obs_date and keep the collection date.
        write_components(mod.LINE, obs_date or today, result.get("components"))

        flag = "  TREMBLING" if trembling else ""
        print(
            f"[{mod.LINE:16} t{tier}] raw={row['raw_value'] or 'NA':>10}  "
            f"z={row['z_score'] or 'NA':>7} {status:<11}{flag}  "
            f"({row['source_note']})"
        )

    summary["trembling_count"] = str(trembling_count)
    summary["dark_count"] = str(dark_count)
    summary["blind_count"] = str(blind_count)
    summary_path = os.path.join(DATA, "summary.csv")
    srows = _upsert(_read_rows(summary_path), summary, today)
    for r in srows:  # keep every row schema-complete even across format changes
        for k in SUMMARY_HEADER:
            r.setdefault(k, "")
    _write_rows(summary_path, SUMMARY_HEADER, srows)
    extra = ((f", {dark_count} dark" if dark_count else "")
             + (f", {blind_count} blind" if blind_count else ""))
    print(f"\n== {today}: {trembling_count} line(s) trembling{extra} ==")

    # Mirror the data into docs/ so the GitHub Pages dashboard is self-contained.
    os.makedirs(DOCS_DATA, exist_ok=True)
    for name in os.listdir(DATA):
        if name in MIRRORED:
            shutil.copy2(os.path.join(DATA, name), os.path.join(DOCS_DATA, name))


if __name__ == "__main__":
    collect()
