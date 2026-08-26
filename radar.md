# tremor radar — indicator registry

tremor doesn't keep a fixed indicator set; it runs a **radar**. Indicators are
chosen by data, never by gut feel, and the live instrument is always the best few
we have.

**Two tiers:**

| tier | role | target |
|---|---|---|
| **1 — primary** | displayed on the dashboard, counted in the trembling resonance | 4 |
| **2 — collected** | scraped every day, building history; shown only as a muted watchlist, never counted; no cap | all that qualify |

Anything with a real guard and a **verified, working, keyless daily fetcher** is built
and collected immediately, banking evidence toward tier-1. (Keyless is the default;
a source may instead use a **declared load-bearing key** — one with no keyless fallback,
unlike the optional `FRED_API_KEY` / `FINGRID_API_KEY` — only as a stated exception recorded
in the registry. The first is `AGSI_KEY` for eu_gas_storage, R23.1.) Collection is nearly free in
a git-scraping architecture; the history you don't collect is the expensive thing.

The bar to ENTER tier-2 is real, because every collected line is a survivability
liability (one more source that can rot, one more fetch that can flake the daily
run): (1) it passes the guard + cadence gates, or is an explicit never-counted
CONTEXT line; (2) it has a fetcher that has been PROBED returning real numbers, not
just a plausible-looking source; (3) its failure mode is named. Ideas that don't yet
meet (2) are a plain **Backlog** list below — a to-do, not a tier.

The only funnel is tier-1 promotion: a tier-2 line earns a primary slot over ≥60
scored readings, gated on orthogonality and the freshness rule.

## How an indicator is scored

Five metrics, which **unlock as a candidate climbs** (some can only be measured once
data exists):

- **Leverage** — how many distinct forces, direct and indirect, ripple into this one
  number. The more, the better a side-channel it is. *(rubric, idea stage)*
- **Guard × Reach** — is there a real guard + leaking hand (a true tension indicator)?
  × is it global or merely national? **Guard is an absolute gate — no guard, no tier-1,
  however interesting.** *(rubric, idea stage)*
- **Reliability** — fetch uptime over its history. *(computed, once scraping)*
- **Responsiveness** — does it actually move and catch real events, vs flatline/noise?
  *(computed, needs history)*
- **Orthogonality** — how uncorrelated it is from the live tier-1 set; the gate that
  keeps the primary four independent. *(computed, tier-1 gate)*

**Three absolute gates** (fail any → not a counted indicator):
- **Guard gate** — no real guard → never tier-1 (watchlist / "felt vs real" contrast only).
- **Cadence gate** — collection samples once a day, so the disorder must persist at daily
  resolution, OR be aggregated intraday→daily (as `grid_frequency` takes the day's MAX
  deviation). Intraday-transient phenomena that recover within a day — stablecoin
  flash-depegs, a momentary FX wick — are aliased away by a daily snapshot and rejected.
- **Reachability gate** (standing since 2026-07-30; registered here R9) — the line's own
  alarm must be REACHABLE: if |z|>3 requires a move beyond anything in the line's whole
  record, the alarm cannot fire on any day resembling the observed world and the line is
  a decoration, not an instrument. Measured as the threshold distance in Qn units against
  the record's observed range. NOTE: reachability numbers are baseline-relative — a seed
  that deepens the baseline voids the previous arithmetic (this bit the FRED lines, R9).
  **Amended R23.1 (baseline-relative in a young calm record):** a line PASSES if its alarm
  is reachable within its own record OR under a documented **reference regime** — real
  historical episodes of the guarded quantity that blew past the alarm. This is the
  same baseline-relativity the NOTE already declares, made explicit for a young line whose
  own record is too calm to contain its alarm. Applied to cnh_cny: its UP alarm needs +227
  pips vs a 52-obs high of 143 (unreachable WITHIN the record) but real capital-flight
  episodes have run hundreds of pips — it passes. The reference regime must be cited, not
  assumed, and is re-checked at the line's maturity review.

**Freshness rule for tier-1:** a displayed instrument must be FRESH (low publication lag). A
line that is daily but lags a week (e.g. IMF PortWatch, ~10 days measured) only shows a disruption long
after it began — fine for tier-2 (history accumulates, the lag washes out in the rolling
baseline), but too stale to be a live tier-1 instrument. Prefer ≤ ~2-day lag for tier-1.

A line is never demoted without evidence. Rubric scores are 0–3; computed metrics
show `—` until there is enough history (~20 days). Tier-1 holds a target of 4;
tier-2 is uncapped (round 8).

**One rule about new coverage** (added round 7): no new tier-1 line may be justified by a
single episode. New coverage enters at tier-2 and earns promotion over ≥60 scored readings
with a documented tremble rate. An instrument tuned to catch the last crisis is how
instruments stop working on the next one.

### Known limits of the method

Written down because they are structural, not bugs, and a reader deserves them up front.

1. **A rolling z is a CHANGE detector; the founding question is a LEVEL question.** Every
   line is scored against its own recent history, so a disorder that is already running
   sits inside its own baseline and reads calm. A war in its third week is invisible by
   construction; only its onset and its end are visible. This is the single largest gap
   between what tremor measures and what it asks, and no amount of extra coverage closes
   it — it would take an external reference for "normal", which the instrument does not
   yet admit.
   **Measured, not argued** (2026-07-25): replaying 200 days of per-strait transits for the
   Strait of Hormuz through the unmodified scoring rules produces 13 alarm-direction
   trembles, *all* on 2026-03-02..03-14 — and none in June or July. On 2026-07-12, the day
   the strait was reported closed, a dedicated Hormuz line reads **z = −0.47**. The monthly
   medians say why: 72 (Jan), 81.5 (Feb), then 4, 8, 6, 11, 15 (Mar–Jul). By July the
   trailing window's "normal" *was* the blockade. The instrument caught the onset loudly and
   then went blind for five months. Note what this rules out: the July miss was **not**
   primarily a coverage failure — a sensor pointed straight at Hormuz would have missed it
   too.
   **Partially answered** (2026-08-03, R9): the LEVEL LAYER (`tools/level_layer.py`) walks
   the per-strait component record with a pinned pre-event reference — the reference is
   frozen the day a state opens, so a broken state can no longer argue itself normal by
   becoming the baseline. At R9 it held one state open — Hormuz since 2026-04-06, then at
   ~14% of its pinned 72/day (see the R12 update below for the current states). Diagnostic,
   unscored, uncounted — but the level question now has a written answer instead of a shrug.
   **Quantified and located** (2026-08-14, R12): the sum's blindness is now a measured fact,
   not a worry — a full simultaneous closure of the two currently-stuck straits (Hormuz +
   Kerch, pinned 72 + 12 = 84 transits) moves the 28-strait total 1.04 z, 35% of the way to
   its −3z alarm; 3.4 Hormuz-sized straits must close at once for the sum to fire. The level
   layer holds what the sum cannot (two states open now: Hormuz 7%, Kerch since 07-26 at 0%).
   The remaining gap is that its count is not *served* — and the fix belongs OUTSIDE the
   scoring path (a diagnostic panel), never as a `summary.csv` column, which would break the
   side-channel firewall, replay's forward-only re-derivation, and the tier-1-only summary
   contract at once. See round 12.
2. **The tremble bar is not one number — it depends on how much evidence built the
   verdict.** A robust z measures today against an ESTIMATED median in units of an
   ESTIMATED scale, and estimates from ten readings wobble in a way estimates from ninety
   do not: the flat |z|>3 rule fired on a calm day 2.62% of the time at n=10 and 0.391% at
   n=90, a 6.7x spread, with both regimes live on this record at once. Since round 10 the
   bar is a calibrated table (`normalize._C_N`, from `tools/calibrate_threshold.py`):
   **c(10)=4.686, c(20)=3.557, c(30)=3.291, c(60)=3.062, c(90)=3.000**, set so every line
   at every age has the same **0.3916%** odds of a false tremble on a calm day — the odds a
   full window always had, so nothing about a mature line changes. Short-window lines are
   no longer expected to tremble more often than old ones; attribution stays mandatory
   anyway.
   **Measured on REAL data** (2026-08-02, from the 787-row FRED seeds): |z|>3 fires on
   **5.5–8.5% of days** for real credit series — fat tails, autocorrelation and trend that
   no iid simulation carries. The firing days are not scattered: they cluster inside four
   real credit episodes (2023-10, 2024-08, 2025-04, 2026-03) and all three credit lines
   agree on the dates, which is event detection with fat-tailed inputs, not a broken rule.
   Any claim of the form "this line trembles X% of the time" must be read against 6–8%,
   not 0.3%.
3. **Tremble COUNTS are day counts, not episode counts, and on the slow lines the gap is
   about eightfold.** Measured raw lag-1 autocorrelation: 0.986 (credit_spread), 0.993
   (em_corp_oas), 0.992 (euro_hy_spread), 0.964 (polar_temp), 0.892 (vix, gnss) — at which
   a 90-observation baseline carries roughly **one and a half independent readings**. One
   event prints as a run: credit_spread's 66 alarm days are **8 episodes** in 3.01 years,
   em_corp_oas' 48 are 7, polar_temp's 384 are 34. `tools/episodes.py` reports both, and a
   per-day rate must not be quoted for these lines without the episode count beside it.
   The young tier-1 roster is close enough to exchangeable (lag-1 0.07-0.33) that the iid
   null is still honest for the headline — which stops being true the day a second
   credit-like line is promoted.
4. **Below ~60 scored readings a per-line tremble rate cannot be adjudicated.** The
   confidence interval is wider than the difference being argued about. Radar rounds
   should say so rather than rule on n≈20.

### Pending reviews & tripwires (added R21 — promises live here, not in prose)

Every open commitment in one place, so a radar round can check this list instead of
re-reading the log. Close an item by editing it out with a round reference.

- **flights pre-committed review** — due **2026-08-31** (de-cycling engages, n≥60): demote if
  episode-rate Wilson LB >2%, or immediately on the next unadjudicable alarm (set R11).
- **cnh_cny maturity refresh** — at n≥60 scored: re-measure the reach cell + benign-tremble
  recount (queued R13). R23: now n=48 (record range −45..143; 4 trembles, all benign DOWN),
  still <60 — keep waiting.
- **anchored-scale promotion gates** (R15, standing): before ANY anchored line promotes,
  its MATERIALITY must be replay-validated to the R11 bar and an episode/serial-dependence
  overlay run. Applies to stablecoin_peg, fed_srf_takeup.
- **calendar de-cycling debt** (named R20): month/quarter-end rhythm gates fed_srf_takeup's
  promotion and warps tga_days_cash; payable on fed_srf's 1,262-day seed. This repo still
  has no de-cycling beyond weekday.
- **closed-status first live weekend** — RESULT (R23): 08-23 (Sun) correctly read `closed` ✓;
  08-22 (Sat) read `scoring` raw 83 (z−0.24) — Friday's close re-scored, because the weekend
  guard keys on the NEWER leg being Sat/Sun and Saturday-morning still sees two Friday timestamps.
  Follow-up: confirm obs-dedup isn't double-counting Friday's close, and decide whether the guard
  should also cover Saturday (a fetcher change → needs approval).
- **net_outages settle — reconciliation tripwire** (R23.1, CLOSES the R23 sub-sweep-filter item):
  the 08-24 artifact class is fixed by settling the live fetcher to a completed D-1 22:00Z window — the
  GENERAL fix (it removes the whole latency-injection class) rather than a filter fitted to the 08-24
  signature; the queued onset-synchrony/BGP/transience filter is NOT built. `monitor_swept` untouched.
  Standing check: each round (a `tools/` step, live network — never a gate/test) re-query the last ~7
  settled windows vs their stored raws; any mismatch that would flip a verdict reopens the D-2 question
  with data. One-time on the FIRST post-switch round: re-query every seam-era row (2026-07-10→2026-08-25)
  + one interior day of each of the 6 multi-day runs. Carry forward: a synchronized-onset artifact that
  still ALARMS after settle means the mechanism diagnosis was wrong → reopens net_outages' tier-1 status
  (its 37 real episodes stand).
- **level-layer → flights** (opened R23.1) — decide ~Nov 2026 (once flights per-region components banked
  since 08-02 can populate an honest reference window) whether to extend the level layer to flights
  regions; the second headline currently rides one lagging, panel-churning source (PortWatch, ~10d).
- **cnh_cny reachability reference-regime re-check** (R23.1) — the reachability gate passed cnh_cny on a
  cited reference regime (real capital-flight episodes past +227 pips). Re-confirm at n≥60 that the
  reference-regime evidence still holds, alongside the maturity refresh.
- **radar-log.md roll tripwire** — split the log into an archive file when it crosses
  **2,000 lines** (1,406 after R21; ~57 lines/round → around R31-R33).
- **usd_xccy_basis parking review** — re-probe sourcing every ~10 rounds (last: R20);
  downgrade to Rejected if still keyless-blocked at R30.
- **the single-credit-slot bar** (measured R22, standing): US HY (credit_spread, tier-1), EM
  corp (em_corp_oas) and Euro HY (euro_hy_spread) are ONE global credit factor — |max corr|
  +0.80 / +0.74 vs the tier-1 credit line, +0.86 to each other. NO second credit-family line
  may be promoted to tier-1: it would fail the orthogonality gate AND break the headline's iid
  null (Known limits #3). The genuinely-orthogonal financial challenger is `sofr_iorb_spread`
  (max corr +0.34, n=35 — defer until ≥60 scored).

---

## Tier 1 — primary  (4 / 4 · reviewed R11 · metrics refreshed R21)

The four displayed, counted instruments — four distinct domains. Decided round 3,
applied round 4.

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | Orthog | status |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| flights | airspace (EU/US/JP) | 3 | 3 | 2 | 60/60 | 1 alarm in 50 scored, the adjudicated 07-05 artifact | ≤0.08 (n≈50, R21) | ⚠️ **RETAINED WITH CONDITIONS, R11** — sole current-rule alarm is an artifact; review pre-committed 2026-08-31 (de-cycling engages, n≥60): demote if episode-rate Wilson LB >2%, or immediately on the next unadjudicable alarm |
| credit_spread | financial (US→global) | 3 | 3 | 3 | 816/817 | 66 alarm days = 8 episodes, all 4 real events | ≤0.08 (n=788, R21) | ✅ global bellwether; alarm at the 45th pctile of its 788-day record |
| cnh_cny | capital controls (China) | 2 | 3 | — | 56/60* | 0 alarms (4 benign down-trembles) in 44 scored | ≤0.12 (n≈44, R21) | ✅ slot 4 (user-decided); reach cell MEASURED R13 — the alarming (up) side needs +227 pips vs a 52-obs record high of 143 (a decoration WITHIN this young calm record; baseline-relative — real capital-flight episodes blow far past it), while all four |z|>3 events are benign DOWN trembles (offshore yuan stronger). Still <60, insufficient to adjudicate; refresh at the maturity review (*4 darks are weekend/leg-timing rejections, not failures; the 08-16 dark ran hours before R18's closed status landed — weekends read `closed` from the first post-R18 weekend, 08-22/23, on) |
| net_outages | communications (global) | 2 | 3 | 3 | 1656/1668 | 58 alarm days; 37 real episodes; grid-strike + blackout events attributable. **R23: the 2026-08-24 z=4.69 spike (12 countries) was a FALSE ALARM** — an IODA active-probing common-mode artifact (10 synced ~40-min ping-slash24 events across 4 ocean basins, no BGP, settles 12→4 on re-query), triple-refuted (timing/infra/web); a sub-scrub sibling of the annotation-97 monitor sweeps (see log R23) | ≤0.12 (R23) | ✅ **CONFIRMED R11** — every gate passed at the pre-committed review (see round 11). **R23:** one false alarm (08-24 artifact) exposed a guard gap — the sweep guard misses a 12-country synchronized-onset artifact; a synchrony/BGP/transience filter is queued (Pending reviews). NOT a demotion — 37 real episodes stand, the artifact is caught and documented |

## Tier 2 — collected  (13 candidates + 5 context + 1 control · no cap)

Collected daily by CI, building history; shown only as a muted watchlist, never counted. The global 3/3/3 lines
are tier-1 challengers banking evidence. There is no slot cap (round 8): any candidate
with a real guard and a probed, working fetcher is collected. Below them sit the **context lines** — they fail
the guard gate and can never promote or be counted; they ride along only to aid
interpretation.

**The context-line admission bar** (formalized R22): a context line is exempt from the guard
gate BY DESIGN, but not from earning its keep — every collected line is a survivability liability
(one more source that can rot, one more fetch that can flake). So a context line must NAME the
specific ambiguity it resolves in an existing line, falling into one of three established roles,
or it is decoration and is rejected. "It's free to collect" is never a reason — that is exactly
the liability this bar refuses. The three roles, with the five context lines placed:

- **felt-vs-real contrast** — how disordered the world FEELS, set against how disordered it
  measurably IS: `gdelt`, `gdelt_tone`, `vix`.
- **slow-level read** — an external "normal" for the LEVEL question the rolling z answers poorly:
  `polar_temp`, against a fixed 1958-2002 climate normal (added round 8 under the
  **provisional-watch** disposition, see below).
- **confounder-subtractor** — strips an exogenous driver out of a counted/tension line's reading:
  `space_weather` (daily-max Kp, R22), which says whether a `gnss_interference` / `grid_frequency`
  tremble was a geomagnetic storm or a human hand.

None occupy a candidate slot. Below even those sits `control_daylength`, the CONTROL line: it
contains no world at all — it exists to catch the pipeline lying, and any signal in it is
measurement error by definition.

**Provisional-watch** (disposition added round 8): a source that is verified free+daily
but whose ROLE is undecided is collected now — never counted — so its history accumulates
while the decision is deferred. It is the honest home for "we're not sure yet": no gut-feel
add, no premature reject. `polar_temp` is its first use.

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | note |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| port_throughput | trade (global) | 3 | 3 | 3 | — | — | ~4729 global port calls/day (2065 ports) |
| chokepoint_breadth | trade (global) | 3 | 3 | 3 | — | — | 28 straits, ~1810/day (Hormuz blockaded) — strong, but PortWatch lags ~10 days: too stale to display live. R12: the SUM is structurally blind to 1–2 small straits going silent (a full Hormuz+Kerch closure = 84 transits = 1.04z, 35% to alarm) — the level layer, not this line, carries that signal |
| sofr_iorb_spread | financial plumbing | 3 | 3 | 3 | — | — | SOFR−IORB ~−2bps (calm) — keyless FRED |
| em_corp_oas | EM financial (global) | 3 | 2 | 3 | — | — | EM corp OAS ~1.38pp. R22 MEASURES the standing "orthogonal to US HY" claim FALSE: |max corr| vs the live tier-1 set = **+0.80 vs credit_spread** (n=789) — the same global credit factor, not an orthogonal domain. Stays tier-2 for breadth/confirmation; NOT a tier-1 promotion candidate (would fail the orthogonality gate and break the headline's iid null — see Known limits #3) |
| gnss_interference | navigation/EW (global) | 3 | 3 | 1* | 31/31 | 3.4% | demoted R7 — *effective* reach is 1, not 3: one worldwide ratio has no regional sensitivity. Seeded R9 to 2022-07 (1,466 rows): it fires 49 alarm-direction trembles in 1,452 scored days, and the Gulf window peaks at z=2.87 — under-powered, not motionless (see the R9 corrections). Its global floor rose 1.64x in four years with no single day ever unusual |
| capital_premium | capital controls (Korea) | 2 | 3 | 1 | — | — | demoted R4 (redundant with China); kept on watch |
| grid_frequency | infrastructure (Nordic) | 2 | 3 | 1 | — | — | demoted R4 (regional); kept on watch — may re-challenge on orthogonality |
| euro_hy_spread | financial (EU) | 3 | 2 | 2 | — | — | built R8 — ICE BofA Euro HY OAS ~2.5pp, keyless FRED. R22: the "different central bank → orthogonal" intuition is MEASURED FALSE — |max corr| = **+0.74 vs credit_spread** (n=783), and +0.86 vs em_corp_oas: US HY, EM corp and Euro HY are ONE global credit factor at daily z. Tier-2 for breadth; not a tier-1 candidate (redundant with the credit slot) |
| fx_parallel_premium | capital controls (AR) | 2 | 3 | 2 | — | — | built R8 — Argentina blue-vs-official FX premium, keyless dolarapi; a hard-controlled regime, distinct from cnh_cny/kimchi |
| hkma_aggr_balance | capital (HK) | 3 | 3 | 2 | — | — | built R8 — HK currency-board aggregate balance, keyless HKMA API; falls as the peg is defended under outflow |
| — gdelt | feel: conflict share (global) | 1 | 0 | 3 | — | — | contrast line (guard gate) — v2 full-day aggregation, not a candidate slot |
| — gdelt_tone | feel: news tone (global) | 1 | 0 | 3 | — | — | contrast line — full-day average tone, same pass as gdelt |
| — vix | feel: priced fear (global) | 1 | 0 | 3 | — | — | contrast line — keyless FRED VIXCLS, seeded 180d from archive |
| — polar_temp | context: planetary level (Arctic 80N) | 1 | 0 | 2 | — | — | context line, provisional-watch — DMI +80N daily anomaly vs the 1958-2002 normal (keyless, ~1d lag). A LEVEL read, not a tension indicator; the long baseline is vendored in core/arctic_clim.py. Seeded R9 to 2019 (2,740 rows): 384 warm trembles vs 4 cold — the asymmetry is the warming |
| — space_weather | context: geomagnetic storm (global) | 1 | 0 | 3 | 1.00 (0 dark / 1486) | 39 trembles in 1476 | **built R22** — daily MAX planetary **Kp** index, rolling z (QUANTUM=1/3), keyless: NOAA SWPC live + GFZ Potsdam definitive archive, seeded to 2022-07-27 to ALIGN with gnss_interference. A CONTEXT line (fails guard gate — the Sun is the exogenous force, not a guarded equilibrium): never counted, never promotable. Its ROLE is a **confounder-subtractor** for gnss_interference + grid_frequency — a storm degrades GNSS worldwide and stresses grids, the same signatures a human hand leaves; Kp says which. Validated: the up-trembles are exactly the real G1-G5 storms — the May-2024 Gannon superstorm (Kp 9, strongest in 20y) fires on both peak days, as do the Oct-2024 and Mar-2024 storms |
| tga_days_cash | fiscal plumbing (US) | 3 | 3 | 2 | — | — | built R11.1 — Treasury cash buffer in DAYS OF ITS OWN OUTFLOWS (closing TGA balance / trailing-20-business-day mean withdrawal), keyless Treasury Fiscal Data, T+1. The guard is visible not asserted: median 5.3 business days against Treasury's announced ~1-week policy, and the June-2023 X-date reads 0.21 days |
| fed_srf_takeup | financial plumbing (US→global) | 3 | 3 | 3 | 1.00 (0 dark / 1262) | 3 trembles in 1262 scored | **built R20** — daily Standing Repo Facility take-up ($m), keyless NY Fed markets API (`/api/rp/...`), seeded to 2021-07-28 (SRF inception). Take-up = Σ accepted across the day's Repo ops (RRP excluded); anchored scale-mode (ANCHOR=0, MATERIALITY=$10bn → alarm $30bn, set ABOVE the ~$20-26bn month/quarter-end friction band). 767/1262 days are exactly $0 and score an honest z=0; only the three genuine >$30bn scarcity spikes fire — year-end 2025 $74.6bn (z=7.5, the record), Oct-2025 $50.4bn (z=5.0), mid-month 2026-02-17 $30.5bn (z=3.05, no calendar). Settle boundary is explicit UTC (TZ-robust, never partial). Promotion gated on a de-cycling pass for the sub-alarm month-end clustering (this repo has none) |
| stablecoin_peg | crypto dollar peg (global) | 3 | 3 | 3 | — | 3 trembles (SVB z=12.6) in 2128 | **built R14, scored R15** — worst-of-{USDC,USDT} deviation-from-$1 in bp, settled daily CLOSE, keyless Bitstamp OHLC, seeded 2020-10→now. Guard clean; cadence-reject OVERTURNED (SVB was a multi-day close-visible depeg, USDC close $0.9685). Now scored in **anchored scale-mode** (ANCHOR=0, MATERIALITY=25bp → alarm at 75bp) instead of the rolling z: the R14 build fired 214 trembles ≈10%/day on USDT's normal ~10bp venue discount; scale-mode drops that to **3 real trembles (SVB 03-11 z=12.6, 03-12 z=3.4, a 2021-01-07 wobble), 0 blind**, ordinary fuzz z<1. Honestly scored now; promotion still gated on materiality-validation + an episode / serial-dependence overlay |
| — control_daylength | CONTROL: pipeline canary (no world) | 0 | 0 | — | — | — | control line, added 2026-07-30, registered R9 — day length at 51.4779N, 0.0E (sunrise-sunset.org). Set by orbital mechanics; nothing on Earth moves it, so any tremble here is measurement error by definition. obs_date is RECORDED, not inferred, so a one-day pipeline slip trips the ~1-minute canary tolerance even near the solstices |

## Backlog — ideas not yet built

Real guard, plausible free source, but NOT yet a collected line: each needs a
fetcher that has been probed returning real numbers before it can enter tier-2.
A to-do list, not a tier. (The round-8 restructure BUILT the three that were ready —
euro_hy_spread, fx_parallel_premium, hkma_aggr_balance — they are now tier-2 lines
above.)

| candidate | domain | hypothesis (guard → leak) | what it still needs |
|---|---|---|---|
| euro_fragmentation | financial (EU) | ECB defends cohesion → a widening periphery-core 10y spread leaks euro-breakup stress | a DAILY periphery-core spread source — the probed ECB SDMX IRS series is MONTHLY, which can't be a daily line; find the daily government-yield series |
| entsog_gas_flow | energy (EU) | pipelines keep gas flowing → a drop in cross-border physical flow leaks cutoff / sabotage | **source CONFIRMED keyless-live R20** — `.../api/v1/operationaldata?indicator=Physical Flow&periodType=day` returns real daily per-point flows (Fos LNG 129 GWh/d 2026-08-16, ~2d lag, no key); guard/cadence/reachability all pass. The ONLY remaining blocker is the AGGREGATION DESIGN: picking a non-diluting, non-frame-churning set of import points (dilution is a known failure mode). No longer sourcing-blocked — design-blocked |
| bgp_instability | infrastructure | networks keep routes stable → a surge in BGP withdrawals leaks outages, hijacks, war | the right global formulation — RIPEstat routing-status for one AS is not a global instability measure; a withdrawal/update-rate is exposed to sensor-inflation and low-count-integer failure modes and must be designed against them. **Re-probed R20, still blocked:** RIPEstat is keyless but `resource=` is mandatory on every routing endpoint → SINGLE-AS only; the one true global aggregate (Cloudflare Radar BGP) requires an `Authorization: Bearer` token even free-tier |
| cp_funding_spread | financial (US) | the Fed backstops the CP market → a CP-minus-funds spike leaks short-term funding stress | **construction RESOLVED R13, now cadence-BLOCKED** — `CPFF` IS exactly (3M AA-financial CP − fed funds), verified to the cent (2020-03-25 CPFF 2.43 = CP 2.53 − DFF 0.10; equivalently `RIFSPPFAAD90NB − DFF`), keyless daily, reachable (+240 bp in Mar-2020). BUT the term-CP leg is blank on a ~50%-and-rising, STRESS-CLUSTERED share of business days (2019 7% → 2024 56% → 2026 50%) and the ENTIRE 2023-03 SVB window is missing, so a daily differenced z would need a fill across exactly the gap carrying the signal; the only dense leg (overnight CP) is arbitrage-pinned and leaks nothing. **Scoring UNBLOCKED R15** (anchored scale-mode, ANCHOR=0, MATERIALITY≈15bp → alarm 45bp, Mar-2020 +240bp → z=16, each PRESENT day honest with no differencing-across-a-gap) — but scale-mode cannot conjure the missing days; still BLOCKED on SOURCING, a denser term-CP feed, not on scale |
| **border_wait** | trade / mobility (US land borders) | borders are staffed open for trade → a sustained spike in commercial-lane wait times, or an UNSCHEDULED closure of a 24h crossing, leaks blockade / coercion / crisis at a land chokepoint the maritime (PortWatch) and air (ADS-B) lines cannot see | **new R13, live-probed** — `bwt.cbp.gov/api/waittimes` returns real keyless JSON, 85 land ports (55 MX, 30 CA), 2026-08-14 snapshot Laredo 55m / Otay Mesa 40m / median 0 / max 55. Needs an AGGREGATION DESIGN before it is a line: restrict to COMMERCIAL lanes, git-scrape at a FIXED daily UTC hour so same-hour comparison cancels the commuter intraday cycle (cadence gate), and count only closures UNSCHEDULED against each port's `hours` field (raw Closed is dominated by nightly scheduled closures). Reach NATIONAL (US-MX/CA); no free historical backfill — build forward, zero baseline day 1. Global land-border non-find: WFP/HDX is a static location inventory, no free daily waits |
| crypto_capital_flight_premium | capital controls (per country) | a state defends an official FX rate / capital controls → residents buy USDT to move value out, so its local-currency P2P price trades ABOVE the official rate; a widening premium leaks accelerating flight — the same guard as cnh_cny / fx_parallel_premium, a faster mechanism | **probed R14 — guard real, cadence PASSES (a structural premium persists for weeks, unlike a transient depeg), Binance P2P adv/search is keyless + live.** BLOCKED because reachable ∩ orthogonal ∩ strong-guard ∩ clean-keyless-official-leg is nearly empty: ARS (+4%) and CNY (−1%, a banned gray discount) are redundant with existing lines, NGN/RUB return 0 ads (Binance banned/exited), TRY/EGP are weak-guard floats, and the one orthogonal hard-controlled case — Venezuela VES (+14% vs a near-parallel rate; the true BCV gap is 85%+) — has no keyless TRUE-official leg. Parked on official-leg sourcing + order-book aggregation, same shape as `usd_xccy_basis`. If ever built: a single USDT/VES line with a keyless BCV official leg, not China/Argentina, not Nigeria via Binance |
| usd_xccy_basis | financial plumbing (global) | central-bank USD swap lines cap the FX-swap-implied cost of borrowing dollars → a deeply negative 3M cross-currency basis leaks a dollar funding shortage, and swap-line drawings are the leaking hand | **new R13 — guard is arguably the cleanest defended equilibrium in the registry (it is literally what the swap lines defend); cadence + reachability pass (−150 to −200 bp in 2008, −80 to −140 bp Mar-2020).** BLOCKED on SOURCE: keyless daily basis is EXHAUSTED — FRED is spot-only (no forwards; `EURUSD3M*`/`XCCYBASIS` 404), OFR STFM carries no FX series, ECB spot-only, forward points paywalled, CME's daily basis index needs a self-service key. No free-pieces construction path (unlike cp_funding_spread — there are no forwards on FRED, do not re-attempt). **Re-probed 2026-08-19 (R20), STILL exhausted:** OFR STFM exposes only {FNYR, MMF, NYPD, REPO, TYLD} — no FX; FRED `XCCYBASIS3M` 403; cbonds + CME paywalled/keyed. Parked on sourcing like `eu_gas_storage`; downgrade to reject if no keyless forward-point feed ever appears |
| eu_gas_storage | energy (EU) | member states defend storage-fill trajectories → falling behind the injection path leaks supply cutoff | designed R11.1 as `eu_gas_storage_path` — weekly fill change MINUS the seasonal-normal weekly change, because the raw level is all season. **BUILD-READY, PROBED R23.1:** AGSI+ live with a registered `AGSI_KEY` (HTTP 200, EU aggregate daily fill 62.99% on 2026-08-23, injection/withdrawal/full% fields, ~2-day lag) — key set locally and as a CI Secret. This is the registry's **first LOAD-BEARING key** (no keyless fallback; the spoofed-User-Agent path this project won't ship is retired) — see the amended build criterion above. Remaining to build (its own round): the fetcher + a vendored 365-entry seasonal-normal table for the de-cycling |

### Context / confounder candidates (no guard by design — never counted)

Not in the Backlog above, because that table demands a real guard. These fail the guard gate
on purpose and can never be tier-1 or counted — they ride along only to help INTERPRET the
guarded lines (the `polar_temp` / `vix` disposition). Registered here when live-probed.

| candidate | source | role | disposition |
|---|---|---|---|
| **space_weather** | NOAA SWPC planetary **Kp** live + GFZ Potsdam definitive archive (keyless), 3-hourly → **daily MAX Kp** (the `grid_frequency` cadence pattern) | **confounder-subtractor for `gnss_interference` and `grid_frequency`**: when either trembles, Kp says whether a geomagnetic storm (exogenous) or a human hand (jamming / grid attack) drove it — GNSS tremble + calm Kp = real interference; both up = the sun. The sun is not a guarded equilibrium → **fails the guard gate**, context line only | **BUILT R22** — now a tier-2 context row above (seeded 2022-07-27→, 1,486 days, 39 storm trembles, 0 dark; May-2024 Kp-9 superstorm caught on both peak days). Failure mode: SWPC endpoint rot → `dark`, same as any fetch. Companion SWPC feeds also 200/keyless if ever wanted: F10.7 solar flux, GOES X-ray flares |

**NOAA sweep (R22):** the rest of NOAA is a guard-gate desert for this instrument. Its daily
keyless feeds are physical/natural (weather, CO2 at Mauna Loa, river gauges, seismic) — nature
defends no equilibrium a hidden hand can overpower, so they are context at best and mostly
redundant with `polar_temp`'s planetary-level role. **Space weather (SWPC) is the one NOAA feed
that adds orthogonal value**, and only as the confounder line above — not as a counted indicator.

### Rejected
| candidate | reason |
|---|---|
| tail_risk_market | fails the **guard gate** — prediction-market prices are a free-floating read with no defended equilibrium (Guard ~1). Interesting, but not a tension indicator. |
| marine_war_risk | R11 non-find: war-risk insurance premia are the perfect orthogonal guard signal and have **no free daily machine-readable source** — recorded so the search is not repeated. |
| sovereign_cds | R11 non-find: same shape — the guarded quantity is real, every daily source is paywalled. |
| onrrp_takeup | R20: fails the **guard gate**. Source is live/keyless/daily/fresh (FRED `RRPONTSYD`, $0.155B on 2026-08-18, drained from a $2.55T peak), but the Fed defends the RRP offering RATE (the floor), not the take-up QUANTITY — take-up is a market-determined residual cash-parking LEVEL with no guardian, so nothing leaks when it moves. The genuinely-guarded number in this plumbing is already collected as `sofr_iorb_spread`. |
| ais_dark_activity | R20 non-find + guard-questionable: vessels going dark (disabling AIS) would leak sanctions evasion / pre-conflict staging, but every source is key-gated (Global Fishing Watch Events = HTTP 401 without a free-registration token; SkyTruth/Datalastic/MarineTraffic/UN Global Platform all keyed or commercial), and a dark-ship count is an INFERRED detection, not a number a guardian defends. Same lineage as marine_war_risk. |
| tropical_cyclone (context) | R22: fails the **context-line admission bar on PAYOFF** — not on source, not on design (both are solved). SOURCES ARE EXCELLENT and verified keyless + all-basin, banked so the search is not repeated: **GDACS** `EVENTS4APP` GeoJSON (live, ~hourly, every active global TC with intensity, CORS-open) + **IBTrACS** v04r01 `since1980.list` CSV at NCEI (seed, dense 6-hourly best-track 1980→present, `last3years` as the 90-day window) — both close the NHC/CPHC West-Pacific gap. A non-diluting AGGREGATION also exists (port/hub-**gated worst-of**: the strongest storm within ~500 km of a fixed top-20 port/airspace-hub list — MAX-form kills dilution and frame-churn). It is REJECTED anyway because the two lines it would disambiguate are BOTH too diluted for a cyclone to move: **measured**, a full Shanghai+Ningbo closure moves port_throughput only **z=0.49**, and the ENTIRE E-Asia/Japan airspace going dark moves flights only **z=0.63** — both far under the \|z\|>3 alarm, because the storm's footprint (<1% of 2065 global ports; ~8% of a 4-region flight sample) is smaller than each line's own daily noise (Qn 245 calls; 199 aircraft). So a cyclone essentially never creates a weather-tremble to SUBTRACT — the "named ambiguity" the admission bar demands is empirically empty. This is the exact OPPOSITE of `space_weather`/gnss, where a geomagnetic storm degrades the WHOLE global GNSS at once, undiluted — which is why Kp cleared the bar and cyclones do not. (A workflow scouted this R22 and returned BUILD-READY on qualitative reasoning; the load-bearing "typhoon dips flights" claim was then MEASURED and failed. Sources are build-ready the day a globally-cyclone-sensitive line, or a per-hub sub-line — a Shanghai-only port line, a Japan-only flights line — exists to carry the signal undiluted; until then, do not build.) |

---

## Calibration log — round index

The full round-by-round reasoning lives in **[radar-log.md](radar-log.md)** (append-only).
One line per round below; open the log for the measured detail and the numbers behind any
decision. A new round is appended to `radar-log.md` and gets one line added here.

- **Round 1** — 2026-06-22 · seed
- **Round 1.1** — 2026-06-22 · cadence gate added
- **Round 2** — 2026-06-22 · re-probe + rethink
- **Round 3** — 2026-06-22 · tier-1 decided + 6-domain candidate hunt
- **Round 3.2** — 2026-06-22 · build
- **Round 3.3** — 2026-06-22 · tier-2 filled to 8/8
- **Round 4** — 2026-06-22 · apply the decided tier-1 = 4
- **Round 5** — 2026-06-22 · freshness rule; swap chokepoint → gnss in tier-1
- **Round 6** — 2026-07-10 · first live-signal review, 19 days of history
- **Round 6.1** — 2026-07-10 · methodology batch from the live-signal review
- **Round 6.2** — 2026-07-10 · the "feels" half, rendered
- **Round 7** — 2026-07-22 · the scale estimator; a miss, and a correction
- **Round 7.1** — 2026-07-22 · tier-1 swap; the status column; PortWatch rebuilt
- **Round 8** — 2026-07-23 · tier-2 red/blue divergence; cn_flights retired
- **Round 9** — 2026-08-03 · bookkeeping: the registry catches up with the instrument
- **Round 10** — 2026-08-04 · the calibration round: the bar, the floor, the rhythm, the drift
- **Round 11** — 2026-08-04 · the tier-1 composition review: held, and the set survives it
- **Round 11.1** — 2026-08-04 · the three candidates, probed properly; one built, two blocked
- **Round 12** — 2026-08-14 · the chokepoint blind spot: measured, sourced, and its fix located outside the scoring path
- **Round 13** — 2026-08-15 · metrics refresh + three candidates probed live; no tier move is due
- **Round 14** — 2026-08-15 · crypto, probed and built: one line ships, and its own replay names the wall
- **Round 15** — 2026-08-16 · the materiality wall, answered: anchored scale-mode, built into the scorer
- **Round 16** — 2026-08-16 · the registry corrects its own arithmetic, and the counts get a source
- **Round 17** — 2026-08-16 · the second headline: the level layer becomes a counted probe
- **Round 18** — 2026-08-16 · a status the dark column always owed: market closure, split from failure
- **Round 19** — 2026-08-16 · housekeeping: the log moves out to radar-log.md, and the one dead file leaves
- **Round 20** — 2026-08-19 · the possibilities sweep: six probes across domains; fed_srf confirmed build-ready then BUILT (tier 2, seeded to 2021, 3 trembles), onrrp + ais_dark rejected, entsog source confirmed keyless, bgp + xccy still blocked
- **Round 21** — 2026-08-20 · the 5S round: whole-repo audit (waste/drift/strategic) drives registry corrections + a Pending-reviews block; port slide attributed (real, broad-based, revision artifact refuted <1%); fed_srf first live seam clean; no tier moves
- **Round 22** — 2026-08-21 · the credit-redundancy + space sweep, then a build: the "orthogonal to US HY" claims on em_corp_oas (+0.80) and euro_hy_spread (+0.74) MEASURED FALSE — one global credit factor, a single-credit-slot bar registered; NOAA sweep = guard-gate desert except space weather; **space_weather BUILT** (tier-2 context, daily max Kp, SWPC live + GFZ seed to 2022, 1,486 days / 39 storm trembles, a confounder-subtractor for gnss/grid — Gannon Kp-9 superstorm caught); the **context-line admission bar formalized** (name the ambiguity you resolve, or you're decoration — three roles); **tropical_cyclone REJECTED on measured payoff** (sources excellent & banked — GDACS+IBTrACS keyless global — but a full Shanghai+Ningbo closure moves port z=0.49, all-Japan airspace dark moves flights z=0.63, both under alarm: the confounder has nothing to subtract); no tier moves among counted lines
- **Round 23** — 2026-08-25 · the false-alarm round: the 2026-08-24 net_outages spike (12 countries, z=4.69, a tier-1 alarm) adjudicated by a 5-agent probe as a FALSE ALARM — an IODA active-probing common-mode artifact (10 synced ~40-min ping events across 4 ocean basins, no BGP, settles 12→4 on re-query), triple-refuted (timing/infra/web); a guard gap opened (the ≥100-country sweep guard misses a 12-country synchronized-onset sibling); closed-status tripwire result (Sun closed ✓, Sat re-scored Friday's close); cnh_cny still n=48<60; flights review holds to 08-31; no tier moves
- **Round 23.1** — 2026-08-25 · settle + last-mile tightening: net_outages SETTLED to a completed D-1 22:00Z window (validated: 08-24 settles 12→4, 7 historical alarms reproduce byte-exact incl. small; monitor_swept untouched, replay 0-divergence); the reachability gate AMENDED (baseline-relative in a young calm record → cnh_cny passes on a cited reference regime); eu_gas_storage BUILD-READY-probed (AGSI+ live, the registry's first load-bearing key); two integrity tests (docs/data subset-gate, LINES-invariant gate); covBlind + round-index-order fixes; no tier moves. **[claim corrected R23.2]**
- **Round 23.2** — 2026-08-26 · the settle claim, corrected by its own tripwire: the reconciliation tool's first-run seam audit found settle STABILIZES the count but does NOT filter the artifact — the 08-24 twelve-country synchronized-onset cluster lives, stably, in the settled 08-23 window (the same 12 countries), so a future artifact of this shape would still alarm on its own date. Settle kept (count-stability + seed-alignment are real; the trailing window was genuinely unstable); the synchronized-onset class stays DETECT-AND-ADJUDICATE via the tripwire + R23 playbook; net_outages not demoted; no tier moves
