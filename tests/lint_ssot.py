"""One-home guards for arithmetic that must have exactly one definition (SSOT
= single source of truth). Shared across tasks; net_outages' settled-window
boundary (T1) is the first tenant.

The net_outages settle boundary (R23.1) is the one place a drift silently
writes a WRONG tier-1 raw that forward-only then freezes forever: the live
collection path (fetchers/net_outages.py:window_for/window_for_day), the
reconciliation tool and the seeder all have to agree on "24h ending at the
most recent 22:00:00Z", so this scans for the ARITHMETIC that produces that
boundary (``datetime.time(22, 0)`` / bare ``time(22, 0)``, and the
``.replace(hour=22, ...)`` form) rather than the bare literal ``22``, which
also appears harmlessly in prose (e.g. "24h to <date> 22:00Z" source notes at
fetchers/net_outages.py and tools/seed_ioda.py).

LINT, not gate: a source scan, not a property of the running instrument, so
it runs on push via ``unittest discover tests -p "lint_*.py"`` (ci.yml's
lint job) and is deliberately NOT part of daily.yml's pre-collect gate — a
convention violation here must never cost an irreplaceable collection day.
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support

# ``datetime.time(22, 0)`` or a bare ``time(22, 0)`` (net_outages.py imports
# ``time`` directly), and the ``.replace(hour=22, ...)`` form _settled_window
# used before extraction. Whitespace-tolerant; deliberately NOT the bare
# literal 22, which also shows up in unrelated prose and other code.
_ARITHMETIC = re.compile(r'\btime\(\s*22\s*,\s*0\s*\)|\bhour\s*=\s*22\b')

_ONE_HOME = os.path.join("fetchers", "net_outages.py")
# This file itself names the arithmetic it hunts for, in prose (the module
# docstring and the assertion message) — excluded from its own scan, the way
# any lint necessarily mentions the pattern it forbids.
_SELF = os.path.join("tests", "lint_ssot.py")


def _all_py_files():
    """Every tracked-looking .py file under the repo, skipping caches/venvs."""
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ("__pycache__", ".git", "node_modules")
                       and not d.startswith(".venv")]
        for f in filenames:
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
                if rel != _SELF:
                    found.append(rel)
    return sorted(found)


class TestSettledWindowArithmeticIsOneHome(unittest.TestCase):
    def test_files_scanned_include_the_one_home(self):
        # A canary against an over-narrow walk silently finding nothing.
        self.assertIn(_ONE_HOME, _all_py_files())

    def test_window_boundary_arithmetic_appears_in_exactly_one_file(self):
        hits = []
        for rel in _all_py_files():
            src = support.read_text(os.path.join(ROOT, rel))
            if _ARITHMETIC.search(src):
                hits.append(rel)
        self.assertEqual(hits, [_ONE_HOME],
                          "settled-window boundary arithmetic (datetime.time(22, 0) "
                          "/ hour=22) must live only in fetchers/net_outages.py — "
                          "tools/reconcile_net_outages.py and tools/seed_ioda.py "
                          "must call net_outages.window_for_day instead of "
                          "re-deriving the boundary")

    def test_the_bare_literal_22_is_not_the_target(self):
        # The prose the module docstrings name (source notes with "22:00Z")
        # must not make this lint fire — only the boundary math should.
        prose = 'f"IODA {count} countries with {_DATASOURCE} outages (24h to {obs} 22:00Z)'
        self.assertIsNone(_ARITHMETIC.search(prose))


if __name__ == "__main__":
    unittest.main()
