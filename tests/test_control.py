"""The control line's job is to be checkable. This is the LOGIC half of the check.

Day length at a fixed point is an exact function of the date, so every committed
row can be verified against astronomy WITHOUT the network and WITHOUT the
scoring machinery. The verification of the COMMITTED rows lives in
audit_record.py (which imports this module's astronomy) and runs after the
commit — a canary tripping is exactly when collection must keep running and the
alarm must fire, so it cannot sit in the pre-collect gate. What stays here is
everything derivable without the record: the canary's own sensitivity, the
line's constants, and the estimator's known behavior on a pure trend.
"""
import datetime
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers import control_daylength as control


def astronomical_day_length_h(lat_deg, day):
    """Day length in hours, reproducing the SOURCE's published model, not
    astronomical truth.

    sunrise-sunset.org does not publish a textbook sunrise equation: its
    ``day_length`` reproduces Paul Schlyter's sunriset routine (the same one
    carried by PHP's ``date_sun_info``) — sun position at 12h local mean solar
    time, at altitude -50' with the apparent semidiameter (0.2666 deg / r)
    subtracted a SECOND time, for an effective depression near 1.10 deg rather
    than the standard 0.833 deg. Reproducing the source's own model here,
    instead of a more accurate NOAA/Meeus one, is the point: the canary this
    function feeds compares a recorded value to what the SOURCE would have
    said for that date, so it is a DATE check, not an astronomy check. An
    accurate formula would be off by several minutes on every row and would
    misidentify the closest day on the committed record.

    The source-redefinition tell: a UNIFORM +3.5-4.5 minute offset appearing
    on every row from one date onward means sunrise-sunset.org changed its
    published model, not that a date slipped — the consecutive-jump audit
    (0.15 h/day) will NOT fire on a uniform shift, because it looks at
    day-to-day differences, not levels. Recovery from that is an annotation
    plus a forward-only bump of this model, never a rewrite of past rows.
    """
    d = (day - datetime.date(1999, 12, 31)).days + 0.5 - control.LON / 360.0
    w = (282.9404 + 4.70935e-5 * d) % 360.0
    e = 0.016709 - 1.151e-9 * d
    M = (356.0470 + 0.9856002585 * d) % 360.0
    M_r = math.radians(M)
    # eccentric anomaly; e * (180/pi) scales the radians correction term into the
    # degrees that M is carried in (e is the dimensionless eccentricity, not an angle).
    Es = math.radians(M + e * (180.0 / math.pi) * math.sin(M_r) * (1 + e * math.cos(M_r)))
    xv = math.cos(Es) - e
    yv = math.sqrt(1 - e * e) * math.sin(Es)
    r = math.sqrt(xv * xv + yv * yv)
    lon_sun = (math.degrees(math.atan2(yv, xv)) + w) % 360.0
    obl = 23.4393 - 3.563e-7 * d
    lon_r, obl_r = math.radians(lon_sun), math.radians(obl)
    # declination in radians, fed straight to sin/cos below — the reference model's
    # convert-to-degrees-then-back-to-radians step cancels, so it is dropped here.
    decl = math.atan2(r * math.sin(lon_r) * math.sin(obl_r),
                       math.sqrt((r * math.cos(lon_r)) ** 2
                                 + (r * math.sin(lon_r) * math.cos(obl_r)) ** 2))
    altit = math.radians(-50.0 / 60.0 - 0.2666 / r)
    lat = math.radians(lat_deg)
    cost = ((math.sin(altit) - math.sin(lat) * math.sin(decl))
            / (math.cos(lat) * math.cos(decl)))
    return 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, cost)))) / 15.0


MARGIN_H = 5.0 / 3600.0  # 5 seconds, in hours


def closest_day_margin(lat_deg, obs_date, recorded_h, margin_h=MARGIN_H):
    """Closest-day margin check, shared by the GATE proof below and the record
    audit (``tests/audit_record.py``) so the k-loop logic lives in one place.

    Compares ``recorded_h`` against the model for ``obs_date`` and for each of
    the three days on either side. Returns ``(skip, resid0, best)``: ``resid0``
    is the residual against day 0 (the day the row claims), ``best`` is the
    smallest residual over the 7-day window, and ``skip`` is True when the
    window's own neighbours sit within ``margin_h`` of day 0 — meaning the
    days are too close together to resolve which one is really closest. That
    happens by construction near a solstice (e.g. 2026-12-21 vs 2026-12-22
    differ by under a second) and must not be allowed to trip the caller's
    assertion on which side of a near-tie floating point happens to land on;
    the caller should skip its assertion for that row and rely on the coarser
    absolute-tolerance check instead.

    When not skipped, the caller's assertion is a MARGIN — ``resid0 <= best +
    margin_h`` — never strict argmin equality, because day 0 legitimately
    ties or nearly ties the true closest day whenever the model changes
    slowly from one day to the next.
    """
    models = {k: astronomical_day_length_h(lat_deg, obs_date + datetime.timedelta(days=k))
              for k in range(-3, 4)}
    resid0 = abs(recorded_h - models[0])
    best = min(abs(recorded_h - m) for m in models.values())
    neighbour_gap = min(abs(models[k] - models[0]) for k in models if k != 0)
    skip = neighbour_gap < margin_h
    return skip, resid0, best


class TestControlLine(unittest.TestCase):
    def test_a_one_day_slip_would_now_be_caught(self):
        """The canary must be able to fail. Prove it on a date away from solstice."""
        day = datetime.date(2026, 8, 1)
        drift = abs(astronomical_day_length_h(control.LAT, day)
                    - astronomical_day_length_h(control.LAT,
                                                day - datetime.timedelta(days=1)))
        self.assertGreater(drift, 0.017,
                           "a one-day slip is smaller than the tolerance; the canary is blind")

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


class TestReproducesTheSourcesPublishedModel(unittest.TestCase):
    """Pins the formula to values sunrise-sunset.org actually published — not to
    any formula, however standard. This is the test issue #3 exists to add: it
    is a DATE check on the SOURCE's model, and its ground truth is the vendor's
    own output, never a re-derivation.

    source: https://api.sunrise-sunset.org/json; lat 51.4779 lng 0.0
    formatted=0; fetched 2026-09-08.
    """

    REFERENCE_SECONDS = {
        "2025-12-21": 28456, "2026-01-05": 29157, "2026-02-11": 35408,
        "2026-03-20": 44024, "2026-04-15": 50147, "2026-05-20": 57313,
        "2026-06-21": 60148, "2026-07-15": 58467, "2026-09-06": 47902,
        "2026-09-22": 44166, "2026-10-15": 38799, "2026-11-03": 34586,
        "2026-12-21": 28457,
    }

    def test_matches_the_published_day_length_within_five_seconds(self):
        for date_s, ref_seconds in self.REFERENCE_SECONDS.items():
            day = datetime.date.fromisoformat(date_s)
            got = astronomical_day_length_h(control.LAT, day) * 3600
            self.assertLessEqual(
                abs(got - ref_seconds), 5,
                f"{date_s}: source published {ref_seconds}s, model gives "
                f"{got:.1f}s — the model has drifted off the source it must "
                f"reproduce")


class TestClosestDayMarginLogic(unittest.TestCase):
    """Proves the closest-day margin helper (``closest_day_margin``, shared
    with tests/audit_record.py) is a MARGIN check, not strict argmin, and
    that its skip condition is real rather than decorative.

    2026-12-21 vs 2026-12-22: the model's day length differs by only about
    0.89 seconds — far under the 5 s MARGIN — so a row naming either date
    must be exempted from the closest-day assertion (the coarser 0.017 h
    absolute-tolerance check still covers it). Do NOT tighten the skip
    condition or replace the margin with strict argmin equality: either
    change reintroduces a guaranteed false trip at every solstice, because
    Python's ``min()`` breaks a tie by returning the first (most negative) k,
    which has no relationship to which day the row actually describes.
    """

    def test_silent_near_the_december_solstice_near_tie(self):
        obs_date = datetime.date(2026, 12, 21)
        # A row that actually describes the NEXT day, mislabeled as this one
        # -- exactly the shape of slip the check exists to catch elsewhere,
        # but here the neighbours are too close to resolve it.
        recorded = astronomical_day_length_h(control.LAT,
                                              obs_date + datetime.timedelta(days=1))
        skip, _, _ = closest_day_margin(control.LAT, obs_date, recorded)
        self.assertTrue(skip, "solstice neighbours differ by under a second; "
                              "the check must not attempt to resolve them")

    def test_fires_on_a_synthetic_one_day_slip_in_august(self):
        obs_date = datetime.date(2026, 8, 1)
        # A row that actually describes the NEXT day, mislabeled as this one
        # -- a real 1-day slip, far from any solstice, where the days ARE
        # resolvable and the margin check must catch it.
        recorded = astronomical_day_length_h(control.LAT,
                                              obs_date + datetime.timedelta(days=1))
        skip, resid0, best = closest_day_margin(control.LAT, obs_date, recorded)
        self.assertFalse(skip, "August neighbours are resolvable; this row "
                               "should not be exempted")
        self.assertGreater(resid0, best + MARGIN_H,
                           "a real 1-day slip must miss day 0 by more than "
                           "the best candidate plus the margin, or the check "
                           "is blind")


if __name__ == "__main__":
    unittest.main()
