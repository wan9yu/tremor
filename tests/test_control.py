"""The control line's job is to be checkable. This is the check.

Day length at a fixed point is an exact function of the date, so every committed
row can be verified against astronomy WITHOUT the network and WITHOUT the
scoring machinery. That is the point: it catches the class of bug no z-score can
see — a row filed under the wrong date, a same-day overwrite from another run, a
timezone boundary, a dedup misfire. This project has already been bitten by a
+1 date-label offset and by manual re-runs overwriting a day.
"""
import csv
import datetime
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers import control_daylength as control


def astronomical_day_length_h(lat_deg, day):
    """Day length in hours from solar geometry — the ground truth, no network.

    Standard sunrise-equation form (CBM model), accurate to a few minutes, which
    is far tighter than the errors this test exists to catch: a wrong date moves
    the value by tens of minutes to hours.
    """
    n = day.timetuple().tm_yday
    decl = math.asin(0.39795 * math.cos(
        0.2163108 + 2 * math.atan(0.9671396 * math.tan(0.00860 * (n - 186)))))
    lat = math.radians(lat_deg)
    x = ((math.sin(math.radians(0.8333)) + math.sin(lat) * math.sin(decl))
         / (math.cos(lat) * math.cos(decl)))
    return 24 - (24 / math.pi) * math.acos(max(-1.0, min(1.0, x)))


class TestControlLine(unittest.TestCase):
    PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "control_daylength.csv")

    def _rows(self):
        if not os.path.exists(self.PATH):
            self.skipTest("control line has no data yet")
        with open(self.PATH, newline="") as f:
            return [r for r in csv.DictReader(f) if r["raw_value"]]

    def test_every_row_matches_the_astronomy_for_its_own_date(self):
        """The canary. A mismatch means the pipeline mishandled a date."""
        for r in self._rows():
            day = datetime.date.fromisoformat(r["date"])
            expected = astronomical_day_length_h(control.LAT, day)
            actual = float(r["raw_value"]) / 3600.0
            self.assertLess(
                abs(actual - expected), 0.25,  # 15 minutes; a wrong date costs far more
                f"{r['date']}: recorded {actual:.4f}h but its own date implies "
                f"{expected:.4f}h — the pipeline mishandled a date")

    def test_consecutive_rows_move_by_a_physically_possible_amount(self):
        """Catches a row overwritten by a run from a different day."""
        rows = self._rows()
        for prev, cur in zip(rows, rows[1:]):
            days = (datetime.date.fromisoformat(cur["date"])
                    - datetime.date.fromisoformat(prev["date"])).days
            jump = abs(float(cur["raw_value"]) - float(prev["raw_value"])) / 3600.0
            # This latitude gains/loses at most ~4.5 min a day, even at equinox.
            self.assertLess(jump, 0.1 * max(days, 1) + 0.05,
                            f"{prev['date']} -> {cur['date']}: {jump:.3f}h in {days} day(s)")

    def test_it_is_a_control_and_can_never_be_counted(self):
        self.assertEqual(control.TIER, 2)
        self.assertIn("CONTROL", control.fetch_daily.__module__ and
                      control.__doc__.upper())

    def test_the_location_is_fixed(self):
        """Moving it would silently redefine the series."""
        self.assertEqual((control.LAT, control.LON), (51.4779, 0.0))

    def test_the_estimator_fires_on_a_pure_trend_and_we_know_when(self):
        """Ground truth for reading this line: it SHOULD be noisy near the equinoxes.

        400 days of day length contain no disorder whatsoever, yet the scoring
        rules raise trembles on it, because a rolling median lags a sustained
        trend. Locking the shape here means a tremble at the wrong time of year
        is immediately legible as the instrument rather than the trend.
        """
        from core import normalize as N
        start = datetime.date(2025, 7, 1)
        hist, dates, months = [], [], []
        for i in range(400):
            day = start + datetime.timedelta(days=i)
            value = round(astronomical_day_length_h(control.LAT, day) * 3600)
            _, trembling, _, _, _ = N.judge(hist, dates, [""] * len(hist),
                                            float(value), "", day.isoformat())
            if trembling:
                months.append(day.month)
            hist.append(float(value))
            dates.append(day.isoformat())
        self.assertTrue(months, "a pure trend used to fire; if it no longer does, "
                                "the estimator changed and this line's baseline "
                                "expectation must be re-derived")
        # Every firing sits in the steep run-up to an equinox, not scattered.
        self.assertTrue(set(months) <= {2, 3, 9, 10},
                        f"trembles outside the equinox run-ups: {sorted(set(months))}")


if __name__ == "__main__":
    unittest.main()
