"""Binds the customer-facing surface — docs/index.html's per-line definitions
and status vocabulary, and a small README.md claims table — to core/normalize.py
so the page and the docs cannot silently drift from what the code actually
emits.

Six things are checked:
  1. Status vocabulary. core/normalize.py defines six status strings a line's
     verdict can carry (STATUS_SCORING plus five others). docs/index.html
     carries TWO ``statusLabel`` maps (English ~:416, Chinese ~:470) that give
     a display label to every one of them — including "scoring", the normal
     state, whose label the public-surface migration added so every status a
     row can carry has page copy. This lint asserts the EN and ZH maps declare
     the SAME key set, and that key set is EXACTLY normalize's six statuses:
     every status the code can emit has a label in both languages, and no
     label exists for a status the code never emits.
     ``TestStatusLabelsBindToNormalize`` also corroborates the ``ALL_STATUSES``
     literal below directly against normalize.py's own ``STATUS_*`` constants
     (see that constant's comment), so a new status added to normalize.py is
     caught even before docs/index.html catches up.

     docs/index.html also already declares ``const BLIND=["warming-up",
     "no-spread"];`` (~:577, commented "Mirrors normalize.BLIND_STATUSES") —
     this lint asserts that array's VALUES, as a set, equal
     ``core.normalize.BLIND_STATUSES`` exactly, so mutating either side alone
     goes red instead of silently drifting.

     T20 adds two more consts, bound the same source-vs-source way, no data
     read either:

       - ``const STATUS=[...]`` names the full status vocabulary (all six).
         ``TestStatusConstBindsToNormalize`` asserts its VALUES, as a set,
         equal ``ALL_STATUSES`` exactly (the six ``STATUS_*`` constants
         ``core/normalize.py`` declares) — same equality relationship as
         ``BLIND``/``BLIND_STATUSES`` above, just against the full vocabulary
         rather than the non-scoring subset.
       - ``const GAP_STATUSES=[...]`` names which statuses make a tier-2
         line's watchlist item render a "NO DATA" gap chip once a line has
         held one of them for ``GAP_RUN_LOUD`` consecutive collections (see
         that const's own comment in docs/index.html). Unlike ``STATUS`` and
         ``BLIND``, this is NOT asserted equal to anything — it is a chosen
         subset (today just ``dark``), not a restatement of a fixed set
         ``core/normalize.py`` itself defines. ``TestGapStatusesConstIsBound``
         asserts it is non-empty and a SUBSET of ``ALL_STATUSES`` — every name
         it carries must be a status the code can actually emit — which is
         the full binding relationship a chosen subset admits; whether a row
         with a ``GAP_STATUSES`` status actually carries no reading is a
         property of the committed record, not of these two sources against
         each other, and belongs to (and is checked by)
         tests/audit_public_surface.py instead.

     The completion phase removed the ``verdictLabel`` map and its EN/ZH
     parity test with the deck's decision (design §6): the headline no longer
     paraphrases an adjudication, and dated annotation text stays in the
     record detail. ``TestDeckStatusAndPanelCopy`` asserts the map is gone.

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

     T17 adds a second bound claim: how many tier-1 lines run KEYLESS. Unlike
     the tier-1 count, this needs each tier-1 fetcher module's own FILE, not
     just its LINE id or a docs/index.html `const LINES` entry — neither says
     anything about API keys — so this module gets the tier-1 LINE-id SET
     from lint_registry.py's own ``_collect_registry()`` (memoized; already
     applies the TIER-defaults-to-1 rule once, reused here rather than
     re-derived a second time), resolves each collect.LINES alias to its
     fetcher FILE via that same module's ``_parse``, ``_fetcher_alias_map``
     and ``_collect_lines_aliases`` helpers (fetcher modules are never
     imported — see that module's own docstring for why), and ast-walks each
     tier-1 fetcher's own source text for an ``os.environ.get(...)`` /
     ``os.getenv(...)`` call whose argument looks like an API-key env var
     (contains "KEY"). A fetcher with no such call is keyless by
     construction. One that has a call counts as keyless only if the code
     PROVES the key is optional: an ``if not key:`` guard whose body
     delegates to another function (``fetchers/credit_spread.py``'s coded
     ``_keyless()`` fallback) rather than hard-failing in place
     (``fetchers/grid_frequency.py``'s ``return None, "missing
     FINGRID_API_KEY"`` — a tier-2 fetcher today, so it does not count either
     way, but is exactly the hard-fail shape this rule would catch on a
     tier-1 line). See ``_fetcher_is_keyless``'s own docstring for the exact
     rule and its known scope limit (it reads only the fetcher module's own
     source, not transitively through the ``core/`` helpers it imports).

  3. The line detail's definitions. Each ``const LINES`` entry in
     docs/index.html carries a bilingual ``measures`` block: the quantity the
     line measures, over what population or region, sampled how often, in
     what unit. This lint binds every parsed entry to a non-empty EN and ZH
     definition (against lint_registry.py's own entry parse, so a line cannot
     ship without one), asserts the retired causal ``explain`` field is gone,
     and asserts no definition contains one of ``CAUSAL_CONNECTIVES`` — a
     definition that explains why a reading moved is exactly the claim the
     migration removed from the page.

  4. The chart titles. ``render.py`` writes one committed PNG per primary
     line plus the summary PNG. The per-line title states the comparison
     direction recorded when the series was selected (each fetcher's own
     ``ANOMALY_DIRECTION``), in the deck's words, and never calls that
     direction an alarm. The summary title says what the bars count
     (readings in each line's recorded direction per day) and no longer calls
     that count a resonance.

  5. One neutral reading treatment. The page reports whether a reading is
     unusual; it does not report whether that is better or worse. A
     green-through-red ramp answers "more unusual = worse" on the reader's
     behalf, so the count, the reference count, the reading cards, the
     status line and the unusual marker share one neutral ink tone
     (``--reading-mark``), with emphasis coming from size, weight and the
     status wording. This lint asserts the four-way ``countColor()`` is gone,
     the two numbers are painted by the neutral rule rather than in JS, the
     stylesheet carries no severity hue, and the adjudication hatch and the
     direction-coloured chart marker are gone. ``TestNeutralReadingTreatment``'s
     docstring states the scope: CSS class and variable SPELLING is out of
     scope (``--alarm``, ``.sysstatus.alarm`` keep their names in this
     bundle), as are series hues on chart traces.

  6. Public-copy vocabulary. The reader-facing copy names a reading and its
     comparison, never an alarm, a zero state or a layer. This lint scans the
     string VALUES of docs/index.html's `const T` locale objects, each `const
     LINES` entry's ``label``/``source``/``measures``/``watches``/``domain``
     values, and README.md's prose for ``alarm``, ``报警``, ``resonance``,
     ``共振``, ``calm``, ``平静`` and the layer vocabulary. See
     `TestPublicCopyVocabulary`'s section comment for why CSS class names and
     internal identifiers stay out of the corpus.

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
import ast
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
RENDER = os.path.join(ROOT, "render.py")

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

    def test_statusLabel_keys_equal_normalizes_status_vocabulary(self):
        en_keys, _ = _status_label_key_sets()
        missing = sorted(ALL_STATUSES - en_keys)
        self.assertEqual(missing, [],
                         "core/normalize.py status(es) with no dashboard "
                         f"label in docs/index.html's statusLabel maps: {missing}")
        extra = sorted(en_keys - ALL_STATUSES)
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


# --- docs/index.html's `const NAME=[...]` status arrays ---------------------
# BLIND, STATUS and GAP_STATUSES are all `const NAME=["a","b"];` arrays read
# the same way; support.docs_const_array does the regex extraction.


@functools.lru_cache(maxsize=None)
def _docs_const(name):
    """The set of status strings inside docs/index.html's `const <name>=[...]`
    array. Memoized (see `_status_label_key_sets` above)."""
    values = support.docs_const_array(DOCS_INDEX, name)
    assert values is not None, f"docs/index.html: could not locate `const {name}=[...]`"
    assert values, f"docs/index.html: `const {name}` parsed with no values"
    return values


class TestBlindConstBindsToNormalize(unittest.TestCase):
    def test_blind_const_equals_normalize_blind_statuses(self):
        docs_blind = _docs_const("BLIND")
        want = set(normalize.BLIND_STATUSES)
        missing = sorted(want - docs_blind)
        self.assertEqual(missing, [],
                          "core.normalize.BLIND_STATUSES status(es) missing "
                          f"from docs/index.html's `const BLIND`: {missing}")
        extra = sorted(docs_blind - want)
        self.assertEqual(extra, [],
                          "docs/index.html's `const BLIND` carries status(es) "
                          f"not in core.normalize.BLIND_STATUSES: {extra}")


class TestStatusConstBindsToNormalize(unittest.TestCase):
    def test_status_const_equals_normalizes_all_statuses(self):
        docs_status = _docs_const("STATUS")
        missing = sorted(ALL_STATUSES - docs_status)
        self.assertEqual(missing, [],
                          "core/normalize.py status(es) missing from "
                          f"docs/index.html's `const STATUS`: {missing}")
        extra = sorted(docs_status - ALL_STATUSES)
        self.assertEqual(extra, [],
                          "docs/index.html's `const STATUS` carries status(es) "
                          f"core/normalize.py never emits: {extra}")


class TestGapStatusesConstIsBound(unittest.TestCase):
    def test_gap_statuses_const_is_a_nonempty_subset_of_all_statuses(self):
        gap = _docs_const("GAP_STATUSES")
        self.assertTrue(gap, "docs/index.html's `const GAP_STATUSES` is empty")
        extra = sorted(gap - ALL_STATUSES)
        self.assertEqual(extra, [],
                          "docs/index.html's `const GAP_STATUSES` carries "
                          f"status(es) core/normalize.py never emits: {extra}")


# --- docs/index.html's `verdictLabel:{...}` map (removed) --------------------
# This map used to turn an annotations.csv `verdict` into a generated headline
# qualifier. The completion phase removed it with the deck's decision (design
# doc §6: nested `verdictLabel` values -> none; no generated paraphrase of an
# adjudication). The dated annotation text still renders in the line and
# watchlist details, so the disclosure moved rather than disappeared; the
# absence of the map is bound by TestDeckStatusAndPanelCopy below, and
# tests/render_smoke.js's T22/T23 still bind the precedence rules through the
# machine-lean suppression they control.


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


# --- tier-1 line-count PARITY in the customer-facing copy --------------------
#
# The claims table binding above (TestReadmeClaimsBindToSource) already
# covers README's ONE tier-1-count TABLE row. It says nothing about the
# tier-1 count written out in PROSE elsewhere — docs/index.html's `const T`
# customer copy ("three primary lines", "三条主线") and README's own prose
# above the claims table ("Three lines", "three primary lines" x2) — which is
# exactly what R28 had to hunt down by hand when the tier count last changed.
# This is a PARITY check, not a prohibition: it asserts every such claim
# EQUALS the real tier-1 count, not that no claim exists — "three primary
# lines" is correct today and stays correct after this lint lands.
#
# Scope is deliberately NOT the whole file in either case:
#   - docs/index.html: only the `const T = {...};` block (EN + ZH customer
#     copy). The non-greedy DOTALL slice below stops at the first `\n};` it
#     meets, which lands on that block's own close despite the `${}`-style
#     template interpolations appearing inside earlier string values in the
#     file (verified against the file as committed).
#   - README.md: only the PROSE before "## Machine-checked claims" — the
#     table below that heading is already bound by TestReadmeClaimsBindToSource
#     above; scanning it too would just re-count the same claim twice.
#
# The EN regex is compiled case-INsensitively (re.I) — MANDATORY: README's
# own "Three lines" (capital T, the section's opening sentence) is missed
# without it, silently dropping one of the five claims below to a false
# green. 1/one/一 are deliberately excluded from both regexes — "One line
# moving alone" (docs, resonance prose) and "单独一根线动"/"一条海峡" (ZH) are
# not tier-1-COUNT claims and would be false positives if two/three/four/five
# admitted their singular "one" alongside them. ZH also deliberately excludes
# the bare measure words 根/条 without 主线 following — "根线"/"条线" appear
# in non-tier-1 copy (e.g. "N 根线"/"N 条线" counts of TREMBLING lines, a
# different number entirely) — the measure word is only meaningful here
# immediately before 主线 itself.
_DOCS_CONST_T_BLOCK = re.compile(r'const T = \{(.*?)\n\s*\};', re.S)
_TIER1_COUNT_EN = re.compile(
    r'(?i)(?<![\w-])(?:two|three|four|five|[2-9])\s+(?:primary\s+)?(?:lines|instruments)(?![\w-])',
    re.I)
_TIER1_COUNT_ZH = re.compile(r'[二两三四五][条根台]?主线')

# Explicit numeral -> int map, not a positional int() cast: a ZH match's own
# text carries a measure word right after the numeral character (e.g. "三条
# 主线"), so the match text itself is never a bare number to int()-cast.
_NUMERAL_TO_INT = {
    "two": 2, "three": 3, "four": 4, "five": 5,
    "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
}


def _numeral_value(token):
    """Map one matched numeral token to its int value: an EN word (any
    case — callers lowercase first) or bare digit string via
    `_NUMERAL_TO_INT` / `int()`, or a single ZH numeral character via the
    same map. Never receives more than the numeral itself — see the two
    call sites in `_tier1_line_count_claims` below, which each slice just
    that substring out of the full regex match before calling this."""
    key = token.lower()
    if key in _NUMERAL_TO_INT:
        return _NUMERAL_TO_INT[key]
    return int(key)


@functools.lru_cache(maxsize=None)
def _docs_const_T_block():
    """The text inside docs/index.html's `const T = {...};` block (English +
    Chinese customer copy) — see the module-level scope note above for why
    this non-greedy DOTALL slice lands on the block's own close. Memoized
    (see `_status_label_key_sets` above)."""
    html = support.read_text(DOCS_INDEX)
    m = _DOCS_CONST_T_BLOCK.search(html)
    assert m, "docs/index.html: could not locate a `const T = {...};` block"
    return m.group(1)


@functools.lru_cache(maxsize=None)
def _readme_prose_before_claims_table():
    """README.md's text up to (not including) the "## Machine-checked
    claims" heading — the claims TABLE past that heading is already scanned
    by `_readme_claims` above; this is the unbound PROSE before it."""
    readme = support.read_text(README)
    return readme.split("## Machine-checked claims")[0]


def _tier1_line_count_claims():
    """Every tier-1-line-count numeral claimed in the customer-facing copy —
    docs/index.html's `const T` block and README's prose before the claims
    table — as a flat list of ints, one per regex match, in source order
    (docs EN, docs ZH, then README EN; README carries no ZH prose). Not a
    set: a correct claim appearing twice is two matches, both expected to
    equal the real count downstream, same as a single wrong one appearing
    once is one mismatch."""
    values = []
    for text in (_docs_const_T_block(), _readme_prose_before_claims_table()):
        for m in _TIER1_COUNT_EN.finditer(text):
            values.append(_numeral_value(m.group(0).split()[0]))
        for m in _TIER1_COUNT_ZH.finditer(text):
            values.append(_numeral_value(m.group(0)[0]))
    return values


class TestTier1LineCountClaimsBindToSource(unittest.TestCase):
    def test_every_tier1_count_claim_in_the_public_copy_matches_the_real_count(self):
        matches = _tier1_line_count_claims()
        self.assertTrue(matches, "no tier-1-count claim found in docs/index.html's "
                         "`const T` block or README.md's prose — this check would "
                         "pass vacuously")
        want = _docs_tier1_line_count()
        wrong = sorted(set(v for v in matches if v != want))
        self.assertEqual(wrong, [],
                          f"public copy claims a tier-1 line count of {wrong} "
                          f"somewhere, but the real tier-1 count is {want} — grep "
                          "docs/index.html's `const T` block and README.md's prose "
                          "above '## Machine-checked claims' for a stale "
                          "\"N lines\"/\"N primary lines\"/\"N条主线\" claim")


# --- README.md's "primary lines that run keyless" claim ----------------------
#
# docs/index.html's `const LINES` and lint_registry.py's parses of it say
# nothing about API keys, so this claim cannot reuse those the way the
# tier-1 COUNT claim above does. Instead it gets the tier-1 LINE-id SET off
# lint_registry.py's own memoized `_collect_registry()` (which already
# applies the TIER-defaults-to-1 rule — reused here, not re-derived a second
# time), resolves each collect.LINES alias to its fetcher FILE via that same
# module's `_parse`/`_fetcher_alias_map`/`_collect_lines_aliases` helpers,
# and ast-walks each tier-1 fetcher's own source text. No fetcher module is
# ever imported (see the module docstring): every fetcher imports `requests`
# at module scope, which ci.yml's lint job never installs.

@functools.lru_cache(maxsize=None)
def _tier1_fetcher_trees():
    """[(modname, ast.Module)] for every collect.LINES alias whose fetcher
    module's own LINE id lint_registry._collect_registry() marks tier 1.
    Memoized — pure and no-arg, same pattern as this file's other
    source-parsing helpers (`_readme_claims`, `_docs_const`, etc.)."""
    registry, _ = lint_registry._collect_registry()
    tier1_ids = {line_id for line_id, meta in registry.items() if meta["tier"] == 1}
    collect_tree = lint_registry._parse(lint_registry.COLLECT_PATH)
    alias_map = lint_registry._fetcher_alias_map(collect_tree)
    aliases = lint_registry._collect_lines_aliases(collect_tree)
    assert aliases, "collect.py: no module-level `LINES = [...]` assignment found"
    out = []
    for alias in aliases:
        modname = alias_map.get(alias)
        assert modname, (f"collect.LINES references {alias!r}, which does not resolve "
                          "to a `from fetchers import ...` (or `import fetchers.mod as "
                          "...`) binding in collect.py")
        tree = lint_registry._parse(
            os.path.join(lint_registry.FETCHERS_DIR, f"{modname}.py"))
        line_id = lint_registry._module_level_const(tree, "LINE")
        if line_id in tier1_ids:
            out.append((modname, tree))
    return out


_KEY_ENV_VAR = re.compile(r'KEY', re.I)


def _is_key_lookup_call(node):
    """True if ``node`` is ``os.environ.get("...")`` / ``os.getenv("...")``
    whose string-constant argument looks like an API-key env var (contains
    "KEY", case-insensitively — matches both ``FRED_API_KEY`` and
    ``FINGRID_API_KEY``, the only two such lookups under fetchers/ today;
    see fetchers/credit_spread.py and fetchers/grid_frequency.py)."""
    if not isinstance(node, ast.Call) or not node.args:
        return False
    func = node.func
    is_environ_get = (
        isinstance(func, ast.Attribute) and func.attr == "get"
        and isinstance(func.value, ast.Attribute) and func.value.attr == "environ"
        and isinstance(func.value.value, ast.Name) and func.value.value.id == "os")
    is_getenv = (
        isinstance(func, ast.Attribute) and func.attr == "getenv"
        and isinstance(func.value, ast.Name) and func.value.id == "os")
    if not (is_environ_get or is_getenv):
        return False
    arg = node.args[0]
    return (isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            and _KEY_ENV_VAR.search(arg.value) is not None)


def _key_lookups(tree):
    """[(call, varname_or_None)] — one entry per key-lookup call anywhere in
    ``tree`` (see ``_is_key_lookup_call``), paired with the bare variable
    name it is assigned to (``key`` in ``key = os.environ.get(
    "FRED_API_KEY")``), or None when it is not a simple single-name
    assignment — which ``_fetcher_is_keyless`` then treats as a required
    (not provably optional) key. A SINGLE ``ast.walk`` answers both "is this
    a key lookup" and "what name does it bind to": an ``Assign`` node's own
    Call value is visited by the same walk that visits the Call directly, so
    recording ``{id(call): varname}`` for every Call-valued Assign while
    walking, then pairing each matching Call against that map afterward,
    needs no second traversal (unlike looking up each call's assignment with
    its own separate ``ast.walk`` call)."""
    assigned = {}
    calls = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call)):
            assigned[id(node.value)] = node.targets[0].id
        elif isinstance(node, ast.Call):
            calls.append(node)
    return [(c, assigned.get(id(c))) for c in calls if _is_key_lookup_call(c)]


def _guard_delegates_on_missing_key(tree, varname):
    """True if the module contains ``if not <varname>: ...`` (or ``if
    <varname> is None: ...``) whose body RETURNS THE RESULT OF CALLING
    another function — a coded fallback path, exactly
    fetchers/credit_spread.py's own ``if not key: return
    _keyless(reason)`` — rather than a value built in place right there (a
    literal dict/tuple/None), which means the fetch hard-fails without the
    key: fetchers/grid_frequency.py's own ``if not key: return None,
    "missing FINGRID_API_KEY"`` is exactly that hard-fail shape (a tier-2
    fetcher today; this is what would make it count as NOT keyless if it
    were ever promoted to tier 1)."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        is_not_var = (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
                      and isinstance(test.operand, ast.Name)
                      and test.operand.id == varname)
        is_none_check = (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
                          and test.left.id == varname and len(test.ops) == 1
                          and isinstance(test.ops[0], ast.Is) and len(test.comparators) == 1
                          and isinstance(test.comparators[0], ast.Constant)
                          and test.comparators[0].value is None)
        if not (is_not_var or is_none_check):
            continue
        if any(isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call)
               for stmt in node.body):
            return True
    return False


def _fetcher_is_keyless(tree):
    """A tier-1 fetcher module counts as keyless if it either never looks up
    an API-key-shaped env var at all (fetchers/flights.py,
    fetchers/cnh_cny.py and fetchers/net_outages.py today — no
    ``os.environ``/``os.getenv`` call anywhere in the module), or it does and
    every such lookup is provably OPTIONAL — guarded by an ``if not key:``
    check that DELEGATES to another function rather than hard-failing in
    place (fetchers/credit_spread.py's coded ``_keyless()`` fallback: the
    public fredgraph.csv path FRED_API_KEY's absence falls back to, per that
    module's own docstring). Scoped to the fetcher module's own source only,
    not transitively through ``core/`` helpers it imports — true of every
    tier-1 fetcher today (checked by hand: none of core/adsb.py,
    core/fred.py, core/useragent.py or core/clock.py reference any env var),
    but a future fetcher that hid a required key inside a core/ helper would
    not be caught by this check."""
    lookups = _key_lookups(tree)
    if not lookups:
        return True
    for _, varname in lookups:
        if varname is None or not _guard_delegates_on_missing_key(tree, varname):
            return False
    return True


def _tier1_keyless_line_count():
    """How many of collect.LINES's tier-1 fetcher modules are keyless per
    ``_fetcher_is_keyless`` above."""
    return sum(1 for _, tree in _tier1_fetcher_trees() if _fetcher_is_keyless(tree))


# --- LINES[].measures: what a line measures, never why it moved -------------
#
# The public line detail renders one definition per line: the quantity, the
# population or region, the sampling cadence and the unit. The causal `explain`
# paragraphs it replaced asserted what a reading means about the world, which a
# measurement cannot support. The vocabulary bound here is therefore closed by
# assertion rather than by review: no definition may carry a causal connective,
# and the retired field may not come back.

CAUSAL_CONNECTIVES = ("because", "causes", "caused by", "means that",
                     "说明", "意味着", "导致", "正是因为")

_LINES_BLOCK = re.compile(r'const LINES = \[(.*?)\n\];', re.S)
# The opening of one `const LINES` entry -- `{ id:"flights", color:"..."`.
_JS_ENTRY_START = re.compile(r'\{\s*id:"([^"]+)"')
# A `measures:{en:"...", zh:"..."}` block. No definition contains a `}` (they
# are prose about a series), so a negated character class lands on the block's
# own close without needing to balance braces.
_MEASURES_BLOCK = re.compile(r'measures:\{([^}]*)\}')
_MEASURES_VALUE = re.compile(r'(en|zh):"([^"]*)"')


@functools.cache
def _docs_measures():
    """{line id: {lang: definition}} for every `measures:{...}` block inside
    docs/index.html's `const LINES` entries. A line with no block maps to `{}`,
    so a missing definition is reported as a missing definition rather than
    silently left out of the mapping. Memoized (see `_status_label_key_sets`)."""
    block = _LINES_BLOCK.search(support.read_text(DOCS_INDEX))
    assert block, "docs/index.html: could not locate `const LINES = [ ... ];`"
    body = block.group(1)
    starts = list(_JS_ENTRY_START.finditer(body))
    assert starts, "docs/index.html: no `const LINES` entry parsed"
    out = {}
    for i, start in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(body)
        found = _MEASURES_BLOCK.search(body[start.start():end])
        out[start.group(1)] = dict(_MEASURES_VALUE.findall(found.group(1))) if found else {}
    return out


class TestLineDetailStatesWhatIsMeasured(unittest.TestCase):
    def test_every_line_declares_a_bilingual_measures_definition(self):
        measures = _docs_measures()
        registry, _ = lint_registry._docs_registry()
        self.assertEqual(sorted(measures), sorted(registry),
                          "docs/index.html's `const LINES` entries and the lines "
                          "carrying a `measures` block are not the same set: "
                          f"no definition {sorted(set(registry) - set(measures))}, "
                          f"unknown line {sorted(set(measures) - set(registry))}")
        incomplete = sorted(line_id for line_id, by_lang in measures.items()
                            if set(by_lang) != {"en", "zh"}
                            or not all(text.strip() for text in by_lang.values()))
        self.assertEqual(incomplete, [],
                          "line(s) with a missing or empty `measures` value in one "
                          f"language: {incomplete}")

    def test_the_causal_explain_field_is_gone(self):
        html = support.read_text(DOCS_INDEX)
        self.assertNotIn("explain:", html,
                          "docs/index.html still declares an `explain` field -- the "
                          "line detail states what a line measures, not why a value moved")
        self.assertNotIn(".explain", html,
                          "docs/index.html still reads an `.explain` field")

    def test_no_measures_definition_carries_a_causal_connective(self):
        hits = []
        for line_id, by_lang in sorted(_docs_measures().items()):
            for lang, text in sorted(by_lang.items()):
                folded = text.lower()
                for word in CAUSAL_CONNECTIVES:
                    if word.lower() in folded:
                        hits.append(f"{line_id}.{lang}: {word!r}")
        self.assertEqual(hits, [],
                          "`measures` definition(s) carry a causal connective, which "
                          "puts an explanation of a reading back on the page: "
                          f"{hits}")


class TestChartTitlesStateTheRecordedDirection(unittest.TestCase):
    """A per-line chart title records a selection note, not a verdict.

    ``render.py`` used to title every committed PNG ``alarming when up`` /
    ``alarming when down``. That reads the direction as an alarm — a judgment
    about the world — while the same direction is, in the registry, the one
    written down when the line was built. The title says that, in the deck's
    words, with the fetcher's own direction interpolated.
    """

    def test_per_line_chart_title_names_the_recorded_comparison_direction(self):
        src = support.read_text(RENDER)
        self.assertNotIn("alarming when", src,
                         "render.py still titles a per-line chart `alarming when …`")
        calls = re.findall(r"ax\.set_title\((.*?)\)", src, re.S)
        title = next((re.sub(r"\s+", " ", c) for c in calls
                      if "ANOMALY_DIRECTION" in c), None)
        if title is None:
            self.fail("render.py no longer interpolates a line's ANOMALY_DIRECTION "
                      "into any chart title")
        self.assertIn("Comparison direction noted when this series was selected:", title,
                      "render.py's per-line chart title does not state the recorded "
                      "comparison direction")
        self.assertIn("{mod.ANOMALY_DIRECTION}", title,
                      "render.py's per-line chart title does not interpolate the "
                      "line's own direction")

    def test_overview_title_states_what_the_bars_count(self):
        src = support.read_text(RENDER)
        self.assertNotIn("resonance", src.lower(),
                         "render.py still describes the summary PNG as a resonance; "
                         "the bars count readings in their recorded direction")
        titles = re.findall(r'ax\.set_title\(f"([^"]*)"', src)
        summary = [t for t in titles if "(0-" in t]
        self.assertEqual(len(summary), 1,
                         "render.py no longer titles the summary chart with its "
                         f"dynamic 0-N ceiling: {titles}")
        self.assertIn("recorded direction", summary[0],
                      "render.py's summary chart title does not say that the bars "
                      f"count readings in their recorded direction: {summary[0]!r}")


class TestRealVsFeltChartIsGone(unittest.TestCase):
    """The real-vs-felt chart is deleted, not renamed.

    The deck removes the chart, its explanation and its render path: two unlike
    series on one picture invite a comparison the record cannot support, and
    the copy around it carried the last world-disorder framing on the page.
    ``data/leans.csv`` stays served — its same-day machine lean is read by the
    headline (``leanMap``), a different consumer.
    """

    def test_no_feel_chart_code_remains(self):
        html = support.read_text(DOCS_INDEX)
        for token in ("feelchart", "feelChart", "FEEL_IDS", "isDivergent",
                      "FEEL_HOT"):
            self.assertNotIn(token, html,
                             f"docs/index.html still carries feel-chart code {token!r}")

    def test_no_feel_chart_copy_remains(self):
        html = support.read_text(DOCS_INDEX)
        for key in ("feelTitle", "feelHint", "feelGapNote", "feelBars"):
            self.assertNotIn(f"{key}:", html,
                             f"docs/index.html still declares the retired copy key "
                             f"{key!r}")


class TestDeckStatusAndPanelCopy(unittest.TestCase):
    """The banner, panel headings, dated notes and footer carry the deck's words.

    The retired banner keys read an absence of data as a signal (``alarmDarkB``:
    "widespread source failure is itself a signal") and split a collection gap
    into a heading plus a body. The deck replaces them with complete sentences:
    ``manyDark``, ``disruption``, ``noRecord``, and the four ``statusOk`` /
    ``awaiting`` / ``warnH`` / ``warnB`` rows.
    """

    def test_retired_banner_keys_are_gone(self):
        html = support.read_text(DOCS_INDEX)
        for key in ("alarmDarkH", "alarmDarkB", "disruptH", "disruptB"):
            self.assertNotIn(f"{key}:", html,
                             f"docs/index.html still declares the retired banner key "
                             f"{key!r}")

    def test_deck_keys_are_declared_in_both_locales(self):
        html = support.read_text(DOCS_INDEX)
        for key in ("manyDark", "disruption", "noRecord", "annoBody",
                    "zAxis", "close", "aboutTitle", "aboutBody"):
            self.assertEqual(html.count(f"{key}:"), 2,
                             f"docs/index.html should declare {key!r} in both "
                             f"locales, found {html.count(f'{key}:')}")

    def test_main_chart_axis_title_uses_the_z_axis_key(self):
        html = support.read_text(DOCS_INDEX)
        self.assertIn("text:T[lang].zAxis", html,
                      "the history chart still hardcodes its vertical-axis label "
                      "instead of reading the deck's `zAxis` key")

    def test_the_run_is_direction_free(self):
        html = support.read_text(DOCS_INDEX)
        self.assertNotIn("tremblingRunLength", html,
                         "the page still stops a run at the first departure that "
                         "moves against the line's recorded direction")
        self.assertIn("function unusualRunLength(rows)", html,
                      "the page has no direction-free run helper")

    def test_the_adjudication_paraphrase_is_gone(self):
        html = support.read_text(DOCS_INDEX)
        self.assertNotIn("verdictLabel", html,
                         "docs/index.html still declares or reads the retired "
                         "`verdictLabel` map; the deck keeps dated notes in the "
                         "record detail and no generated paraphrase in the headline")


# --- the neutral reading mark: one tone, no severity ramp -------------------
#
# The four severity colours the old ramp was built from, by CSS variable name
# and by the literal spellings the stylesheet used for them. A status is read
# from its word, never from a hue; series colours identify a chart trace and
# never encode a status or a magnitude.
SEVERITY_TOKENS = (
    "--calm", "--amber", "--orange", "--alarm",
    "#3fb27f", "#e0a83d", "#e07b39", "#d64545", "#ff6b6b",
    "63,178,127", "224,168,61", "224,123,57", "214,69,69",
)
_STYLE_BLOCK = re.compile(r"<style>(.*?)</style>", re.S)
# `.count .n` is the element rule that covers both `#count-n` and `#level-n`
# (the fixed-reference block reuses `.count .count-level`).
_COUNT_NUMBER_RULE = re.compile(r"\.count \.n\{([^}]*)\}")


@functools.cache
def _docs_style_block():
    """The text inside docs/index.html's single ``<style>`` block. Memoized
    (see `_status_label_key_sets` above)."""
    block = _STYLE_BLOCK.search(support.read_text(DOCS_INDEX))
    assert block, "docs/index.html: could not locate a `<style>...</style>` block"
    return block.group(1)


class TestNeutralReadingTreatment(unittest.TestCase):
    """One neutral tone for every reading, in both directions.

    SCOPE: this is a docs/index.html STYLE check, not a vocabulary check. CSS
    class and variable SPELLING is deliberately not policed -- the plan keeps
    ``--alarm`` and ``.sysstatus.alarm`` as names in this bundle, and renaming
    internal identifiers is a separate job. What must not survive is a hue
    TREATMENT on a number, a card, the status line or the unusual marker.
    Series hues (``L.color``, a chart dataset's own border/point colour) are
    out of scope too: they identify a series and never a status.
    """

    def test_count_color_is_gone(self):
        html = support.read_text(DOCS_INDEX)
        self.assertNotIn("countColor", html,
                          "docs/index.html still defines or calls countColor -- the "
                          "count is one neutral reading, not a severity ramp")

    def test_the_count_and_reference_numbers_use_the_neutral_reading_mark(self):
        html = support.read_text(DOCS_INDEX)
        self.assertRegex(html, r"--reading-mark:\s*#c7ccd6",
                         "docs/index.html declares no neutral `--reading-mark`")
        rule = _COUNT_NUMBER_RULE.search(_docs_style_block())
        self.assertIsNotNone(rule, "docs/index.html: no `.count .n{...}` rule found")
        assert rule is not None
        self.assertIn("color:var(--reading-mark)", rule.group(1),
                      "the count and reference numbers (`.count .n`, i.e. #count-n and "
                      "#level-n) are not painted with the neutral reading mark")
        for element in ("count-n", "level-n"):
            writes = [ln for ln in html.splitlines()
                      if f'getElementById("{element}")' in ln]
            self.assertTrue(writes,
                            f"docs/index.html no longer writes #{element}")
            painted = [ln for ln in writes if "style.color" in ln]
            self.assertEqual(painted, [],
                             f"#{element} is painted with a hue in JS instead of the "
                             f"neutral reading mark: {painted}")

    def test_no_severity_hue_remains_in_the_stylesheet(self):
        style = _docs_style_block()
        folded = style.lower()
        hits = [token for token in SEVERITY_TOKENS if token.lower() in folded]
        self.assertEqual(hits, [],
                         "docs/index.html's stylesheet still carries the old severity "
                         f"ramp colour(s) {hits}; one neutral tone replaces it")
        self.assertNotIn("--dot", support.read_text(DOCS_INDEX),
                         "a reading card still paints a series-colour accent (`--dot`); "
                         "series hues belong to chart traces only")

    def test_the_unusual_marker_does_not_hatch(self):
        html = support.read_text(DOCS_INDEX)
        self.assertNotIn(".pill.trembling.adjudicated", html,
                          "docs/index.html still declares the adjudicated hatch rule")
        self.assertNotIn('" adjudicated"', html,
                          "the unusual marker still emits an adjudication-specific class")
        self.assertNotIn("ptColor", html,
                          "the history chart still colours a tremble point by direction")
        self.assertNotIn("rgba(214,69,69,.45)", html,
                          "the trembling-threshold guide is still painted in the alarm hue")


# --- the public-copy vocabulary guard ---------------------------------------
#
# A reading is not a verdict about the world, so the reader-facing copy cannot
# call a departure an "alarm", call a day without one "calm", call several at
# once "resonance", or describe the roster as layers. The strings the page and
# the README used to carry for those terms are gone; these tests keep them from
# coming back.
#
# SCOPE -- user-visible VALUES only, from three surfaces:
#   * every double-quoted string VALUE inside docs/index.html's `const T`
#     locale objects (English and Chinese),
#   * each `const LINES` entry's `label`, `source`, `measures`, `watches` and
#     `domain` values, both languages,
#   * README.md's prose (the whole file).
# Deliberately NOT scanned: the stylesheet, markup attribute values, JS code and
# comments. CSS class and custom-property spellings (--alarm,
# .sysstatus.alarm), the `trembling` pill class and JS identifiers keep their
# spelling in this bundle, and an unquoted T key name such as `alarmDarkH` is an
# internal identifier, not copy -- its VALUE ("N of M instruments dark.") is what
# a reader sees and what this guard reads.
# `test_the_guard_scans_visible_copy_only` binds that scope: widening the corpus
# to the whole file (or to the stylesheet) turns it red.
BANNED_COPY_WORDS = ("alarm", "报警", "resonance", "共振", "calm", "平静")
# `calm`/`平静` are banned outright rather than only in a narrow "zero-state"
# sense: on this page every use of the word reads the absence of a departure as
# a state of the world, which is the claim the migration removed.
_LAYER_VOCABULARY = (
    (re.compile(r"第[一二三]层"), "第一层/第二层/第三层"),
    (re.compile(r"(?i)\blayers?\s*[123]\b"), "Layer 1/2/3"),
    (re.compile(r"\bL[123]\b"), "L1/L2/L3"),
    (re.compile(r"(?i)\btier of analysis\b"), "tier of analysis"),
)

# A JS double-quoted string on one line; an escaped quote does not end it.
# Backtick text is NOT read: inside this block the backtick spans are code
# comments naming internal values (`real`, `benign`), not copy.
_JS_STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')
# One `field:{en:"...",zh:"..."}` pair on a single line. `unit` is left out on
# purpose: it is a measure word ("aircraft", "架"), not prose.
_JS_LINE_COPY_FIELD = re.compile(
    r'(?:watches|domain|label|source):\s*\{en:"((?:[^"\\\n]|\\.)*)",'
    r'\s*zh:"((?:[^"\\\n]|\\.)*)"\}')


def _line_of(html, needle):
    """1-based line number of `needle` in `html`; fails loudly if absent."""
    at = html.find(needle)
    assert at != -1, f"docs/index.html: copy string not found: {needle[:60]!r}"
    return html[:at].count("\n") + 1


@functools.cache
def _visible_copy(surface):
    """[(where, text)] for one user-visible surface: ``"locale"`` for the T
    block's string values, ``"lines"`` for the five copy fields of every
    ``const LINES`` entry, ``"readme"`` for README.md. Memoized (see
    `_status_label_key_sets` above)."""
    if surface == "readme":
        return [("README.md", support.read_text(README))]

    html = support.read_text(DOCS_INDEX)
    if surface == "locale":
        block = _DOCS_CONST_T_BLOCK.search(html)
        assert block, "docs/index.html: could not locate a `const T = {...};` block"
        body, start = block.group(1), block.start(1)
        out = []
        for m in _JS_STRING.finditer(body):
            if body.startswith(":", m.end()):
                continue                      # a quoted KEY, not a value
            line = html[:start + m.start()].count("\n") + 1
            out.append((f"docs/index.html:{line}", m.group(0)[1:-1]))
        assert out, "docs/index.html's `const T` block parsed with no string values"
        return out

    assert surface == "lines", f"unknown copy surface {surface!r}"
    block = _LINES_BLOCK.search(html)
    assert block, "docs/index.html: could not locate `const LINES = [ ... ];`"
    body, start = block.group(1), block.start(1)
    out = []
    for m in _JS_LINE_COPY_FIELD.finditer(body):
        line = html[:start + m.start()].count("\n") + 1
        out.append((f"docs/index.html:{line}", m.group(1)))
        out.append((f"docs/index.html:{line}", m.group(2)))
    for by_lang in _docs_measures().values():
        for text in by_lang.values():
            out.append((f"docs/index.html:{_line_of(html, text)}", text))
    # 24 lines x (label, source, domain) x 2 languages is the floor; a parse
    # that silently drops the block fails here rather than passing vacuously.
    assert len(out) >= 24 * 3 * 2, (
        "docs/index.html's `const LINES` copy fields parsed to only "
        f"{len(out)} values -- the block's shape changed")
    return out


def _banned_copy_hits(text):
    """The banned token(s) one copy string carries, in declaration order."""
    folded = text.lower()
    hits = [word for word in BANNED_COPY_WORDS if word.lower() in folded]
    hits.extend(label for pattern, label in _LAYER_VOCABULARY if pattern.search(text))
    return hits


class TestPublicCopyVocabulary(unittest.TestCase):
    """No reader-facing string names an alarm, a zero state or a layer.

    See the section comment above for the exact corpus and its exclusions: the
    ban reaches user-visible VALUES, not CSS class names or internal
    identifiers.
    """

    def _assert_clean(self, surface):
        offenders = []
        for where, text in _visible_copy(surface):
            hits = _banned_copy_hits(text)
            if hits:
                offenders.append(f"{where}: {hits} in {text[:90]!r}")
        self.assertEqual(offenders, [],
                         "user-visible copy still carries retired reading "
                         f"vocabulary ({surface}):\n" + "\n".join(offenders))

    def test_locale_strings_carry_no_banned_vocabulary(self):
        self._assert_clean("locale")

    def test_line_metadata_carries_no_banned_vocabulary(self):
        self._assert_clean("lines")

    def test_readme_prose_carries_no_banned_vocabulary(self):
        self._assert_clean("readme")

    def test_the_guard_scans_visible_copy_only(self):
        corpus = "\n".join(text for surface in ("locale", "lines", "readme")
                           for _, text in _visible_copy(surface))
        # Every in-scope surface is represented.
        self.assertIn("A statistical comparison, not a judgment of conditions.", corpus)
        self.assertIn("Aircraft reported airborne across W/C Europe", corpus)
        self.assertIn("## Machine-checked claims", corpus)
        # Internal spellings the ban deliberately exempts. Widening the corpus
        # to the whole file or to the stylesheet would put these in it.
        for internal in ("--reading-mark", ".sysstatus", "alarmDarkH",
                         "const LINES", "<style>"):
            self.assertNotIn(internal, corpus,
                             "the vocabulary guard's corpus includes the internal "
                             f"spelling {internal!r}; it must scan copy only")


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
            ("primary lines that run keyless", _tier1_keyless_line_count(),
             "README.md claims a keyless tier-1 line count that does not "
             "match what fetchers/*.py's tier-1 modules actually require "
             "(see _fetcher_is_keyless's docstring for the exact rule)"),
        ]
        for label, expected, msg in checks:
            with self.subTest(label=label):
                self.assertIn(label, claims,
                               f"README.md's Machine-checked claims table has no {label!r} row")
                self.assertEqual(claims[label], expected, msg)


class TestMarkupHasOneAuditedSink(unittest.TestCase):
    """docs/index.html writes markup in exactly one place, and that place is audited.

    Every row this page shows comes from a CSV, and some of those cells are
    written by a fetcher from whatever a remote answered: the record already
    holds a gateway's whole HTML error page in an ``hkma_aggr_balance``
    ``source_note``, and the FRED incident put ``<link href=…`` into five lines'
    notes. A page that interpolates such a cell into ``innerHTML`` executes
    whatever the upstream sent, in every reader's browser, forever — the CSV is
    append-only, so the payload is never retracted.

    The defence is two-part and both parts are checked here:

    * ``esc()`` is applied to the record-derived strings (``source_note``, an
      annotation's ``note``/``verdict``) at the sink. ``tests/render_smoke.js``
      proves it end to end with a payload fixture, in both languages.
    * every markup write goes through ``setMarkup(el, html)``, so there is ONE
      line in the file that can do harm and reviewing it is a two-second job. A
      new ``el.innerHTML = someRow.source_note`` cannot be added quietly.

    STDLIB-ONLY (lint tier): the file is read as text, never parsed or executed.
    """

    def _html(self):
        with open(DOCS_INDEX, encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def _code_lines(text):
        """The file's lines with comments and blank lines dropped.

        A comment may name the thing being banned — the ``setMarkup`` docstring
        does, on purpose — without that counting as a use of it.
        """
        out = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            out.append(line)
        return out

    def test_exactly_one_inner_html_assignment_exists(self):
        code = [ln for ln in self._code_lines(self._html()) if "innerHTML" in ln]
        self.assertEqual(
            len(code), 1,
            "docs/index.html should write markup in exactly one place (setMarkup); "
            f"found {len(code)} lines naming innerHTML outside comments: {code}")

    def test_the_one_assignment_is_inside_set_markup(self):
        code = [ln for ln in self._code_lines(self._html()) if "innerHTML" in ln]
        self.assertTrue(code, "no innerHTML assignment found — did setMarkup go away?")
        self.assertIn("function setMarkup(", code[0])
        self.assertIn("el.innerHTML", code[0])

    def test_set_markup_is_the_only_door(self):
        """No ``.innerHTML`` may be written other than through setMarkup."""
        text = self._html()
        self.assertIn("function setMarkup(el,html)", text)
        # every push into the DOM goes through the helper: count its uses, and
        # require that no other line assigns to an element's innerHTML
        code = self._code_lines(text)
        other = [ln for ln in code
                 if "innerHTML" in ln and "function setMarkup(" not in ln]
        self.assertEqual(other, [], f"markup written outside setMarkup: {other}")

    def test_esc_escapes_all_five_metacharacters(self):
        """The helper must cover every character that can start markup or a scheme.

        The escape map is read off the one ``esc()`` line rather than re-stated:
        asserting that the source text contains a particular pair of quote
        characters would test how Python spells them, not what the page escapes.
        """
        line = next((ln for ln in self._html().splitlines()
                     if "function esc(v)" in ln), None)
        if line is None:
            self.fail("esc() is gone from docs/index.html")
        char_class = re.search(r"replace\(/\[(.*?)\]/g", line)
        if char_class is None:
            self.fail("esc() no longer takes a character class")
        matched = char_class.group(1)
        for ch in ("&", "<", ">", '"', "'"):
            self.assertIn(ch, matched, f"esc() does not match {ch!r}")
        for entity in ("&amp;", "&lt;", "&gt;", "&quot;", "&#39;"):
            self.assertIn(entity, line, f"esc() does not emit {entity}")

    def test_the_record_derived_strings_go_through_esc(self):
        """The three sinks that render a CSV cell must call esc() on it."""
        text = self._html()
        self.assertIn("esc(todayRow.source_note)", text,
                      "a dark row's source_note reaches the DOM unescaped")
        self.assertIn("esc(a.note)", text, "an annotation note reaches the DOM unescaped")
        self.assertIn("esc(a.verdict)", text, "an annotation verdict reaches the DOM unescaped")


if __name__ == "__main__":
    unittest.main()
