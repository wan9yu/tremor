"""Name counted lines whose just-committed row is a sample-hour refusal.

The daily job stays green when the guard refuses a reading. This tool is the
read the workflow uses to open a separate issue. It does not score, does not
write a row, and does not call GitHub.

A hit is a counted line (``TIER`` absent means 1, as in ``collect``) that
declares ``SAMPLE_TARGET_UTC_H``, on the China collection date, whose
``source_note`` starts with the sentence ``apply_sample_guard`` writes.
Status is not consulted: a weekend closure can still carry that sentence.
"""
import csv
import os
import sys

GUARD_PREFIX = "no reading: sampled "


def _repo():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    import collect
    from core import clock
    return collect, clock


def refused_lines(modules, rows_by_line, today):
    """Lines whose row dated ``today`` starts with the guard sentence.

    ``today`` is the China collection date. Rows on any other date are ignored,
    so an older refusal cannot mark a later on-time day.
    """
    hits = []
    for mod in modules:
        if getattr(mod, "SAMPLE_TARGET_UTC_H", None) is None:
            continue
        if getattr(mod, "TIER", 1) != 1:
            continue
        row = None
        for candidate in rows_by_line.get(mod.LINE, []):
            if candidate.get("date") == today:
                row = candidate
        if row is None:
            continue
        note = row.get("source_note") or ""
        if note.startswith(GUARD_PREFIX):
            hits.append(mod.LINE)
    return hits


def _rows(path):
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def notice_line(data_dir, today, modules):
    """``'YYYY-MM-DD line ...'`` when this collection date has a refusal, else ``''``."""
    rows_by_line = {
        mod.LINE: _rows(os.path.join(data_dir, mod.LINE + ".csv"))
        for mod in modules
    }
    hits = refused_lines(modules, rows_by_line, today)
    if not hits:
        return ""
    return today + " " + " ".join(hits)


def main():
    collect, clock = _repo()
    text = notice_line(collect.DATA, clock.china_today(), collect.LINES)
    if text:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
