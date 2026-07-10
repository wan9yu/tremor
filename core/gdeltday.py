"""Shared full-day GDELT 2.0 aggregation — one download pass, two feel lines.

GDELT publishes a global event file every 15 minutes (96/day). Sampling a single
file made the daily reading noise-dominated (share swung 8→23% in a week), so
the feel lines aggregate the WHOLE previous UTC day: material-conflict share
(QuadClass 4) and average tone. Both fetchers read from one cached pass so the
day's ~96 files are downloaded once per run.

Honesty: if under half the day's files are available the day returns None with
a reason — a partial day would bias the share, and we'd rather say so.
"""
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests

_URL = "http://data.gdeltproject.org/gdeltv2/{stamp}.export.CSV.zip"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}
_QUADCLASS_COL = 29  # 0-based; "4" == material conflict
_TONE_COL = 34       # AvgTone
_MIN_FILES = 48      # under half a day would bias the aggregates

_cache = {}


def _fetch_file(stamp):
    """(total, conflict, tone_sum, toned_rows) for one 15-min file, or None."""
    try:
        r = requests.get(_URL.format(stamp=stamp), headers=_HEADERS, timeout=25)
        if r.status_code != 200:
            return None
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        rows = zf.read(zf.namelist()[0]).decode("utf-8", "replace").splitlines()
    except Exception:  # one corrupt file must not kill the day
        return None
    total = conflict = toned = 0
    tone_sum = 0.0
    for row in rows:
        cols = row.split("\t")
        if len(cols) > _TONE_COL:
            total += 1
            if cols[_QUADCLASS_COL] == "4":
                conflict += 1
            try:
                tone_sum += float(cols[_TONE_COL])
                toned += 1
            except ValueError:
                pass
    return total, conflict, tone_sum, toned


def day_stats(day=None):
    """Aggregate a UTC day (default: yesterday). Returns (stats | None, note).

    stats = {"share": %, "tone": avg, "events": n, "files": n, "obs_date": iso}.
    """
    if day is None:
        day = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y%m%d")
    if day in _cache:
        return _cache[day]
    stamps = [f"{day}{h:02d}{m:02d}00" for h in range(24) for m in (0, 15, 30, 45)]
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = [r for r in ex.map(_fetch_file, stamps) if r]
    if len(results) < _MIN_FILES:
        out = (None, f"GDELT day {day}: only {len(results)}/96 files available")
    else:
        total = sum(r[0] for r in results)
        conflict = sum(r[1] for r in results)
        tone_sum = sum(r[2] for r in results)
        toned = sum(r[3] for r in results)
        if total == 0 or toned == 0:
            out = (None, f"GDELT day {day}: no usable events")
        else:
            obs = f"{day[:4]}-{day[4:6]}-{day[6:]}"
            out = ({"share": round(conflict / total * 100.0, 3),
                    "tone": round(tone_sum / toned, 3),
                    "events": total, "files": len(results), "obs_date": obs}, "")
    _cache[day] = out
    return out
