"""ONE grammar for a pending review's firing condition, parsed out of
radar.md and checked against the committed record.

Pending reviews and tripwires used to live only as radar.md PROSE ("re-check
at n>=60", "decide ~Nov 2026") — nothing ever warned when one came due. This
gives an OPEN pending item one machine-parseable trailing tag, appended to
the end of its bullet in radar.md's "### Pending reviews & tripwires" block:

    [opened R13 · owner R26 · fires: distinct_scored(cnh_cny) >= 60]

``opened``/``owner`` are round references (parsed, not evaluated — informational:
the round the item was queued, and the round currently carrying it). ``fires``
is one of six predicate forms:

    scored(<line>) >= <int>            total scored rows of a line
    distinct_scored(<line>) >= <int>   distinct-obs scored rows (an obs_date
                                        scored more than once counts once)
    rows_since(<line>, <YYYY-MM-DD>) >= <int>   scored rows with obs_date (or
                                        date, for an unlagged line) on/after
    round >= <int>                     current round index (radar.md's own
                                        Calibration log — round index)
    date >= <YYYY-MM-DD>               calendar date (core.clock.china_today)
    manual                             never auto-fires; a human decides

An item FIRES ("is OVERDUE") when its predicate is currently true while the
item is still open (still tagged and still in the block — the block's own
convention is to close an item by deleting it, per its header note).

    python tools/pending.py             # human-readable table
    python tools/pending.py --json      # machine-readable
    python tools/pending.py --markdown  # radar-metrics.md ## Pending reviews section
    python tools/pending.py --check     # exit nonzero: any UNPARSEABLE tag,
                                         # or any item currently OVERDUE

Reuses ``seedlib.read_line`` (the same reader ``episodes.py`` and the seeders
use), ``collect.is_scored`` (the same "does this row carry a verdict" filter
``episodes.py`` uses) and ``collect.LINES`` to validate a predicate's line
name — this module never re-implements scoring; it only counts rows
``collect.score_row`` already scored.

An item is a plain dict (label/opened/owner/predicate_text/kind/args, then
current/threshold/fired once evaluated) — every other tools/ module
(episodes.py, drift_layer.py, stuck_panel.py) passes rows as plain dicts
rather than a data class, so this follows suit.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect
import seedlib
from core import clock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADAR_MD = os.path.join(ROOT, "radar.md")

# The block this reads from, and the next top-level heading that ends it —
# a text-scan boundary (not a markdown parse), the same pragmatic approach
# tests/lint_workflows.py takes to its own text.
_BLOCK_HEADER = "### Pending reviews & tripwires"
_BLOCK_END_RE = re.compile(r"^## ", re.MULTILINE)

# A top-level bullet: a line starting "- " at column 0. Continuation lines
# inside one bullet are indented (this block uses two spaces); a nested list
# is not used anywhere in the block today.
_BULLET_SPLIT_RE = re.compile(r"\n(?=- )")
_LABEL_RE = re.compile(r"^-\s+\*\*(?P<label>[^*]+)\*\*")

# A candidate tag: any bracket containing "fires:" — deliberately loose (not
# the strict grammar) so a MALFORMED tag attempt still gets caught as
# unparseable instead of silently ignored because it didn't match up front.
_TAG_CANDIDATE_RE = re.compile(r"\[[^\[\]]*fires:[^\[\]]*\]")
_TAG_STRICT_RE = re.compile(
    r"^\[opened R(?P<opened>\d+(?:\.\d+)?)\s*·\s*owner R(?P<owner>\d+(?:\.\d+)?)\s*·\s*"
    r"fires:\s*(?P<predicate>.+)\]$"
)

_ROUND_LOG_RE = re.compile(r"^-\s+\*\*Round (?P<n>\d+(?:\.\d+)?)\*\*", re.MULTILINE)

_LINE = r"[a-zA-Z_][a-zA-Z0-9_]*"
_DATE = r"\d{4}-\d{2}-\d{2}"
_PREDICATE_FORMS = (
    ("scored", re.compile(rf"^scored\((?P<line>{_LINE})\)\s*>=\s*(?P<n>\d+)$")),
    ("distinct_scored", re.compile(rf"^distinct_scored\((?P<line>{_LINE})\)\s*>=\s*(?P<n>\d+)$")),
    ("rows_since", re.compile(rf"^rows_since\((?P<line>{_LINE}),\s*(?P<since>{_DATE})\)\s*>=\s*(?P<n>\d+)$")),
    ("round", re.compile(r"^round\s*>=\s*(?P<n>\d+)$")),
    ("date", re.compile(rf"^date\s*>=\s*(?P<date>{_DATE})$")),
    ("manual", re.compile(r"^manual$")),
)

DATA_DEPENDENT_KINDS = frozenset({"scored", "distinct_scored", "rows_since"})

VALID_LINES = frozenset(mod.LINE for mod in collect.LINES)


class PendingParseError(ValueError):
    """A tag (or the predicate inside one) does not fit the grammar."""


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _pending_block(text):
    start = text.find(_BLOCK_HEADER)
    if start == -1:
        raise PendingParseError(f"{_BLOCK_HEADER!r} not found in radar.md")
    m = _BLOCK_END_RE.search(text, start + len(_BLOCK_HEADER))
    end = m.start() if m else len(text)
    return text[start:end]


def current_round(text=None):
    """The highest round number in radar.md's Calibration log — round index."""
    text = text if text is not None else _read(RADAR_MD)
    rounds = [float(m["n"]) for m in _ROUND_LOG_RE.finditer(text)]
    if not rounds:
        raise PendingParseError("no round-index entries found in radar.md's "
                                 "Calibration log")
    return max(rounds)


def parse_predicate(predicate_text):
    """Parse one ``fires:`` predicate string into (kind, args-dict).

    Raises PendingParseError on anything not matching one of the six forms,
    or a data-dependent predicate naming a line ``collect.LINES`` does not
    declare.
    """
    text = predicate_text.strip()
    for kind, rx in _PREDICATE_FORMS:
        m = rx.match(text)
        if not m:
            continue
        args = m.groupdict()
        if "n" in args:
            args["n"] = int(args["n"])
        if kind in DATA_DEPENDENT_KINDS and args["line"] not in VALID_LINES:
            raise PendingParseError(
                f"predicate {text!r} names an unknown line {args['line']!r} "
                f"(not in collect.LINES)")
        return kind, args
    raise PendingParseError(f"unrecognized predicate: {text!r}")


def _label(bullet):
    m = _LABEL_RE.match(bullet.strip())
    return m["label"].strip() if m else bullet.strip().splitlines()[0][:60]


def collect_items(text=None):
    """Every OPEN, tagged item in radar.md's Pending block, parsed into a
    plain dict: label/opened/owner/predicate_text/kind/args, plus
    current/threshold/fired (None/None/False until ``evaluate`` fills them in).

    Raises PendingParseError on the first bracket that looks like a tag
    (contains "fires:") but does not fit the strict grammar, or whose
    predicate does not parse — an unparseable tag is a defect to fix, not a
    row to silently skip.
    """
    text = text if text is not None else _read(RADAR_MD)
    block = _pending_block(text)
    items = []
    for bullet in _BULLET_SPLIT_RE.split(block):
        if not bullet.strip().startswith("- "):
            continue
        label = _label(bullet)
        for raw_tag in _TAG_CANDIDATE_RE.findall(bullet):
            m = _TAG_STRICT_RE.match(raw_tag)
            if not m:
                raise PendingParseError(
                    f"{label!r}: tag does not fit the grammar "
                    f"([opened R<n> · owner R<n> · fires: <predicate>]): {raw_tag!r}")
            kind, args = parse_predicate(m["predicate"])
            items.append({
                "label": label, "opened": m["opened"], "owner": m["owner"],
                "predicate_text": m["predicate"].strip(), "kind": kind, "args": args,
                "current": None, "threshold": None, "fired": False,
            })
    return items


def evaluate(item, data_cache=None, round_now=None, today=None):
    """Fill in ``item["current"]``/``["threshold"]``/``["fired"]`` in place;
    also returns it.

    ``data_cache`` (``{line: rows}``) is read/written for the three
    data-dependent forms so evaluating several tagged items against the same
    line reads its CSV once — this will matter once a second data-dependent
    item shares a line (T15 adds a second cnh_cny one).
    """
    data_cache = {} if data_cache is None else data_cache
    kind, args = item["kind"], item["args"]

    if kind in DATA_DEPENDENT_KINDS:
        line = args["line"]
        if line not in data_cache:
            data_cache[line] = seedlib.read_line(line)
        rows = data_cache[line]
        scored = [r for r in rows if collect.is_scored(r)]
        if kind == "scored":
            current = len(scored)
        elif kind == "distinct_scored":
            current = len({(r["obs_date"] or r["date"]) for r in scored})
        else:  # rows_since
            since = args["since"]
            current = sum(1 for r in scored if (r["obs_date"] or r["date"]) >= since)
        item["current"], item["threshold"] = current, args["n"]
        item["fired"] = current >= args["n"]
    elif kind == "round":
        round_now = current_round() if round_now is None else round_now
        item["current"], item["threshold"] = round_now, args["n"]
        item["fired"] = round_now >= args["n"]
    elif kind == "date":
        today = clock.china_today() if today is None else today
        item["current"], item["threshold"] = today, args["date"]
        item["fired"] = today >= args["date"]
    else:  # manual
        item["current"], item["threshold"] = None, None
        item["fired"] = False
    return item


def report(text=None):
    """collect_items() + evaluate() every item — the shared entry point for
    --check/--markdown/--json/the human table, and for tests/audit_registry.py
    to regenerate the ## Pending reviews section in memory.

    Reads radar.md exactly once (not once per helper call) and hands that
    same text to both ``collect_items`` and ``current_round``.
    """
    text = text if text is not None else _read(RADAR_MD)
    items = collect_items(text)
    data_cache, round_now, today = {}, current_round(text), clock.china_today()
    for item in items:
        evaluate(item, data_cache=data_cache, round_now=round_now, today=today)
    return items


def _status_text(item):
    """'distinct_scored(cnh_cny) = 44 / 60'-shaped current-status string."""
    if item["kind"] == "manual":
        return "manual — never auto-fires"
    if item["kind"] == "round":
        return f"round = {item['current']:g} / {item['threshold']}"
    if item["kind"] == "date":
        return f"date = {item['current']} / {item['threshold']}"
    return (f"{item['predicate_text'].split('>=')[0].strip()} = "
            f"{item['current']} / {item['threshold']}")


def render_markdown(items):
    """Render ``items`` (report() output) as the ``## Pending reviews``
    section appended to radar-metrics.md.

    A pure function of ``items`` — no clock, no filesystem — so calling it
    twice on the same input byte-equals (audit_registry.py's freshness check
    relies on this the same way episodes.render_markdown does).
    """
    lines = [
        "",
        "## Pending reviews",
        "",
        "Generated by `python tools/pending.py --markdown` — do not hand-edit. Every OPEN",
        "item in radar.md's Pending block that carries a `[opened R.. · owner R.. · fires:",
        "...]` tag (an untagged item stays prose-only, not tracked here). OVERDUE marks a",
        "predicate that is now true while the item is still open — `pending.py --check`",
        "fails on it.",
        "",
    ]
    if not items:
        lines.append("No tagged pending items.")
        return "\n".join(lines) + "\n"
    for item in items:
        marker = " · **OVERDUE**" if item["fired"] else ""
        lines.append(
            f"- **{item['label']}** — opened R{item['opened']} · owner R{item['owner']} · "
            f"fires: {item['predicate_text']} · {_status_text(item)}{marker}")
    return "\n".join(lines) + "\n"


def main(argv):
    try:
        items = report()
    except PendingParseError as e:
        print(f"UNPARSEABLE: {e}", file=sys.stderr)
        return 1

    if "--markdown" in argv:
        sys.stdout.write(render_markdown(items))
        return 0
    if "--json" in argv:
        print(json.dumps(items, indent=2))
        return 0
    if "--check" in argv:
        overdue = [i for i in items if i["fired"]]
        if overdue:
            for i in overdue:
                print(f"OVERDUE: {i['label']} — {i['predicate_text']} "
                      f"({_status_text(i)})")
            return 1
        print(f"OK — {len(items)} tagged pending item(s), 0 overdue, 0 unparseable")
        return 0

    print(f"{'item':45} {'opened':>7} {'owner':>7}  fires / status")
    for i in items:
        flag = " OVERDUE" if i["fired"] else ""
        print(f"{i['label'][:45]:45} {('R' + i['opened']):>7} {('R' + i['owner']):>7}  "
              f"{i['predicate_text']} — {_status_text(i)}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
