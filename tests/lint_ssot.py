"""One-home guards for arithmetic and ids that must have exactly one
definition (SSOT = single source of truth). Shared across tasks; net_outages'
settled-window boundary (T1) is the first tenant, FRED series ids (T2) the
second, the User-Agent header (T3) the third.

The net_outages settle boundary (R23.1) is the one place a drift silently
writes a WRONG tier-1 raw that forward-only then freezes forever: the live
collection path (fetchers/net_outages.py:window_for/window_for_day), the
reconciliation tool and the seeder all have to agree on "24h ending at the
most recent 22:00:00Z", so this scans for the ARITHMETIC that produces that
boundary (``datetime.time(22, 0)`` / bare ``time(22, 0)``, and the
``.replace(hour=22, ...)`` form) rather than the bare literal ``22``, which
also appears harmlessly in prose (e.g. "24h to <date> 22:00Z" source notes at
fetchers/net_outages.py and tools/seed_ioda.py).

The FRED series ids (T2) are a smaller instance of the same shape: each
FRED-backed fetcher is the one place its series id(s) may be typed as a
string literal (a public module-level ``SERIES``); tools/seed_fred.py and
tools/repair_fred_seed.py must read ``mod.SERIES`` rather than re-typing the
id, so a rotated or renamed series id cannot drift between the fetcher and
the seed tool that rebuilds its history.

The User-Agent header (T3) is the same shape again: every network fetcher
used to carry its own copy of the literal ``tremor/1.0
(+https://github.com/wan9yu/tremor)`` (plus cnh_cny's browser-shaped Yahoo
variant and a truncated third in tools/reconcile_net_outages.py); a wrong UA
only gets a source blocked (a recoverable dark row, never a frozen wrong
raw), so the risk here is drift, not corruption — but cnh_cny's variant is
load-bearing for Yahoo and stays a deliberate second exception
(``core.useragent.COMPAT_HEADERS``), not a violation.

LINT, not gate: a source scan, not a property of the running instrument, so
it runs on push via ``unittest discover tests -p "lint_*.py"`` (ci.yml's
lint job) and is deliberately NOT part of daily.yml's pre-collect gate — a
convention violation here must never cost an irreplaceable collection day.
"""
import ast
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support
from core import useragent

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


# --- FRED series ids (T2): declared once, read by seeders -----------------

FETCHERS_DIR = "fetchers"
TOOLS_DIR = "tools"

# A top-level (module-scope) import of core.fred — the fetcher whose job is
# reading one (or a paired two) FRED series, as opposed to a tool that merely
# calls a generically-supplied id through core/fred.py's helpers.
_FRED_IMPORT = re.compile(r'^(?:from core import fred\b|import core\.fred\b)', re.M)

# String-literal extraction uses ``ast``, not a hand-rolled quote-pairing
# regex: several of these fetcher/tool docstrings themselves quote prose
# (e.g. credit_spread.py's docstring quotes the wrong sentence it corrects),
# which desyncs a naive ``"([^"]+)"`` scan against the file's real string
# boundaries — ast.parse tokenizes the same way the Python interpreter does,
# so it is immune to that.


def _fetchers_importing_fred():
    """fetchers/*.py files with a module-level ``from core import fred`` (or
    ``import core.fred``) — the modules whose job is reading FRED series."""
    found = []
    for f in sorted(os.listdir(os.path.join(ROOT, FETCHERS_DIR))):
        if f.endswith(".py"):
            rel = os.path.join(FETCHERS_DIR, f)
            if _FRED_IMPORT.search(support.read_text(os.path.join(ROOT, rel))):
                found.append(rel)
    return found


def _tools_py_files():
    return sorted(os.path.join(TOOLS_DIR, f)
                  for f in os.listdir(os.path.join(ROOT, TOOLS_DIR))
                  if f.endswith(".py"))


def _parse(rel):
    path = os.path.join(ROOT, rel)
    return ast.parse(support.read_text(path), filename=path)


def _module_level_series_value(tree):
    """The AST value node of a module-level ``SERIES = ...`` assignment (a
    direct statement in the module body — not indented inside a function or
    class, which would not be the public declaration this checks for), or
    None if the module declares no such name."""
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "SERIES"):
            return node.value
    return None


def _string_literals(node):
    """Every plain string embedded in an AST value node — a bare constant,
    or the members of a Tuple/List (sofr_iorb's two-leg
    ``SERIES = ("SOFR", "IORB")``)."""
    if node is None:
        return []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [s for elt in node.elts for s in _string_literals(elt)]
    return []


def _all_string_literals(tree):
    """Every string literal anywhere in a parsed module — docstrings, plain
    strings, and the static text segments of f-strings alike — so a
    re-hard-coded id is caught even folded into a longer note string."""
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


class TestFredSeriesDeclaredOnceReadBySeeders(unittest.TestCase):
    def test_fetchers_importing_fred_are_found(self):
        # A canary against an over-narrow walk silently finding nothing.
        self.assertIn(os.path.join(FETCHERS_DIR, "credit_spread.py"),
                      _fetchers_importing_fred())

    def test_every_fred_fetcher_declares_a_module_level_series(self):
        missing = [rel for rel in _fetchers_importing_fred()
                   if _module_level_series_value(_parse(rel)) is None]
        self.assertEqual(missing, [],
                          f"{missing} import core.fred but declare no "
                          "module-level SERIES — every FRED-backed fetcher "
                          "must expose its series id(s) as SERIES so seeders "
                          "read it from the module instead of re-hard-coding "
                          "the id")

    def test_tools_read_mod_series_instead_of_rehardcoding_the_id(self):
        # Every id string a fetcher declares as SERIES must not reappear
        # (even as a substring of a longer literal) in any tools/*.py file —
        # a re-hard-coded id there is exactly the drift this SSOT guards
        # against (T2's rationale: a rotated or renamed series id could
        # silently diverge between the live fetcher and the seed tool that
        # rebuilds its history).
        declared = {}  # id -> owning fetcher
        for rel in _fetchers_importing_fred():
            for sid in _string_literals(_module_level_series_value(_parse(rel))):
                declared.setdefault(sid, rel)
        self.assertTrue(declared, "no FRED series ids were discovered to check")

        offenders = []
        for rel in _tools_py_files():
            literals = _all_string_literals(_parse(rel))
            for sid, owner in declared.items():
                if any(sid in lit for lit in literals):
                    offenders.append((rel, sid, owner))
        self.assertEqual(offenders, [],
                          "FRED series id re-hard-coded outside its owning "
                          f"fetcher (read mod.SERIES instead): {offenders}")


# --- User-Agent header (T3): one literal, read by every network fetcher ---

_UA_HOME = os.path.join("core", "useragent.py")
# Read from core.useragent itself rather than re-typed here — two homes for
# the same literal would let this lint go stale the moment either string is
# ever revised (round 26's own /simplify finding on this file).
_UA_LITERAL = useragent.HEADERS["User-Agent"]
_COMPAT_LITERAL = useragent.COMPAT_HEADERS["User-Agent"]
_COMPAT_OWNER = os.path.join(FETCHERS_DIR, "cnh_cny.py")


def _imports_core_useragent(tree):
    """True if ``tree`` has a module-level import binding the name
    ``useragent`` for core.useragent — ``from core import useragent`` (alone
    or alongside other core imports, e.g. ``from core import clock,
    useragent``) or ``import core.useragent``. Module-level only (not
    indented inside a function), the same restriction
    ``_module_level_import_names`` in lint_stub_style.py applies to its own
    stub-target scan."""
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "core":
            if any(alias.name == "useragent" for alias in node.names):
                return True
        elif isinstance(node, ast.Import):
            if any(alias.name == "core.useragent" for alias in node.names):
                return True
    return False


def _references_attr(tree, module, attr):
    """True if ``tree`` reads ``<module>.<attr>`` anywhere — a direct use,
    a call (``collect.counts_as_tremble(...)``), or unpacked via
    ``**useragent.HEADERS`` as core/adsb.py does. ``ast.walk`` already
    descends into a ``Call`` node's ``func``, so this one attribute-access
    scan covers both shapes without a separate ``ast.Call`` case."""
    return any(isinstance(node, ast.Attribute) and node.attr == attr
               and isinstance(node.value, ast.Name) and node.value.id == module
               for node in ast.walk(tree))


def _files_importing_useragent():
    """Every tracked .py file (outside core/useragent.py itself) with a
    module-level import of core.useragent — discovered structurally, the
    same shape ``_fetchers_importing_fred`` uses for T2's fred import above,
    generalized to the whole tree since UA callers span core/, fetchers/,
    and tools/ rather than one directory. Deliberately NOT a hand-maintained
    list: that went stale the moment a file was migrated without also
    updating it (round 26's own /simplify finding on this file)."""
    return [rel for rel in _all_py_files()
            if rel != _UA_HOME and _imports_core_useragent(_parse(rel))]


class TestUserAgentIsOneHome(unittest.TestCase):
    def test_useragent_importers_are_found(self):
        # A canary against an over-narrow walk silently finding nothing.
        self.assertIn(os.path.join(FETCHERS_DIR, "net_outages.py"),
                      _files_importing_useragent())

    def test_ua_literal_appears_only_in_core_useragent(self):
        # ast, not a substring grep: several of these fetcher docstrings
        # quote their own source URLs and headers in prose, and ast.walk
        # tokenizes the same way the interpreter does (T2's rationale above),
        # catching a re-typed literal even folded into a longer f-string.
        hits = []
        for rel in _all_py_files():
            if rel == _UA_HOME:
                continue
            literals = _all_string_literals(_parse(rel))
            if any(_UA_LITERAL in s or _COMPAT_LITERAL in s for s in literals):
                hits.append(rel)
        self.assertEqual(hits, [],
                          "the tremor User-Agent literal (standard or the "
                          "cnh_cny Mozilla COMPAT_HEADERS variant) must live "
                          f"only in {_UA_HOME} — found it re-typed in: {hits}")

    def test_every_useragent_importer_reads_headers_or_compat_headers(self):
        importers = _files_importing_useragent()
        self.assertTrue(importers, "no files importing core.useragent were discovered")
        dead = [rel for rel in importers
                if not (_references_attr(_parse(rel), "useragent", "HEADERS")
                        or _references_attr(_parse(rel), "useragent", "COMPAT_HEADERS"))]
        self.assertEqual(dead, [],
                          f"{dead} import core.useragent but never read HEADERS "
                          "or COMPAT_HEADERS from it — drop the unused import")

    def test_compat_headers_referenced_only_in_cnh_cny(self):
        # COMPAT_HEADERS exists solely because Yahoo's chart endpoint is
        # load-bearing on cnh_cny's browser-shaped UA — an ownership check
        # (T2's SERIES-ownership shape above) so a second caller reaching
        # for it would be caught rather than quietly normalizing the
        # exception into a habit.
        hits = [rel for rel in _all_py_files()
                if rel != _UA_HOME and _references_attr(_parse(rel), "useragent", "COMPAT_HEADERS")]
        self.assertEqual(hits, [_COMPAT_OWNER],
                          "core.useragent.COMPAT_HEADERS is cnh_cny's Yahoo-only "
                          f"exception, not a general header — found it read in: {hits}")


# --- tremble-count predicate (T4): one owner, replay/episodes consume it --

_TREMBLE_OWNER = "collect.py"


def _has_direction_compare(tree):
    """True if ``tree`` has a ``Compare`` node equating something with a
    module's ``ANOMALY_DIRECTION`` attribute — the shape of the
    tremble-count predicate, ``row["direction"] == mod.ANOMALY_DIRECTION``.
    Structural, not textual: render.py's chart-title f-string
    (``{mod.ANOMALY_DIRECTION}``) is an attribute access with no comparison
    around it, and collect.py's own module-docstring mention of the attr
    name is prose — neither builds a Compare node, so neither can
    false-flag this."""
    return any(isinstance(node, ast.Compare)
               and any(isinstance(n, ast.Attribute) and n.attr == "ANOMALY_DIRECTION"
                       for n in [node.left] + node.comparators)
               for node in ast.walk(tree))


def _files_with_direction_compare():
    return [rel for rel in _all_py_files() if _has_direction_compare(_parse(rel))]


class TestTrembleCountPredicateIsOneHome(unittest.TestCase):
    def test_the_owner_is_found(self):
        # A canary against an over-narrow walk silently finding nothing.
        self.assertIn(_TREMBLE_OWNER, _all_py_files())

    def test_direction_equality_compare_appears_only_in_collect(self):
        hits = _files_with_direction_compare()
        self.assertEqual(hits, [_TREMBLE_OWNER],
                          "the tremble-count predicate (comparing a row's "
                          "direction against mod.ANOMALY_DIRECTION) must "
                          f"live only in {_TREMBLE_OWNER}'s counts_as_tremble "
                          f"— found it re-typed in: {hits}")

    def test_replay_and_episodes_call_the_shared_helper(self):
        offenders = [rel for rel in (os.path.join(TOOLS_DIR, "replay.py"),
                                      os.path.join(TOOLS_DIR, "episodes.py"))
                     if not _references_attr(_parse(rel), "collect", "counts_as_tremble")]
        self.assertEqual(offenders, [],
                          f"{offenders} must call collect.counts_as_tremble(...) "
                          "rather than re-deriving the tremble-count predicate")


if __name__ == "__main__":
    unittest.main()
