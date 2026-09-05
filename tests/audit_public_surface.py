"""AUDIT: docs/index.html's served surface and its new tier-2 gap-chip claim,
checked against the committed record.

Two things, neither owned by any existing check:

  1. MIRRORED byte-equality. daily.yml's push step copies ``data/`` onto
     ``docs/data/`` verbatim (``tools/ci_push.sh ... data/ docs/data/``), and
     the dashboard reads ONLY ``docs/data/*.csv`` — never ``data/*.csv``
     directly (see tests/test_side_channel.py's own allow-list reasoning).
     ``collect.MIRRORED`` is the exact set of files that copy step is
     supposed to leave byte-identical (every line CSV, ``summary.csv``,
     ``annotations.csv``). ``docs/data/stuck.csv`` is deliberately NOT
     checked here: it is not a mirror of a same-named ``data/`` file at all —
     ``tools/stuck_panel.py`` DERIVES it fresh from ``data/levels.csv`` every
     run and serves it directly to ``docs/data/`` only (that module's own
     docstring: "served BY THE REPORTER, never through collect.MIRRORED"), so
     there is no ``data/stuck.csv`` for a byte-cmp to even name.
     A silent divergence in what IS mirrored means the live page is showing
     something other than what the record actually says, with nothing else
     positioned to catch it: lint_*.py never reads ``data/`` (lint_public_surface.py's
     own module docstring), and audit_registry.py's freshness check is scoped
     to ``radar-metrics.md``, not the CSVs the dashboard fetches.

  2. The tier-2 gap chip's claim, recomputed from the record. T20 wired
     docs/index.html's ``GAP_STATUSES``/``GAP_RUN_LOUD`` consts in so a
     tier-2 line stuck ``GAP_RUN_LOUD``-or-more consecutive collections deep
     in a ``GAP_STATUSES`` status renders a "NO DATA" gap chip instead of
     looking calm — see that module's own const comments. The chip's whole
     promise is "this line has NO reading", so every status named in
     ``GAP_STATUSES`` must, in the actual committed CSVs, carry an empty
     ``raw_value`` on every row — a status that DOES carry a value (``stale``,
     ``no-spread``, a mis-added future status) would show "NO DATA" beside a
     line that demonstrably has a number. ``GAP_STATUSES`` itself is read
     back out of docs/index.html (the same regex-over-text technique
     tests/lint_public_surface.py uses for ``const BLIND``), not
     re-typed here, so this stays bound to whatever the page actually
     declares rather than a second hardcoded copy that could drift from it.

     Deliberately NOT here: re-deriving ``summary.csv``'s
     trembling_count/dark_count/blind_count from a fresh per-line recount.
     ``tools/replay.py --check`` already owns that — "per-row drift AND the
     summary re-derivation... One owner, one O(n^2) replay per day"
     (audit_registry.py's own module docstring, explaining why IT does not
     duplicate replay either). Duplicating it a third time here would only
     multiply the same O(n^2) pass for a check tools/replay.py already makes.

  3. ``docs/data/leans.csv`` (T2: the dashboard headline reads this as a
     same-day machine lean). Like ``docs/data/stuck.csv``, it is DERIVED and
     served straight to ``docs/data/`` by its own reporter
     (``tools/lean_panel.py``) — never through ``collect.MIRRORED`` — so
     nothing else checks it. If the file is present: every ``line`` value
     must be a tier-1 line id (read off ``lean_panel.TIER1``, the reporter's
     own list, rather than re-derived here — the reporter is what actually
     decides which lines it serves), and every ``lean`` value must be one of
     the three the reporter's classifier can emit. This audit reads
     ``data/`` (the tier-1 line set) so it lives here, not in a lint.

AUDIT, not gate/lint: reads ``data/`` (the committed record) and imports
``collect`` (which imports every fetcher), which the pre-collect gate
(``test_*.py``) may never do (tests/test_side_channel.py's
``TestGateNeverReadsTheCommittedRecord``) and ci.yml's stdlib-only lint job
cannot do either. Runs post-commit via ``python -m unittest discover tests
-p "audit_*.py"``: a failure here is an alarm issue, never a lost day.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import collect
import lean_panel
import support
from core import normalize

DATA_DIR = os.path.join(ROOT, "data")
DOCS_DATA_DIR = os.path.join(ROOT, "docs", "data")
DOCS_INDEX = os.path.join(ROOT, "docs", "index.html")
DOCS_LEANS = os.path.join(DOCS_DATA_DIR, "leans.csv")


# --- 1. MIRRORED byte-equality ------------------------------------------

class TestMirroredFilesAreByteIdentical(unittest.TestCase):
    """Every file daily.yml's push step is supposed to copy verbatim from
    ``data/`` onto ``docs/data/`` — exactly ``collect.MIRRORED`` (see this
    module's own docstring for why ``stuck.csv`` is not part of this check)
    — must actually BE byte-identical in both locations, since the served
    page reads only the ``docs/data/`` copy.
    """

    def test_every_mirrored_file_is_byte_identical(self):
        names = sorted(collect.MIRRORED)
        self.assertTrue(names, "collect.MIRRORED is unexpectedly empty")
        offenders = []
        for name in names:
            src = os.path.join(DATA_DIR, name)
            dst = os.path.join(DOCS_DATA_DIR, name)
            if not os.path.exists(src):
                offenders.append(f"{name}: missing from data/")
                continue
            if not os.path.exists(dst):
                offenders.append(f"{name}: missing from docs/data/ (never mirrored)")
                continue
            with open(src, "rb") as f:
                a = f.read()
            with open(dst, "rb") as f:
                b = f.read()
            if a != b:
                offenders.append(f"{name}: data/ and docs/data/ differ")
        self.assertEqual(offenders, [], "\n".join(offenders))


# --- 2. the tier-2 gap chip's claim, bound to docs/index.html's own consts --


def _docs_gap_statuses():
    """The status strings inside docs/index.html's `const GAP_STATUSES=[...]`,
    read back from the page text — not re-typed here — so this audit stays
    bound to whatever the page actually declares (tests/lint_public_surface.py
    separately asserts this const is a subset of core.normalize's statuses;
    this module only reuses its VALUES, it does not re-check that binding)."""
    values = support.docs_const_array(DOCS_INDEX, "GAP_STATUSES")
    assert values, "docs/index.html: `const GAP_STATUSES=[...]` absent or empty"
    return values


class TestGapChipStatusesHaveNoReading(unittest.TestCase):
    """A GAP chip means "this line has no reading" — literally the "NO DATA"
    label docs/index.html wires in for it. That claim is only true if every
    status named in GAP_STATUSES carries an empty raw_value on every row of
    the real record; a status that carries a value would show "NO DATA" next
    to a line that demonstrably has a number.
    """

    def test_every_gap_status_row_carries_no_raw_value(self):
        gap_statuses = _docs_gap_statuses()
        offenders = []
        for mod in collect.LINES:
            rows = collect._read_rows(os.path.join(DATA_DIR, mod.LINE + ".csv"))
            for row in rows:
                if row.get("status") in gap_statuses and row.get("raw_value"):
                    offenders.append(
                        f"{mod.LINE} {row['date']}: status={row['status']!r} "
                        f"(a GAP_STATUSES status) but raw_value={row['raw_value']!r}")
        self.assertEqual(offenders, [], "\n".join(offenders))


# --- 3. leans.csv: well-formed, and scoped to tier-1 -------------------------

# The three lean values tools/lean_panel.py's own `_classify` can emit (see
# its docstring) -- not a code-level enum (there is none to bind to; the
# function just returns one of these three literals), so named here by hand
# and revisited if that function ever grows a fourth.
LEAN_VALUES = {"common-mode", "ok", "unavailable"}


class TestLeansCsvIsWellFormedAndTier1Only(unittest.TestCase):
    """docs/data/leans.csv is optional (a fresh checkout before the derive
    step has ever run holds none), so this skips rather than fails when it is
    absent. When present, every row must name a tier-1 line — lean_panel.py
    is built to serve firing TIER-1 lines only, so any other line id here
    means the reporter and the dashboard have drifted on what "tier-1" means
    — and every `lean` must be a value the reporter's classifier can actually
    produce.
    """

    def test_leans_csv_is_well_formed_and_scoped_to_tier1(self):
        if not os.path.exists(DOCS_LEANS):
            self.skipTest("docs/data/leans.csv not present")
        rows = collect._read_rows(DOCS_LEANS)
        tier1_ids = {mod.LINE for mod in lean_panel.TIER1}
        offenders = []
        for row in rows:
            line = row.get("line")
            if line not in tier1_ids:
                offenders.append(f"{row.get('date')}: line {line!r} is not a tier-1 line")
            lean = row.get("lean")
            if lean not in LEAN_VALUES:
                offenders.append(f"{row.get('date')} {line}: unrecognized lean {lean!r}")
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
