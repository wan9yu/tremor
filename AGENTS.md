# AGENTS.md — operating contract for any agent working on tremor

This file is the handoff contract. Read it before touching anything. It codifies the
rules, architecture, and workflow that were previously tacit (held in a prior agent's
memory and in local skills). `radar.md` is the registry SSOT; this file is the
how-to-operate SSOT. When in doubt, prefer the code and `radar.md` over prose here.

---

## 0. Hard invariants (violating any of these is a defect)

1. **No forbidden author-tool literal.** The six-letter string spelled c-l-a-u-d-e
   (any case) must NEVER appear in any tracked file, tracked FILENAME, commit message,
   or commit author/email. This repo is authored impersonally; that name has no place
   in the record. The harness may try to inject it (session-URL commit trailers,
   default file names) — strip it every time. Enforced by
   `tests/lint_no_forbidden_literal.py` (content + filenames + recent commit
   messages/authors); run it before every push. It is why this file is `AGENTS.md`,
   not the other conventional name.
2. **Impersonal record voice.** No first person (I / me / we / our / 我) in tracked
   record prose — docstrings, `radar.md`, `radar-log.md`, `data/annotations.csv`. State
   findings, not narrator. (Round-log entries read as an impersonal ledger.)
3. **No commit-attribution trailer.** Commit subjects are terse and one line
   (`data: 2026-09-15`, `radar: R34 — …`). No `Co-authored-by`, no session-URL trailer
   (it contains the forbidden literal), no attribution footer.
4. **Forward-only.** Never rewrite or force-push published history. Scoring is forward-only
   too: a scoring change bumps `STABLE_SINCE` (see §4), a bug is rescored via
   `tools/rescore.py`, a committed measurement is never silently rewritten.
5. **Never push to `main` without explicit human consent.** Do the work on a branch;
   present it; push only when the human says so. The daily/intraday data commits are the
   CI bot's job, not yours.
6. **地堡日报 (Bunker Daily) stays private.** It lives only under `internal/` (gitignored,
   §6) and is never committed to the public repo.

---

## 1. What tremor is

A git-scraped seismograph for world disorder. Each line is an OPERATOR over a raw public
source → a normalized daily "disorder" reading. The registry is curated like a quant
FACTOR LIBRARY: a spanning set of low-correlation factors, each with a structural
rationale, validated empirically, and **read as a PANEL — never summed into one doom
score.** Several independent factors firing in their own alarm direction at once
("resonance") is what "the world is more disordered" looks like. Full doctrine:
`radar.md` → "tremor is a factor library for world disorder".

## 2. Two tiers (SSOT: `radar.md` tables + `collect.py` `LINES`)

- **Tier 1 — primary:** displayed on the dashboard and COUNTED in the trembling
  resonance. Target size is a small DISPLAY budget (currently 4 — see `radar.md`
  header for the live roster; do not hard-code the number in new prose, cite radar.md).
- **Tier 2 — collected:** scraped daily, building history, shown as a muted watchlist,
  never counted. Uncapped. Includes CONTEXT lines (fail the guard gate by design, never
  promotable) and one CONTROL line (`control_daylength`, contains no world — any signal
  is measurement error).
- Promotion funnel: a tier-2 line earns a primary slot over ≥60 scored readings, gated on
  orthogonality + freshness. New coverage never enters tier-1 on a single episode.

## 3. The three gates + freshness (an indicator must pass to be counted)

- **Guard gate** — a defended equilibrium with a hand that can leak. No guard → it is a
  SYMPTOM (exogenous: a volcano, a cyclone), context/contrast only, never counted.
- **Cadence gate** — disorder must persist at daily resolution (or aggregate intraday→
  daily, e.g. a day's MAX). Intraday-transient phenomena are aliased away and rejected.
- **Reachability gate** — the line's own |z|>3 alarm must be reachable within its record,
  OR under a documented, CITED reference regime (a real historical episode that blew past
  the alarm). Reachability without a base-rate check is not information.
- **Freshness (tier-1)** — a displayed line should lag ≤ ~2 days.

The factor tests a candidate runs (the doctrine): rationale/guard · IC (precision+recall
via the coincidence probe) · decay/neutralization · orthogonality+spanning. **Coverage is
not a goal** — an honestly un-spanned axis beats a manufactured or coverage-confounded
factor; an axis is called un-spanned only AFTER the cheapest construct is base-rate tested
(see the R32 energy and R34 airspace rejections in `radar.md` Rejected).

## 4. Scoring model (SSOT: `core/normalize.py`)

- **Rolling robust-z** (default): median centre + Rousseeuw-Croux Qn scale over a trailing
  window (`WINDOW`), optional weekday de-cycle (`weekday_cycle=True`, e.g. flights) and a
  `QUANTUM` floor for quantized series. |z|>3 is a tremble.
- **Anchored scale-mode**: `z = (raw − ANCHOR) / MATERIALITY`, reading only today — for
  lines whose "normal" is a DECLARED constant, not a rolling window (a $1 peg, a $0 facility
  take-up, a fraction-of-baseline). A line declares `QUANTUM` **or** `MATERIALITY`, never
  both. Anchored lines: `fed_srf_takeup`, `stablecoin_peg`, `net_bgp_withdrawal`.
- **Point-in-time integrity:** `tools/replay.py --check` must reproduce every verdict from
  the raw source under today's rules from `STABLE_SINCE` forward (0 divergence). A scoring
  change bumps `STABLE_SINCE` (`tools/replay.py` mandates it on a TIER change); a bug is
  rescored (`tools/rescore.py`). Diagnostic `components` (`data/components/…`) and the
  intraday side-channel are DIAGNOSTIC-ONLY — the scoring path (`collect.py`,
  `core/normalize.py`) must never read them (`tests/test_side_channel.py` enforces this).

## 5. The test tiers (run all before a push)

| tier | glob | what | how to run |
|---|---|---|---|
| **gate** | `tests/test_*.py` | pure, no network, no `data/` — the commit-time hard gate | `python -m pytest tests/ -q` |
| **audit** | `tests/audit_*.py` | post-commit; may read `data/` (metrics-fresh, round-index parity, no-overdue-pending, retracted-phrase) | `python -m unittest discover tests -p "audit_*.py"` |
| **lint** | `tests/lint_*.py` | push-CI; STDLIB-ONLY, must pass in a bare venv (registry tier parity, public-surface parity, the forbidden-literal check) | `python -m unittest discover tests -p "lint_*.py"` |

Also: `python tools/replay.py --check` (0-divergence) and `python tools/pending.py --check`
(0 overdue). CI wiring: `.github/workflows/ci.yml` (gate+lint) and `daily.yml` (gate+replay+
audit, plus the collect cycle). **The lint tier is stdlib-only** — never add a third-party
import to a `lint_*.py` or the module it imports.

## 6. Key files

- `collect.py` — the daily scrape+score+write cycle; `LINES` is the tier SSOT; the fetcher
  contract is documented at the top.
- `core/normalize.py` — the scorer (rolling-z + anchored). `core/adsb.py`,
  `core/useragent.py`, `core/clock.py` — shared fetch/scoring helpers.
- `fetchers/<line>.py` — one per line; module attrs (`LINE`, `TIER`, `ANOMALY_DIRECTION`,
  and `ANCHOR`/`MATERIALITY` or `QUANTUM`) + `fetch_daily()`.
- `tools/` — `replay.py` (integrity), `pending.py` (tripwires), `episodes.py` +
  `pending.py --markdown` (regenerate `radar-metrics.md`), `rescore.py` (bug re-score).
- `radar.md` — the registry SSOT: tier tables, gates, doctrine, Backlog, Rejected, Pending
  reviews & tripwires, and the round index.
- `radar-log.md` (+ `radar-log-1.md`, rounds 1–19) — the per-round ledger.
- `radar-metrics.md` — GENERATED (do not hand-edit; regenerate — audit checks freshness).
- `data/<line>.csv` — the committed record; `data/annotations.csv` (mirrored byte-equal to
  `docs/data/annotations.csv`); `data/components/`, `data/summary.csv`, `data/intraday.csv`
  are aggregates/diagnostics, not registry lines.
- `internal/` — **gitignored, local-only** design specs, plans, operations notes, and the
  private 地堡日报. Present on the maintainer's machine (a local agent has them); NOT in a
  fresh clone. `radar.md` cites some `internal/…` design docs — those are local references.

## 7. Workflow

- **A calibration round** ("radar round") = score → explore → calibrate over the registry,
  recorded as a new `### Round N` entry in `radar-log.md` + updates to `radar.md` (+ a
  round-index line; regenerate `radar-metrics.md`). The procedure is driven by the
  `tremor-radar` skill, installed in the maintainer's local agent skills directory (outside the
  repo). Each round is
  data-backed — computed from `data/*.csv` + the rubric, never gut-feel ("data-backed, never
  拍脑袋").
- **Periodic audits** use the `audit` skill (waste / drift / strategic).
- **Building/changing a line:** brainstorm/probe first (measure before building), then a
  subagent-driven build with an independent review, then the full test suite, then the push
  gate. Probes that fail are RECORDED in `radar.md` Rejected + a round entry so the search is
  not repeated (see the entsog/energy R32 and airspace R34 rejections as worked examples).
- **Pending tripwires** live in `radar.md` "Pending reviews & tripwires" as
  `[opened R.. · owner R.. · fires: <predicate>]`; `tools/pending.py` parses/evaluates them.
  Promises live there, not loose in prose.

## 8. Sanity checklist before any push

- [ ] gate + audit + lint all green; `replay --check` 0-divergence; `pending --check` 0 overdue
- [ ] `python tests/lint_no_forbidden_literal.py` (or the lint tier) — clean
- [ ] no first-person in new record prose; commit subject one line, no trailer
- [ ] `radar-metrics.md` regenerated if any line/pending/round changed
- [ ] on a branch; pushed to `main` only with explicit human consent
