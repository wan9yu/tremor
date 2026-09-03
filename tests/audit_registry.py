"""AUDIT: radar-metrics.md must equal what regenerating it produces right now.

D6 (see internal/2026-09-02-round26-zero-debt-plan.md) retired the hand-copied
``Reliab``/``Respons`` cells radar.md used to carry — four of those cells were
caught measured stale, and a hand-copied metric drifts the day after it is
fixed. The replacement, ``radar-metrics.md``, is GENERATED — its ``# radar
metrics`` table from ``python tools/episodes.py --markdown``, then its
``## Pending reviews`` section APPENDED from ``python tools/pending.py
--markdown`` (T9) — which only keeps its promise if the committed file is
never allowed to fall behind the record it describes. This is the freshness
check: regenerate BOTH sections, in that same order, in memory from the
committed CSVs and radar.md's Pending-block tags, and byte-compare the whole
thing against the committed ``radar-metrics.md``. Regenerating only the
episodes half here would fail this audit EVERY SINGLE DAY on an
un-regenerated pending section — a permanent alarm trains alarm-blindness —
so both generators run, in daily.yml's derive-step order.

AUDIT, not gate: this reads ``data/`` (the committed record), which the
pre-collect gate (``test_*.py``, ``python -m unittest discover tests``) may
never do — a stale registry cell must never be able to abort a collection day
(see tests/test_side_channel.py's ``TestGateNeverReadsTheCommittedRecord``,
and section 3 of the zero-debt plan). It runs post-commit via
``python -m unittest discover tests -p "audit_*.py"``: a failure here is an
alarm issue, never a lost day. daily.yml's derive step already regenerates
and commits ``radar-metrics.md`` every run, so in the ordinary case this never
fires; it exists for the rarer path — a seed, backfill, or record correction
that lands without regenerating the file in the same commit.

T13 (P3-6) extends this module with three more record invariants, each its own
class below: a QUANTUM-floor invariant (the three quantized lines' raw Qn
never sits strictly between 0 and QUANTUM), a no-overdue-pending check (the
data-aware complement to ``tests/lint_pending.py``'s syntax-only grammar
check), and a retracted-phrase scan (a claim this record RETRACTED must never
be re-asserted on a live served surface). All three read ``data/`` and/or
import ``collect``/``pending``, which is exactly what makes them AUDIT-tier
and not gate-tier.
"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import collect
import episodes
import pending
import replay
import support
from core import normalize


class TestRadarMetricsIsFresh(unittest.TestCase):
    PATH = os.path.join(ROOT, "radar-metrics.md")

    def test_committed_file_matches_a_fresh_regeneration(self):
        self.assertTrue(os.path.exists(self.PATH),
                         "radar-metrics.md is missing at the repo root")
        committed = support.read_text(self.PATH)
        out = [r for r in (episodes.report_line(mod) for mod in collect.LINES) if r]
        fresh = episodes.render_markdown(out)
        fresh += pending.render_markdown(pending.report())
        self.assertEqual(
            committed, fresh,
            "radar-metrics.md is stale — regenerate with `python tools/episodes.py "
            "--markdown > radar-metrics.md && python tools/pending.py --markdown "
            ">> radar-metrics.md` and commit the result")


def _replay_qn(mod):
    """Recompute every scored row's raw Qn for ``mod``'s committed CSV --
    reusing ``tools/replay.py``'s own row replay (``replay.replay_line``,
    which drives ``collect.score_row`` in row order exactly as the daily
    collector and ``replay.py --check`` do) instead of a second hand-rolled
    loop -- with ``normalize._qn`` wrapped to record the raw (pre-floor)
    scale every call produces. Returns ``[(date, qn), ...]`` for rows that
    ended up ``STATUS_SCORING``.

    ``replay_line`` is a plain function, not a generator: every ``_qn`` call
    it triggers happens before it returns, so ``captured`` is complete, in
    row order, by the time the loop below starts. None of the three
    quantized lines uses ``weekly_cycle`` decycling (see
    ``collect.scoring_attrs``), so ``_qn`` is called exactly once per row
    that ends ``STATUS_SCORING`` and never for any other status --
    filtering the replayed rows down to ``STATUS_SCORING`` (in that same row
    order) and pairing them positionally with ``captured`` reconstructs the
    same per-row pairing the original hand loop built incrementally; the
    length-equality assert is that same "one _qn call per scored row, no
    more, no less" sanity check, restated for a non-generator replay.

    Same technique an earlier one-off measurement script
    (``qn_floor_measure.py``) used to characterize the record once. Making
    it a standing audit turns that one-time measurement into a check that
    re-runs every day.
    """
    captured = []
    real_qn = normalize._qn

    def recording_qn(values):
        q = real_qn(values)
        captured.append(q)
        return q

    normalize._qn = recording_qn
    try:
        scored = []
        for date, _, replayed in replay.replay_line(mod):
            if replayed["status"] != normalize.STATUS_SCORING:
                continue
            scored.append(date)
    finally:
        normalize._qn = real_qn

    assert len(captured) == len(scored), (
        mod.LINE, "expected exactly one _qn call per scored row",
        len(captured), len(scored))
    return list(zip(scored, captured))


class TestQuantumFloorNeverStraddled(unittest.TestCase):
    """Every quantized line's raw Qn is either exactly 0 (the floor binds) or
    already at/above its QUANTUM — never strictly between the two.

    Three lines declare ``QUANTUM`` (the measurement resolution
    ``core.normalize._scale_z`` floors the robust scale to, so a calm
    small-integer stretch cannot leave the line unable to judge the spike
    that follows it — see that function's docstring): ``net_outages``
    (QUANTUM=1 country), ``sofr_iorb_spread`` (QUANTUM=1 basis point),
    ``space_weather`` (QUANTUM=1/3, Kp's own reporting granularity). The
    floor is supposed to catch ONLY the case where Qn has collapsed all the
    way to exactly 0.0 (a quarter of the baseline window's pairs tied); if a
    row's raw Qn were instead some small positive value strictly below
    QUANTUM, flooring it would DISCARD real, measured dispersion the record
    actually has rather than standing in for dispersion genuinely absent —
    the failure this asserts never happens.

    ``_replay_qn`` above replays every committed row of each quantized line
    through the real scorer, WINDOW=90 most-recent / MIN_POINTS gating
    exactly as the daily collector applies them (nothing here reimplements
    that gating — it is exercised by calling ``collect.score_row`` itself).

    Measured on the current record (2026-09-04): net_outages' Qn is exactly
    0.0 on 34 rows (2022-02-05..2022-03-10 — the floor binding, its earliest
    stretch) and >= 2.045 on every other scored row; sofr_iorb_spread never
    collapses to 0 and its smallest Qn is 1.610 (>= QUANTUM=1);
    space_weather never collapses to 0 either and its smallest Qn is 0.5378
    (>= QUANTUM=1/3=0.3333...). No row on any of the three lines sits
    strictly between 0 and its QUANTUM, so this passes today; a future row
    that DID would mean the floor has started masking real dispersion —
    worth an alarm, never a silent pass.
    """

    def test_no_scored_row_has_a_raw_qn_strictly_between_zero_and_quantum(self):
        offenders = []
        for mod in collect.LINES:
            quantum = getattr(mod, "QUANTUM", None)
            if not quantum:
                continue
            quantum = float(quantum)
            for date, qn in _replay_qn(mod):
                if 0 < qn < quantum:
                    offenders.append(
                        f"{mod.LINE} {date}: raw Qn={qn!r} sits strictly between "
                        f"0 and QUANTUM={quantum!r} — the floor is masking real "
                        f"dispersion instead of standing in for none")
        self.assertEqual(offenders, [], "\n".join(offenders))


class TestNoPendingItemIsOverdue(unittest.TestCase):
    """Post-commit, data-aware complement to ``tests/lint_pending.py``.

    lint_pending is a push-CI LINT: it parses every ``[opened R.. · owner R..
    · fires: ...]`` tag in radar.md's Pending block and checks the GRAMMAR — a
    tag fits the six predicate forms, a data-dependent predicate names a real
    line, a round/date literal parses — never the DATA, so it can run
    pre-commit with no import of ``collect``/``requests`` (see its own
    module docstring). Three of the six predicate forms (``scored``,
    ``distinct_scored``, ``rows_since``) can only be EVALUATED against
    ``data/`` — has the count actually crossed the stated threshold — which
    lint_pending structurally cannot check. This is that check:
    ``tools/pending.report()`` parses every open tagged item AND evaluates it
    (the two clock-driven forms against ``core.clock``/radar.md's own round
    index, the three data-dependent ones against the committed CSVs via
    ``seedlib.read_line``/``collect.is_scored`` — exactly what ``pending.py
    --check`` runs) and this asserts none of them has FIRED while the item is
    still open — an OVERDUE item, a promise that came due with nobody having
    closed or re-opened its bullet. This reuses ``pending.report()`` rather
    than re-evaluating anything itself, per the module's own stated rule that
    it is the one place pending-item evaluation lives.

    On the current record (2026-09-04): cnh_cny's maturity refresh sits at
    distinct_scored 54/60 (queued R13, still short); net_outages'
    reconciliation tripwire is ``manual`` (never auto-fires); the
    level-layer -> flights item fires on ``date >= 2026-11-01``, still ahead.
    None is overdue, so this passes today — a future item crossing its
    threshold with nobody having closed the bullet is exactly what this
    exists to catch.
    """

    def test_no_open_pending_item_has_fired(self):
        items = pending.report()
        overdue = [item for item in items if item["fired"]]
        self.assertEqual(
            overdue, [],
            "OVERDUE pending item(s) in radar.md's Pending block: " + "; ".join(
                f"{item['label']} (fires: {item['predicate_text']})"
                for item in overdue))


# A retraction row's note starts with one or more single-quoted phrases,
# comma-separated, immediately after "RETRACTED:" (see the class docstring
# below) — e.g. ``RETRACTED: 'phrase one', 'phrase two' — citation...``.
# ``_LEADING_QUOTES_RE`` captures that whole leading run; ``_QUOTED_RE`` then
# pulls every individual phrase out of it. The comma between phrases is
# REQUIRED in both regexes (``,`` not ``,?``) — an author who forgets it
# between two quoted phrases must not have the second one silently absorbed
# as an extra retracted phrase (or, worse, a later quoted citation title
# mistaken for one); requiring the comma means a malformed row instead stops
# the leading-run match short, so a phrase-count check downstream would
# catch it rather than mis-scoping the phrase list.
_LEADING_QUOTES_RE = re.compile(r"^RETRACTED:\s*('[^']+'(?:\s*,\s*'[^']+')*)")
_QUOTED_RE = re.compile(r"'([^']+)'")

# The live served surfaces a retracted claim must never be re-asserted on.
# radar-log.md is deliberately EXCLUDED — it is the round-by-round history,
# and quoting a retracted phrase IN ORDER TO retract it (as every citation in
# TestNoRetractedClaimIsLive's docstring does) is the log doing its job, not
# re-asserting the claim.
_LIVE_SURFACES = ("radar.md", "docs/index.html", "README.md", "radar-metrics.md")


class TestNoRetractedClaimIsLive(unittest.TestCase):
    """A claim this record RETRACTED must never be re-asserted anywhere current.

    CONVENTION (established by this test — annotations.csv carried no
    machine-readable retraction marker before it; every prior one was free
    text, e.g. radar-log.md:561's "> **RETRACTED IN ROUND 10.**" and
    radar-log.md:1656-1671's Round 23.2 write-up). A retraction is now a
    ``data/annotations.csv`` row whose ``verdict`` column reads
    ``retraction`` and whose ``note`` column STARTS with
    ``RETRACTED: '<phrase>'[, '<phrase>'...]`` — one or more comma-separated,
    single-quoted phrases, each the exact wording that was found wrong
    (single-quoted per this repo's existing convention for an inline quote
    inside a double-quoted CSV field — see the 2026-08-04 correction row,
    which already quotes "cannot structurally exceed ~2 of 4" the same way).
    More than one phrase belongs on the same row when a single retracted
    CLAIM was rendered in more than one exact wording across the live
    surfaces (an EN phrasing, a separate ZH phrasing, a paraphrase in a
    fetcher docstring) — one retraction EVENT, several exact strings the scan
    must independently catch. The quoted phrase(s) are followed by an em
    dash and a citation of what retracted the claim and where.
    ``annotations.csv`` is append-only (a published row is never edited), so
    a retraction is recorded going forward exactly like any other verdict —
    it never rewrites the row that made the original claim; it must also stay
    mirrored byte-for-byte to ``docs/data/annotations.csv``, like every other
    row (daily.yml's push step copies ``data/`` onto ``docs/data/`` verbatim —
    ``cmp``'d by hand whenever this convention's rows are seeded or corrected).

    A seeded phrase must be the wording an actual LIVE surface carried, not
    the log's own compressed paraphrase of it — a phrase that was never on a
    live surface passes trivially and protects nothing (the mistake round-26
    review caught in an earlier draft of this test's phrase 2, below: the
    log's paraphrase 'read 0.47% through a Gulf air war and never moved' was
    seeded and passed, while the dashboard's own wording of the same claim
    stayed live and unchecked).

    Seeded with the claims this record is known to have retracted, verified
    against radar-log.md:

      1. 'cannot structurally exceed ~2 of 4' — Round 9's resonance-ceiling
         headline, marked "> **RETRACTED IN ROUND 10.**" at radar-log.md:561
         ("The ceiling claim above is false...") and reaffirmed at
         radar-log.md:641 ("The resonance ceiling claim of round 9 is
         retracted"); Round 10's own retraction was itself corrected at
         radar-log.md:1100-1108 (Round 16, the co-scoring share — ~778/796
         days, not "33").
      2. 'read 0.47% and never moved', 'sat at 0.47% and did not move',
         'tenfold growth in the sampling frame', and (ZH, the fuller sentence
         rather than its bare four-character idiom below) '这根线停在 0.47%
         纹丝不动' — Round 7.1's claim (radar-log.md:290) that
         gnss_interference's global ratio never registered the July Gulf
         escalation, and round 7's estimate that its sampling frame had grown
         roughly tenfold, both retracted at radar-log.md:502-511 (**Round 9**,
         2026-08-03 — not Round 8, which is 2026-07-23 and unrelated; the gnss
         seed). Re-scored against four years of real history the July 2026
         window peaks at z=+2.87 (a separate fact from, not the same as, its
         49 alarm-direction trembles record-wide across 1,452 scored
         observations) — the line was under-powered, not motionless; and by
         yearly median the sampling frame grew ~1.23x, not tenfold (9 broken
         partial files out of 1,423). The bare ZH idiom 纹丝不动 ("motionless")
         is NOT itself seeded — tga_days_cash's own (unrelated, still-valid)
         explainer legitimately uses the same four characters in an unrelated
         sentence, and a bare-idiom match would false-positive on it; the
         fuller sentence is specific to the retracted gnss claim. Both
         docs/index.html:277-278 (EN+ZH) and fetchers/gnss.py's docstring
         asserted this retracted wording as fact until this correction —
         reworded here (gnss.py gains a "CORRECTED round 9" note in the same
         style as fetchers/net_outages.py's own correction note), citing this
         round.
      3. 'removes the whole latency-injection class' — Round 23.1's
         description of the net_outages settle fix (radar-log.md:1615;
         fetchers/net_outages.py's own "CORRECTED 2026-08-26" note),
         corrected at radar-log.md:1656-1671 (Round 23.2) once the
         reconciliation tripwire's first run found a synchronized-onset
         cluster relocates to its settled window and would still alarm
         there — settle stabilizes and relocates the count, it does not
         eliminate that artifact class. radar.md's own Pending-block bullet
         for this item (`net_outages settle — reconciliation tripwire`)
         still carried the retracted phrasing verbatim until this same
         commit fixed it — the first thing this test caught.
    """

    def _retracted_phrases(self):
        rows = collect._read_rows(os.path.join(collect.DATA, "annotations.csv"))
        phrases = []
        for row in rows:
            if row.get("verdict") != "retraction":
                continue
            m = _LEADING_QUOTES_RE.match(row.get("note") or "")
            self.assertIsNotNone(
                m, f"annotations.csv {row['date']} {row['line']}: a 'retraction' "
                   f"row's note must start with RETRACTED: '<phrase>'[, ...] — got "
                   f"{(row.get('note') or '')[:80]!r}")
            phrases.extend(_QUOTED_RE.findall(m.group(1)))
        self.assertTrue(
            phrases, "no 'retraction' rows found in annotations.csv — the "
                      "RETRACTED: convention has nothing seeded")
        return phrases

    def test_no_retracted_phrase_appears_in_a_live_surface(self):
        phrases = self._retracted_phrases()
        offenders = []
        for relpath in _LIVE_SURFACES:
            text = support.read_text(os.path.join(ROOT, relpath))
            for phrase in phrases:
                if phrase in text:
                    offenders.append(
                        f"{relpath}: still asserts retracted phrase {phrase!r}")
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
