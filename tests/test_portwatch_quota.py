"""PortWatch answers a quota breach with HTTP 200 and an error body.

Measured 2026-11-07 (body kept in internal/plans/evidence-2026-11-07/):

    HTTP 200
    {"error": {"code": 429, "message": "Unable to perform query. Too many
     requests.", "details": ["API calls quota exceeded (6248 request units)!
     maximum allowed request units (6000) per Minute. Retry after 60 sec."]}}

``daily_totals`` read ``features`` off that body, found none, and reported
"PortWatch returned no usable daily rows" -- the sentence ``radar.md`` calls a
source outage -- and ``components_at`` returned ``{}`` with no reason at all, so
a scored chokepoint row could sit beside a missing per-strait breakdown with
nothing in the record saying why. These tests pin: the reason names the quota;
a quota breach is waited out ONCE per process, never more than 60 s; nothing
else is retried; and a good body is read exactly as before.

No network: ``requests.get`` is stubbed and the wait is stubbed, so nothing
sleeps.
"""
import contextlib
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import support  # noqa: E402

from core import portwatch  # noqa: E402
from fetchers import chokepoint  # noqa: E402

QUOTA_BODY = {"error": {
    "code": 429,
    "message": "Unable to perform query. Too many requests.",
    "details": ["API calls quota exceeded (6248 request units)! maximum allowed "
                "request units (6000) per Minute. Retry after 60 sec."],
}}


def _stats(*pairs):
    """A statistics response: [(date 'YYYY-MM-DD', total)] newest first."""
    return {"features": [{"attributes": {"date": d, "total": t}} for d, t in pairs]}


def _features(**by_name):
    return {"features": [{"attributes": {"portname": n, "n_total": v}}
                         for n, v in by_name.items()]}


def _resp(body, status=200):
    def _json():
        if isinstance(body, Exception):
            raise body
        return body
    return types.SimpleNamespace(status_code=status, json=_json)


class _Script:
    """``requests.get`` stand-in that answers from a list, recording each call."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = 0

    def __call__(self, url, **kwargs):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class _Quiet(unittest.TestCase):
    """Stub the wait and give each test a fresh once-per-process budget."""

    def setUp(self):
        self.waits = []
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(support.stub_attr(portwatch, "_sleep", self.waits.append))
        stack.enter_context(support.stub_attr(portwatch, "_quota_waits_left", 1))

    def run_with(self, script, fn, *args):
        with support.stub_requests(portwatch, script):
            return fn(*args)


class TestQuotaReason(_Quiet):
    def test_daily_totals_names_the_quota_not_a_missing_series(self):
        script = _Script(_resp(QUOTA_BODY), _resp(QUOTA_BODY))
        rows, reason = self.run_with(script, portwatch.daily_totals, "svc", "f")
        self.assertIsNone(rows)
        self.assertIn("quota", reason)
        self.assertIn("429", reason)
        self.assertNotIn("no usable daily rows", reason)

    def test_components_at_gives_the_reason_instead_of_a_bare_empty_dict(self):
        script = _Script(_resp(QUOTA_BODY), _resp(QUOTA_BODY))
        comps, reason = self.run_with(script, portwatch.components_at,
                                      "svc", "f", "portname", "2026-10-24")
        self.assertEqual(comps, {})
        self.assertIn("quota", reason)

    def test_another_error_code_is_named_as_an_error_body_not_a_quota(self):
        body = {"error": {"code": 400, "message": "Invalid query parameters"}}
        rows, reason = self.run_with(_Script(_resp(body)), portwatch.daily_totals,
                                     "svc", "f")
        self.assertIsNone(rows)
        self.assertIn("error body", reason)
        self.assertIn("400", reason)
        self.assertNotIn("quota", reason)

    def test_an_odd_error_value_cannot_inject_into_the_note(self):
        body = {"error": {"code": "4\n29\r<x>" + "z" * 200}}
        _, reason = self.run_with(_Script(_resp(body)), portwatch.daily_totals,
                                  "svc", "f")
        self.assertNotIn("\n", reason)
        self.assertNotIn("\r", reason)
        self.assertLessEqual(len(reason), 80)
        # the dashboard renders a dark row's note as HTML, so no markup-capable
        # byte may leave this module
        for ch in "<>\"'&":
            self.assertNotIn(ch, reason)

    def test_a_json_list_is_a_stated_shape_problem_not_an_attribute_error(self):
        rows, reason = self.run_with(_Script(_resp([1, 2, 3])), portwatch.daily_totals,
                                     "svc", "f")
        self.assertIsNone(rows)
        self.assertIn("unexpected JSON shape", reason)

    def test_a_non_200_and_a_non_json_body_keep_their_existing_reasons(self):
        rows, reason = self.run_with(_Script(_resp({}, status=503)),
                                     portwatch.daily_totals, "svc", "f")
        self.assertEqual((rows, reason), (None, "PortWatch HTTP 503"))
        rows, reason = self.run_with(_Script(_resp(ValueError("x"))),
                                     portwatch.daily_totals, "svc", "f")
        self.assertEqual((rows, reason), (None, "PortWatch returned a non-JSON body"))

    def test_a_transport_failure_keeps_its_existing_reason(self):
        rows, reason = self.run_with(_Script(portwatch.requests.RequestException()),
                                     portwatch.daily_totals, "svc", "f")
        self.assertIsNone(rows)
        self.assertTrue(reason.startswith("PortWatch request failed: "))

    def test_an_empty_but_valid_answer_is_still_no_usable_rows(self):
        rows, reason = self.run_with(_Script(_resp({"features": []})),
                                     portwatch.daily_totals, "svc", "f")
        self.assertEqual((rows, reason), (None, "PortWatch returned no usable daily rows"))


class TestOneWaitPerProcess(_Quiet):
    def test_a_quota_breach_waits_the_stated_time_once_then_succeeds(self):
        script = _Script(_resp(QUOTA_BODY), _resp(_stats(("2026-10-25", 1726.0))))
        rows, reason = self.run_with(script, portwatch.daily_totals, "svc", "f")
        self.assertEqual(reason, "")
        assert rows is not None, reason
        self.assertEqual(rows[0][1], 1726.0)
        self.assertEqual(self.waits, [60])
        self.assertEqual(script.calls, 2)

    def test_the_wait_is_never_longer_than_sixty_seconds(self):
        self.assertLessEqual(portwatch.QUOTA_WAIT_S, 60)

    def test_a_second_breach_is_not_retried_again(self):
        script = _Script(_resp(QUOTA_BODY), _resp(QUOTA_BODY))
        rows, _ = self.run_with(script, portwatch.daily_totals, "svc", "f")
        self.assertIsNone(rows)
        self.assertEqual(self.waits, [60])
        self.assertEqual(script.calls, 2)

    def test_the_budget_is_per_process_not_per_request(self):
        # the first call spends the wait; a later call in the same run gets none
        first = _Script(_resp(QUOTA_BODY), _resp(_stats(("2026-10-25", 1.0))))
        self.run_with(first, portwatch.daily_totals, "svc", "f")
        second = _Script(_resp(QUOTA_BODY))
        comps, reason = self.run_with(second, portwatch.components_at,
                                      "svc", "f", "portname", "2026-10-24")
        self.assertEqual(comps, {})
        self.assertIn("quota", reason)
        self.assertEqual(second.calls, 1, "no second wait is allowed")
        self.assertEqual(self.waits, [60], "a whole run waits at most once")

    def test_nothing_else_is_retried(self):
        for answer in (_resp({}, status=503), _resp(ValueError("x")),
                       _resp({"features": []}),
                       _resp({"error": {"code": 400}}),
                       portwatch.requests.RequestException()):
            self.waits.clear()
            script = _Script(answer)
            self.run_with(script, portwatch.daily_totals, "svc", "f")
            self.assertEqual(script.calls, 1)
            self.assertEqual(self.waits, [])


class TestGoodBodiesAreUnchanged(_Quiet):
    def test_daily_totals_sorts_newest_first(self):
        body = _stats(("2026-10-23", 1549.0), ("2026-10-25", 1726.0), ("2026-10-24", 1890.0))
        rows, reason = self.run_with(_Script(_resp(body)), portwatch.daily_totals, "s", "f")
        self.assertEqual(reason, "")
        assert rows is not None, reason
        self.assertEqual([t for _, t in rows], [1726.0, 1890.0, 1549.0])
        self.assertEqual(self.waits, [])

    def test_components_at_returns_the_breakdown_and_an_empty_reason(self):
        body = _features(**{"Strait of Hormuz": 3.0, "Suez Canal": 40.0})
        comps, reason = self.run_with(_Script(_resp(body)), portwatch.components_at,
                                      "svc", "n_total", "portname", "2026-10-24")
        self.assertEqual(comps, {"Strait of Hormuz": 3.0, "Suez Canal": 40.0})
        self.assertEqual(reason, "")

    def test_components_at_with_no_features_says_so(self):
        comps, reason = self.run_with(_Script(_resp({"features": []})),
                                      portwatch.components_at,
                                      "svc", "f", "portname", "2026-10-24")
        self.assertEqual(comps, {})
        self.assertIn("2026-10-24", reason)

    def test_daily_sum_at_lag_still_passes_the_reason_through(self):
        script = _Script(_resp(QUOTA_BODY), _resp(QUOTA_BODY))
        total, obs, note = self.run_with(script, portwatch.daily_sum_at_lag,
                                         "svc", "f", "2026-11-07")
        self.assertIsNone(total)
        self.assertIsNone(obs)
        self.assertIn("quota", note)


class TestChokepointRecordsWhyComponentsAreMissing(_Quiet):
    """The scored total can be fine while the breakdown is not; the row says so."""

    def _fetch(self, *answers):
        script = _Script(*answers)
        with support.stub_requests(portwatch, script), \
                support.stub_attr(chokepoint.clock, "china_today", lambda: "2026-11-06"):
            return chokepoint.fetch_daily()

    def test_a_scored_total_with_a_quota_blocked_breakdown_says_so_in_the_note(self):
        totals = _resp(_stats(("2026-10-26", 1726.0)))
        # the single per-process wait is already spent, so the breakdown query fails
        with support.stub_attr(portwatch, "_quota_waits_left", 0):
            out = self._fetch(totals, _resp(QUOTA_BODY))
        self.assertEqual(out["raw_value"], 1726.0)
        self.assertEqual(out["obs_date"], "2026-10-26")
        self.assertIn("[components: unavailable (", out["source_note"])
        self.assertIn("quota", out["source_note"])
        self.assertFalse(out["components"])

    def test_a_full_panel_adds_nothing_to_the_note(self):
        panel = {f"S{i}": float(i) for i in range(chokepoint.PANEL)}
        totals = _resp(_stats(("2026-10-26", 1726.0)))
        out = self._fetch(totals, _resp(_features(**panel)))
        self.assertNotIn("components:", out["source_note"])
        self.assertEqual(len(out["components"]), chokepoint.PANEL)

    def test_a_short_panel_is_still_reported_as_before(self):
        totals = _resp(_stats(("2026-10-26", 1726.0)))
        out = self._fetch(totals, _resp(_features(A=1.0, B=2.0)))
        self.assertIn("2 straits in the response", out["source_note"])

    def test_a_dark_total_carries_the_quota_reason_not_a_missing_series(self):
        with support.stub_attr(portwatch, "_quota_waits_left", 0):
            out = self._fetch(_resp(QUOTA_BODY))
        self.assertIsNone(out["raw_value"])
        self.assertIn("quota", out["source_note"])


if __name__ == "__main__":
    unittest.main()
