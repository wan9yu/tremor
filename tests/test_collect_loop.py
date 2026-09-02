"""The collector spine: `collect()` is the loop the whole instrument runs
through every day, and until now nothing exercised it directly.

Every test here calls the real `collect()` against stub fetcher modules, with
the module's own record-directory and workflow-list attributes redirected to
scratch locations for the block (never a real path under the repository's
record directory). No stub fetcher ever returns a `components` breakdown, so
the collector's separate diagnostic-file writer is never reached either. This
file reads no committed record and is safe in the pre-collect gate.
"""
import contextlib
import datetime
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
         note="stub", target=None, tol=1.5):
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
        return {"raw_value": raw, "source_note": note}
    m.fetch_daily = fetch_daily
    return m


class _CollectRunMixin:
    """Runs the real ``collect()`` against ``mods`` inside a pair of scratch
    directories that are discarded when the block ends, then hands back the
    rows it wrote for inspection. Extra ``(attr, value)`` pairs are stubbed on
    the module for the same block (used to spy on ``score_row``)."""

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
        return lines, summary


class TestOneBadSourceCannotAbortTheRun(unittest.TestCase, _CollectRunMixin):
    """A fetcher that raises, or one that returns garbage instead of raising,
    must dark its own line and let every remaining line still be collected."""

    def test_a_crashing_fetcher_does_not_abort_the_run(self):
        crashed = _mod("crashed_line", crash=True)
        healthy = _mod("healthy_line", raw=1.0)
        lines, _ = self._run([crashed, healthy])

        (row,) = lines["crashed_line"]
        self.assertEqual(row["status"], normalize.STATUS_DARK)
        self.assertIn("fetcher crashed: RuntimeError", row["source_note"])

        # The run did not stop at the crash: the line after it was collected too.
        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")

    def test_a_malformed_result_does_not_abort_the_run(self):
        malformed = _mod("malformed_line", bad=True)
        healthy = _mod("healthy_line", raw=1.0)
        lines, _ = self._run([malformed, healthy])

        (row,) = lines["malformed_line"]
        self.assertEqual(row["status"], normalize.STATUS_DARK)
        self.assertIn("fetcher returned a malformed result", row["source_note"])

        (healthy_row,) = lines["healthy_line"]
        self.assertEqual(healthy_row["raw_value"], "1")


class TestTierOneOnlyCountingAndTheDarkBlindSplit(unittest.TestCase, _CollectRunMixin):
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
        _, summary = self._run(mods, score_row=fake_score_row)

        (row,) = summary
        self.assertEqual(row["trembling_count"], "2")
        self.assertEqual(row["dark_count"], "2")
        self.assertEqual(row["blind_count"], "2")


class TestSampleGuardIsCollectionTimeOnly(unittest.TestCase):
    """``apply_sample_guard`` is a pure helper read straight off the module's
    own attributes; these exercise it directly (see also
    ``tests/test_flights_sample_guard.py`` for the flights/cnh_cny-specific
    tolerances and the schedule-arithmetic checks)."""

    def test_a_module_without_a_target_is_never_guarded(self):
        raw, note, obs = collect.apply_sample_guard(
            1.0, "n", "2026-09-02",
            datetime.datetime(2026, 9, 2, 5, 54, tzinfo=datetime.timezone.utc), None, 1.5)
        self.assertEqual(raw, 1.0)

    def test_an_off_target_reading_is_refused_and_drops_its_obs_date(self):
        raw, note, obs = collect.apply_sample_guard(
            1.0, "n", "2026-09-02",
            datetime.datetime(2026, 9, 2, 5, 54, tzinfo=datetime.timezone.utc), 22.5, 1.5)
        self.assertIsNone(raw)
        self.assertEqual(obs, "")


class TestScoringAttrsNeverReachesTheScorerThroughTheLoop(unittest.TestCase, _CollectRunMixin):
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


if __name__ == "__main__":
    unittest.main()
