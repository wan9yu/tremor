"""The one definition of "today" for tremor.

Rows are dated in China time (UTC+8, no DST): the daily run fires at 06:00
China, so a row dated D was collected on the morning of D, China time — which
matches how the project reads the calendar.

The value is resolved ONCE per process and reused. The collector and the lagged
fetchers each need to know the collection date, and if they each read the clock
independently, a run that straddles midnight would write a row dated D whose
observation target was computed from D-1 — an off-by-one with no trace in the
record. One resolution per process makes them agree by construction rather than
by luck.
"""
from datetime import datetime, timedelta, timezone

CHINA_TZ = timezone(timedelta(hours=8))

_today = None


def china_today():
    """Today's date in China time as an ISO string, fixed for this process."""
    global _today
    if _today is None:
        _today = datetime.now(CHINA_TZ).strftime("%Y-%m-%d")
    return _today
