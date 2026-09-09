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
in the registry. Allowance opened R23.1 for `AGSI_KEY`; no built line uses one yet, since
eu_gas_storage was parked R24 on reachability.) Collection is nearly free in
a git-scraping architecture; the history you don't collect is the expensive thing.

The bar to ENTER tier-2 is real, because every collected line is a survivability
liability (one more source that can rot, one more fetch that can flake the daily
run): (1) it passes the guard + cadence gates, or is an explicit never-counted
CONTEXT line; (2) it has a fetcher that has been PROBED returning real numbers, not
just a plausible-looking source; (3) its failure mode is named. Ideas that don't yet
meet (2) are a plain **Backlog** list below — a to-do, not a tier.

The only funnel is tier-1 promotion: a tier-2 line earns a primary slot over ≥60
scored readings, gated on orthogonality and the freshness rule.

---

## Tier 1 — primary  (4 / 4 · open slot filled by fed_srf_takeup R30 · reviewed R11)

The displayed, counted instruments — distinct domains, all four slots filled.
Decided round 3, applied round 4 (slot 4 = cnh_cny, user-decided); the communications
slot ran net_outages until R28 demoted it to tier-2 (condition (c) tripped — see Known
limit 7), leaving that slot empty until R30 filled the roster back to 4/4 with
fed_srf_takeup — a 4th FINANCIAL line (dollar-plumbing), its two standing gates
cleared — rather than a comms line, because the sole comms candidate was still unbuilt.
Communications now rides tier-2 as net_bgp_withdrawal, the standing candidate for a
future slot. Per-line reliability/reach metrics are generated — see
[radar-metrics.md](radar-metrics.md).

| indicator | domain | Lev | Guard | Reach | Orthog | status |
|---|---|:--:|:--:|:--:|:--:|---|
| flights | airspace (4 regions; only US alarm-reachable) | 3 | 3 | 2 | ≤0.08 (n≈50, R21) | ⚠️ **RETAINED at the pre-committed review, R25** — the 2026-08-31 review ran (de-cycling engaged on schedule at window-row 71): replayed episode-rate Wilson 95% LB = 0.89% < 2% bar, and the 08-28 alarm is ADJUDICATED (not just adjudicable) by the R11-named intraday sampler — 08-28T23:22Z read 1660 at baseline hour while the daily 05:54Z snapshot read 1035; the drop is a CI-queue sample-hour artifact, not airspace. Neither demotion condition met → retained. Both of flights' alarms are now artifacts; the sample-hour confound is STRUCTURAL (snapshot line, GH-Actions queue-drifted sample hour, weekday de-cycling is orthogonal to it). Fix SHIPPED R25.1 (re-review pending) |
| credit_spread | financial (US→global) | 3 | 3 | 3 | ≤0.08 (n=788, R21) | ✅ global bellwether; alarm at the 45th pctile of its 788-day record |
| cnh_cny | capital controls (China) | 2 | 3 | — | ≤0.08 (n=42 vs credit_spread / 57 vs flights, R29) | ✅ slot 4 (user-decided); orthogonality RE-MEASURED R29 — |max Pearson| +0.076 vs credit_spread (n=42), −0.036 vs flights: the most orthogonal tier-1 line. Reach RE-MEASURED R29 — the UP alarm bar sits at ≈223 pips, +80 above the all-time record high of 143 (unreachable WITHIN this young calm record; baseline-relative; reference regime intact). All five |z|>3 events are benign DOWN trembles (07-02/07-07/07-25/08-10/08-26, offshore yuan stronger) — 0 UP-trembles in its scored history (57 at R29, 2026-09-08). RETAINED on a WEAKER external-reference-regime standard than credit_spread/flights: retention rests entirely on a real, CITED reference regime — the 2015-16 RMB devaluation / capital-flight episode (dated citation in the reachability gate below) — which is the SAME reachability standard net_outages FAILED at R28, and cnh_cny passes only because its regime is a documented, sourced world event where net_outages' 8 largest adjudicated to none. Still <60 scored (see radar-metrics.md for the live count), insufficient to adjudicate (Known limit 4: below 60, defer); refresh at the maturity review (*4 darks are weekend/leg-timing rejections, not failures; the 08-16 dark ran hours before R18's closed status landed — weekends read `closed` from the first post-R18 weekend, 08-22/23, on) |
| fed_srf_takeup | financial plumbing (US→global) | 3 | 3 | 3 | \|max Pearson\| 0.008 vs credit_spread (n=750), 0.10 vs flights (n=45), 0.10 vs cnh_cny (n=40) — shared-date pairs, R30; the most orthogonal candidate (1274 scored overall) | ✅ **PROMOTED R30** — fills the roster back to 4/4 (the open communications slot net_outages vacated at R28, repurposed for a financial line). Daily Standing Repo Facility take-up ($m), keyless NY Fed markets API, anchored scale-mode (ANCHOR=0, MATERIALITY=$10bn → alarm $30bn). Both standing promotion gates CLEARED on the data (gate-work: R30). **R20 de-cycling debt — CLEARS:** structurally MOOT for anchored scoring (normalize.robust_z's materiality branch reads only today, never the rolling window, so month/quarter-end baseline-warping cannot move the z), and the month-turn friction band tops at $26.0bn (z 2.60), $4.0bn under the $30bn alarm — routine calendar ops never approach it. **R15 anchored-scale gates — CLEAR:** MATERIALITY validated (routine median $0 / p90 $10m / p95 $100m, max-routine z 2.60, a clean 0.45z empty gap to the lowest fire z 3.05; 85.4% of nonzero days <$100m dust at z<0.01), and the 3 alarms are 3 DISTINCT single-day episodes (2025-10-31 z 5.04, 2025-12-31 z 7.46 record, 2026-02-17 z 3.05; 61/48 days apart, lag-1 autocorr 0.406, no adjacent fires — 3 trembling days = 3 episodes 1:1, the iid null is not threatened). DOMAIN DECISION: a 4th FINANCIAL line accepted (airspace + credit + capital-controls + dollar-plumbing) because the sole comms candidate net_bgp_withdrawal was unbuilt at the decision; comms is now the tier-2 BGP line, the standing candidate for a future slot |

## Tier 2 — collected  (14 candidates + 5 context + 1 control · no cap)

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

Per-line reliability/reach metrics are generated — see [radar-metrics.md](radar-metrics.md).

| indicator | domain | Lev | Guard | Reach | note |
|---|---|:--:|:--:|:--:|---|
| port_throughput | trade (global) | 3 | 3 | 3 | ~4729 global port calls/day (2065 ports) |
| chokepoint_breadth | trade (global) | 3 | 3 | 3 | 28 straits, ~1810/day (Hormuz blockaded) — strong, but PortWatch lags ~10 days: too stale to display live. R12: the SUM is structurally blind to 1–2 small straits going silent (a full Hormuz+Kerch closure = 84 transits = 1.04z, 35% to alarm) — the level layer, not this line, carries that signal |
| sofr_iorb_spread | financial plumbing | 3 | 3 | 3 | SOFR−IORB ~−2bps (calm) — keyless FRED |
| em_corp_oas | EM financial (global) | 3 | 2 | 3 | EM corp OAS ~1.38pp. R22 MEASURES the standing "orthogonal to US HY" claim FALSE: |max corr| vs the live tier-1 set = **+0.80 vs credit_spread** (n=789) — the same global credit factor, not an orthogonal domain. Stays tier-2 for breadth/confirmation; NOT a tier-1 promotion candidate (would fail the orthogonality gate and break the headline's iid null — see Known limits #3) |
| net_outages | communications (global) | 2 | 3 | 3 | **DEMOTED R28** from tier-1 (was CONFIRMED R11 BY RATE, held under a named weaker standard from R11; see Known limit 7). Condition (c) of the R27 reach standard tripped: the 8 largest readings (45, 44, 41, 40, 30, 30, 29, 28) were adjudicated under the R23 playbook — a live IODA re-query plus a multi-source attribution search (data/archive/ioda_8largest_requery_2026-09-08.csv) — and none survives as a cited world event. Seven are common-mode active-probing artifacts (large synchronized ping-slash24-only batches, sparse corroboration); 2024-10-03 (44 countries, a 38-country synchronized batch 29 of it ping-only at 76% — a near-miss just under the 80% common-mode share bar — 13/44 corroborated) is the one reading the classifier does not lean common-mode, corroborated but unattributable (no cited event, geographically incoherent, chronic-contaminated, single-day — corroboration is a measurement, not a reference regime). The line never reached its own alarm bar on the world from a cited reference, the reachability standard cnh_cny was held to at R13/R23.1. Keeps collecting as a watchlist candidate (history + z-score accumulate); the tier-1 global-communications slot is left empty and disclosed. See the 2026-09-08 DEMOTED annotation |
| net_bgp_withdrawal | communications (global) | 2 | 3 | 3 | **BUILT R30** into the empty communications slot as the route-WITHDRAWAL candidate the R29 probe validated (evidence data/archive/bgp_probe_2026-09-08.csv). Passive-BGP worst-of route visibility: a size-floored 153-country watch-list (median daily-median visible-/24 ≥ 512), each country's daily-min ÷ its 28-day rolling-median baseline, worst-of across the list, scored DOWN in anchored scale-mode (ANCHOR=1.0, MATERIALITY=0.10 → alarm at fraction 0.70, below the ~0.75 structural benign floor). Fires strongly on the cited events — Syria 2022-05-30 frac 0.031 → z−9.69, Sudan 2023-04-24 frac 0.314 → z−6.86 — and is structurally immune to the active-probing common-mode that demoted net_outages (BGP is a passive read of route announcements, no probe vantage to lose). Orthogonal (probe |max Pearson| 0.167 vs flights). Enters at tier-2 and earns tier-1 over the ≥60-scored funnel, NOT by declaration. **BASE-RATE CALIBRATION (pre-promotion item):** the anchored bar (frac<0.70) fires ~21% of the seed (352/1673 days), NOT a bump-only line — because it flags CHRONIC route-withdrawal states each day: Sudan 61 / Iraq 58 / Syria 51 (≈48% of runs), Cameroon 40; by year 6%/25%/34%/25%/10%. The probe's rolling-Qn read ~5% on the recent calm 2026 window (matched by the anchored bar's ~6.4% on 2026-03..09), so the "ordinary days read a bump, not a tremble" claim holds only on a calm window, not the full seed. Before any tier-1 promotion this needs a calibration pass — a sustained-DURATION variant, or a re-set materiality / explicit chronic-state handling — so the count reflects new withdrawals, not standing ones. **DISCLOSURE (route-WITHDRAWAL only, the gnss "effective reach 1" precedent):** BGP measures route ANNOUNCEMENT, not reachability — it catches shutdowns/cable-cuts/transit failures that WITHDRAW prefixes but MISSES access-layer blackouts where routes stay announced. Gaza 2023-10 total blackout read only ~−4% (PS frac ~0.96, z≈−0.4, never near the alarm) — the ASes kept announcing into the dark. It does not close the slot's full "is the country reachable" question, only the withdrawal subclass |
| gnss_interference | navigation/EW (global) | 3 | 3 | 1* | demoted R7 — *effective* reach is 1, not 3: one worldwide ratio has no regional sensitivity. Seeded R9 to 2022-07 (1,466 rows): it fires 49 alarm-direction trembles in 1,452 scored days, and the Gulf window peaks at z=2.87 — under-powered, not motionless (see the R9 corrections). Its global floor rose 1.64x in four years with no single day ever unusual |
| capital_premium | capital controls (Korea) | 2 | 3 | 1 | demoted R4 (redundant with China); kept on watch |
| grid_frequency | infrastructure (Nordic) | 2 | 3 | 1 | demoted R4 (regional); kept on watch — may re-challenge on orthogonality |
| euro_hy_spread | financial (EU) | 3 | 2 | 2 | built R8 — ICE BofA Euro HY OAS ~2.5pp, keyless FRED. R22: the "different central bank → orthogonal" intuition is MEASURED FALSE — |max corr| = **+0.74 vs credit_spread** (n=783), and +0.86 vs em_corp_oas: US HY, EM corp and Euro HY are ONE global credit factor at daily z. Tier-2 for breadth; not a tier-1 candidate (redundant with the credit slot) |
| fx_parallel_premium | capital controls (AR) | 2 | 3 | 2 | built R8 — Argentina blue-vs-official FX premium, keyless dolarapi; a hard-controlled regime, distinct from cnh_cny/kimchi |
| hkma_aggr_balance | capital (HK) | 3 | 3 | 2 | built R8 — HK currency-board aggregate balance, keyless HKMA API; falls as the peg is defended under outflow. **FLAGGED R29 before it counts as a promotion candidate:** 16 dark days scattered across 07-31→09-07 (not contiguous), reliability 0.871 = scored/(scored+dark) = 108/124 (radar-metrics.md's read/rows definition gives 0.888 = 127/143; worst-in-set either way, next-worst cnh 0.949), and |z|>3 on 14 of 108 days (10 flagged trembles, all benign-direction/up — hkma alarms down, so these count as no disorder), z up to 65 (max 03-18) driven by discrete step-jumps — evaluate moving it from rolling z to anchored/scale scoring like the other discrete-step financial lines. It crosses 60 scored (108) and is orthogonal, but the worst-in-set reliability plus a mis-calibrated over-firing scorer disqualify it now |
| — gdelt | feel: conflict share (global) | 1 | 0 | 3 | contrast line (guard gate) — v2 full-day aggregation, not a candidate slot |
| — gdelt_tone | feel: news tone (global) | 1 | 0 | 3 | contrast line — full-day average tone, same pass as gdelt |
| — vix | feel: priced fear (global) | 1 | 0 | 3 | contrast line — keyless FRED VIXCLS, seeded 180d from archive |
| — polar_temp | context: planetary level (Arctic 80N) | 1 | 0 | 2 | context line, provisional-watch — DMI +80N daily anomaly vs the 1958-2002 normal (keyless, ~1d lag). A LEVEL read, not a tension indicator; the long baseline is vendored in core/arctic_clim.py. Seeded R9 to 2019 (2,740 rows): 384 warm trembles vs 4 cold — the asymmetry is the warming |
| — space_weather | context: geomagnetic storm (global) | 1 | 0 | 3 | **built R22** — daily MAX planetary **Kp** index, rolling z (QUANTUM=1/3), keyless: NOAA SWPC live + GFZ Potsdam definitive archive, seeded to 2022-07-27 to ALIGN with gnss_interference. A CONTEXT line (fails guard gate — the Sun is the exogenous force, not a guarded equilibrium): never counted, never promotable. Its ROLE is a **confounder-subtractor** for gnss_interference + grid_frequency — a storm degrades GNSS worldwide and stresses grids, the same signatures a human hand leaves; Kp says which. Validated: the up-trembles are exactly the real G1-G5 storms — the May-2024 Gannon superstorm (Kp 9, strongest in 20y) fires on both peak days, as do the Oct-2024 and Mar-2024 storms |
| tga_days_cash | fiscal plumbing (US) | 3 | 3 | 2 | built R11.1 — Treasury cash buffer in DAYS OF ITS OWN OUTFLOWS (closing TGA balance / trailing-20-business-day mean withdrawal), keyless Treasury Fiscal Data, T+1. The guard is visible not asserted: median 5.3 business days against Treasury's announced ~1-week policy, and the June-2023 X-date reads 0.21 days |
| stablecoin_peg | crypto dollar peg (global) | 3 | 3 | 3 | **built R14, scored R15** — worst-of-{USDC,USDT} deviation-from-$1 in bp, settled daily CLOSE, keyless Bitstamp OHLC, seeded 2020-10→now. Guard clean; cadence-reject OVERTURNED (SVB was a multi-day close-visible depeg, USDC close $0.9685). Now scored in **anchored scale-mode** (ANCHOR=0, MATERIALITY=25bp → alarm at 75bp) instead of the rolling z: the R14 build fired 214 trembles ≈10%/day on USDT's normal ~10bp venue discount; scale-mode drops that to **3 real trembles (SVB 03-11 z=12.6, 03-12 z=3.4, a 2021-01-07 wobble), 0 blind**, ordinary fuzz z<1. Honestly scored now; promotion still gated on materiality-validation + an episode / serial-dependence overlay |
| — control_daylength | CONTROL: pipeline canary (no world) | 0 | 0 | — | control line, added 2026-07-30, registered R9 — day length at 51.4779N, 0.0E (sunrise-sunset.org). Set by orbital mechanics; nothing on Earth moves it, so any tremble here is measurement error by definition. obs_date is RECORDED, not inferred, so a one-day pipeline slip trips the ~1-minute canary tolerance even near the solstices |

## Backlog — ideas not yet built

Real guard, plausible free source, but NOT yet a collected line: each needs a
fetcher that has been probed returning real numbers before it can enter tier-2.
A to-do list, not a tier. (The round-8 restructure BUILT the three that were ready —
euro_hy_spread, fx_parallel_premium, hkma_aggr_balance — they are now tier-2 lines
above. R30 BUILT the R29-probed bgp_instability idea as net_bgp_withdrawal, now a
tier-2 line above.)

| candidate | domain | hypothesis (guard → leak) | what it still needs |
|---|---|---|---|
| third ADS-B provider (flights redundancy) | airspace — same guard as tier-1 `flights` (airlines defend on-time profit → closed airspace, weather, pandemic leaks) | not a new domain — a REDUNDANCY item for the existing `flights` line. `airplanes.live` was removed from `core/adsb.py` PROVIDERS 2026-09-08: it had returned HTTP 403 since before 2026-08-12 (an access-policy block — the response body asks for a project description, and every User-Agent fails, so this is not the keyless-header case a workaround could restore). `flights` still runs under the max-of-providers rule on the two survivors (`adsb.fi`, `adsb.lol`), both answering; removing the third provider moved the region max by only ~1-2%, inside noise. But two providers is one fewer corroborating source than the line shipped with | find and probe a third keyless, un-gated community ADS-B aggregator (`adsb.one` is the obvious first candidate; any host must serve live JSON shaped like `{"ac": [...]}` with `alt_baro`, no key, no access-policy gate) before it is added back to `core/adsb.py` PROVIDERS. **R29:** the two survivors adsb.fi (900) and adsb.lol (897) are <1% apart with 0 dark/79, and are accepted for now (the R28 health audit alarms on a silent death). The keyless-mirror search is NOT repeated — adsb.one returns Cloudflare 403, airplanes.live an access-policy 403, adsbiq a feeder 403/429, and OpenSky is anonymous-deprecated with GH-Actions shared-IP unreliability. Cheap future re-probe: is OpenSky /states/all reliable from GH-Actions IPs post-2026-03 OAuth2? (untested since) |
| euro_fragmentation | financial (EU) | ECB defends cohesion → a widening periphery-core 10y spread leaks euro-breakup stress | a DAILY periphery-core spread source — the probed ECB SDMX IRS series is MONTHLY, which can't be a daily line; find the daily government-yield series |
| entsog_gas_flow | energy (EU) | pipelines keep gas flowing → a drop in cross-border physical flow leaks cutoff / sabotage | **source CONFIRMED keyless-live R20** — `.../api/v1/operationaldata?indicator=Physical Flow&periodType=day` returns real daily per-point flows (Fos LNG 129 GWh/d 2026-08-16, ~2d lag, no key); guard/cadence/reachability all pass. The ONLY remaining blocker is the AGGREGATION DESIGN: picking a non-diluting, non-frame-churning set of import points (dilution is a known failure mode). No longer sourcing-blocked — design-blocked |
| cp_funding_spread | financial (US) | the Fed backstops the CP market → a CP-minus-funds spike leaks short-term funding stress | **construction RESOLVED R13, now cadence-BLOCKED** — `CPFF` IS exactly (3M AA-financial CP − fed funds), verified to the cent (2020-03-25 CPFF 2.43 = CP 2.53 − DFF 0.10; equivalently `RIFSPPFAAD90NB − DFF`), keyless daily, reachable (+240 bp in Mar-2020). BUT the term-CP leg is blank on a ~50%-and-rising, STRESS-CLUSTERED share of business days (2019 7% → 2024 56% → 2026 50%) and the ENTIRE 2023-03 SVB window is missing, so a daily differenced z would need a fill across exactly the gap carrying the signal; the only dense leg (overnight CP) is arbitrage-pinned and leaks nothing. **Scoring UNBLOCKED R15** (anchored scale-mode, ANCHOR=0, MATERIALITY≈15bp → alarm 45bp, Mar-2020 +240bp → z=16, each PRESENT day honest with no differencing-across-a-gap) — but scale-mode cannot conjure the missing days; still BLOCKED on SOURCING, a denser term-CP feed, not on scale |
| **border_wait** | trade / mobility (US land borders) | borders are staffed open for trade → a sustained spike in commercial-lane wait times, or an UNSCHEDULED closure of a 24h crossing, leaks blockade / coercion / crisis at a land chokepoint the maritime (PortWatch) and air (ADS-B) lines cannot see | **new R13, live-probed** — `bwt.cbp.gov/api/waittimes` returns real keyless JSON, 85 land ports (55 MX, 30 CA), 2026-08-14 snapshot Laredo 55m / Otay Mesa 40m / median 0 / max 55. Needs an AGGREGATION DESIGN before it is a line: restrict to COMMERCIAL lanes, git-scrape at a FIXED daily UTC hour so same-hour comparison cancels the commuter intraday cycle (cadence gate), and count only closures UNSCHEDULED against each port's `hours` field (raw Closed is dominated by nightly scheduled closures). Reach NATIONAL (US-MX/CA); no free historical backfill — build forward, zero baseline day 1. Global land-border non-find: WFP/HDX is a static location inventory, no free daily waits |
| crypto_capital_flight_premium | capital controls (per country) | a state defends an official FX rate / capital controls → residents buy USDT to move value out, so its local-currency P2P price trades ABOVE the official rate; a widening premium leaks accelerating flight — the same guard as cnh_cny / fx_parallel_premium, a faster mechanism | **probed R14 — guard real, cadence PASSES (a structural premium persists for weeks, unlike a transient depeg), Binance P2P adv/search is keyless + live.** BLOCKED because reachable ∩ orthogonal ∩ strong-guard ∩ clean-keyless-official-leg is nearly empty: ARS (+4%) and CNY (−1%, a banned gray discount) are redundant with existing lines, NGN/RUB return 0 ads (Binance banned/exited), TRY/EGP are weak-guard floats, and the one orthogonal hard-controlled case — Venezuela VES (+14% vs a near-parallel rate; the true BCV gap is 85%+) — has no keyless TRUE-official leg. Parked on official-leg sourcing + order-book aggregation, same shape as `usd_xccy_basis`. If ever built: a single USDT/VES line with a keyless BCV official leg, not China/Argentina, not Nigeria via Binance |
| usd_xccy_basis | financial plumbing (global) | central-bank USD swap lines cap the FX-swap-implied cost of borrowing dollars → a deeply negative 3M cross-currency basis leaks a dollar funding shortage, and swap-line drawings are the leaking hand | **new R13 — guard is arguably the cleanest defended equilibrium in the registry (it is literally what the swap lines defend); cadence + reachability pass (−150 to −200 bp in 2008, −80 to −140 bp Mar-2020).** BLOCKED on SOURCE: keyless daily basis is EXHAUSTED — FRED is spot-only (no forwards; `EURUSD3M*`/`XCCYBASIS` 404), OFR STFM carries no FX series, ECB spot-only, forward points paywalled, CME's daily basis index needs a self-service key. No free-pieces construction path (unlike cp_funding_spread — there are no forwards on FRED, do not re-attempt). **Re-probed 2026-08-19 (R20), STILL exhausted:** OFR STFM exposes only {FNYR, MMF, NYPD, REPO, TYLD} — no FX; FRED `XCCYBASIS3M` 403; cbonds + CME paywalled/keyed. **Re-probed 2026-09-09 (R30), STILL exhausted:** FRED `XCCYBASIS3M` now 404 (still no series), OFR STFM mnemonics list carries zero xccy/basis/fx-swap/forward series (still {FNYR, MMF, NYPD, REPO, TYLD}); cadence rolled to R40. Parked on sourcing like `eu_gas_storage`; downgrade to reject if no keyless forward-point feed ever appears |
| eu_gas_storage | energy (EU) | member states defend storage-fill trajectories → falling behind the injection path leaks supply cutoff | **SOURCE PROBED R23.1 / PARKED R24 on the reachability gate.** AGSI+ is live with a registered `AGSI_KEY` (HTTP 200, EU daily fill, ~2-day lag; key banked locally + as a CI Secret — would be the registry's first load-bearing key). But the natural metric — fill DEVIATION from the seasonal-normal full% (day-of-year median, 2016-2026, 3,889 days) — FAILS reachability: the deviation's normal spread is ±14pp (p5 −14.4, p95 +22.2) while the worst downside in ten years is only ~−16pp, so no MATERIALITY yields an alarm both reachable (≤ −16pp) AND clean (a −3z alarm lands at ~−33pp, never observed). Cause: the storage LEVEL is a defended-holds quantity — the 2022 war-onset crisis dented fill only −9pp in March and refilled to ~95% by Nov via record prices + demand destruction, so the stress showed in PRICE, not level; the guard holds. The seasonal baseline is also regime-confounded (post-2022 90%-by-Nov mandate lifted 2023-25 fill). LIVE NOTE: EU 2026 sits at −15pp (63.3% vs a 78.4% normal), the ten-year deviation low — genuinely running behind, worth a dashboard/briefing mention. TO UN-PARK: a cleaner guard — deviation from the EU regulatory TARGET PATH (the actual defended trajectory: intermediate fill mandates, 90% by Nov 1), not a blended seasonal median. Same shape as the tropical_cyclone finding: source excellent, natural metric gated |

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

**Instrument-hygiene follow-ups opened R28** — three items the net_outages demotion surfaced,
recorded so the search is not repeated. (1) **DONE R29 (C2)** — a lint now binds every tier-1
line-count literal in the public copy to the source (the `docs/index.html` `const T` block + the
README claims above its machine-checked table), so a future hard-coded count cannot drift from
`TIER1`; `countColor`'s separate 4-step colour ramp (`n>=3`) is deliberately out of that scope.
(2) **DONE R29 (C1)** — the dark-count banner threshold is now the TIER1.length-derived majority
rule `darkCount*2 > TIER1.length` (2-of-3 today, reproducing the historical 3-of-5 / 3-of-4), a
chosen semantic (majority, not all-dark). (3) **per-line STABLE_SINCE map — DEFERRED R29 (C3), no
code.** Four facts are banked: (a) `scoring_attrs` omits TIER, so per-line replay is tier-independent
(527 rows, 0 divergence since 08-17); (b) only the summary re-derivation loop (replay.py :134 filter
→ :175-192) is tier-sensitive; (c) the lighter fix is a separate `TIER_CHANGED_SINCE` used only at
the summary guard, with `STABLE_SINCE` reverted and its ledger block ordering kept per lint_ssot T6;
(d) DEFERRED because the restored ~504-row per-line window is daily-checked-while-recent,
tier-independent, and frozen — zero detection benefit at ~22× the daily `--check` cost.

---

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
  own record is too calm to contain its alarm. Applied to cnh_cny: its UP alarm bar sits at
  ≈223 pips, +80 above the all-time record high of 143 (unreachable WITHIN the record), but a
  real capital-flight regime has blown far past it — **the 2015-16 RMB devaluation / capital-flight
  episode** (PBOC surprise devaluation of the onshore fix 2015-08-11, the first since 1994; the
  offshore squeeze of 2016-01-12 drove overnight CNH HIBOR to a record ~66-67%, punishing yuan
  short-sellers; the CNH-CNY spread ran to the hundreds of pips, multiples of the ~223-pip alarm
  bar) — so it passes. Sources (cited, not assumed, per this very rule): BIS Working Paper No. 446
  "One currency, two markets: the renminbi's growing influence", and CNBC 2016-01-12 for the record
  overnight CNH HIBOR spike. This is the same reachability standard net_outages FAILED at R28 (its 8
  largest readings adjudicated to no cited event); cnh_cny passes only because its reference regime
  is a documented, sourced world event. The reference regime must be cited, not assumed, and is
  re-checked at the line's maturity review (n=57 <60 as of R29).

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
5. **A re-stamped weekend quote is not a session.** A live FX vendor can re-print both
   legs of a frozen weekend quote with a fresh timestamp inside the closed window, and a
   fetcher that reads the raw stamp names a trading session that never happened. cnh_cny
   hit this class: Yahoo re-stamps its frozen Saturday/Sunday legs, so `obs_date =
   min(cnh_t, cny_t)` minted a fresh dedup key every China-Monday collection even though
   no onshore session had opened. Five Monday rows scored as new observations under the
   raw-stamp rule — 2026-07-27, 08-03, 08-10, 08-17, 08-24 — and one of them (08-10, z
   −3.213, benign DOWN, uncounted) is a scored artifact of the defect rather than a
   market move (`data/annotations.csv`, 2026-09-02 method row). Closed going forward by
   a session-snap fix (`fetchers/cnh_cny.py`'s `_session_date()`: a Sat/Sun stamp maps
   to its Friday session); the five rows stand forward-only, and the class is a standing
   risk for any other weekend-closed spread line this registry ever adds.
6. **A published row is not the same as a distinct observation.** `scored(n)` counts
   every row a fetcher judged, but a row is not a new look at the world if its
   `obs_date` repeats an already-scored `obs_date`, its legs are byte-identical to the
   immediately preceding row, or its stamps fall inside a weekend — the rule behind the
   session-snap fix recorded in `data/annotations.csv` (2026-09-02, cnh_cny, method:
   "SESSION SNAP (Round 26)"). Applied to cnh_cny (2026-09-04): 8 of its 54 scored rows
   are non-distinct by this rule — the 5 weekend-restamped Mondays of limit 5 above,
   plus 3 pre-fix Sunday rows byte-identical to their preceding Saturday (2026-07-05,
   07-12, 07-19) — so the honest distinct-observation count is 46, not 54.
   `tools/pending.py`'s `distinct_scored` predicate only dedups by `obs_date`, which
   catches none of these 8 (each minted its own unique `obs_date`, or predates
   `obs_date` entirely), so it currently equals raw `scored` and must not be read as
   already implementing this rule; a maturity gate keyed to it now reads `scored`, not
   `distinct_scored`, until the predicate implements the rule in full.
7. **net_outages held a tier-1 slot under a weaker standard than the registry's own
   demotion clauses — until R28 demoted it on that standard's own reach condition.**
   Its R11 confirmation was by episode rate on a 4.5-year seed whose episodes were
   never individually attributed; the 2026-09-06 corroboration probe re-labeled 16 of
   its 39 episodes — 7 of its 8 largest readings — as leaning IODA active-probing
   common-mode, the class behind all three of its live tier-1 alarms, and measured
   that no corroborated exit exists; the one named world event in its seed (the
   2025-04-28 Iberian blackout) read sub-alarm. It was kept, at first, because it was
   the only global communications-domain candidate and an empty disclosed slot was
   judged worse (2026-07-22) — under an adjudication clause with deadlines rather than
   the other tier-1 lines' rate-and-fix clauses, because the line had no fix and no
   exit path and a rate bar diluted by a 1,600-day seed cannot fire on a class that
   recurs monthly. R28 discharged the reach deadline (condition (c)): the 8 largest
   readings were adjudicated under the R23 playbook (a live IODA re-query plus a
   multi-source attribution search, data/archive/ioda_8largest_requery_2026-09-08.csv)
   and none survives as a cited world event — seven are common-mode artifacts, and
   2024-10-03 (44 countries, a 38-country synchronized batch 29 of it ping-only at 76%,
   a near-miss just under the 80% common-mode share bar; 13/44 corroborated) is
   corroborated but unattributable. The 2023-09-06 reading is the one with a real same-day
   event — a Cogent Communications backbone outage — yet its 22-country synchronized batch
   is predominantly Caribbean/Pacific/South-Asian island and small-state probes with no coherent Cogent
   footprint, and the GOVERNING reading holds regardless: a single shared-transit-provider
   fan-out is not the world reaching the alarm bar, so 2023-09-06 fails condition (c) on the
   standard's meaning even if a paywalled source names 17 Cogent-downstream countries. So
   net_outages is now tier-2, the communications slot left empty and disclosed (roster filled R30
   by a financial line, fed_srf_takeup; communications remains UNCOUNTED, now covered by the tier-2
   net_bgp_withdrawal candidate). The weakness is resolved by demotion, the empty-slot cost the
   registry pre-committed to at promotion, not by copying the standard.

### Pending reviews & tripwires (added R21 — promises live here, not in prose)

Every open commitment in one place, so a radar round can check this list instead of
re-reading the log. Close an item by editing it out with a round reference.

- **flights sample-hour fix — SHIPPED R25.1** (opened R25, which CLOSED the R11 pre-committed
  review: RETAINED, neither demotion condition met; replayed episode-rate Wilson LB 0.89% < 2%, the
  08-28 alarm ADJUDICATED via the intraday sampler as a CI-queue sample-hour artifact). The fix
  fixes the sample TIME, not the reading: the daily workflow schedules early (`0 18 * * *`) and
  SLEEPS to 22:30:00Z before collecting, so — GH queue delay being one-sided (always late, measured
  +0.44..+7.91h) — the sample lands on the fixed hour whenever the delay is within the 4.5h
  head-start (all 31 non-trough days of the record). 22:30Z is the historical effective hour, so the
  baseline is continuous (no reseed). A backstop guard (`collect.py apply_sample_guard`, declared
  via `flights.SAMPLE_TARGET_UTC_H`=22.5 / `SAMPLE_TOL_H`=1.5, bound to the CI target by a test)
  darks a reading still >1.5h off on a run delayed past the sleep window (~1/34). Collection-time
  decision frozen into the stored raw → replay 0-divergence, STABLE_SINCE untouched; the 3 pre-fix
  off-hour rows stay forward-only. Simulated over 34 days: 31/34 land exactly at 22:30Z, 08-28
  darks, the other two troughs score near-target without trembling, 0 clean days newly darken. STILL
  OPEN: **re-review after ~60 collection days of the fixed-hour regime** confirming the live
  18Z-cron delay distribution behaves (its own delay is unmeasured — 2pm ET may differ) and that no
  artifact of this class recurs. ANTI-LOOPHOLE (standing): a repeat of this adjudicated artifact
  class AFTER the fix is itself demotion-disqualifying.
  [opened R25 · owner R26 · fires: rows_since(flights, 2026-09-02) >= 60]
- **cnh_cny maturity refresh** — at n≥60 scored: re-measure the reach cell + benign-tremble recount
  (queued R13). R23: now n=48 (record range −45..143; 4 trembles, all benign DOWN), still <60 — keep
  waiting. R29: now n=57 (5 trembles, all benign DOWN: 07-02/07-07/07-25/08-10/08-26), still <60 —
  keep waiting; bank the open question for the n≥60 review — is the zero UP-alarm-direction reach a
  young-calm-record artifact (guard sound, tail unsampled) or a sign the bar/statistic needs
  revisiting (post-fix responsiveness is thin — only 08-26 −43 pips is a clean attributable reading).
  Respelled from `distinct_scored` to `scored`: the record carries 8 non-distinct cnh_cny
  rows by the distinct-observation rule (Known limits #6), so `distinct_scored` currently equals raw
  `scored` and cannot honestly stand in for a dedup the tool does not yet implement; the maturity
  review has always used the raw scored count n, so `scored` is the honest predicate until the rule
  is built into the tool. [opened R13 · owner R26 · fires: scored(cnh_cny) >= 60]
- **anchored-scale promotion gates** (R15, standing): before ANY anchored line promotes, its
  MATERIALITY must be replay-validated to the R11 bar and an episode/serial-dependence overlay run.
  Applies to stablecoin_peg, fed_srf_takeup. **CLEARED for fed_srf_takeup at R30** (promoted): the
  gate-work replay-validated its MATERIALITY (routine median $0 / p90 $10m, max-routine z 2.60, a
  clean 0.45z gap to the lowest fire) and found 3 DISTINCT single-day episodes (lag-1 0.406, no
  adjacent fires) — see the Tier-1 cell + radar-log.md R30. STILL STANDS for stablecoin_peg (tier-2,
  unpromoted) and any future anchored line.
- **calendar de-cycling debt** (named R20): month/quarter-end rhythm warps tga_days_cash; once
  gated fed_srf_takeup's promotion. This repo still has no de-cycling beyond weekday. **CLEARED for
  fed_srf_takeup at R30** (promoted): the debt is structurally MOOT for an anchored line — its z
  reads only today (normalize.robust_z materiality branch), never the rolling window, so the
  month/quarter-end friction band (tops $26bn / z 2.60, $4bn under the $30bn alarm) cannot warp it.
  The tga_days_cash warp remains noted (tga is not a promotion candidate).
- **closed-status first live weekend** — RESULT (R23): 08-23 (Sun) correctly read `closed` ✓; 08-22
  (Sat) read `scoring` raw 83 (z−0.24) — Friday's close re-scored, because the weekend guard keys on
  the NEWER leg being Sat/Sun and Saturday-morning still sees two Friday timestamps. Follow-up:
  confirm obs-dedup isn't double-counting Friday's close, and decide whether the guard should also
  cover Saturday (a fetcher change → needs approval).
- **net_outages — DEMOTED TO TIER-2, R28 (condition (c) fired) — CLOSED** (opened R23.1 as the settle
  tripwire; rewritten R27; closed R28). Both tags removed — the reach-deadline (`date >= 2026-10-15`)
  fired, and the per-recurrence `manual` tripwire is no longer a tier-1 duty. Full reasoning and evidence:
  Known limit 7 and the 2026-09-08 net_outages DEMOTED annotation.
- **level-layer → flights** (opened R23.1) — decide ~Nov 2026 (once flights per-region components
  banked since 08-02 can populate an honest reference window) whether to extend the level layer to
  flights regions; the second headline currently rides one lagging, panel-churning source
  (PortWatch, ~10d). R29: flights structural work stays DEFERRED to the two scheduled reviews that
  both mature ~Nov — this item (fires date≥2026-11-01) and the fixed-hour re-review (fires
  rows_since(flights)≥60, now ~7/60). The planned Nov fix is a per-region **worst-of-region z**
  (restores Europe −7.84z / Japan −7.33z at the EXISTING 22:30Z hour) — a REFORMULATION of the single
  flights slot, not new counted lines; a second sample hour is REJECTED (regional peaks are staggered
  globally, so no hour makes all four regions large-share — a 2nd hour only shifts which region is
  drowned while doubling fetch fragility). [opened R23.1 · owner R26 · fires: date >= 2026-11-01]
- **cnh_cny reachability reference-regime re-check** (opened R23.1) — the reachability gate passed
  cnh_cny on a cited reference regime, now WRITTEN into the record at R29: the 2015-16 RMB
  devaluation / capital-flight episode (PBOC devaluation 2015-08-11; overnight CNH HIBOR ~66-67% on
  2016-01-12; CNH-CNY spread to the hundreds of pips vs the ~223-pip alarm bar; BIS WP No. 446, CNBC
  2016-01-12 — see the reachability gate). Re-confirm at n≥60 that the reference-regime evidence still
  holds, alongside the maturity refresh. [opened R23.1 · owner R26 · fires: scored(cnh_cny) >= 60]
- **radar-log.md roll tripwire — DONE R29** — the log split into an archive once it crossed its
  self-set **2,000-line** threshold (crossed at R28, which took radar-log.md to 2,036 lines). R29 ran
  `tools/roll_radar_log.py --split-round 20` (byte-identity + round-coverage verified): rounds 1-19
  are now in **[radar-log-1.md](radar-log-1.md)**, rounds 20+ stay in radar-log.md, and
  `lint_registry`'s round-index parity globs `radar-log*.md`, so both files are swept in and the 1-28
  index still matches with no lint change. Two citation mappings hold going forward. (a) Every
  archived round KEEPS its line number: the archive preamble is padded to the same 6 lines
  radar-log.md's own preamble had, so a rounds-<20 citation moves by file name only — e.g. the gnss
  seed at radar-log.md:499-511 is radar-log-1.md:499-511, and Round 10's yearly-median table stays a
  rounds-<20 reference. (b) A rounds-≥20 citation into radar-log.md shifts line N → N−1223 (rounds
  1-19, 1,225 lines, left the file, replaced by a 2-line archive pointer): annotation 130's frozen
  radar-log.md:1615 is now radar-log.md:392, and its radar-log.md:1656-1671 is now
  radar-log.md:433-448. A further roll must target a fresh radar-log-N.md — the tool now refuses to
  overwrite an existing archive.
- **usd_xccy_basis parking review** (opened R20) — re-probe sourcing every ~10 rounds. **Re-probed
  2026-09-09 (R30): STILL exhausted** — FRED `XCCYBASIS3M` returns 404, and the OFR STFM mnemonics
  list carries zero xccy/basis/fx-swap/forward series (still {FNYR, MMF, NYPD, REPO, TYLD}), so no
  keyless true-official cross-currency basis leg exists. KEPT (not downgraded) on that evidence, with
  the cadence rolled to the next ~10-round window; downgrade to Rejected if still keyless-blocked at
  the R40 re-probe. [opened R20 · owner R26 · fires: round >= 40]
- **the single-credit-slot bar** (measured R22, standing): US HY (credit_spread, tier-1), EM corp
  (em_corp_oas) and Euro HY (euro_hy_spread) are ONE global credit factor — |max corr| +0.80 / +0.74
  vs the tier-1 credit line, +0.86 to each other. NO second credit-family line may be promoted to
  tier-1: it would fail the orthogonality gate AND break the headline's iid null (Known limits #3).
  The genuinely-orthogonal financial challenger is `sofr_iorb_spread`, now n=49 as of R29 (the note
  cited n=35) with |max corr| 0.231 vs cnh_cny — keep deferred until n≥60 scored, then re-measure
  orthogonality.

---

## Calibration log — round index

The full round-by-round reasoning lives in the append-only calibration log, split across
**[radar-log-1.md](radar-log-1.md)** (rounds 1-19, archived at R29) and
**[radar-log.md](radar-log.md)** (rounds 20 onward). One line per round below; open the log for the
measured detail and the numbers behind any decision. A new round is appended to `radar-log.md` and
gets one line added here.

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
- **Round 22** — 2026-08-21 · the credit-redundancy + space sweep, then a build: the "orthogonal to US HY" claims on
  em_corp_oas (+0.80) and euro_hy_spread (+0.74) MEASURED FALSE — one global credit factor, a single-credit-slot bar
  registered; NOAA sweep = guard-gate desert except space weather; **space_weather BUILT** (tier-2 context, daily max
  Kp, SWPC live + GFZ seed to 2022, 1,486 days / 39 storm trembles, a confounder-subtractor for gnss/grid — Gannon
  Kp-9 superstorm caught); the **context-line admission bar formalized** (name the ambiguity you resolve, or you're
  decoration — three roles); **tropical_cyclone REJECTED on measured payoff** (sources excellent & banked —
  GDACS+IBTrACS keyless global — but a full Shanghai+Ningbo closure moves port z=0.49, all-Japan airspace dark moves
  flights z=0.63, both under alarm: the confounder has nothing to subtract); no tier moves among counted lines
- **Round 23** — 2026-08-25 · the false-alarm round: the 2026-08-24 net_outages spike (12 countries, z=4.69, a tier-1
  alarm) adjudicated by a 5-agent probe as a FALSE ALARM — an IODA active-probing common-mode artifact (10 synced
  ~40-min ping events across 4 ocean basins, no BGP, settles 12→4 on re-query), triple-refuted (timing/infra/web); a
  guard gap opened (the ≥100-country sweep guard misses a 12-country synchronized-onset sibling); closed-status
  tripwire result (Sun closed ✓, Sat re-scored Friday's close); cnh_cny still n=48<60; flights review holds to 08-31;
  no tier moves
- **Round 23.1** — 2026-08-25 · settle + last-mile tightening: net_outages SETTLED to a completed D-1 22:00Z window
  (validated: 08-24 settles 12→4, 7 historical alarms reproduce byte-exact incl. small; monitor_swept untouched,
  replay 0-divergence); the reachability gate AMENDED (baseline-relative in a young calm record → cnh_cny passes on a
  cited reference regime); eu_gas_storage BUILD-READY-probed (AGSI+ live, the registry's first load-bearing key); two
  integrity tests (docs/data subset-gate, LINES-invariant gate); covBlind + round-index-order fixes; no tier moves.
  **[claim corrected R23.2]**
- **Round 23.2** — 2026-08-26 · the settle claim, corrected by its own tripwire: the reconciliation tool's first-run
  seam audit found settle STABILIZES the count but does NOT filter the artifact — the 08-24 twelve-country
  synchronized-onset cluster lives, stably, in the settled 08-23 window (the same 12 countries), so a future artifact
  of this shape would still alarm on its own date. Settle kept (count-stability + seed-alignment are real; the
  trailing window was genuinely unstable); the synchronized-onset class stays DETECT-AND-ADJUDICATE via the tripwire +
  R23 playbook; net_outages not demoted; no tier moves
- **Round 24** — 2026-08-26 · park + state check: eu_gas_storage PARKED on the reachability gate (AGSI source/keyed
  confirmed, but the fill-deviation metric fails — normal ±14pp vs a worst downside of −16pp over 2016-2026; the
  storage level is a defended-holds quantity, 2022 stayed near-full via price/demand; un-park needs the EU regulatory
  target path, not a blended seasonal median). State: headline calm (resonance 0, 2-day streak), cnh_cny's 5th benign
  DOWN tremble (−43 pips, offshore-yuan strength, uncounted), mood calm; live note EU gas storage at a ten-year
  deviation low (−15pp). No tier moves
- **Round 25** — 2026-09-01 · the flights pre-committed review: RETAINED. The 2026-08-31 review ran (weekday
  de-cycling engaged on schedule at window-row 71); the 2026-08-28 tremble (z=−3.05, the "next alarm") is ADJUDICATED
  — not merely adjudicable — as a CI-queue SAMPLE-HOUR artifact: flights is a concurrent snapshot, its GH-Actions cron
  (`0 22 * * *`) slipped to 02-06Z on 08-27..29 (into the diurnal trough), and the R11-named intraday sampler read
  1660/1398/1562 at 22-23Z the same days (airspace normal). Replayed episode-rate Wilson 95% LB = 0.89% < 2% bar;
  sample hour perfectly separates the 3 off-hour lows from all 31 near-baseline reads (min z −2.31). Neither
  pre-committed demotion condition met → retained; both of flights' alarms are now artifacts; a sample-hour guard is
  queued (needs approval) with an anti-loophole clause. Reconciliation tripwire clean (0/7); cnh_cny n=52 (<60); no
  tier moves. Audited by an external model (GO-WITH-CHANGES; three must-fixes folded in)
- **Round 25.1** — 2026-09-01 · the flights sample-hour fix SHIPPED: sleep-to-target. The daily workflow schedules
  early (18Z) and sleeps to 22:30:00Z before collecting, so the one-sided GH queue delay lands the sample on a fixed
  hour (all 31 non-trough days of the record); a declarative backstop guard (`collect.py apply_sample_guard`,
  `flights.SAMPLE_TARGET_UTC_H`=22.5/`SAMPLE_TOL_H`=1.5, bound to the CI target by a test) darks the rare run delayed
  past the window. Fixes the sample TIME not the reading; no firewall change, no lag, no reseed, replay 0-divergence,
  STABLE_SINCE untouched. Chosen over a discard-guard (loses coverage) and a settle-from-intraday design (rejected:
  ±1h→68% dark, components freeze, ~1-day lag, load-bearing sampler) after two external-model review rounds. 15 new
  tests; simulated over 34 days (31/34 land exactly at 22:30Z, 08-28 darks, 0 clean days newly dark)
- **Round 26** — 2026-09-04 · the P2–P6 zero-debt remainder (executed 09-03/09-04): instrument
  hygiene, no reading, no tier move, replay 0-divergence throughout, ~two dozen reviewed commits. Single sources of
  truth (one alarm predicate in
  `collect.py` consumed by replay/episodes; scoring constants read from `normalize`; net_outages `window_for`; FRED
  series ids; one User-Agent; STABLE_SINCE ledger completed). A stdlib-only lint layer (`lint_ssot`/`_registry`/
  `_workflows`/`_pending`/`_public_surface`) plus post-commit audits (`audit_registry` retracted-phrase + QUANTUM-floor
  + no-overdue; `audit_charts` byte cap; `audit_public_surface` mirror byte-equality + gap-status-no-reading).
  Retracted claims fixed at source (gnss "never moved"→z=+2.87 on dashboard+fetcher; net_outages settle claim), with
  three annotation retraction rows the scan now guards. Generators: `episodes.py --markdown`→`radar-metrics.md` (retired episodes.json), `pending.py` grammar + overdue lint,
  `roll_radar_log` (byte-identity, not yet fired ~R27), `calibration.yml`. Customer surface: tier-2 gap chips (dark
  hkma_aggr_balance, 5 straight days, stops rendering calm); credit-independence copy corrected to R22's measurement
  (em_corp_oas +0.80, euro_hy_spread +0.74 vs credit_spread, +0.86 vs em_corp_oas — one global credit factor, both stay
  tier-2, neither a tier-1 candidate); cnh_cny weekend-cadence note (~5 not 7 pts/wk); render_smoke real cookie so the
  zh path executes. render.py 64-colour quantize (largest chart 61.6→24.9 KB), pillow pinned to the CI-resolved 12.3.0,
  audit_charts cap 70000→40000. Suite: 260 gate / 49 lint (bare-venv) / 17 audit; replay 412/0/0 since 2026-08-17.
- **Round 27** — 2026-09-08 · the corroboration probe: a corroborated net_outages sibling line is CUT (the probe
  labeled all ~60 alarm windows live — corroboration is sparse on every band and cannot be told from calm, so it
  would deflate real and artifact days alike; no exit path named). net_outages RETAINED under a named weaker standard,
  demotion clause tightened to three conditions ((a) unadjudicable · (b) unadjudicated 14 days · (c) reach by
  2026-10-15 on the 8 largest readings). Annotations: 09-05 artifact (recurrence adjudicated), 09-06 method
  (corroboration measured, not a filter), 09-06 correction (withdraw R11's 2025 Iberian-blackout attribution — the
  alarm was 0/41 corroborated synced ping-only; the real blackout day read 7 countries, sub-alarm). The 09-04/09-05
  common-mode was a 2-day transient, cleared 09-06. Suite green, replay 0-divergence, no tier moves. (Separate/open:
  control_daylength canary false positive near the equinox, issue #3.)
- **Round 28** — 2026-09-08 · the reach adjudication + demotion, folded with two spine fixes: (1)
  control_daylength's canary now reproduces the SOURCE's day-length model (Schlyter sunriset, ≈1.10°
  effective depression), not astronomical truth, and a margin closest-day check replaces strict argmin
  (solstice-safe) — the equinox false positive (issue #3) is CLOSED; (2) A1 spine hardening — a
  non-numeric or non-finite fetcher value is darkened at the collect() boundary instead of aborting the
  run or being stored as 'nan'/'inf' into the forward-only record; (3) net_outages' 8 largest readings
  adjudicated under the R23 playbook (a live IODA re-query + a multi-source attribution search, evidence
  data/archive/ioda_8largest_requery_2026-09-08.csv) — condition (c) tripped, NONE survives as a cited
  world event (2024-10-03 corroborated but unattributable; 2023-09-06's coincident Cogent backbone outage
  does not correspond to the ping-only IODA reading) — so net_outages is DEMOTED to tier-2, the tier-1
  global-communications slot left empty and disclosed. 9 annotations (8 artifact + 1 DEMOTED method);
  STABLE_SINCE bumped to 2026-09-08 (a tier change alters the summary re-derivation); replay
  0-divergence. Roll tripwire CROSSED (radar-log.md past 2,000 lines); the roll is deferred to R29.
- **Round 29** — 2026-09-08 · the discipline-holding round: no tier move — roll the log (rounds 1-19
  → radar-log-1.md), refresh cnh_cny's stale cells and WRITE its cited reference regime (the 2015-16
  RMB devaluation / capital-flight episode; overnight CNH HIBOR ~66-67% on 2016-01-12; BIS WP No.
  446) so retention on the weaker standard is cited not assumed, and the net_outages symmetry stated;
  probe (probe-only) the IODA passive-BGP comms candidate (plausibly passes all gates, route-
  WITHDRAWAL-only disclosure, net_bgp_withdrawal a tier-2 candidate — not built); C1 darkCount
  majority banner + C2 tier-1-count lint; S3-S7 registry bookkeeping (bgp Backlog consolidation,
  flights defer to ~Nov, fed_srf named lead challenger, hkma investigation flag, sofr note n=49); C3
  per-line STABLE_SINCE defer. bgp probe evidence CSV committed
- **Round 30** — 2026-09-09 · the promote-one round: fed_srf_takeup PROMOTED tier-2 → tier-1 (the
  open slot net_outages vacated at R28), filling the roster back to 4/4. Whole board scored; fed_srf
  the data-backed pick — the most orthogonal candidate (|max Pearson| 0.008 vs credit_spread n=750,
  0.10 vs flights n=45, 0.10 vs cnh_cny n=40; shared-date pairs), fresh NY-Fed T+1, guard 3, 3 clean
  scarcity alarms. Its two standing
  gates BOTH CLEARED on the data (gate-work): R20 de-cycling MOOT for anchored scoring (z reads only
  today; friction band tops z 2.60 / $26bn, $4bn under the $30bn alarm), R15 anchored-scale VALIDATED
  (0.45z gap to the lowest fire z 3.05, 85% of nonzero days <$100m dust, 3 distinct single-day
  episodes, lag-1 0.406). DOMAIN DECISION: a 4th FINANCIAL line accepted (airspace + credit +
  capital-controls + dollar-plumbing) — comms had no built candidate, and is now covered by the new
  tier-2 net_bgp_withdrawal (BUILT R30, passive-BGP route-WITHDRAWAL, disclosure: catches
  withdrawals, misses access-layer blackouts), the standing candidate for a future slot. STABLE_SINCE
  bumped to 2026-09-09 (a tier change alters the summary re-derivation; fed_srf stale that day →
  0/0/0 re-derives byte-exact), replay 0-divergence. C2 tier-1-count copy 3→4 across docs/README;
  C1 darkCount majority now spans 4 lines. Pending: fed_srf's R20+R15 gate items closed (cleared),
  usd_xccy_basis cadence rolled to R40.
