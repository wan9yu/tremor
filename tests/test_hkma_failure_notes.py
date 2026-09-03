"""hkma_aggr_balance records EVIDENCE on every failure path, not just a verdict.

The endpoint fails in phases of tens of minutes during which the connect and TLS
handshake complete and no body follows. Across six weeks the record held only a
bare exception name or a bare status code, so the ten ReadTimeout days and the
five HTTP 502 days could not be shown to be one fault, and no failure ever named
the layer that produced it. These lock the evidence into the note.

Pure logic against a stubbed transport: no network, no committed record read, so
this belongs in the pre-collect gate.
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import fetchers.hkma_aggr_balance as M
from support import stub_requests

ELAPSED = re.compile(r"after \d+\.\d+s")


class _Resp:
    def __init__(self, status=200, headers=None, text="", payload=None):
        self.status_code = status
        self.headers = headers or {}
        self.text = text
        self.content = text.encode()   # what the fetcher actually reads
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no JSON")
        return self._payload


def _fetch(**kw):
    """One fetch_daily against a stubbed response built from ``kw``."""
    with stub_requests(M, get=lambda *a, **k: _Resp(**kw)):
        return M.fetch_daily()


class TestTidy(unittest.TestCase):
    def test_collapses_every_kind_of_whitespace(self):
        # A raw newline would split a CSV row open to grep and tail even though
        # csv quotes it correctly.
        self.assertEqual(M._tidy("a\n b\t\tc\r\nd"), "a b c d")

    def test_accepts_the_raw_bytes_the_fetcher_passes(self):
        # The call sites hand it r.content, never the uncached r.text.
        self.assertEqual(M._tidy(b"a\n b\t\tc"), "a b c")

    def test_undecodable_bytes_do_not_raise(self):
        # An error page in an unknown charset must still yield a note.
        self.assertEqual(M._tidy(b"ok \xff\xfe done"), "ok \ufffd\ufffd done")

    def test_a_long_string_is_bounded_too(self):
        # The bytes path slices before decoding; this proves the str path bounds
        # as well, so _tidy cannot be made quadratic by handing it text.
        self.assertEqual(M._tidy(" " * M._BODY_PREFIX + "buried"), "")

    def test_only_a_bounded_prefix_is_ever_examined(self):
        # Normalising the whole body to keep 200 chars cost 123ms and +25.7MB on
        # a 1.6MB page; the prefix is what makes that impossible.
        self.assertEqual(M._tidy(b" " * M._BODY_PREFIX + b"buried"), "")

    def test_bounds_the_length(self):
        self.assertEqual(len(M._tidy("x" * 5000)), 200)

    def test_honours_an_explicit_limit(self):
        self.assertEqual(M._tidy("x" * 500, 120), "x" * 120)

    def test_survives_an_empty_body(self):
        self.assertEqual(M._tidy(None), "")
        self.assertEqual(M._tidy(""), "")


class TestNon200CarriesEvidence(unittest.TestCase):
    def test_a_gateway_502_names_the_gateway(self):
        out = _fetch(status=502,
                          headers={"Via": "kong/2.5.1",
                                   "X-Kong-Upstream-Latency": "706"},
                          text='{"message":"failure to get a peer"}')
        note = out["source_note"]
        self.assertIsNone(out["raw_value"])
        self.assertIn("HTTP 502", note)
        self.assertIn("Via=kong/2.5.1", note)
        self.assertIn("X-Kong-Upstream-Latency=706", note)
        self.assertIn("failure to get a peer", note)
        self.assertRegex(note, ELAPSED)

    def test_an_edge_502_says_the_gateway_never_answered(self):
        # No Via/X-Kong-* means the edge minted it before Kong was reached. That
        # is a different fault with a different owner, and the whole point of
        # this note is that the two can be told apart afterwards.
        out = _fetch(status=502, headers={"Server": "Tengine"},
                          text="<html>502 Bad Gateway</html>")
        self.assertIn("no gateway headers", out["source_note"])
        self.assertNotIn("Via=", out["source_note"])

    def test_the_body_is_flattened_and_bounded(self):
        out = _fetch(status=503, text="line one\nline two\n" + "z" * 5000)
        note = out["source_note"]
        self.assertNotIn("\n", note)
        self.assertIn("line one line two", note)
        self.assertLess(len(note), 400)


class TestExceptionPathCarriesEvidence(unittest.TestCase):
    def test_it_names_the_exception_and_the_time_it_burned(self):
        class ReadTimeout(Exception):
            pass

        def boom(*a, **k):
            raise ReadTimeout("stalled")

        with stub_requests(M, get=boom):
            out = M.fetch_daily()
        self.assertIsNone(out["raw_value"])
        # The elapsed time is what separates "refused instantly" from "burned the
        # full read budget in silence" — the signature of this endpoint's fault.
        self.assertIn("ReadTimeout", out["source_note"])
        self.assertRegex(out["source_note"], ELAPSED)


class TestNonJsonBodyCarriesEvidence(unittest.TestCase):
    def test_a_200_that_is_not_json_shows_what_arrived(self):
        out = _fetch(text="<html>oops</html>")
        self.assertIsNone(out["raw_value"])
        self.assertIn("non-JSON", out["source_note"])
        self.assertIn("oops", out["source_note"])


class TestSuccessNoteIsUnchanged(unittest.TestCase):
    def test_a_good_read_carries_no_diagnostics(self):
        # The diagnostics must stay on the failure paths: a scored row's note is
        # read by people, and replay compares nothing else about it.
        # raw_value/obs_date parsing is locked by tests/test_new_fetchers.py;
        # what is new here is that no diagnostic leaks onto a good read.
        out = _fetch(payload={"result": {"records": [
            {"end_of_date": "2026-07-22", "closing_balance": 53934}]}})
        self.assertNotRegex(out["source_note"], ELAPSED)
        self.assertNotIn("Via", out["source_note"])
        # The wording is a shared constant, not a literal typed twice: the seeder
        # builds its imported rows from the same NOTE, so a reworded reading
        # cannot leave seeded and live rows phrased differently in one column.
        self.assertTrue(out["source_note"].startswith(M.NOTE), out["source_note"])


class TestTimeoutIsSplit(unittest.TestCase):
    def test_connect_and_read_are_separate_budgets(self):
        # A single scalar cannot distinguish a stalled handshake from a stalled
        # body, which is the one distinction this endpoint's fault turns on.
        self.assertIsInstance(M._TIMEOUT, tuple)
        connect, read = M._TIMEOUT
        self.assertEqual(read, 25, "the read budget must not change silently")
        self.assertLess(connect, read)

    def test_the_declared_timeout_is_the_one_passed(self):
        seen = {}

        def capture(*a, **k):
            seen.update(k)
            return _Resp(payload={"result": {"records": [
                {"end_of_date": "2026-07-22", "closing_balance": 1.0}]}})

        with stub_requests(M, get=capture):
            M.fetch_daily()
        self.assertEqual(seen.get("timeout"), M._TIMEOUT)


if __name__ == "__main__":
    unittest.main()
