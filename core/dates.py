"""The record's one date shape: ``YYYY-MM-DD`` and nothing else.

Every date column in ``data/`` is written this way, and three layers need to
test for it: the collector's ``obs_date`` gate (``collect.obs_date_problem``),
the derive step's ``drift_layer.series_for``, and the FRED body parser
(``core.fred.series``). Each used to spell the test out, with a comment saying
the copies must not diverge. They share this function now, so they cannot.

Deliberately NOT ``date.fromisoformat``: from Python 3.11 that also accepts the
basic form ``20261022``, which sorts as a distinct key and would then be written
into a date column the rest of the record never uses. The shape is checked
first and the calendar second, so ``2026-02-30`` is refused too.

Stdlib only, and importing no other project module: ``core.fred`` is a fetch
layer and must not reach up into ``collect``, and the lint tier runs in a bare
venv.

``tests/audit_record.py`` keeps its own copy on purpose. An audit that imports
the code it audits cannot notice that code loosening; ``tests/test_dates.py``
holds the shared predicate to the same table of inputs.
"""
import re
from datetime import date

_SHAPE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


def is_strict_date(value):
    """True only for a ``YYYY-MM-DD`` string that names a real calendar day.

    Total over any input: a non-string is ``False``, never an exception, so a
    caller can pass a parsed field without checking its type first. ``\\Z`` (not
    ``$``) keeps a trailing newline from passing.
    """
    if not isinstance(value, str) or not _SHAPE.match(value):
        return False
    try:
        date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return False
    return True
