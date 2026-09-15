---
name: tremor-radar
description: Calibrate the tremor indicator radar — run one round of score→explore→calibrate over the two-tier registry (4 primary / uncapped collected watchlist + Backlog), updating the tracked radar.md registry. Use when the user says "/radar", "tremor radar", "calibrate indicators", "run a radar round", or wants to reassess which tension indicators are primary vs collected. Decisions are data-backed (computed from data/*.csv history + an explicit rubric), never gut-feel.
---

# tremor radar — one round of thinking

You maintain tremor's **indicator radar**. Each invocation runs ONE round.
Decisions must be **data-backed, never 拍脑袋** — every promotion/demotion cites
a score.

Work in the tremor repo (`/Users/wangyu/repositories/tremor`). The living registry is
the tracked file `radar.md` — READ IT FIRST; its "How an indicator is scored" section,
the three gates, Known limits, the tier tables, Backlog and Rejected are the living law,
and where this file and radar.md disagree, radar.md wins. The full round-by-round
calibration log lives in `radar-log.md` (split out R19 to keep the registry under
~300 lines); radar.md carries only a one-line round INDEX pointing into it — read
radar-log.md when you need the measured reasoning behind a past round. Historical design:
`internal/radar-skill-design.md` (describes the retired 4-8-16 funnel; round 8 collapsed it).

## The structure (two tiers + a backlog — round 8, no caps on tier-2)

| tier | role | target | in repo |
|---|---|---|---|
| 1 | primary — displayed, counted in resonance | 4 | fetcher `TIER=1` + `tier:1` in docs/index.html |
| 2 | collected — scraped daily by CI, building history; not counted | no cap | fetcher `TIER=2` + `tier:2` |
| Backlog | ideas without a probed fetcher yet | — | a plain list in radar.md |

Tier-2 also holds **context lines** (gdelt, gdelt_tone, vix, polar_temp — fail
the guard gate, never promotable, never counted) and one **control line**
(control_daylength — contains no world; any signal in it is measurement error).

Anything with a real guard and a PROBED working keyless daily fetcher is built
and collected immediately. The only funnel is tier-1 promotion: ≥60 scored
readings, orthogonality, freshness. Never demote a tier-1 line without evidence.

## The 5 metrics (unlock as a candidate climbs)

- **Leverage** (rubric 0-3) — how many distinct forces ripple into this number.
- **Guard × Reach** (rubric 0-3 each) — real guard + leaking hand? global or national?
- **Reliability** (computed) — fetch uptime over its CSV history.
- **Responsiveness** (computed) — does it move and catch attributable real events?
- **Orthogonality** (computed) — |max corr| of z-history vs the live tier-1 set.

## Absolute gates (fail any → cannot be a counted indicator)

- **Guard gate** — no real guard → never tier-1; context/contrast only.
- **Cadence gate** — the disorder must persist at daily resolution, or be honestly
  aggregated intraday→daily (as grid_frequency takes the day's MAX |dev|).
- **Reachability gate** (standing 2026-07-30) — the alarm must be reachable: if
  |z|>3 requires exceeding the line's whole record, it is a decoration.
  Reachability arithmetic is BASELINE-RELATIVE: recompute it after any seed
  (the FRED reseed voided the 07-29/30 figures — see radar.md round 9).

**Freshness rule (tier-1 only):** prefer ≤ ~2-day publication lag. PortWatch-lagged
lines (~10 days) stay tier-2 regardless of strength.

## Round procedure

1. **Load** `radar.md` (the registry) and every `data/<line>.csv`; open `radar-log.md`
   only when you need the measured reasoning behind a past round.
2. **Score** each on its available metrics; `—` under ~20 rows, and below ~60
   scored readings say "insufficient to adjudicate", don't rule.
3. **Explore (diverge)** — reason 1-3 NEW candidates from the thesis, web-verify a
   free stable daily source for each; add the strongest to the Backlog (or build
   directly if probed live during the round and the user approves).
4. **Calibrate (converge)** — rank; list moves with cited evidence.
5. **Apply** — mechanical moves only (TIER flag + docs/index.html tier). Building
   a new fetcher needs approval.
6. **Write** — update the radar.md registry tables, APPEND the round to `radar-log.md`,
   and add its one-line entry to radar.md's round index. Commit with a simple English
   message. Print a short report.

## Computing the data metrics

CSV columns: `date,raw_value,z_score,trembling,direction,source_note,obs_date,status`.
- **Reliability** = 1 − (rows with status `dark`) / total rows. Note `stale` is a
  source republishing, not a failure; `warming-up`/`no-spread` are blind, not dark;
  `closed` (R18: a market shut for the weekend) is by-design, neither dark nor blind.
- **Responsiveness** = robust dynamic range + attributable trembles. The rolling scale
  estimator is Rousseeuw-Croux **Qn** in core/normalize.py (not MAD) — except ANCHORED
  lines (R15: fetcher declares ANCHOR + MATERIALITY, e.g. stablecoin_peg, fed_srf_takeup),
  which score z = (raw − anchor) / materiality against their declared constant instead of
  any rolling window. Remember the measured false-alarm floor: since R10 the bar is the
  calibrated `normalize._C_N` table (c(10)=4.686 … c(90)=3.000), holding every line at the
  same 0.392% false-tremble odds on a calm iid day; on real credit series |z|>3 fires
  5.5–8.5%/day, clustered in real episodes.
- **Orthogonality** = |max Pearson corr| of z vs each tier-1 line (≥20 shared points).
- `tools/replay.py` re-derives every verdict under today's rules; use it for any
  "what would the record say now" question. `tools/level_layer.py --report` shows
  which per-strait states are currently OPEN (the level question the z cannot answer).

## Discipline

- Data-backed only; every tier change cites a number or an explicit rubric reason.
- Honor all three gates absolutely; below 60 scored readings, defer, don't decide.
- Dedup by observation: seeded lines carry archive-import rows — their `source_note`
  says so; do not read a seeded row as a live detection.
- The string c-l-a-u-d-e (any case) must never appear in anything committed to this repo.
- This skill calibrates only; CI already runs the daily collection.
