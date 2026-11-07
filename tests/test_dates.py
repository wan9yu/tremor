"""One strict-date predicate, many entry points: they must agree on every input.

The record's date columns are ``YYYY-MM-DD`` and nothing else. Three layers need
that test (the collector's ``obs_date`` gate, the derive step's ``series_for``,
and the FRED body parser) and each used to spell it out. They now share
``core.dates.is_strict_date``; this table is what keeps the shared predicate
from drifting and what kept the refactor from changing a verdict.

``tests/audit_record.py`` keeps its own copy on purpose: an audit that imports
the code it audits cannot notice that code loosening. That copy is deliberately
NOT bound to this table, so loosening the shared predicate cannot loosen the
audit with it; the audit goes red on a bad committed date instead.

Pure: no network, no ``data/``.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import collect  # noqa: E402
from core import dates, fred  # noqa: E402
from tools import drift_layer  # noqa: E402

# (value, expected). Strings only: the entry points also accept non-strings and
# answer False, which the second table covers.
STRING_PROBES = [
    ("2026-10-22", True),
    ("2024-02-29", True),            # leap day
    ("9999-12-31", True),
    ("20261022", False),             # basic form: fromisoformat accepts it on 3.11+
    ("2026-1-2", False),
    ("26-10-22", False),             # strptime("%Y-%m-%d") alone would take this
    ("999-12-31", False),            # ...and this; the shape check comes first
    ("2026-02-30", False),           # right shape, no such day
    ("2025-02-29", False),           # not a leap year
    ("0000-01-01", False),           # year 0 is not a calendar year
    ("2026-13-01", False),
    ("\uff12\uff10\uff12\uff16-10-22", False),   # full-width digits
    ("2026-10-22\n", False),         # a trailing newline must not pass
    (" 2026-10-22", False),
    ("2026-10-22T00:00:00", False),
    ("", False),
    ("not a date", False),
    ("<!DOCTYPE html>", False),
]

NON_STRING_PROBES = [None, 20261022, 2026.1022, b"2026-10-22", ["2026-10-22"]]

ENTRY_POINTS = {
    "core.dates.is_strict_date": dates.is_strict_date,
    "collect.is_strict_date": collect.is_strict_date,
    "drift_layer.is_strict_date": drift_layer.is_strict_date,
    "core.fred._is_iso_date": fred._is_iso_date,
}


class TestEveryEntryPointAgrees(unittest.TestCase):
    def test_strings(self):
        for name, fn in ENTRY_POINTS.items():
            for value, expected in STRING_PROBES:
                with self.subTest(entry=name, value=value):
                    self.assertIs(fn(value), expected)

    def test_non_strings_are_false_not_an_exception(self):
        for name, fn in ENTRY_POINTS.items():
            for value in NON_STRING_PROBES:
                with self.subTest(entry=name, value=value):
                    self.assertIs(fn(value), False)


class TestOneDefinition(unittest.TestCase):
    """The entry points are the shared predicate, not look-alikes of it."""

    def test_the_re_exports_are_the_shared_function(self):
        self.assertIs(collect.is_strict_date, dates.is_strict_date)
        self.assertIs(drift_layer.is_strict_date, dates.is_strict_date)
        self.assertIs(fred._is_iso_date, dates.is_strict_date)


if __name__ == "__main__":
    unittest.main()
