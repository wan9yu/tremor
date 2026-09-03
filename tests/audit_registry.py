"""AUDIT: radar-metrics.md must equal what regenerating it produces right now.

D6 (see internal/2026-09-02-round26-zero-debt-plan.md) retired the hand-copied
``Reliab``/``Respons`` cells radar.md used to carry — four of those cells were
caught measured stale, and a hand-copied metric drifts the day after it is
fixed. The replacement, ``radar-metrics.md``, is GENERATED
(``python tools/episodes.py --markdown``), which only keeps its promise if the
committed file is never allowed to fall behind the record it describes. This
is the freshness check: regenerate the table in memory from the committed
CSVs and byte-compare it against the committed ``radar-metrics.md``.

AUDIT, not gate: this reads ``data/`` (the committed record), which the
pre-collect gate (``test_*.py``, ``python -m unittest discover tests``) may
never do — a stale registry cell must never be able to abort a collection day
(see tests/test_side_channel.py's ``TestGateNeverReadsTheCommittedRecord``,
and section 3 of the zero-debt plan). It runs post-commit via
``python -m unittest discover tests -p "audit_*.py"``: a failure here is an
alarm issue, never a lost day. daily.yml's derive step already regenerates
and commits ``radar-metrics.md`` every run, so in the ordinary case this never
fires; it exists for the rarer path — a seed, backfill, or record correction
that lands without regenerating the file in the same commit.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import collect
import episodes
import support


class TestRadarMetricsIsFresh(unittest.TestCase):
    PATH = os.path.join(ROOT, "radar-metrics.md")

    def test_committed_file_matches_a_fresh_regeneration(self):
        self.assertTrue(os.path.exists(self.PATH),
                         "radar-metrics.md is missing at the repo root")
        committed = support.read_text(self.PATH)
        out = [r for r in (episodes.report_line(mod) for mod in collect.LINES) if r]
        fresh = episodes.render_markdown(out)
        self.assertEqual(
            committed, fresh,
            "radar-metrics.md is stale — regenerate with `python tools/episodes.py "
            "--markdown > radar-metrics.md` and commit the result")


if __name__ == "__main__":
    unittest.main()
