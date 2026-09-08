"""The collector spine: `collect()` is the loop the whole instrument runs
through every day, and until now nothing exercised it directly.

Every test here calls the real `collect()` against stub fetcher modules, with
the module's own record-directory and workflow-list attributes redirected to
scratch locations for the block (never a real path under the repository's
record directory). A stub fetcher may return a `components` breakdown via
`_mod`'s `components=` kwarg, which exercises the collector's separate
diagnostic-file writer too, through that same scratch-redirected components
directory — `_CollectCase._run` reads it back by its scratch PATH, never
through the module attribute the collector itself uses for it (a name
`test_side_channel.py` forbids spelling out in any `test_*.py`). This file
reads no committed record and is safe in the pre-collect gate.
"""
import contextlib
import io
import os
import sys
import tempfile
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import collect
import support
from core import normalize


def _mod(line, tier=1, direction="down", crash=False, bad=False, raw=1.0,
         note="stub", target=None, tol=1.5, components=None):
    """A minimal stand-in for a ``fetchers/*.py`` module."""
    m = types.SimpleNamespace(LINE=line, LABEL=line, UNIT="u", TIER=tier,
                              ANOMALY_DIRECTION=direction)
    if target is not None:
        m.SAMPLE_TARGET_UTC_H = target
        m.SAMPLE_TOL_H = tol

    def fetch_daily():
        if crash:
            raise RuntimeError("source exploded")
        if bad:
            return "not a dict"
        result = {"raw_value": raw, "source_note": note}
        if components is not None:
            result["components"] = components
        return result
    m.fetch_daily = fetch_daily
    return m


class _CollectCase(unittest.TestCase):
    """Base for any test that runs the real ``collect()`` against ``mods``
    inside a pair of scratch directories, discarded when the block ends, then
    hands back the rows it wrote for inspection. Extra ``(attr, value)``
    pairs are stubbed on the module for the same block (used to spy on
    ``score_row``)."""

    def _run(self, mods, **extra_stubs):
        with tempfile.TemporaryDirectory() as scratch, \
             tempfile.TemporaryDirectory() as scratch_docs, \
             support.stub_attr(collect, "LINES", mods), \
             support.stub_attr(collect, "DATA", scratch), \
             support.stub_attr(collect, "DOCS_DATA", scratch_docs), \
             support.stub_attr(collect, "COMPONENTS", os.path.join(scratch, "components")), \
             contextlib.ExitStack() as stack:
            for attr, value in extra_stubs.items():
                stack.enter_context(support.stub_attr(collect, attr, value))
            # collect() prints one line per module plus a summary line; the gate
            # runs `unittest discover` without `-b`, so left un-silenced this is
            # the only test in the suite that prints instead of dotting.
            with contextlib.redirect_stdout(io.StringIO()):
                collect.collect()
            lines = {mod.LINE: collect._read_rows(os.path.join(scratch, mod.LINE + ".csv"))
                     for mod in mods}
            summary = collect._read_rows(os.path.join(scratch, "summary.csv"))
            # Read the scratch components directory back BY PATH, not through
            # the collector's own module-level constant for it (spelling
            # that out is forbidden in any test_*.py by test_side_channel.py)
            # — a module with no components breakdown simply reads back an
            # empty list, since write_components never created its file.
            components = {mod.LINE: collect._read_rows(
                              os.path.join(scratch, "components", mod.LINE + ".csv"))
                         for mod in mods}
        return lines, summary, components


class TestOneBadSourceCannotAbortTheRun(_CollectCase):
    """A fetcher that raises, or one that returns garbage instead of raising,
    must dark its own line and let every remaining line still be collected."""

    def test_a_crashing_fetcher_does_not_abort_the_run(self):
        crashed = _mod("crashed_line", crash=True)
        healthy = _mod("healthy_line", raw=1.0)
        lines, _, _ = self._run([crashed, healthy])

        (row,) = lines["crashed_line"]
        self.assertEqual(row["status"], normalize.STATUS_DARK)
        self.assertIn("fetcher crashed: RuntimeError", row["source_note"])

        # The run did not stop at the crash: the line after it was collected too.
        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")

    def test_a_malformed_result_does_not_abort_the_run(self):
        malformed = _mod("malformed_line", bad=True)
        healthy = _mod("healthy_line", raw=1.0)
        lines, _, _ = self._run([malformed, healthy])

        (row,) = lines["malformed_line"]
        self.assertEqual(row["status"], normalize.STATUS_DARK)
        self.assertIn("fetcher returned a malformed result", row["source_note"])

        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")


class TestTierOneOnlyCountingAndTheDarkBlindSplit(_CollectCase):
    """``score_row`` is stubbed to return a canned verdict keyed by each stub's
    (unique) raw value, so the aggregation in ``collect()`` — not
    ``normalize.judge`` — is what is under test: only tier-1 lines count
    toward any of the three summary tallies, and trembling counts only when
    the direction matches the line's declared alarm direction.

    Each category (trembling, dark, blind) fields TWO tier-1 members against
    only ONE tier-2 member, and the trembling category also fields two
    direction-matching members against only one mismatching member — every
    expected count is therefore asymmetric. A 1-vs-1 fixture cannot tell
    ``tier == 1`` apart from its inverse ``tier == 2`` (every count would
    still land on the same total with the roles swapped), nor
    ``direction == alarm`` apart from ``!=``; the asymmetry here means either
    inversion moves at least one of the three totals away from its expected
    value."""

    def test_only_tier_one_and_direction_matched_trembles_count(self):
        # (status, trembling, VERDICT direction) keyed by each stub's raw value.
        canned = {
            # trembling: two tier-1 matches, one tier-1 mismatch, one tier-2 match
            1.0: (normalize.STATUS_SCORING, 1, "down"),   # tier1, matches -> counts
            2.0: (normalize.STATUS_SCORING, 1, "down"),   # tier1, matches -> counts
            3.0: (normalize.STATUS_SCORING, 1, "up"),     # tier1, wrong direction
            4.0: (normalize.STATUS_SCORING, 1, "down"),   # tier2, matches but demoted
            # dark: two tier-1, one tier-2
            5.0: (normalize.STATUS_DARK, 0, ""),
            6.0: (normalize.STATUS_DARK, 0, ""),
            7.0: (normalize.STATUS_DARK, 0, ""),          # tier2 dark (must not count)
            # blind: two tier-1 (one WARMING, one FLAT), one tier-2
            8.0: (normalize.STATUS_WARMING, 0, ""),
            9.0: (normalize.STATUS_FLAT, 0, ""),
            10.0: (normalize.STATUS_WARMING, 0, ""),      # tier2 blind (must not count)
        }

        def fake_score_row(date, raw, note, obs_date, prior_rows, **kwargs):
            status, trembling, direction = canned[raw]
            return {"date": date, "raw_value": collect._fmt(raw), "z_score": "",
                    "trembling": str(trembling), "direction": direction,
                    "source_note": note, "obs_date": obs_date or "", "status": status}

        # Every module here declares the SAME alarm direction ("down"); only
        # t1_tremble_mismatch's canned verdict direction disagrees with it.
        mods = [
            _mod("t1_tremble_match_a", tier=1, direction="down", raw=1.0),
            _mod("t1_tremble_match_b", tier=1, direction="down", raw=2.0),
            _mod("t1_tremble_mismatch", tier=1, direction="down", raw=3.0),
            _mod("t2_tremble_match", tier=2, direction="down", raw=4.0),
            _mod("t1_dark_a", tier=1, raw=5.0),
            _mod("t1_dark_b", tier=1, raw=6.0),
            _mod("t2_dark", tier=2, raw=7.0),
            _mod("t1_blind_a", tier=1, raw=8.0),
            _mod("t1_blind_b", tier=1, raw=9.0),
            _mod("t2_blind", tier=2, raw=10.0),
        ]
        _, summary, _ = self._run(mods, score_row=fake_score_row)

        (row,) = summary
        self.assertEqual(row["trembling_count"], "2")
        self.assertEqual(row["dark_count"], "2")
        self.assertEqual(row["blind_count"], "2")


class TestSampleGuardAttrsRequireBothTogether(unittest.TestCase):
    """``_sample_guard_attrs`` is what ``collect()`` reads a line's sample-hour
    guard settings through. ``SAMPLE_TOL_H`` has no line-agnostic default it
    could safely fall back to — it is derived from THAT line's own diurnal
    curve (flights' 1.5h from aircraft-aloft slopes, cnh_cny's tighter 0.5h
    from its own hour-means) — so a module declaring only
    ``SAMPLE_TARGET_UTC_H`` must be refused, not silently given another
    line's tolerance. (``apply_sample_guard`` itself is exercised directly in
    ``tests/test_flights_sample_guard.py``, along with the flights/cnh_cny
    tolerances and the schedule-arithmetic checks.)"""

    def test_no_target_needs_no_tolerance(self):
        mod = types.SimpleNamespace(LINE="untargeted_line")
        self.assertEqual(collect._sample_guard_attrs(mod), (None, None))

    def test_a_target_without_its_own_tolerance_is_refused(self):
        mod = types.SimpleNamespace(LINE="new_line", SAMPLE_TARGET_UTC_H=22.5)
        with self.assertRaises(ValueError) as cm:
            collect._sample_guard_attrs(mod)
        self.assertIn("new_line", str(cm.exception))
        self.assertIn("SAMPLE_TOL_H", str(cm.exception))

    def test_a_target_with_its_own_tolerance_is_returned_as_declared(self):
        mod = types.SimpleNamespace(LINE="cnh_cny", SAMPLE_TARGET_UTC_H=22.5,
                                    SAMPLE_TOL_H=0.5)
        self.assertEqual(collect._sample_guard_attrs(mod), (22.5, 0.5))


class TestScoringAttrsNeverReachesTheScorerThroughTheLoop(_CollectCase):
    """``scoring_attrs`` already has a direct check for flights in
    ``tests/test_flights_sample_guard.py``; this covers the loop's own
    behavior instead of repeating it — a spy on ``score_row`` captures the
    exact keyword set ``collect()`` passes it for a module that declares a
    sample target, proving the collection-time attribute never crosses into
    the scoring call even though it lives on the same module object."""

    def test_a_guarded_modules_sample_attrs_never_reach_score_row(self):
        captured = {}
        real_score_row = collect.score_row

        def spy_score_row(date, raw, note, obs_date, prior_rows, **kwargs):
            captured["kwargs"] = kwargs
            return real_score_row(date, raw, note, obs_date, prior_rows, **kwargs)

        guarded = _mod("guarded_line", raw=1.0, target=22.5, tol=1.5)
        self._run([guarded], score_row=spy_score_row)

        self.assertEqual(set(captured["kwargs"]),
                         {"weekly_cycle", "quantum", "anchor", "materiality",
                          "weekend_market"})
        for banned in ("sample_target_utc_h", "SAMPLE_TARGET_UTC_H",
                       "sample_tol_h", "SAMPLE_TOL_H"):
            self.assertNotIn(banned, captured["kwargs"])


class TestNonNumericOrNonFiniteRawIsDarkened(_CollectCase):
    """A fetcher can also return a well-SHAPED result whose ``raw_value`` is
    not a finite number: ``"banana"``, a bool, or nan/inf (which ``float()``
    happily accepts). ``coerce_finite`` in ``collect()`` closes that boundary
    gap — this line must be darkened, exactly like the crashing/malformed
    fetchers in ``TestOneBadSourceCannotAbortTheRun`` above, and must never
    let a stored ``'nan'``/``'inf'`` string reach the forward-only CSV."""

    def test_each_bad_raw_shape_is_darkened_and_the_run_continues(self):
        for bad_raw in ("banana", True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(raw=bad_raw):
                bad = _mod("bad_line", raw=bad_raw)
                healthy = _mod("healthy_line", raw=1.0)
                lines, _, _ = self._run([bad, healthy])

                (row,) = lines["bad_line"]
                self.assertEqual(row["status"], normalize.STATUS_DARK)
                self.assertEqual(row["raw_value"], "")
                self.assertEqual(row["obs_date"], "")
                self.assertEqual(row["z_score"], "")
                self.assertIn("non-numeric/non-finite raw_value", row["source_note"])
                # The failure this guards against: a stored 'nan'/'inf'
                # STRING in a SCORED field. (The prose note legitimately
                # names the rejected value for diagnosis, so it is not
                # checked here.)
                for field in ("raw_value", "z_score"):
                    self.assertNotIn("nan", row[field])
                    self.assertNotIn("inf", row[field])

                # The run did not stop at the bad line: the line after it
                # was still collected.
                (healthy_row,) = lines["healthy_line"]
                self.assertEqual(healthy_row["raw_value"], "1")


class TestGoodRawShapesAreStoredByteIdenticalAcrossTheCoercionStep(_CollectCase):
    """``coerce_finite``'s new step in ``collect()`` must be invisible to
    every GOOD ``raw_value``. This pins the exact stored
    ``raw_value``/``z_score``/``trembling``/``status`` strings for a battery
    of ordinary shapes a fetcher already returns today (an int, a float with
    more than four decimals, a float with a trailing zero, a numeric
    string), so a regression in the new boundary code — re-rendering ``raw``
    a second time, or losing a string's original precision — fails here even
    though ``TestNonNumericOrNonFiniteRawIsDarkened`` above only exercises
    the FAILURE modes ``coerce_finite`` exists for.

    ``tools/replay.py --check`` cannot stand in for this: it re-scores the
    STORED csv string, never this live coercion step.
    """

    CASES = [
        ("int_line", 45, "45"),
        ("many_decimals_line", 45.12345, "45.1234"),
        ("trailing_zero_line", 1.0, "1"),
        ("plain_int_line", 7, "7"),
        ("numeric_string_line", "45.5", "45.5"),
    ]

    def test_ordinary_raw_shapes_are_stored_exactly_as_before(self):
        mods = [_mod(name, raw=raw) for name, raw, _ in self.CASES]
        lines, _, _ = self._run(mods)
        for name, _, expected_raw in self.CASES:
            (row,) = lines[name]
            self.assertEqual(row["raw_value"], expected_raw)
            self.assertEqual(row["z_score"], "")
            self.assertEqual(row["trembling"], "0")
            self.assertEqual(row["status"], normalize.STATUS_WARMING)


class TestCoerceFiniteDirectly(unittest.TestCase):
    """``coerce_finite`` is the pure predicate ``collect()`` darkens a
    ``raw_value`` through; exercised directly here so each branch has its
    own assertion, not just an end-to-end darkened row."""

    def test_none_passes_through_unchanged(self):
        self.assertEqual(collect.coerce_finite(None), (None, None))

    def test_int_is_kept(self):
        self.assertEqual(collect.coerce_finite(45), (45, None))

    def test_numeric_string_is_kept(self):
        self.assertEqual(collect.coerce_finite("45.5"), ("45.5", None))

    def test_non_numeric_string_is_darkened(self):
        raw, reason = collect.coerce_finite("banana")
        self.assertIsNone(raw)
        self.assertIn("banana", reason)

    def test_bool_is_darkened_even_though_float_of_it_is_finite(self):
        # float(True) == 1.0, finite -- but score_row would then re-render it
        # through _fmt as the string "True", which float() cannot parse.
        raw, reason = collect.coerce_finite(True)
        self.assertIsNone(raw)
        self.assertIn("True", reason)

    def test_nan_is_darkened(self):
        raw, reason = collect.coerce_finite(float("nan"))
        self.assertIsNone(raw)
        self.assertIn("nan", reason)

    def test_inf_is_darkened(self):
        raw, reason = collect.coerce_finite(float("inf"))
        self.assertIsNone(raw)
        self.assertIn("inf", reason)

    def test_negative_inf_is_darkened(self):
        raw, reason = collect.coerce_finite(float("-inf"))
        self.assertIsNone(raw)
        self.assertIn("-inf", reason)


class TestWriteComponentsSkipsBadValuesWithoutCrashing(_CollectCase):
    """``write_components`` has the same non-numeric/non-finite exposure as
    ``raw_value``, plus a shape exposure of its own: a non-mapping
    ``components`` (a list, a string) hits ``.items()`` OUTSIDE any
    try/except. Neither a single bad component nor a malformed container may
    cost the line its own scalar reading, let alone abort the line
    dispatched after it — components are diagnostic-only."""

    def test_bad_components_are_dropped_the_good_sibling_and_scalar_survive(self):
        mixed = _mod("mixed_components_line", raw=1.0,
                     components={"good": 2.0, "none_val": None,
                                 "banana": "banana", "nan_val": float("nan"),
                                 "inf_val": float("inf")})
        healthy = _mod("healthy_line", raw=1.0)
        lines, _, components = self._run([mixed, healthy])

        (row,) = lines["mixed_components_line"]
        self.assertEqual(row["raw_value"], "1")

        comp_rows = {r["component"]: r["value"]
                    for r in components["mixed_components_line"]}
        self.assertEqual(comp_rows, {"good": "2"})

        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")

    def test_a_non_mapping_components_writes_nothing_and_does_not_abort(self):
        bad_container = _mod("bad_container_line", raw=1.0, components=["x"])
        healthy = _mod("healthy_line", raw=1.0)
        lines, _, components = self._run([bad_container, healthy])

        (row,) = lines["bad_container_line"]
        self.assertEqual(row["raw_value"], "1")
        self.assertEqual(components["bad_container_line"], [])

        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")


if __name__ == "__main__":
    unittest.main()
