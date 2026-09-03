"""GATE: unit tests for tools/pending.py's grammar (parse_predicate) and
evaluation (evaluate) — pure logic, never reads ``data/``.

``scored``/``rows_since``/``round`` had zero coverage before this file (only
the two committed real-item tags exercising ``distinct_scored``/``date``/
``manual`` were ever run, via tests/lint_pending.py and pending.py --check
against the live record). The data-dependent forms here are evaluated
against STUBBED row lists fed straight into ``evaluate``'s ``data_cache`` —
the committed CSVs are never opened — so this belongs in the gate tier
(``python -m unittest discover tests``, pre-collect) rather than an audit.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pending


def _row(date, z_score="", obs_date=""):
    """A minimal stub row shaped like collect.score_row's return."""
    return {"date": date, "raw_value": "1", "z_score": z_score, "trembling": "0",
            "direction": "", "source_note": "", "obs_date": obs_date, "status": "scoring"}


def _item(kind, args, predicate_text="stub"):
    """A fresh, unevaluated pending item — the plain-dict shape collect_items
    builds (label/opened/owner/predicate_text/kind/args, current/threshold/
    fired not yet filled in)."""
    return {"label": "test item", "opened": "1", "owner": "2",
            "predicate_text": predicate_text, "kind": kind, "args": args,
            "current": None, "threshold": None, "fired": False}


class TestParsePredicateValidForms(unittest.TestCase):
    """All six grammar forms parse to the expected (kind, args)."""

    def test_scored(self):
        kind, args = pending.parse_predicate("scored(net_outages) >= 60")
        self.assertEqual(kind, "scored")
        self.assertEqual(args, {"line": "net_outages", "n": 60})

    def test_distinct_scored(self):
        kind, args = pending.parse_predicate("distinct_scored(cnh_cny) >= 60")
        self.assertEqual(kind, "distinct_scored")
        self.assertEqual(args, {"line": "cnh_cny", "n": 60})

    def test_rows_since(self):
        kind, args = pending.parse_predicate(
            "rows_since(net_outages, 2026-08-25) >= 60")
        self.assertEqual(kind, "rows_since")
        self.assertEqual(args, {"line": "net_outages", "since": "2026-08-25", "n": 60})

    def test_round(self):
        kind, args = pending.parse_predicate("round >= 26")
        self.assertEqual(kind, "round")
        self.assertEqual(args, {"n": 26})

    def test_date(self):
        kind, args = pending.parse_predicate("date >= 2026-11-01")
        self.assertEqual(kind, "date")
        self.assertEqual(args, {"date": "2026-11-01"})

    def test_manual(self):
        kind, args = pending.parse_predicate("manual")
        self.assertEqual(kind, "manual")
        self.assertEqual(args, {})

    def test_surrounding_whitespace_is_tolerated(self):
        kind, args = pending.parse_predicate("  round >= 5  ")
        self.assertEqual((kind, args), ("round", {"n": 5}))


class TestParsePredicateRejectsMalformed(unittest.TestCase):
    def test_unknown_line_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("scored(not_a_real_line) >= 60")

    def test_distinct_scored_unknown_line_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("distinct_scored(not_a_real_line) >= 60")

    def test_rows_since_unknown_line_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("rows_since(not_a_real_line, 2026-08-25) >= 60")

    def test_wrong_operator_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("scored(cnh_cny) > 60")

    def test_garbage_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("not a predicate at all")

    def test_manual_with_trailing_text_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("manual now")

    def test_rows_since_without_a_date_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("rows_since(net_outages) >= 60")

    def test_round_without_a_threshold_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("round >=")

    def test_date_with_a_malformed_date_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("date >= 2026/11/01")

    def test_empty_string_is_rejected(self):
        with self.assertRaises(pending.PendingParseError):
            pending.parse_predicate("")


class TestEvaluatePureForms(unittest.TestCase):
    """round/date need no data/ — round_now/today are injected directly."""

    def test_round_not_yet_fired(self):
        item = _item("round", {"n": 30})
        pending.evaluate(item, round_now=25.1)
        self.assertEqual(item["current"], 25.1)
        self.assertEqual(item["threshold"], 30)
        self.assertFalse(item["fired"])

    def test_round_fires_when_current_meets_threshold(self):
        item = _item("round", {"n": 25})
        pending.evaluate(item, round_now=25.1)
        self.assertTrue(item["fired"])

    def test_round_fires_exactly_at_the_threshold(self):
        item = _item("round", {"n": 26})
        pending.evaluate(item, round_now=26.0)
        self.assertTrue(item["fired"])

    def test_date_not_yet_fired(self):
        item = _item("date", {"date": "2026-11-01"})
        pending.evaluate(item, today="2026-09-04")
        self.assertEqual(item["current"], "2026-09-04")
        self.assertEqual(item["threshold"], "2026-11-01")
        self.assertFalse(item["fired"])

    def test_date_fires_when_today_meets_threshold(self):
        item = _item("date", {"date": "2026-09-01"})
        pending.evaluate(item, today="2026-09-04")
        self.assertTrue(item["fired"])

    def test_manual_never_fires(self):
        item = _item("manual", {})
        pending.evaluate(item, round_now=999, today="2099-01-01")
        self.assertFalse(item["fired"])
        self.assertIsNone(item["current"])
        self.assertIsNone(item["threshold"])


class TestEvaluateDataDependentFormsAgainstStubbedRows(unittest.TestCase):
    """scored/distinct_scored/rows_since, exercised with fabricated rows
    pre-seeded into evaluate()'s data_cache — the line reader is never
    called, so nothing here touches data/."""

    def test_scored_counts_only_scored_rows(self):
        rows = [_row("2026-01-01", z_score="0.1"),
                _row("2026-01-02", z_score=""),  # dark/unscored — excluded
                _row("2026-01-03", z_score="-1.2")]
        item = _item("scored", {"line": "net_outages", "n": 3})
        cache = {"net_outages": rows}
        pending.evaluate(item, data_cache=cache)
        self.assertEqual(item["current"], 2)
        self.assertFalse(item["fired"])

    def test_scored_fires_once_the_threshold_is_met(self):
        rows = [_row(f"2026-01-{d:02d}", z_score="0.1") for d in range(1, 4)]
        item = _item("scored", {"line": "net_outages", "n": 3})
        pending.evaluate(item, data_cache={"net_outages": rows})
        self.assertEqual(item["current"], 3)
        self.assertTrue(item["fired"])

    def test_distinct_scored_dedupes_by_obs_date(self):
        rows = [_row("2026-01-01", z_score="0.1", obs_date="2026-01-01"),
                # a stale republish of the same observation — counts once
                _row("2026-01-02", z_score="0.2", obs_date="2026-01-01"),
                _row("2026-01-03", z_score="0.3", obs_date="2026-01-03")]
        item = _item("distinct_scored", {"line": "cnh_cny", "n": 2})
        pending.evaluate(item, data_cache={"cnh_cny": rows})
        self.assertEqual(item["current"], 2)
        self.assertTrue(item["fired"])

    def test_distinct_scored_falls_back_to_date_when_obs_date_is_blank(self):
        rows = [_row("2026-01-01", z_score="0.1", obs_date=""),
                _row("2026-01-02", z_score="0.2", obs_date="")]
        item = _item("distinct_scored", {"line": "cnh_cny", "n": 3})
        pending.evaluate(item, data_cache={"cnh_cny": rows})
        self.assertEqual(item["current"], 2)
        self.assertFalse(item["fired"])

    def test_rows_since_counts_only_on_or_after_the_given_date(self):
        rows = [_row("2026-08-20", z_score="0.1", obs_date="2026-08-20"),
                _row("2026-08-25", z_score="0.2", obs_date="2026-08-25"),
                _row("2026-08-26", z_score="0.3", obs_date="2026-08-26")]
        item = _item("rows_since",
                      {"line": "net_outages", "since": "2026-08-25", "n": 2})
        pending.evaluate(item, data_cache={"net_outages": rows})
        self.assertEqual(item["current"], 2)
        self.assertTrue(item["fired"])

    def test_rows_since_excludes_unscored_rows(self):
        rows = [_row("2026-08-25", z_score="", obs_date="2026-08-25"),  # dark
                _row("2026-08-26", z_score="0.3", obs_date="2026-08-26")]
        item = _item("rows_since",
                      {"line": "net_outages", "since": "2026-08-25", "n": 2})
        pending.evaluate(item, data_cache={"net_outages": rows})
        self.assertEqual(item["current"], 1)
        self.assertFalse(item["fired"])

    def test_data_cache_is_reused_across_items_sharing_a_line(self):
        rows = [_row("2026-01-01", z_score="0.1")]
        cache = {"net_outages": rows}
        item1 = _item("scored", {"line": "net_outages", "n": 1})
        item2 = _item("scored", {"line": "net_outages", "n": 5})
        pending.evaluate(item1, data_cache=cache)
        pending.evaluate(item2, data_cache=cache)
        # Still the exact same list object — evaluate never re-fetched it.
        self.assertIs(cache["net_outages"], rows)
        self.assertEqual(item1["current"], 1)
        self.assertEqual(item2["current"], 1)


if __name__ == "__main__":
    unittest.main()
