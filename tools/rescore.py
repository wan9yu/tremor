"""Re-score a line's committed rows under today's rules. For BUGS, not changes.

THE DISTINCTION THIS TOOL LIVES OR DIES BY, because it is the one thing in the
repo that rewrites published verdicts:

  * A scoring CHANGE — a new threshold table, a new estimator, a rule the
    instrument did not have before — applies FORWARD ONLY. History keeps what
    the code of its day produced, ``STABLE_SINCE`` moves, and the divergence
    is the record showing its seams honestly. NEVER run this for that.

  * A scoring BUG — rows judged by rules that were already declared and simply
    failed to reach them — is different. Those rows were never the instrument's
    verdict; they are its misfire. Re-scoring them is a correction, and the
    protocol is the usual one: archive the file first, log a method row in
    annotations.csv, say what changed and why.

Twice now the second case has been real, both times at the same seam: a seeder
scoring rows without a per-line option the live collector had. ``net_outages``
holds ``QUANTUM = 1`` and its 1,621-row seed was written without it, leaving 34
rows — including a 45-country day on a tier-1 line — with no verdict at all.

Every published row keeps its date, its raw value and its prose. Only the
VERDICT fields are recomputed, through ``collect.score_row`` with the module's
own ``collect.scoring_attrs``, replayed strictly oldest-first so no row is ever
judged against readings from its own future.

    python tools/rescore.py net_outages --dry-run
    python tools/rescore.py net_outages
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect
import seedlib


def line_module(name):
    for mod in collect.LINES:
        if mod.LINE == name:
            return mod
    raise SystemExit(f"no collected line called {name!r}")


def rescore(mod, dry):
    rows = seedlib.read_line(mod.LINE)
    if not rows:
        raise SystemExit(f"{mod.LINE}: no rows to re-score")

    # An empty history means "import nothing": merge then only preserves the
    # published rows, which is exactly the plan a re-score needs.
    plan, _ = seedlib.merge([], rows, lambda obs, value: "")
    before = {r["date"]: (r["z_score"], r["trembling"], r["status"]) for r in rows}
    out = seedlib.score_series(plan, mod)
    changed = [r for r in out
               if before[r["date"]] != (r["z_score"], r["trembling"], r["status"])]

    print(f"{mod.LINE}: {len(rows)} rows, {len(changed)} verdicts change")
    for r in changed[:8]:
        was = before[r["date"]]
        print(f"  {r['date']}  z {was[0] or '—':>8} -> {r['z_score'] or '—':>8}   "
              f"{was[2]:<11} -> {r['status']}")
    if len(changed) > 8:
        print(f"  ... and {len(changed) - 8} more")
    if not changed:
        print("  nothing to do — the record already reflects today's rules")
        return 0
    if dry:
        print("  (dry run — nothing written)")
        return 0

    archived = seedlib.archive_current(mod.LINE, "prerescore")
    collect.write_line(mod.LINE, out)
    print(f"  archived {os.path.basename(archived)}, rewrote {len(out)} rows")
    print("  NOW: add a method row to data/annotations.csv saying what was wrong "
          "and what changed — a rewritten verdict without a written reason is "
          "the thing this protocol exists to prevent")
    return 0


def main(argv):
    names = [a for a in argv if not a.startswith("--")]
    if len(names) != 1:
        raise SystemExit(__doc__.strip().splitlines()[-1].strip())
    return rescore(line_module(names[0]), "--dry-run" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
