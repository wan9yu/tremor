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


def _day_length_h(lat_deg, day, depression_deg_of_r):
    """The reference geometry both published generations share: Paul Schlyter's
    sunriset routine, solved for the day length at a fixed point.

    ``depression_deg_of_r(r)`` returns the solar altitude, in degrees (negative
    = below the horizon), at which the day starts and ends, given the
    earth-sun distance ``r`` in AU. The source's two published generations
    differ ONLY in that argument — see ``astronomical_day_length_h`` and
    ``astronomical_day_length_h_v2`` — so the geometry lives here once rather
    than twice.
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
    altit = math.radians(depression_deg_of_r(r))
    lat = math.radians(lat_deg)
    cost = ((math.sin(altit) - math.sin(lat) * math.sin(decl))
            / (math.cos(lat) * math.cos(decl)))
    return 2.0 * math.degrees(math.acos(max(-1.0, min(1.0, cost)))) / 15.0


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

    The source-redefinition tell: a UNIFORM offset — the same direction and
    size on every row from one date onward — means sunrise-sunset.org changed
    its published model, not that a date slipped. The observed direction and
    size belong to that particular shift and are measured from the record, so
    no band is quoted here. The consecutive-jump audit (0.15 h/day) will NOT
    fire on a uniform shift, because it looks at day-to-day differences, not
    levels. Recovery from that is an annotation plus a forward-only bump of
    this model, never a rewrite of past rows.

    This is the FIRST of the source's two published generations. From
    observation date 2026-10-21 the source published a shorter day, and it
    recomputed earlier dates too; every committed row up to observation date
    2026-10-20 was collected under THIS generation, so these numbers stay as
    they were and the second generation is pinned beside them
    (``astronomical_day_length_h_v2``, dispatched by ``source_day_length_h``).
    """
    return _day_length_h(lat_deg, day, lambda r: -50.0 / 60.0 - 0.2666 / r)


# The observation date the source's second published generation starts at. Its
# first committed row is dated 2026-10-22 with obs_date 2026-10-21 (the fetch
# that ran 2026-10-22T22:30Z); the 2026-10-21 row, obs_date 2026-10-20, still
# carries the first generation exactly.
SOURCE_MODEL_CHANGE_OBS_DATE = datetime.date(2026, 10, 21)

# A single effective depression below the horizon minus the first generation's
# semidiameter double-subtraction. Fitted to the vendor's own output, never
# re-derived: pinned by TestReproducesTheSourcesSecondPublishedModel.
_V2_DEPRESSION_DEG = -0.84984


def astronomical_day_length_h_v2(lat_deg, day):
    """Day length in hours, reproducing the source's SECOND published model,
    not astronomical truth.

    Same geometry as the first generation, with the semidiameter
    double-subtraction gone: one flat effective depression of about -0.85°
    reproduces the source's published ``day_length`` to within 4.5 s across
    the 19 samples pinned in TestReproducesTheSourcesSecondPublishedModel (one
    per month for a year, plus the seven around the change). It is a curve
    pinned to the vendor's output, not a re-derivation of the vendor's
    internals — the same discipline as the first generation, and the reason a
    comparison against it is a DATE check.

    A further published shift moves this pin and needs its OWN dated
    generation; it never edits this one, because rows already scored under it
    are published and forward-only.
    """
    return _day_length_h(lat_deg, day, lambda r: _V2_DEPRESSION_DEG)


def source_model_for(obs_date):
    """The model FUNCTION the source published on observation date ``obs_date``.

    One generation per row: the caller applies the returned function to every
    day it wants to ask about, because a row was collected at one moment, when
    the source published ONE generation for all dates. Comparing a row against
    a window whose days come from different generations would compare a value
    produced by one model definition to a model definition that never produced
    it.
    """
    if obs_date >= SOURCE_MODEL_CHANGE_OBS_DATE:
        return astronomical_day_length_h_v2
    return astronomical_day_length_h


def source_day_length_h(lat_deg, day):
    """The day length the source published for ``day`` under the generation
    that was in force on that observation date.

    A dated correction, applied here — the comparison site — and not inside
    either pinned model. The committed record holds both generations at once:
    rows collected before the change carry the first, rows from observation
    date 2026-10-21 on carry the second, and the source recomputed its own
    past dates, so its current answer for a pre-change date says nothing about
    which generation that row was collected under. Only the row's obs_date
    does.
    """
    return source_model_for(day)(lat_deg, day)


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

    The model is ``source_model_for(obs_date)``: the generation the source
    published on the row's own observation date, applied to all seven
    candidate days, because the row was collected under that one generation
    and the two differ by more than the margin. Dispatching per candidate day
    instead would let a boundary row compare itself against a day modelled by
    the generation that never produced it.
    """
    model = source_model_for(obs_date)
    models = {k: model(lat_deg, obs_date + datetime.timedelta(days=k))
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
        doc = control.__doc__ or self.fail(
            "fetchers/control_daylength.py carries no module docstring, so it "
            "cannot declare what it is")
        self.assertIn("CONTROL", doc.upper())

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
    any formula, however standard. This is the test the R28 canary fix added: it
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


class TestReproducesTheSourcesSecondPublishedModel(unittest.TestCase):
    """Pins the SECOND generation of the source's published model.

    sunrise-sunset.org re-defined its published day-length model between the
    2026-10-21 and 2026-10-22 22:30Z collections. Every committed control row
    from observation date 2026-10-21 onward records a day about 200 s shorter
    than the first generation's model says, and the source now answers a
    request for a date BEFORE the change with the shorter value too: 2026-10-15
    asked on 2026-11-01 returned 38601 s, where the same date asked on
    2026-09-08 (the first generation's own fetch) returned 38799 s. That is a
    published-model change, not a date-label slip — the record's notes carry
    the source's sunrise and sunset for the claimed date and the pair sums to
    the recorded day length, and the source's current value for each claimed
    date equals the recorded value exactly.

    This table is the second generation's ground truth: the vendor's own
    output, one sample per month for a year plus the seven samples around the
    change. ``astronomical_day_length_h_v2`` is a SINGLE effective depression
    fitted to them (the first generation's semidiameter double-subtraction is
    gone), which is why the tolerance is 10 s rather than the 5 s the first
    generation pins — the fit's residual is a ±4.4 s annual sinusoid. The
    record check keeps its own 1.02 min tolerance (tests/audit_record.py), so
    this pin is a further-source-shift alarm, not the canary's working bar.

    source: https://api.sunrise-sunset.org/json; lat 51.4779 lng 0.0
    formatted=0; fetched 2026-11-01.
    """

    REFERENCE_SECONDS = {
        "2026-10-14": 38832, "2026-10-15": 38601, "2026-10-20": 37457,
        "2026-10-21": 37231, "2026-10-22": 37005, "2026-10-30": 35232,
        "2026-11-03": 34376, "2026-11-15": 31990, "2026-12-15": 28342,
        "2027-01-15": 30076, "2027-02-15": 36035, "2027-03-15": 42581,
        "2027-04-15": 49890, "2027-05-15": 56181, "2027-06-15": 59780,
        "2027-07-15": 58255, "2027-08-15": 52689, "2027-09-15": 45669,
        "2027-10-15": 38658,
    }

    def test_matches_the_published_day_length_within_ten_seconds(self):
        for date_s, ref_seconds in self.REFERENCE_SECONDS.items():
            day = datetime.date.fromisoformat(date_s)
            got = astronomical_day_length_h_v2(control.LAT, day) * 3600
            self.assertLessEqual(
                abs(got - ref_seconds), 10,
                f"{date_s}: source published {ref_seconds}s, the second-generation "
                f"model gives {got:.1f}s — the source's model has moved again")


class TestTheComparisonSiteFollowsTheModelGeneration(unittest.TestCase):
    """The record holds two published generations at once, so the comparison
    site picks by the ROW's observation date, never by "the model today".

    The source recomputed dates before its own change as well, so asking the
    source what it says NOW cannot tell a pre-change row which generation it
    was collected under; only the observation date can. Read forward-only:
    the pre-change rows were published under the first generation and stay
    checked against it.

    Tolerance for the committed-row assertions below is the record check's
    own 1.02 min (tests/audit_record.py), not the 5 s published-model
    fidelity pin — these assert that the dated correction puts the committed
    values where the canary needs them, not that the fit is perfect.
    """

    # The ten committed rows dated 2026-10-22 or later: (row date, claimed
    # observation date, recorded seconds), copied from data/control_daylength.csv
    # at 2026-10-31. A gate test may not read data/, so the values are pinned.
    COMMITTED_POST_CHANGE = (
        ("2026-10-22", "2026-10-21", 37231),
        ("2026-10-23", "2026-10-22", 37005),
        ("2026-10-24", "2026-10-23", 36780),
        ("2026-10-25", "2026-10-24", 36556),
        ("2026-10-26", "2026-10-25", 36332),
        ("2026-10-27", "2026-10-26", 36110),
        ("2026-10-28", "2026-10-27", 35889),
        ("2026-10-29", "2026-10-28", 35669),
        ("2026-10-30", "2026-10-29", 35449),
        ("2026-10-31", "2026-10-30", 35232),
    )

    RECORD_TOL_H = 0.017  # 1.02 min, tests/audit_record.py's obs_date bar

    def test_the_generation_switches_on_the_2026_10_21_observation_date(self):
        before = datetime.date(2026, 10, 20)
        after = datetime.date(2026, 10, 21)
        self.assertEqual(source_day_length_h(control.LAT, before),
                         astronomical_day_length_h(control.LAT, before),
                         "observation date 2026-10-20 was collected under the "
                         "first generation and must stay on it")
        self.assertEqual(source_day_length_h(control.LAT, after),
                         astronomical_day_length_h_v2(control.LAT, after),
                         "observation date 2026-10-21 is the first row of the "
                         "second generation")

    def test_the_two_generations_are_further_apart_than_the_record_tolerance(self):
        """If they were not, the dated correction would be decoration."""
        day = datetime.date(2026, 10, 21)
        gap_h = abs(astronomical_day_length_h(control.LAT, day)
                    - astronomical_day_length_h_v2(control.LAT, day))
        self.assertGreater(
            gap_h, self.RECORD_TOL_H,
            f"the two generations differ by only {gap_h * 3600:.1f}s at "
            f"2026-10-21 — under the {self.RECORD_TOL_H * 3600:.0f}s record "
            f"tolerance the choice would not matter")

    def test_every_committed_post_change_row_lands_on_the_second_generation(self):
        for row_date, obs_date, seconds in self.COMMITTED_POST_CHANGE:
            day = datetime.date.fromisoformat(obs_date)
            recorded_h = seconds / 3600.0
            self.assertLess(
                abs(recorded_h - source_day_length_h(control.LAT, day)),
                self.RECORD_TOL_H,
                f"{row_date}: recorded {recorded_h:.4f}h but observation date "
                f"{obs_date} implies "
                f"{source_day_length_h(control.LAT, day):.4f}h under the "
                f"generation in force")

    def test_the_margin_helper_models_every_candidate_day_with_one_generation(self):
        """A boundary row's whole seven-day window uses the generation it was
        collected under, never a mix.

        Synthetic: a row claiming observation date 2026-10-21 (the first
        second-generation date) but carrying the FIRST generation's value for
        2026-10-20. Under one generation every candidate is a second-generation
        day, so no candidate is an exact match and the closest neighbour sits
        about 26 s away. A window that dispatched per candidate day would fall
        back to the first generation for 2026-10-20, find exactly the recorded
        value there and report a perfect neighbour — comparing a
        second-generation row against a first-generation day. Both readings
        still fire the margin alert (resid0 is 428 s either way), so only the
        neighbour residual separates them, which is what this pins.
        """
        obs_date = datetime.date(2026, 10, 21)
        recorded_h = astronomical_day_length_h(
            control.LAT, datetime.date(2026, 10, 20))
        skip, resid0, best = closest_day_margin(control.LAT, obs_date, recorded_h)
        self.assertFalse(skip, "2026-10-21 neighbours are resolvable, so this "
                               "row must not be exempted from the margin check")
        self.assertGreater(resid0, best + MARGIN_H,
                           "a one-generation slip must exceed the margin")
        self.assertGreater(
            best * 3600.0, 1.0,
            "a candidate day matched the recorded value exactly under the "
            "other generation — the window mixed the two generations instead "
            "of using the one the row was collected under")

    def test_the_first_generation_cannot_explain_the_post_change_rows(self):
        """The evidence for the dated correction: the old model misses them."""
        for row_date, obs_date, seconds in self.COMMITTED_POST_CHANGE:
            day = datetime.date.fromisoformat(obs_date)
            recorded_h = seconds / 3600.0
            self.assertGreater(
                abs(recorded_h - astronomical_day_length_h(control.LAT, day)),
                self.RECORD_TOL_H,
                f"{row_date}: the first-generation model already explains the "
                f"recorded value — the generation split is not needed")


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
        recorded = source_day_length_h(control.LAT,
                                      obs_date + datetime.timedelta(days=1))
        skip, _, _ = closest_day_margin(control.LAT, obs_date, recorded)
        self.assertTrue(skip, "solstice neighbours differ by under a second; "
                              "the check must not attempt to resolve them")

    def test_fires_on_a_synthetic_one_day_slip_in_august(self):
        obs_date = datetime.date(2026, 8, 1)
        # A row that actually describes the NEXT day, mislabeled as this one
        # -- a real 1-day slip, far from any solstice, where the days ARE
        # resolvable and the margin check must catch it.
        recorded = source_day_length_h(control.LAT,
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
