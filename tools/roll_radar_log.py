"""Rolls radar-log.md's early rounds out into an archive file, once the live
log approaches its self-set roll threshold (2,000 lines, radar.md:201 —
1,835 lines at T16, ~107 lines/round measured, crossing at ~R27).

WHAT GETS SPLIT. radar-log.md is a short preamble (~6 lines) followed by one
``### Round N — date (title)`` section per round, append-only, in file
order. The split boundary is the ``### Round SPLIT_ROUND`` header
(``SPLIT_ROUND`` below, 20 today): every round before it (1-19 today) moves
into the archive file; every round from it onward stays in radar-log.md.
The boundary is found by PARSING the ``### Round`` headers — the same
pattern tests/lint_registry.py's round-index-parity lint uses to bind
radar.md's round index to radar-log*.md — never by a hardcoded line number,
so a later run (say once R27 has pushed these same headers further down the
file) still finds the right one.

BYTE-IDENTITY GUARANTEE — AND WHY IT IS NOT A TAUTOLOGY. An earlier version
of this tool asserted ``archive_body + remaining_body == round_content``
where both sides were slices of the SAME string computed moments apart.
Python slicing guarantees that equality for any input whatsoever — it can
only fail on an offset-arithmetic bug, never on content actually lost or
corrupted while building the files this tool WRITES. (Proof: corrupt the
input text however you like — drop a line inside a round's body — and that
assertion still passes, because it never compares against anything held
independently of the very computation it is checking.)

The guarantee now instead compares the WRITE PLAN against an independently
held original:

  1. ``LOG_PATH`` is read once into ``original`` and never touched again.
  2. ``build_archive_file``/``build_remaining_file`` construct the EXACT
     strings that would be written to radar-log-1.md and radar-log.md,
     including each file's own added pointer prose (see below).
  3. ``verify_write_plan`` reconstructs ``original`` OUT OF those two
     write-plan strings — stripping only the tool's own known-added prefixes
     (never guessed, never re-derived from the same slicing being checked)
     — and asserts the reconstruction equals ``original`` exactly.
  4. ``verify_round_coverage`` separately re-parses ``### Round`` headers
     straight out of the two write-plan strings (not out of any
     already-partitioned list this tool computed earlier) and asserts they
     are a clean, order-preserving partition of ``original``'s own headers
     — AND that the partition actually lands at ``split_round`` (every
     archived round's floor below it, every remaining round's floor at or
     above it), a property ``verify_write_plan`` does not check: its
     reconstruction succeeds for any cut point, so an off-by-one in
     ``compute_split``'s boundary comparison needs this separate guard.

Both raise ``AssertionError`` — refusing to write anything — the moment a
write-plan string diverges from ``original``: a dropped or duplicated line
anywhere in either constructed file, a pointer that leaked into round
content, or a body swapped between the two files all make one of these
diverge. tests/test_roll_radar_log.py's ``TestByteIdentityCatchesRealCorruption``
proves this by handing ``verify_write_plan``/``verify_round_coverage`` a
deliberately corrupted write-plan string and checking it is refused.

The guarantee covers round content only. Each output file additionally
carries a small pointer paragraph that is genuinely NEW prose, never
preserved bytes and deliberately outside what ``original`` can be
reconstructed from without first stripping it back out: the archive file
gets a one-paragraph preamble of its own (title + a link back to radar.md
and radar-log.md), and radar-log.md's EXISTING preamble is kept byte-for-byte
and gets one added sentence pointing at the archive.

    python tools/roll_radar_log.py --check   # compute + verify the split; write nothing
    python tools/roll_radar_log.py           # write radar-log-1.md, rewrite radar-log.md
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(ROOT, "radar-log.md")
ARCHIVE_PATH = os.path.join(ROOT, "radar-log-1.md")

# Mirrors tests/lint_registry.py's `_ROUND_LOG_HEADER` exactly, so this
# tool's idea of "a round" never drifts from what that lint's
# round-index-parity check counts against radar.md.
ROUND_HEADER = re.compile(r'^###\s+Round\s+([0-9]+(?:\.[0-9]+)?)\b', re.M)

SPLIT_ROUND = 20  # rounds with an integer part < this archive; >= this stay


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class SplitResult:
    """The computed split, in memory only — nothing here has touched disk.

    ``preamble`` is radar-log.md's text before its first ``### Round``
    header, unchanged. ``archive_body``/``remaining_body`` are the round
    content each output file's round section is built from. This grouping
    is NOT itself the byte-identity guarantee (see the module docstring) —
    it is only the input ``build_archive_file``/``build_remaining_file`` and
    the real, write-plan-level checks below work from.
    """

    def __init__(self, preamble, rounds, archive_rounds, remaining_rounds,
                 archive_body, remaining_body):
        self.preamble = preamble
        self.rounds = rounds
        self.archive_rounds = archive_rounds
        self.remaining_rounds = remaining_rounds
        self.archive_body = archive_body
        self.remaining_body = remaining_body


def compute_split(text, split_round=SPLIT_ROUND):
    """Parse ``text`` (radar-log.md's content) and group its rounds into an
    archive side and a remaining side. A pure function — no I/O, no
    assertion about reproducing ``text`` (that would only re-check Python's
    own slicing semantics, true for any input — see the module docstring);
    the real guarantee lives in ``verify_write_plan``/``verify_round_coverage``
    below, which check the ACTUAL write-plan strings against a separately
    held original.
    """
    matches = list(ROUND_HEADER.finditer(text))
    if not matches:
        raise ValueError("no '### Round' headers found — nothing to split")

    offsets = [m.start() for m in matches]
    rounds = [m.group(1) for m in matches]
    preamble = text[:offsets[0]]

    split_i = next((i for i, r in enumerate(rounds)
                     if int(r.split(".")[0]) >= split_round), len(rounds))
    if split_i == 0:
        raise ValueError(f"round {split_round} is the first round in the file "
                          "— nothing precedes it to archive")
    if split_i == len(rounds):
        raise ValueError(f"no round >= {split_round} found — nothing would "
                          "remain in radar-log.md")

    # archive_body/remaining_body are two ADJACENT ranges of the same string
    # (the round headers/bodies are contiguous and in order), so this is a
    # single split point, not a per-round join: text[offsets[0]:offsets[split_i]]
    # and text[offsets[split_i]:] together cover exactly the same bytes a
    # per-round `"".join(spans)` would, with no intermediate list.
    archive_rounds, remaining_rounds = rounds[:split_i], rounds[split_i:]
    archive_body = text[offsets[0]:offsets[split_i]]
    remaining_body = text[offsets[split_i]:]

    return SplitResult(preamble, rounds, archive_rounds, remaining_rounds,
                        archive_body, remaining_body)


def build_archive_file(result):
    """The exact text that would be WRITTEN to radar-log-1.md: a new
    one-paragraph pointer preamble (never preserved bytes — new prose)
    followed by ``result.archive_body``.

    Returns ``(full_text, added_prefix)`` — ``added_prefix`` is exactly the
    preamble this function itself prepended, handed back so
    ``verify_write_plan`` can strip precisely that (and nothing guessed)
    back off ``full_text`` when reconstructing the original.
    """
    first, last = result.archive_rounds[0], result.archive_rounds[-1]
    next_first = result.remaining_rounds[0]
    added_prefix = (
        f"# tremor radar — calibration log (archive: rounds {first}–{last})\n\n"
        f"Rounds {first}–{last} of the append-only round-by-round record behind "
        "the registry in **[radar.md](radar.md)**. Split out by "
        "`tools/roll_radar_log.py` once the live log crossed its self-set roll "
        f"threshold. Current rounds ({next_first}+) are in "
        "**[radar-log.md](radar-log.md)**.\n\n"
    )
    return added_prefix + result.archive_body, added_prefix


def build_remaining_file(result):
    """The exact text that would be WRITTEN to radar-log.md: ``result.preamble``
    byte-identical to what it always was, then one added pointer sentence
    (new prose), then ``result.remaining_body``.

    Returns ``(full_text, preamble, pointer)`` so ``verify_write_plan`` can
    strip exactly those two known pieces back off ``full_text`` — never a
    guess — when reconstructing the original.
    """
    a_first, a_last = result.archive_rounds[0], result.archive_rounds[-1]
    pointer = (
        f"Rounds {a_first}–{a_last} are archived in "
        "**[radar-log-1.md](radar-log-1.md)**.\n\n"
    )
    return result.preamble + pointer + result.remaining_body, result.preamble, pointer


def verify_write_plan(original, archive_full, archive_added,
                       live_full, live_preamble, live_pointer):
    """THE byte-identity guarantee.

    Reconstructs ``original`` — read from disk once, held completely
    separately from ``archive_full``/``live_full`` — out of the exact
    strings this tool would WRITE to each file, stripping only the tool's
    own known-added prefixes (``archive_added``, ``live_pointer`` — exact
    strings ``build_archive_file``/``build_remaining_file`` themselves
    produced, never guessed or re-derived from the slicing that built
    ``archive_full``/``live_full`` in the first place).

    This is deliberately NOT "do two adjacent slices of one string
    recombine" (true for any input, by Python slicing semantics, and hence
    no guarantee at all — see the module docstring). It instead checks the
    ACTUAL write-plan output against an independently-held original: a
    dropped or duplicated line anywhere in either constructed file, a
    pointer that leaked into round content, or a body swapped between the
    two files all make the reconstruction diverge from ``original``, and
    this raises rather than let the tool proceed to write it.
    """
    if not archive_full.startswith(archive_added):
        raise AssertionError(
            "byte-identity check failed: radar-log-1.md's write-plan text "
            "does not start with the preamble build_archive_file added to "
            "it — refusing to write")
    archive_body_out = archive_full[len(archive_added):]

    if not live_full.startswith(live_preamble):
        raise AssertionError(
            "byte-identity check failed: radar-log.md's write-plan text "
            "does not start with its own preserved preamble — refusing to write")
    after_preamble = live_full[len(live_preamble):]
    if not after_preamble.startswith(live_pointer):
        raise AssertionError(
            "byte-identity check failed: radar-log.md's write-plan text does "
            "not have the added pointer immediately after its preamble — "
            "refusing to write")
    remaining_body_out = after_preamble[len(live_pointer):]

    reconstructed = live_preamble + archive_body_out + remaining_body_out
    if reconstructed != original:
        raise AssertionError(
            "byte-identity check failed: reconstructing radar-log.md's "
            "original text from the write plan (preamble + archive body + "
            "remaining body, pointers stripped) does not reproduce the "
            "original byte for byte — refusing to write")


def verify_round_coverage(original, archive_full, live_full, split_round=SPLIT_ROUND):
    """The round-coverage guarantee, checked the same independent way as
    ``verify_write_plan``: re-parses ``### Round`` headers straight out of
    the ACTUAL write-plan strings (never out of an already-partitioned list
    this tool computed earlier — that would have the same self-referential
    weakness ``verify_write_plan``'s docstring describes) and asserts they
    are a clean, order-preserving, non-overlapping partition of the round
    headers found in ``original``.

    That partition check alone is SIDE-AGNOSTIC — it would pass just as
    happily if every round ended up on the wrong side of the boundary, as
    long as none were lost or duplicated (an off-by-one in
    ``compute_split``'s ``>= split_round`` floor comparison, say round 20
    landing in the archive, changes nothing it checks — and
    ``verify_write_plan`` does not check placement either, since
    reconstruction succeeds for any cut point). So this also asserts the
    PLACEMENT itself: every archived round's floor is strictly below
    ``split_round`` and every remaining round's floor is at or above it —
    the one property that is this function's reason to exist alongside
    ``verify_write_plan``, not a duplicate of it.
    """
    original_rounds = ROUND_HEADER.findall(original)
    archive_rounds = ROUND_HEADER.findall(archive_full)
    live_rounds = ROUND_HEADER.findall(live_full)

    if archive_rounds + live_rounds != original_rounds:
        raise AssertionError(
            "round coverage check failed: the write plan's rounds "
            f"(archive {archive_rounds} + live {live_rounds}) do not equal "
            f"original's round headers in order ({original_rounds}) — "
            "refusing to write")
    overlap = set(archive_rounds) & set(live_rounds)
    if overlap:
        raise AssertionError(
            f"round coverage check failed: round(s) {sorted(overlap)} appear "
            "in both write-plan files — refusing to write")
    if not archive_rounds or not live_rounds:
        raise AssertionError(
            "round coverage check failed: one side of the split has no "
            "rounds at all — refusing to write")

    archive_floor_max = max(int(r.split(".")[0]) for r in archive_rounds)
    live_floor_min = min(int(r.split(".")[0]) for r in live_rounds)
    if not (archive_floor_max < split_round <= live_floor_min):
        raise AssertionError(
            "round coverage check failed: the split boundary is not at round "
            f"{split_round} — the archive's highest round floor is "
            f"{archive_floor_max} and the live file's lowest is "
            f"{live_floor_min}; expected archive < {split_round} <= live — "
            "refusing to write")


def plan_split(original, split_round=SPLIT_ROUND):
    """The full pipeline: group rounds, build both would-be-written file
    texts, and verify them against ``original`` (read once, held separately
    throughout — never mutated, never re-sliced to produce the thing it is
    checked against) before returning anything. Raises ``ValueError``/
    ``AssertionError`` — and returns nothing, writes nothing — the moment
    either check fails. Pure — no I/O — so this is exactly what ``--check``
    and the gate test both exercise.
    """
    result = compute_split(original, split_round)
    archive_full, archive_added = build_archive_file(result)
    live_full, live_preamble, live_pointer = build_remaining_file(result)
    verify_write_plan(original, archive_full, archive_added,
                       live_full, live_preamble, live_pointer)
    verify_round_coverage(original, archive_full, live_full, split_round)
    return result, archive_full, live_full


def format_report(result, split_round):
    a_first, a_last = result.archive_rounds[0], result.archive_rounds[-1]
    r_first, r_last = result.remaining_rounds[0], result.remaining_rounds[-1]
    return "\n".join([
        f"split at round {split_round}: "
        f"archive rounds {a_first}-{a_last} "
        f"({len(result.archive_rounds)} headers, {len(result.archive_body)} bytes) / "
        f"remain rounds {r_first}-{r_last} "
        f"({len(result.remaining_rounds)} headers, {len(result.remaining_body)} bytes)",
        "byte-identity: OK — the write plan reconstructs the original exactly "
        "(verify_write_plan)",
        "round coverage: OK — the write plan's rounds are every '### Round' "
        "header in the original, in order, none lost or duplicated, and "
        "correctly placed either side of the boundary (verify_round_coverage)",
    ])


def main(argv):
    """Computes the report (and, unless ``--check`` is given, performs the
    write) and RETURNS ``(message, exit_code)`` rather than printing —
    callable from tests (or any other caller) with no stdout side effect.
    The CLI entry point below is the only thing that actually prints.
    """
    original = _read(LOG_PATH)
    try:
        result, archive_full, live_full = plan_split(original)
    except (ValueError, AssertionError) as e:
        return f"FAIL: {e}", 1

    lines = [format_report(result, SPLIT_ROUND)]

    if "--check" in argv:
        lines.append("--check: no file written")
        return "\n".join(lines), 0

    with open(ARCHIVE_PATH, "w", encoding="utf-8") as fh:
        fh.write(archive_full)
    with open(LOG_PATH, "w", encoding="utf-8") as fh:
        fh.write(live_full)
    lines.append(f"wrote {ARCHIVE_PATH} ({len(archive_full)} bytes) and rewrote "
                 f"{LOG_PATH} ({len(live_full)} bytes)")
    return "\n".join(lines), 0


if __name__ == "__main__":
    _message, _code = main(sys.argv[1:])
    print(_message)
    raise SystemExit(_code)
