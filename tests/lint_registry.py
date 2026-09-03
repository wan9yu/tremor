"""Binds three restatements of the line registry to each other so none can
silently drift from what the code (or the append-only log) actually says:

  1. docs/index.html's ``const LINES`` (the dashboard's own per-line
     metadata) must agree with ``collect.LINES`` as SETS — same ids, and per
     id the same alarm direction and tier. Ordering is deliberately NOT
     checked: collect.py groups its list by domain-diversity comment blocks
     (see its own module docstring), docs/index.html groups by a different
     reading order, and neither ordering is a contract the other side must
     match.
  2. radar.md's two tier tables (``## Tier 1 — primary`` / ``## Tier 2 —
     collected``) must each name every ``collect.LINES`` line exactly once —
     a line missing from both tables, or named twice, is caught.
  3. radar.md's ``## Calibration log — round index`` must list exactly the
     rounds ``radar-log*.md`` documents in full, in the same order. Globbed
     rather than hardcoded to ``radar-log.md`` so a future log-roll (see
     T16) is swept in without a change here.

``collect.LINES`` itself is never imported, nor is ``fetchers`` or
``tools/pending`` (which itself imports ``collect``): every fetcher module
imports ``requests`` at module scope, which is not installed in ci.yml's
lint job (that job installs nothing at all) and would ImportError there.
Instead collect.py's ``LINES = [alias, alias, ...]`` list is read back
ast-side, each alias is resolved to its fetcher module FILE via collect.py's
own ``from fetchers import (...)`` (or ``import fetchers.mod as alias``)
statement, and each resolved ``fetchers/<mod>.py`` is itself ast-parsed for
its module-level ``LINE`` (the canonical id — NOT the alias: e.g. alias
``gnss`` resolves to LINE ``gnss_interference``, ``ports`` to
``port_throughput``, ``sofr_iorb`` to ``sofr_iorb_spread``),
``ANOMALY_DIRECTION``, and ``TIER`` (default 1 when absent — the same
default collect.py's fetcher-contract docstring documents and
docs/index.html's own ``L.tier||1`` reads use). Source-vs-source throughout;
``data/`` is never read.

LINT, not gate: a source-and-docs scan, not a property of the running
instrument, so it runs on push via ``unittest discover tests -p
"lint_*.py"`` (ci.yml's lint job) and is deliberately NOT part of daily.yml's
pre-collect gate — a registry drift must never abort a collection day.
"""
import ast
import glob
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import support

COLLECT_PATH = os.path.join(ROOT, "collect.py")
DOCS_INDEX = os.path.join(ROOT, "docs", "index.html")
RADAR_MD = os.path.join(ROOT, "radar.md")
FETCHERS_DIR = os.path.join(ROOT, "fetchers")

_TIER1_HEADING = "## Tier 1 — primary"
_TIER2_HEADING = "## Tier 2 — collected"


def _parse(path):
    return ast.parse(support.read_text(path), filename=path)


def _fetcher_alias_map(tree):
    """Map every name collect.py's ``LINES`` list can reference to the
    fetchers/ module FILE it is bound to, read from collect.py's own import
    statements — ``from fetchers import (a, b as c, ...)`` and
    ``import fetchers.mod as alias`` alike."""
    mapping = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "fetchers":
            for alias in node.names:
                mapping[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fetchers" or alias.name.startswith("fetchers."):
                    if "." in alias.name:
                        modname = alias.name.split(".", 1)[1]
                        mapping[alias.asname or modname] = modname
    return mapping


def _collect_lines_aliases(tree):
    """The ordered list of bound names in collect.py's module-level
    ``LINES = [...]`` assignment, or None if no such assignment exists."""
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "LINES"):
            return [elt.id for elt in node.value.elts if isinstance(elt, ast.Name)]
    return None


def _module_level_const(tree, name):
    """The value of a module-level ``name = <constant>`` assignment, or None
    if the module declares no such name."""
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name
                and isinstance(node.value, ast.Constant)):
            return node.value.value
    return None


def _collect_registry():
    """{LINE id: {"alarm": ANOMALY_DIRECTION, "tier": TIER}}, built without
    ever importing collect.py or a fetcher module (see the module
    docstring)."""
    collect_tree = _parse(COLLECT_PATH)
    alias_map = _fetcher_alias_map(collect_tree)
    aliases = _collect_lines_aliases(collect_tree)
    assert aliases, "collect.py: no module-level `LINES = [...]` assignment found"
    registry = {}
    for alias in aliases:
        modname = alias_map.get(alias)
        assert modname, (f"collect.LINES references {alias!r}, which does not resolve "
                          "to a `from fetchers import ...` (or `import fetchers.mod as "
                          "...`) binding in collect.py")
        tree = _parse(os.path.join(FETCHERS_DIR, f"{modname}.py"))
        line_id = _module_level_const(tree, "LINE")
        assert line_id, f"fetchers/{modname}.py declares no module-level LINE"
        tier = _module_level_const(tree, "TIER")
        registry[line_id] = {
            "alarm": _module_level_const(tree, "ANOMALY_DIRECTION"),
            "tier": tier if tier is not None else 1,
        }
    return registry, aliases


# --- docs/index.html's `const LINES` (JS side) -----------------------------

# One `const LINES` entry's opening line — id/color/alarm always appear
# together on it, `tier` only when the line is not the (default) tier 1, the
# same default docs/index.html's own `L.tier||1` reads use throughout.
_JS_LINE_ENTRY = re.compile(
    r'^\s*\{\s*id:"(?P<id>[^"]+)",\s*color:"[^"]+",\s*alarm:"(?P<alarm>up|down)",'
    r'(?:\s*tier:(?P<tier>\d+),)?\s*$', re.M)


def _docs_registry():
    """{id: {"alarm":..., "tier":...}} parsed out of docs/index.html's
    `const LINES = [...]` block, plus the ordered list of raw regex matches
    (so a caller can also check for duplicate ids)."""
    html = support.read_text(DOCS_INDEX)
    m = re.search(r'const LINES = \[(.*?)\n\];', html, re.S)
    assert m, "docs/index.html: could not locate `const LINES = [ ... ];`"
    entries = list(_JS_LINE_ENTRY.finditer(m.group(1)))
    registry = {}
    for e in entries:
        registry[e.group("id")] = {
            "alarm": e.group("alarm"),
            "tier": int(e.group("tier")) if e.group("tier") else 1,
        }
    return registry, entries


class TestDashboardLinesMatchCollectLines(unittest.TestCase):
    def test_docs_lines_block_parses_and_has_no_duplicate_id(self):
        registry, entries = _docs_registry()
        self.assertTrue(registry, "no `const LINES` entries parsed out of docs/index.html")
        self.assertEqual(len(entries), len(registry),
                          "docs/index.html's `const LINES` declares a duplicate id")

    def test_collect_lines_resolves_with_no_duplicate_line_id(self):
        registry, aliases = _collect_registry()
        self.assertTrue(registry, "no lines resolved from collect.LINES")
        self.assertEqual(len(aliases), len(registry),
                          "two collect.LINES aliases resolve to the same fetcher LINE id")

    def test_docs_and_collect_agree_on_the_set_of_ids(self):
        docs_registry, _ = _docs_registry()
        collect_registry, _ = _collect_registry()
        docs_ids, collect_ids = set(docs_registry), set(collect_registry)
        self.assertEqual(docs_ids, collect_ids,
                          "docs/index.html's `const LINES` and collect.LINES disagree on "
                          f"the SET of ids — only in docs: {sorted(docs_ids - collect_ids)}; "
                          f"only in collect.LINES: {sorted(collect_ids - docs_ids)}")

    def test_docs_and_collect_agree_on_alarm_direction_and_tier(self):
        docs_registry, _ = _docs_registry()
        collect_registry, _ = _collect_registry()
        mismatches = []
        for line_id in sorted(set(docs_registry) & set(collect_registry)):
            d, c = docs_registry[line_id], collect_registry[line_id]
            if d["alarm"] != c["alarm"] or d["tier"] != c["tier"]:
                mismatches.append({"id": line_id, "docs": d, "collect": c})
        self.assertEqual(mismatches, [],
                          "docs/index.html vs collect.LINES: alarm direction and/or tier "
                          f"disagree: {mismatches}")


# --- radar.md's tier tables --------------------------------------------------

def _section(text, heading):
    """The text strictly between one `## `-level heading and the next — a
    `### ` subheading does not end it, only another `## ` one does."""
    idx = text.find(heading)
    assert idx != -1, f"radar.md: heading {heading!r} not found"
    rest = text[idx + len(heading):]
    nxt = re.search(r'^## ', rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _tier_table_row_ids(section_text):
    """The first-column id of every real table row in one radar.md tier
    section — the header row and the `|---|` separator are skipped, and a
    context line's leading em-dash marker (`— gdelt`) is stripped so the
    result compares directly against a fetcher's own `LINE` id."""
    ids = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = line.split("|")
        if len(cells) < 2:
            continue
        cell = cells[1].strip()
        if not cell or cell == "indicator" or set(cell) <= set("-: "):
            continue  # header row or the markdown table separator
        cell = re.sub(r'^—\s*', '', cell)  # a context line's "— " prefix
        ids.append(cell.strip("*`").strip())
    return ids


class TestRadarMdNamesEveryLineOnceInItsTierSection(unittest.TestCase):
    def test_every_collect_line_appears_exactly_once_across_the_tier_tables(self):
        registry, _ = _collect_registry()
        radar = support.read_text(RADAR_MD)
        tier1_ids = _tier_table_row_ids(_section(radar, _TIER1_HEADING))
        tier2_ids = _tier_table_row_ids(_section(radar, _TIER2_HEADING))
        all_ids = tier1_ids + tier2_ids
        self.assertTrue(all_ids, "no tier-table rows parsed out of radar.md")

        counts = {}
        for i in all_ids:
            counts[i] = counts.get(i, 0) + 1
        duplicated = sorted(i for i, n in counts.items() if n > 1)
        self.assertEqual(duplicated, [],
                          "line(s) named more than once across radar.md's "
                          f"Tier 1/Tier 2 tables: {duplicated}")

        missing = sorted(set(registry) - set(all_ids))
        self.assertEqual(missing, [],
                          f"collect.LINES line(s) missing from radar.md's tier tables: {missing}")

        extra = sorted(set(all_ids) - set(registry))
        self.assertEqual(extra, [],
                          "radar.md tier table row(s) naming a line collect.LINES does "
                          f"not declare: {extra}")


# --- round-index parity across radar-log*.md ---------------------------------

# radar.md's "Calibration log — round index" is a `- **Round N** — date ·
# summary` bullet per round; radar-log*.md carries the full write-up under a
# `### Round N — date (title)` header. Both round numbers are plain digits,
# optionally with one `.N` sub-round suffix (e.g. `23.1`).
_ROUND_INDEX_ENTRY = re.compile(r'^-\s+\*\*Round\s+([0-9]+(?:\.[0-9]+)?)\*\*', re.M)
_ROUND_LOG_HEADER = re.compile(r'^###\s+Round\s+([0-9]+(?:\.[0-9]+)?)\b', re.M)


class TestRoundIndexParityAcrossRadarLog(unittest.TestCase):
    """Globbed against ``radar-log*.md`` (today only radar-log.md exists) so
    a future log-roll adds a file this lint sweeps in automatically."""

    def test_round_index_matches_the_round_log_headers_in_order(self):
        radar = support.read_text(RADAR_MD)
        index_rounds = _ROUND_INDEX_ENTRY.findall(radar)
        self.assertTrue(index_rounds,
                         "no round-index entries found in radar.md's Calibration log")

        log_paths = sorted(glob.glob(os.path.join(ROOT, "radar-log*.md")))
        self.assertTrue(log_paths, "no radar-log*.md file(s) found")
        log_rounds = []
        for path in log_paths:
            log_rounds += _ROUND_LOG_HEADER.findall(support.read_text(path))

        self.assertEqual(index_rounds, log_rounds,
                          "radar.md's round index and radar-log*.md's `### Round` "
                          f"headers have drifted apart — index: {index_rounds}; "
                          f"log: {log_rounds}")


if __name__ == "__main__":
    unittest.main()
