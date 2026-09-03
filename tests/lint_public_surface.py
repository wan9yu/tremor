"""Binds the customer-facing surface — docs/index.html's status vocabulary and
a small README.md claims table — to core/normalize.py so the page and the
docs cannot silently drift from what the code actually emits.

Two things are checked:

  1. Status vocabulary. core/normalize.py defines six status strings a line's
     verdict can carry (STATUS_SCORING plus five others) and, of those, which
     ones are non-scoring. docs/index.html carries TWO ``statusLabel`` maps
     (English ~:416, Chinese ~:470) that give a display label to every
     non-scoring status — "scoring" is the normal state and intentionally has
     no label. This lint asserts the EN and ZH maps declare the SAME key set,
     and that key set is EXACTLY normalize's statuses minus "scoring": every
     non-scoring status the code can emit has a label in both languages, and
     no label exists for a status the code never emits.
     ``TestStatusLabelsBindToNormalize`` also corroborates the ``ALL_STATUSES``
     literal below directly against normalize.py's own ``STATUS_*`` constants
     (see that constant's comment), so a new status added to normalize.py is
     caught even before docs/index.html catches up.

     docs/index.html also already declares ``const BLIND=["warming-up",
     "no-spread"];`` (~:577, commented "Mirrors normalize.BLIND_STATUSES") —
     this lint asserts that array's VALUES, as a set, equal
     ``core.normalize.BLIND_STATUSES`` exactly, so mutating either side alone
     goes red instead of silently drifting.

     Deliberately NOT asserted here: a JS ``STATUS``/``GAP_STATUSES`` const.
     Neither exists in docs/index.html yet (T20/T21 add them) — binding them
     now would keep this lint red from this task through T20 for no code
     that exists yet. ``BLIND`` is the one such const that already exists at
     HEAD, so it is bound above.

  2. README claims. README.md carries a small "Machine-checked claims" table
     (added by this same change) stating a couple of numbers that are true
     of the code today. This lint re-derives each number from source and
     asserts the table still says the same thing — a deliberately small,
     easy-to-extend seed (a table row + a checks-list entry away from a new
     claim); T17 is where README's broader prose claims get the same
     treatment. The primary (tier-1) line count is read from
     tests/lint_registry.py's own already-guarded docs/index.html `const
     LINES` parse (its own count-guard catches a reformat that would
     otherwise silently drop an entry) rather than a second, narrower regex
     here — ``import lint_registry`` is a sibling stdlib-only test module
     (it never imports collect/fetchers/requests), so this stays within the
     stdlib-only property below.

core/normalize.py imports only ``statistics``, ``datetime`` and
``itertools`` (see tests/lint_support_stdlib.py's sibling guarantee for
support.py — normalize.py carries the same property, just unenforced by a
dedicated lint of its own), so importing it here does not break the
stdlib-only property ci.yml's lint job depends on (that job installs
nothing at all). No fetcher module and neither collect.py nor tools/ is
imported — both docs/index.html and README.md are read as plain TEXT via
``support.read_text`` and matched with stdlib ``re``, never a JS/HTML parser.

LINT, not gate: a source-and-docs scan, not a property of the running
instrument, so it runs on push via ``unittest discover tests -p "lint_*.py"``
(ci.yml's lint job) and is deliberately NOT part of daily.yml's pre-collect
gate — a page/README drift must never abort a collection day. ``data/`` is
never read.
"""
import functools
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support
import lint_registry
from core import normalize

DOCS_INDEX = os.path.join(ROOT, "docs", "index.html")
README = os.path.join(ROOT, "README.md")

# The six status strings core/normalize.py's fetcher contract can write to a
# row's `status` column today (see its module docstring). Named explicitly,
# not read off a module-level aggregate, because normalize.py declares none.
# TestStatusLabelsBindToNormalize's
# test_ALL_STATUSES_matches_every_normalize_STATUS_constant below is this
# literal's own corroborating check: it rediscovers every `STATUS_*`
# constant normalize.py actually declares via `dir(normalize)` and asserts
# the two sets are equal, so a status added there without a matching add
# here is caught directly by that test — not only indirectly, via
# docs/index.html's own key-set happening to disagree.
ALL_STATUSES = {
    normalize.STATUS_SCORING,
    normalize.STATUS_WARMING,
    normalize.STATUS_STALE,
    normalize.STATUS_DARK,
    normalize.STATUS_CLOSED,
    normalize.STATUS_FLAT,
}
NON_SCORING_STATUSES = ALL_STATUSES - {normalize.STATUS_SCORING}


# --- docs/index.html's two `statusLabel:{...}` maps -------------------------

# No nested `{` ever appears inside a statusLabel map body (every value is a
# plain quoted string), so a non-greedy DOTALL match from the opening brace
# to the first `},` it meets lands exactly on the map's own close.
_STATUS_LABEL_BLOCK = re.compile(r'statusLabel:\{(.*?)\},', re.S)
# A map KEY is a quoted string immediately followed by `:`; a value never is
# (it is followed by `,` or the block's own close), so this does not also
# pick up label text.
_STATUS_LABEL_KEY = re.compile(r'"([a-z-]+)"\s*:')


@functools.lru_cache(maxsize=None)
def _status_label_key_sets():
    """The key set of each `statusLabel:{...}` map in docs/index.html, in
    source order (today: [EN, ZH]). Memoized — pure, no-arg, and called from
    more than one test method below (same pattern as lint_registry.py's own
    `_docs_registry()`)."""
    html = support.read_text(DOCS_INDEX)
    blocks = _STATUS_LABEL_BLOCK.findall(html)
    assert len(blocks) == 2, (
        "docs/index.html: expected exactly 2 `statusLabel:{...}` maps (EN + "
        f"ZH), found {len(blocks)}")
    return [set(_STATUS_LABEL_KEY.findall(block)) for block in blocks]


class TestStatusLabelsBindToNormalize(unittest.TestCase):
    def test_en_and_zh_statusLabel_maps_declare_the_same_keys(self):
        en_keys, zh_keys = _status_label_key_sets()
        self.assertEqual(en_keys, zh_keys,
                          "docs/index.html: the EN and ZH `statusLabel` maps "
                          f"declare different keys: EN={sorted(en_keys)} "
                          f"ZH={sorted(zh_keys)}")

    def test_statusLabel_keys_equal_normalizes_non_scoring_statuses(self):
        en_keys, _ = _status_label_key_sets()
        missing = sorted(NON_SCORING_STATUSES - en_keys)
        self.assertEqual(missing, [],
                          "core/normalize.py status(es) with no dashboard "
                          f"label in docs/index.html's statusLabel maps: {missing}")
        extra = sorted(en_keys - NON_SCORING_STATUSES)
        self.assertEqual(extra, [],
                          "docs/index.html's statusLabel maps carry a label "
                          f"for status(es) core/normalize.py never emits: {extra}")

    def test_ALL_STATUSES_matches_every_normalize_STATUS_constant(self):
        discovered = {getattr(normalize, name) for name in dir(normalize)
                      if name.startswith("STATUS_")}
        self.assertEqual(ALL_STATUSES, discovered,
                          "this lint's ALL_STATUSES literal has drifted from "
                          "every STATUS_* constant core/normalize.py actually "
                          f"declares: lint={sorted(ALL_STATUSES)} "
                          f"normalize={sorted(discovered)}")


# --- docs/index.html's `const BLIND=[...]` array ----------------------------

_BLIND_CONST = re.compile(r'const BLIND\s*=\s*\[(?P<items>[^\]]*)\];')
_QUOTED_STRING = re.compile(r'"([^"]+)"')


@functools.lru_cache(maxsize=None)
def _docs_blind_values():
    """The set of status strings inside docs/index.html's `const BLIND=[...]`
    array. Memoized (see `_status_label_key_sets` above)."""
    html = support.read_text(DOCS_INDEX)
    m = _BLIND_CONST.search(html)
    assert m, "docs/index.html: could not locate `const BLIND=[...]`"
    values = _QUOTED_STRING.findall(m.group("items"))
    assert values, "docs/index.html: `const BLIND` parsed with no values"
    return set(values)


class TestBlindConstBindsToNormalize(unittest.TestCase):
    def test_blind_const_equals_normalize_blind_statuses(self):
        docs_blind = _docs_blind_values()
        want = set(normalize.BLIND_STATUSES)
        missing = sorted(want - docs_blind)
        self.assertEqual(missing, [],
                          "core.normalize.BLIND_STATUSES status(es) missing "
                          f"from docs/index.html's `const BLIND`: {missing}")
        extra = sorted(docs_blind - want)
        self.assertEqual(extra, [],
                          "docs/index.html's `const BLIND` carries status(es) "
                          f"not in core.normalize.BLIND_STATUSES: {extra}")


# --- README.md's "Machine-checked claims" table ------------------------------

def _readme_section(text, heading):
    idx = text.find(heading)
    assert idx != -1, f"README.md: heading {heading!r} not found"
    rest = text[idx + len(heading):]
    nxt = re.search(r'^## ', rest, re.M)
    return rest[:nxt.start()] if nxt else rest


_CLAIM_ROW = re.compile(r'^\|\s*(?P<label>[^|]+?)\s*\|\s*(?P<value>\d+)\s*\|\s*$', re.M)


@functools.lru_cache(maxsize=None)
def _readme_claims():
    """{label: int(value)} for every ``| label | <digits> |`` row inside
    README.md's "## Machine-checked claims" section (the header row and the
    ``|---|---|`` separator both fail to match — the separator has no
    all-digit cell, the header's value cell is the word "value"). Memoized
    (see `_status_label_key_sets` above)."""
    readme = support.read_text(README)
    section = _readme_section(readme, "## Machine-checked claims")
    claims = {m.group("label"): int(m.group("value")) for m in _CLAIM_ROW.finditer(section)}
    assert claims, "README.md: no claim rows parsed out of the Machine-checked claims table"
    return claims


def _docs_tier1_line_count():
    """Primary (tier-1) line count, read from lint_registry.py's own
    `_docs_registry()` — its docs/index.html `const LINES` parse already
    carries a count-guard (asserts the parsed entry count matches
    collect.LINES's own count), which a second, narrower regex here would
    not have caught a reformat silently missing."""
    registry, _ = lint_registry._docs_registry()
    return sum(1 for meta in registry.values() if meta.get("tier") == 1)


class TestReadmeClaimsBindToSource(unittest.TestCase):
    def test_readme_claims_match_source(self):
        claims = _readme_claims()
        checks = [
            ("primary (tier-1) lines", _docs_tier1_line_count(),
             "README.md claims a primary (tier-1) line count that does not "
             "match docs/index.html's `const LINES`"),
            ("status values `core/normalize.py` can emit", len(ALL_STATUSES),
             "README.md claims a status count that does not match "
             "core/normalize.py's STATUS_* constants"),
        ]
        for label, expected, msg in checks:
            with self.subTest(label=label):
                self.assertIn(label, claims,
                               f"README.md's Machine-checked claims table has no {label!r} row")
                self.assertEqual(claims[label], expected, msg)


if __name__ == "__main__":
    unittest.main()
