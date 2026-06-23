"""GDELT global conflict-event share — "felt vs real" WATCHLIST (tier 2).

NOT a tension indicator, by the project's own rule: event tallies have no guard
and inflate as media coverage densifies. So it stays on the watchlist as the
"felt vs real" contrast — how much conflict the world's news is reporting, set
against the objective lines; the gap is the anxiety premium of the age.

Reading: the share of GDELT events coded as MATERIAL CONFLICT (QuadClass 4 —
assault, fight, mass violence) in the latest 15-minute global event file, in
percent. A rising share is the notable direction.

Source: GDELT 2.0 raw event files at data.gdeltproject.org — static downloads,
no API and no rate limit (the GDELT DOC API is unreliable). The lastupdate
pointer gives the newest export.CSV.zip; we read its events and take the share.
"""
import io
import zipfile

import requests

LINE = "gdelt"
LABEL = "Global conflict-event share (GDELT)"
UNIT = "%"
ANOMALY_DIRECTION = "up"
TIER = 2

_LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}
_QUADCLASS_COL = 29  # 0-based column in the GDELT 2.0 event row; "4" == material conflict


def fetch_daily():
    try:
        lu = requests.get(_LASTUPDATE, headers=_HEADERS, timeout=20)
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"GDELT lastupdate failed: {type(e).__name__}"}
    if lu.status_code != 200:
        return {"raw_value": None, "source_note": f"GDELT lastupdate HTTP {lu.status_code}"}
    url = None
    for line in lu.text.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[2].endswith("export.CSV.zip"):
            url = parts[2]
            break
    if not url:
        return {"raw_value": None, "source_note": "GDELT export file not listed"}
    try:
        z = requests.get(url, headers=_HEADERS, timeout=40)
    except requests.RequestException as e:
        return {"raw_value": None, "source_note": f"GDELT download failed: {type(e).__name__}"}
    if z.status_code != 200:
        return {"raw_value": None, "source_note": f"GDELT download HTTP {z.status_code}"}
    try:
        zf = zipfile.ZipFile(io.BytesIO(z.content))
        rows = zf.read(zf.namelist()[0]).decode("utf-8", "replace").splitlines()
    except (zipfile.BadZipFile, IndexError, KeyError):
        return {"raw_value": None, "source_note": "GDELT file unreadable"}

    total = conflict = 0
    for row in rows:
        cols = row.split("\t")
        if len(cols) > _QUADCLASS_COL:
            total += 1
            if cols[_QUADCLASS_COL] == "4":
                conflict += 1
    if total == 0:
        return {"raw_value": None, "source_note": "GDELT file had no usable events"}
    stamp = url.split("/")[-1][:14]  # YYYYMMDDHHMMSS of the file
    return {
        "raw_value": round(conflict / total * 100.0, 3),
        "source_note": f"GDELT material-conflict share {conflict}/{total} events @ {stamp}",
    }
