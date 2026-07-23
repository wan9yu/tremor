"""Arctic 80N temperature anomaly — a planetary CONTEXT line (never counted).

NOT a tension indicator. There is no guard: nobody defends the temperature of
the Arctic at a set point that a hidden force overpowers — it is a free-floating
physical read, the same category as a river gauge or seismic energy, which the
guard gate excludes. So this line can never be counted in the resonance and can
never be promoted to tier-1, exactly like the vix / gdelt contrast lines.

Its job is auxiliary interpretation. The founding question — "is the world
actually more disordered?" — is a LEVEL question that tremor's change-detecting z
answers poorly for anything slow, and the planet's physical baseline is the
slowest signal of all. This line reads today's DMI mean temperature north of 80N
against the fixed 1958-2002 climate normal, so the number is a direct level: how
far the high Arctic sits from its historical normal today. Positive (warmer) is
the noteworthy direction. Because the seasonal cycle is huge (~-29C in winter,
near 0C in the melt season) and is removed by the anomaly, the daily value is
comparable across the year; the summer normal being near freezing is why summer
anomalies run small while the real warming shows in winter.

Source: DMI (Danish Meteorological Institute), daily mean temperature +80N,
running text file per year. Keyless, ~1-day lag. The long baseline is vendored in
core/arctic_clim.py rather than re-fetched, so each daily reading is self-contained.
"""
from datetime import datetime, timezone

import requests

from core import arctic_clim

LINE = "polar_temp"
LABEL = "Arctic 80N temp anomaly (vs 1958-2002)"
UNIT = "°C"
ANOMALY_DIRECTION = "up"  # warmer than the historical normal is the noteworthy way
TIER = 2  # context line — fails the guard gate, never counted, never promotable

_URL = "https://download.dmi.dk/pub/plus80N_temperatureindex/meanT{year}_running.txt"
_HEADERS = {"User-Agent": "tremor/1.0 (+https://github.com/wan9yu/tremor)"}


def fetch_daily():
    """Return {"raw_value": float | None, "source_note": str, "obs_date": str}.

    raw_value is the anomaly in °C = latest DMI +80N mean temp − the 1958-2002
    normal for that day-of-year. The DMI file is dated by observation, so obs_date
    is set and the dedup rule applies if a day is republished unchanged.
    """
    year = datetime.now(timezone.utc).year
    text = None
    # The file is per calendar year; around New Year the current-year file may not
    # exist yet, so fall back to last year's.
    for y in (year, year - 1):
        try:
            r = requests.get(_URL.format(year=y), headers=_HEADERS, timeout=25)
        except requests.RequestException as e:
            return {"raw_value": None, "source_note": f"DMI request failed: {type(e).__name__}"}
        if r.status_code == 200 and len(r.text) > 40:
            text = r.text
            break
    if text is None:
        return {"raw_value": None, "source_note": "DMI +80N file unavailable"}

    last = None
    for line in text.strip().splitlines():
        parts = line.split()
        # rows are: YYYYMMDD  day_of_year  temp_kelvin
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
            last = parts
    if last is None:
        return {"raw_value": None, "source_note": "DMI +80N file had no data rows"}

    try:
        obs_date = datetime.strptime(last[0], "%Y%m%d").strftime("%Y-%m-%d")
        doy = int(last[1])
        temp_k = float(last[2])
    except (ValueError, IndexError):
        return {"raw_value": None, "source_note": "DMI +80N row unparseable"}

    anomaly = temp_k - arctic_clim.normal_k(doy)
    return {
        "raw_value": round(anomaly, 3),
        "source_note": (f"DMI +80N {obs_date}: {temp_k - 273.15:.2f}°C, "
                        f"{anomaly:+.2f}°C vs 1958-2002 normal (context line, never counted)"),
        "obs_date": obs_date,
    }
