"""tremor — daily collector (an indicator radar).

Calls every tension-line fetcher, appends today's reading to ``data/<line>.csv``
with a robust z-score and a trembling flag, then rewrites ``data/summary.csv``
with the day's trembling count.

Fetcher contract — each module in ``fetchers/`` provides:
  - ``fetch_daily() -> {"raw_value": float | None, "source_note": str,
    "obs_date": str (optional)}``. A LAGGED source (one that republishes the
    same reading until it updates: FRED, PortWatch, GPSJam) MUST set
    ``obs_date`` to the observation's own date, or duplicate readings will
    quietly shrink the MAD baseline — the pseudo-replication the obs-dedup
    rule exists to kill.
  - module attrs: ``LINE``, ``LABEL``, ``UNIT``, ``ANOMALY_DIRECTION``
    ("up"/"down" — the alarm direction; only trembles in this direction feed
    trembling_count), optional ``TIER`` (default 1), optional ``WEEKLY_CYCLE``
    (True for lines with a weekday rhythm, e.g. flights).

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
from datetime import datetime, timedelta, timezone

from core import normalize

# Rows are dated in China time (UTC+8, no DST): the daily run fires at 06:00
# China, so a row dated D was collected on the morning of D, China time — which
# matches how the (China-based) project reads the calendar.
CHINA_TZ = timezone(timedelta(hours=8))
from fetchers import (capital_premium, chokepoint, cn_flights, cnh_cny,
                      credit_spread, em_oas, flights, gdelt, gnss,
                      grid_frequency, net_outages, ports, sofr_iorb)

# Every fetcher, both tiers. The tier-1 lines each guard a DIFFERENT domain
# (airspace / financial system / capital controls / infrastructure), so several
# trembling at once means more than any one moving alone. Tier-2 lines ride along
# to build history until they earn promotion.
LINES = [flights, credit_spread, cnh_cny, gnss,         # tier 1 (primary, displayed)
         capital_premium, grid_frequency, chokepoint,   # tier 2 (lagged/demoted)
         cn_flights, gdelt,                             # tier 2 (watchlist + contrast)
         sofr_iorb, em_oas, ports, net_outages]         # tier 2 (radar builds)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DOCS_DATA = os.path.join(ROOT, "docs", "data")

LINE_HEADER = ["date", "raw_value", "z_score", "trembling", "direction", "source_note",
               "obs_date"]
# Summary holds only the tier-1 aggregates; each line's own z lives in its CSV, so
# the schema stays stable as indicators are added, promoted, or demoted.
SUMMARY_HEADER = ["date", "trembling_count", "dark_count"]


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


def collect():
    today = datetime.now(CHINA_TZ).strftime("%Y-%m-%d")
    summary = {"date": today}
    trembling_count = 0
    dark_count = 0

    for mod in LINES:
        path = os.path.join(DATA, mod.LINE + ".csv")
        rows = _read_rows(path)

        try:
            result = mod.fetch_daily()
        except Exception as e:  # one bad source must never abort the whole run
            result = {"raw_value": None,
                      "source_note": f"fetcher crashed: {type(e).__name__}"}
        raw = result["raw_value"]
        note = result["source_note"]
        obs_date = result.get("obs_date") or ""
        tier = getattr(mod, "TIER", 1)
        primary = tier == 1

        history, hist_dates, hist_obs = _history(rows, today)
        z, trembling, direction, verdict_note = normalize.judge(
            history, hist_dates, hist_obs, raw, obs_date, today,
            weekly_cycle=getattr(mod, "WEEKLY_CYCLE", False),
        )
        if verdict_note:
            note += f" {verdict_note}"
        # Only tier-1 instruments count toward the live resonance and dark count,
        # and only trembles in the line's declared ALARM direction feed the count
        # — a guard visibly reasserting itself (a benign-direction move) is
        # recorded but is not disorder.
        if primary:
            if trembling and direction == mod.ANOMALY_DIRECTION:
                trembling_count += 1
            if raw is None:
                dark_count += 1

        row = {
            "date": today,
            "raw_value": _fmt(raw),
            "z_score": "" if z is None else f"{z:.3f}",
            "trembling": str(trembling),
            "direction": direction,
            "source_note": note,
            "obs_date": obs_date,
        }
        rows = _upsert(rows, row, today)
        _write_rows(path, LINE_HEADER, rows)

        flag = "  TREMBLING" if trembling else ""
        print(
            f"[{mod.LINE:16} t{tier}] raw={row['raw_value'] or 'NA':>10}  "
            f"z={row['z_score'] or 'NA':>7}{flag}  ({note})"
        )

    summary["trembling_count"] = str(trembling_count)
    summary["dark_count"] = str(dark_count)
    summary_path = os.path.join(DATA, "summary.csv")
    srows = _upsert(_read_rows(summary_path), summary, today)
    for r in srows:  # keep every row schema-complete even across format changes
        for k in SUMMARY_HEADER:
            r.setdefault(k, "")
    _write_rows(summary_path, SUMMARY_HEADER, srows)
    dark_note = f", {dark_count} dark" if dark_count else ""
    print(f"\n== {today}: {trembling_count} line(s) trembling{dark_note} ==")

    # Mirror the data into docs/ so the GitHub Pages dashboard is self-contained.
    os.makedirs(DOCS_DATA, exist_ok=True)
    for name in os.listdir(DATA):
        if name.endswith(".csv"):
            shutil.copy2(os.path.join(DATA, name), os.path.join(DOCS_DATA, name))


if __name__ == "__main__":
    collect()
