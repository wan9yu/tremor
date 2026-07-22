"""The one definition of "today" for tremor.

Rows are dated in China time (UTC+8, no DST): the daily run fires at 06:00
China, so a row dated D was collected on the morning of D, China time — which
matches how the project reads the calendar. Lives here so the collector and any
fetcher that needs to know the collection date agree by construction, rather
than computing it twice and disagreeing across a midnight boundary.
"""
from datetime import datetime, timedelta, timezone

CHINA_TZ = timezone(timedelta(hours=8))


def china_today():
    """Today's date in China time, as an ISO string."""
    return datetime.now(CHINA_TZ).strftime("%Y-%m-%d")
