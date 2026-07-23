# tremor radar — indicator registry

tremor doesn't keep a fixed indicator set; it runs a **radar**. Indicators move
through a **4-8-16 funnel** as they earn measurable evidence, so the live
instrument is always the best few we have — chosen by data, never by gut feel.

| tier | role | target |
|---|---|---|
| **1 — primary** | displayed on the dashboard, counted in the trembling resonance | 4 |
| **2 — watchlist** | scraped daily, building history; not shown or counted | 8 |
| **3 — candidate** | researched ideas with a verified-free data source; not yet built | 16 |

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

**Two absolute gates** (fail either → not a counted indicator):
- **Guard gate** — no real guard → never tier-1 (watchlist / "felt vs real" contrast only).
- **Cadence gate** — collection samples once a day, so the disorder must persist at daily
  resolution, OR be aggregated intraday→daily (as `grid_frequency` takes the day's MAX
  deviation). Intraday-transient phenomena that recover within a day — stablecoin
  flash-depegs, a momentary FX wick — are aliased away by a daily snapshot and rejected.

**Freshness rule for tier-1:** a displayed instrument must be FRESH (low publication lag). A
line that is daily but lags a week (e.g. IMF PortWatch, ~8 days) only shows a disruption long
after it began — fine for tier-2 (history accumulates, the lag washes out in the rolling
baseline), but too stale to be a live tier-1 instrument. Prefer ≤ ~2-day lag for tier-1.

4-8-16 is a steady-state target, not a forced cut: a line is never demoted without
evidence. Rubric scores are 0–3; computed metrics show `—` until there is enough
history (~20 days).

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
2. **|z| > 3 is not a 1-in-300 event at the window sizes tremor runs on.** Measured null
   exceedance on iid Gaussian data with the current estimator: **2.7% at n=10, 1.2% at
   n=20, 0.36% at n=90.** (Under the MAD scale used before round 7 it was 5.3% / 2.1% /
   0.56%.) Short-window lines are therefore expected to tremble occasionally with nothing
   happening; that is why attribution is mandatory and why tier-2 exists.
3. **Tremble COUNTS are day counts, not episode counts.** A line with high autocorrelation
   records one event as several trembling days. Rate comparisons across lines are
   correspondingly rough.
4. **Below ~60 scored readings a per-line tremble rate cannot be adjudicated.** The
   confidence interval is wider than the difference being argued about. Radar rounds
   should say so rather than rule on n≈20.

---

## Tier 1 — primary  (4 / 4 ⚠️ one provisional)

The four displayed, counted instruments — four distinct domains. Decided round 3,
applied round 4.

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | Orthog | status |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| flights | airspace (EU/US/JP) | 3 | 3 | 2 | — | — | — | ✅ |
| credit_spread | financial (US→global) | 3 | 3 | 3 | — | — | — | ✅ global bellwether |
| cnh_cny | capital controls (China) | 2 | 3 | 2 | — | — | — | ✅ slot 4 (user-decided) |
| net_outages | communications (global) | 2 | 3 | 3 | 13/13 | — | 0.42 | ⚠️ **PROVISIONAL** — promoted R7 into the slot gnss vacated; only ~13 observations, does NOT meet the 60-reading bar (see the round-7 log) |

## Tier 2 — watchlist  (7 candidates + 3 contrast · 1 slot open)

Collected daily by CI, building history; not shown or counted. The global 3/3/3 lines
are tier-1 challengers banking evidence. (the three feel lines — gdelt, gdelt_tone, vix — sit outside the
8 candidate slots: they fail the guard gate and can never promote; they ride along only
as the "felt vs real" contrast.)

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | note |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| port_throughput | trade (global) | 3 | 3 | 3 | — | — | ~4729 global port calls/day (2065 ports) |
| chokepoint_breadth | trade (global) | 3 | 3 | 3 | — | — | 28 straits, ~1810/day (Hormuz blockaded) — strong, but PortWatch lags ~8 days: too stale to display live |
| sofr_iorb_spread | financial plumbing | 3 | 3 | 3 | — | — | SOFR−IORB ~−2bps (calm) — keyless FRED |
| em_corp_oas | EM financial (global) | 3 | 2 | 3 | — | — | EM corp OAS ~1.38pp — orthogonal to US HY |
| gnss_interference | navigation/EW (global) | 3 | 3 | 1* | 31/31 | 0% | demoted R7 — *effective* reach is 1, not 3: one worldwide ratio has no regional sensitivity and read 0.47% through a Gulf air war |
| capital_premium | capital controls (Korea) | 2 | 3 | 1 | — | — | demoted R4 (redundant with China); kept on watch |
| grid_frequency | infrastructure (Nordic) | 2 | 3 | 1 | — | — | demoted R4 (regional); kept on watch — may re-challenge on orthogonality |
| — gdelt | feel: conflict share (global) | 1 | 0 | 3 | — | — | contrast line (guard gate) — v2 full-day aggregation, not a candidate slot |
| — gdelt_tone | feel: news tone (global) | 1 | 0 | 3 | — | — | contrast line — full-day average tone, same pass as gdelt |
| — vix | feel: priced fear (global) | 1 | 0 | 3 | — | — | contrast line — keyless FRED VIXCLS, seeded 180d from archive |

## Tier 3 — candidate ideas  (7 / 16)

All clear both gates (real guard; daily-persistent or daily-aggregatable). Sorted by strength.
Data sources marked ✅ were live-verified keyless+daily. (Tier 2 is now full at 8/8, so these
wait for a tier-2 slot to open — i.e. a watchlist line graduating to tier-1 or washing out.)

| candidate | domain | hypothesis (guard → leak) | L | G | R | data source (free, daily) |
|---|---|---|:--:|:--:|:--:|---|
| euro_fragmentation | financial (EU) | the ECB defends cohesion → a widening periphery-core 10y spread leaks euro-breakup stress | 3 | 3 | 2 | ✅ ECB SDMX API |
| hkd_aggr_balance | capital (HK) | HKMA's currency board defends the peg → a collapse in the aggregate balance leaks capital flight | 3 | 3 | 2 | ✅ HKMA Open API |
| entsog_gas_flow | energy (EU) | pipelines + economies keep gas flowing → a drop in cross-border physical flow leaks cutoff / sabotage | 3 | 3 | 2 | ✅ ENTSOG API |
| bgp_instability | infrastructure | networks keep routes stable → a surge in BGP withdrawals leaks outages, hijacks, war | 2 | 2 | 3 | ✅ RIPEstat (RIPE NCC) |
| fx_parallel_premium | capital (multi) | central banks defend the official rate → a black-market / crypto premium leaks capital flight (AR, VE, NG, …) | 2 | 3 | 2 | ✅ CriptoYa / dolarapi (keyless) |
| euro_hy_spread | financial (EU) | ECB + banks press EU spreads down → a spike leaks European credit fear | 3 | 2 | 2 | ✅ FRED keyless `BAMLHE00EHYIOAS` |
| cp_funding_spread | financial | the Fed backstops the CP market → a CP-minus-funds spike leaks short-term funding stress | 2 | 2 | 2 | ✅ FRED keyless `CPFF` |

### Rejected
| candidate | reason |
|---|---|
| stablecoin_peg | fails the **cadence gate** — depegs are intraday-transient, a daily snapshot aliases past them. |
| tail_risk_market | fails the **guard gate** — prediction-market prices are a free-floating read with no defended equilibrium (Guard ~1). Interesting, but not a tension indicator. |

---

## Calibration log

### Round 1 — 2026-06-22 (seed)
- **Scored** the 7 existing indicators on the rubric metrics. Computed metrics
  (Reliability / Responsiveness / Orthogonality) are `—`: only ~1 day of history
  exists, far below the ~20 days needed — honest, not fabricated.
- **Explored** (diverge): reasoned 4 global + guarded + high-leverage candidates and
  web-verified their data. `stablecoin_peg` verified keyless and live; `sofr_stress`
  rests on FRED (already working in CI). `chokepoint_transit` and `net_outages` are
  on-thesis but lack a confirmed free source — kept as ideas pending a data find.
- **Calibrated** (converge): tier-1 is **over capacity (5/4)**. The two clearly-global,
  high-leverage lines (credit_spread, flights) are locked. The demotion contest is
  among the three national/regional lines — capital_premium (Korea), grid_frequency
  (Nordic), cnh_cny (China). The right tie-breaker is **Orthogonality**: Korea premium
  and China CNH/CNY are both "Asian capital-control" lines and may move together, in
  which case one is redundant. That needs history. **No demotion applied this round** —
  deciding now would be 拍脑袋.
- **Moves applied:** none (no evidence yet for any promotion/demotion).
- **Proposed for next rounds:**
  1. Once ~20 days accrue, compute Orthogonality among {Korea, Nordic, China} and demote
     the most-redundant to reach tier-1 = 4.
  2. Build `stablecoin_peg` as a tier-2 fetcher (verified free, high leverage/reach) —
     a strong global candidate to start accumulating history. *(needs approval — new code)*
  3. Build `sofr_stress` as tier-2 (FRED, global dollar-funding stress). *(needs approval)*
  4. Keep exploring toward 16 tier-3 ideas; hunt a free AIS source for chokepoint_transit.

### Round 1.1 — 2026-06-22 (cadence gate added)
- **New gate:** added the **cadence gate** to the methodology — an indicator must persist
  at daily resolution or be aggregated intraday→daily, because collection samples once a
  day. A daily snapshot of an intraday-transient phenomenon is dishonest (aliasing).
- **Rejected `stablecoin_peg`:** depegs recover in minutes–hours, so a daily snapshot
  almost always catches it back at $1 and misses the event. Removed from candidates.
- **Added `ar_blue`** (Argentina blue-dollar premium): web-verified keyless on dolarapi;
  a black-market FX premium persists for weeks, so daily sampling is honest. Capital-control
  domain, national reach.
- **Strongest standing candidate is `sofr_stress`** — global, guarded, high-leverage, daily,
  free. The top build target for tier-2.
- **Moves applied:** none (candidate-list refinement only).

### Round 2 — 2026-06-22 (re-probe + rethink)
- **Explored (diverge):** re-probed data sources live and unblocked two strong candidates:
  - `chokepoint_transit` — found **IMF PortWatch** `Daily_Chokepoints_Data` (free, keyless,
    daily vessel counts per chokepoint; Suez at 26–39/day, already depressed by the Red Sea
    crisis). Upgraded Guard 2→3 and marked data verified. Now a 3/3/3 candidate.
  - `net_outages` — found **IODA** (Georgia Tech) free outage signals (bgp / active-probing /
    Google-transparency). Data verified, replacing the token-gated Cloudflare source.
  - Added `ve_parallel` (Venezuela parallel FX), keyless via dolarapi.
- **Rethink of tier-1 (the deeper ask):** two structural problems surfaced, both pointing the
  same way:
  1. **Domain redundancy** — tier-1 holds TWO capital-control lines (capital_premium/Korea and
     cnh_cny/China). The original thesis wants four DIFFERENT domains; two in one domain is
     likely redundant (an Orthogonality question, pending history).
  2. **Global imbalance** — three of five tier-1 lines are national/regional (Korea, Nordic,
     China); only credit_spread and flights are global. The "tier-1 should be global" principle
     favors demoting a national line.
  Both point to demoting one of the national/regional lines — and the natural replacement is a
  **global 3/3/3** line (chokepoint_transit or sofr_stress), which would also add a genuinely
  new domain (trade) or strengthen financial.
- **Moves applied:** none — chokepoint/sofr have no history yet, so per the gates they can't
  jump to tier-1. The honest path is to BUILD them as tier-2 first.
- **Proposed for next round:**
  1. Build `chokepoint_transit` (IMF PortWatch) and `sofr_stress` (FRED) as **tier-2** fetchers
     so CI starts banking their daily history. *(needs approval — new code)*
  2. After ~20 days, compute Orthogonality of the national tier-1 lines vs each other and vs the
     new global challengers; demote the most-redundant national line to reach tier-1 = 4.
  3. Keep filling tier-3 toward 16 (next hunts: a free daily Baltic Dry / freight source; a
     daily sovereign-spread source).

### Round 3 — 2026-06-22 (tier-1 decided + 6-domain candidate hunt)
- **Tier-1 decision (user):** slot 4 = `cnh_cny` (China). Steady-state tier-1 target is
  **flights · credit_spread · chokepoint_breadth · cnh_cny**. `capital_premium` (Korea, redundant
  capital domain) and `grid_frequency` (Nordic, regional) demote to tier-2 once the trade line is
  built and online (so tier-1 never drops below 4).
- **Hunt (diverge):** ran a parallel 6-domain search (financial, trade, infrastructure, capital,
  geopolitical, wildcard) → 29 candidates; curated tier-3 to 13. Key outcomes:
  - **Discovery:** FRED serves a **keyless** CSV (`fredgraph.csv?id=…`) — live-verified — so SOFR,
    IORB, EM/EU OAS, CP spreads are all free without a key.
  - **Refined two existing candidates into sharper forms:** `sofr_stress` → `sofr_iorb_spread`
    (SOFR minus the defended IORB ceiling = the actual guard deviation, not the rate level);
    `chokepoint_transit` → `chokepoint_breadth` (the full 28-chokepoint panel, each a geopolitical
    tripwire — the live data already shows Hormuz at ~2/day under blockade).
  - **New 3/3/3 global candidates:** `port_throughput` (PortWatch ports), `gnss_interference`
    (GPSJam GPS-jamming — a NEW navigation/PNT domain that fingerprints electronic warfare),
    `em_corp_oas` (EM dollar-funding stress, orthogonal to US HY).
  - **Live-verified keyless sources:** FRED CSV, GPSJam, RIPEstat (BGP), IODA, CriptoYa.
  - **Rejected `tail_risk_market`** (Polymarket): fails the guard gate — a free-floating market read.
- **Moves applied:** none (still thin history). The tier-1 demotions are recorded as decided but
  execute when `chokepoint_breadth` is built and online.
- **Proposed for next round:** build the four global 3/3/3 lines as tier-2 to bank history —
  priority `chokepoint_breadth` + `sofr_iorb_spread`, then `gnss_interference` + `port_throughput`.

### Round 3.2 — 2026-06-22 (build)
- **Built four global tier-2 watchlist lines** (user: keep the dashboard tier-1-only, but collect
  tier-1 AND tier-2 data continuously): `chokepoint_breadth` (IMF PortWatch), `gnss_interference`
  (GPSJam), `sofr_iorb_spread` and `em_corp_oas` (keyless FRED via a new `core/fred.py` helper).
  All four span distinct domains (trade / navigation / financial-plumbing / EM-financial).
- **Live values on build day:** chokepoint ~1810 transits/day; GPS-jam share ~0.43%; SOFR−IORB
  ~−2 bps (calm); EM corp OAS ~1.38pp (calm). Tier 2 is now 6/8; dashboard unchanged (5 tier-1).
- **Moves applied:** tier-3 → tier-2 for the four (built). No tier-1 change.
- **Next:** they bank history; after ~20 days, Orthogonality decides which challenges into tier-1
  (chokepoint_breadth is the slot-3 incumbent-elect, displacing Korea/Nordic).

### Round 3.3 — 2026-06-22 (tier-2 filled to 8/8)
- **Built two more tier-2 lines** to fill the watchlist: `port_throughput` (IMF PortWatch global
  port calls, ~4729/day) and `net_outages` (IODA, ~3 countries currently in outage). Extracted a
  shared `core/portwatch.py` so chokepoint + ports don't duplicate the ArcGIS query.
- **Tier 2 is now full: 8/8.** Funnel snapshot — tier-1 5 (target 4), tier-2 8/8, tier-3 7/16.
- **Moves applied:** tier-3 → tier-2 for the two. No tier-1 change.
- **Tier-2 is full**, so further tier-3 builds wait for a slot to open (a watchlist line graduating
  to tier-1 or washing out on poor Reliability/Responsiveness once history accrues).

### Round 4 — 2026-06-22 (apply the decided tier-1 = 4)
- **Applied the standing decision** (always 4 primary; slot 4 = China). Tier-1 is now
  **flights · credit_spread · cnh_cny · chokepoint_breadth** — four distinct domains (airspace,
  financial, capital, trade). The dashboard and resonance count now read 4/4.
- **Moves:** promoted `chokepoint_breadth` (tier-2 → tier-1); demoted `capital_premium` (Korea)
  and `grid_frequency` (Nordic) (tier-1 → tier-2). All still collected daily.
- **Note on discipline:** this is a user-directed promotion ahead of the orthogonality-history
  gate. Justified on the rubric — chokepoint_breadth is global 3/3/3 vs the two demoted national/
  regional lines (Korea redundant with China; Nordic regional). When ~20 days of history exist,
  Orthogonality/Responsiveness can confirm or revise (e.g. Nordic grid may re-challenge if it
  proves more independent than a tier-1 incumbent).
- **Capacity:** tier-2 candidate slots stay at 8 (Korea + Nordic in, chokepoint out); gdelt is
  counted separately as the contrast line. tier-3 = 7/16.

### Round 5 — 2026-06-22 (freshness rule; swap chokepoint → gnss in tier-1)
- **New rule:** added the **freshness rule** — a tier-1 (displayed) instrument must have low
  publication lag. `chokepoint_breadth` is a strong 3/3/3 signal but IMF PortWatch lags ~8 days,
  so it shows a disruption a week late — too stale to be a live instrument.
- **Swap:** demoted `chokepoint_breadth` back to tier-2 (still collected — the lag washes out in a
  rolling baseline), promoted `gnss_interference` (GPSJam, ~1-day lag, global 3/3/3, a fresh
  navigation/electronic-warfare signal that directly fingerprints conflict) into tier-1.
- **Tier-1 now:** flights · credit_spread · cnh_cny · **gnss_interference** — airspace, financial,
  capital, navigation/EW. All ≤ ~3-day lag.
- **Moves:** gnss tier-2 → tier-1; chokepoint tier-1 → tier-2. No other change.

### Round 6 — 2026-07-10 (first live-signal review, 19 days of history)
- **System:** 17 consecutive scheduled runs, zero failures, zero dark days across all 13 lines.
  z-scores active since ~07-01. First trembles observed; every one was attributed (see
  `data/annotations.csv`) — none was a resonance (never more than 1 tier-1 line on a day).
- **Signals attributed:** quarter-end repo turn caught by `sofr_iorb_spread` exactly on 06-30
  (mild, benign — the line's first validation); `cnh_cny` flipped negative twice on offshore-yuan
  strength (07-07 coincided to the day with the PBOC's Hong Kong offshore-yuan package); `flights`
  dipped on the July-4 Sunday (holiday + US storms + Italy ATC strike); Hormuz REOPENED (~2/day
  → 22-42/day), driving chokepoint's benign up-tremble; Super Typhoon Bavi took out Guam's grid.
- **Calibration findings for next rounds:**
  1. `net_outages` z≈10 was mostly a MONITORING ARTIFACT — IODA activated new datasources
     (gtr 07-01, bgp/merit-nt 07-05), inflating the country count against a quiet baseline
     (52/89 spike events were merit-nt micro-events in North Macedonia alone). Consider filtering
     by outage score or datasource for a stabler count before this line can be trusted.
  2. `flights` weekday de-cycling cannot engage until ~10 same-weekday samples (~10 weeks);
     until then weekend/holiday dips can soft-false-positive. Self-heals by ~Sep 2026.
  3. ADS-B provider flakiness (fallbacks fired on 07-04/07-07): a provider returning HTTP 200
     with a degraded aircraft list passes the require-all-regions guard silently. Consider a
     per-region sanity floor.
  4. Trembles in the benign direction (chokepoint up, outages down) count toward the flag; the
     `direction` column disambiguates. Open question: should tier-1 resonance count only
     alarm-direction trembles?
- **Moves applied:** none — no evidence against any tier placement yet; Orthogonality unlocks
  around ~20 days of z history (mid-July).

### Round 6.1 — 2026-07-10 (methodology batch from the live-signal review)
Adjustments approved after a three-lens panel review (statistician / thesis-guardian /
minimalist); all recorded as `method` rows in `data/annotations.csv`, applied FORWARD ONLY
(no committed z/trembling value was rewritten).
- **Observation dedup:** rows gained an `obs_date` column; the z baseline uses only the first
  occurrence of each observation, a republished observation scores no new z and raises no flag,
  and baselines cap at 180 calendar days. Backtest over the 19-day history: the six
  publication-step trembles (chokepoint ×3, port ×1, sofr ×2) would not have fired.
- **Direction-aware resonance:** `trembling_count` now counts only alarm-direction trembles;
  benign-direction moves (a guard reasserting itself, e.g. Hormuz reopening) are recorded and
  shown as "benign shift", not disorder. Under the new rule the July history would have counted
  1 tremble (flights 07-05), not 3.
- **Weekly-cycle warm-up veto:** with 3–9 same-weekday samples, a full-window tremble whose
  level lies inside the same-weekday min–max envelope is suppressed, auditable in source_note.
  Nonparametric by design — a genuine crisis value cannot be vetoed.
- **net_outages v2:** count restricted to IODA's ping-slash24 datasource (v1 counted every
  datasource and measured IODA's sensor rollout, not disorder — live check: v2 reads 3
  countries where v1 read 17). v1 archived at `data/archive/net_outages_v1.csv`; v2 restarts
  under warm-up.
- **ADS-B region floor:** under-floor (<30 aircraft) from one provider = suspected degraded
  feed, try the next; two providers agreeing under-floor = accepted as a real reading
  (corroboration keeps the instrument from blinding itself during a genuine collapse).
  Per-region counts now recorded in source_note.
- **Dashboard:** trembled points now carry their attribution notes from annotations.csv
  (tooltip + per-line modal); alarm-direction trembles read red, benign shifts read calm green;
  lines with <30 unique observations show a "calibrating" badge.
- **CHANGE FREEZE:** methodology is now frozen until the next radar round (~30 days of clean
  history), barring a correctness-critical failure. Open items parked for that round: MAD is
  ill-suited to low-count integer lines (net_outages); a small holiday calendar as annotation;
  a false-positive budget review of the |z|>3 threshold at ~90 days.

### Round 6.2 — 2026-07-10 (the "feels" half, rendered)
The mission audit scored the second clause of the founding question ("或只是感觉更乱了")
3/10: the feel side was collected but 0% displayed. This round builds it out:
- **gdelt v2:** conflict share now aggregates the entire previous UTC day (~96 files,
  ~100k events) instead of one 15-minute sample that swung 8→23% in a week; obs_date set;
  v1 archived. **gdelt_tone** added from the same download pass (news valence vs event mix).
- **vix** added as the priced-fear channel (keyless FRED VIXCLS), seeded with 180 days of
  archive scored through the standard pipeline — feel z is live immediately (13 archive
  trembles, incl. the Mar-2026 VIX-31 episode). Contrast lines are exempt from the guard
  gate by design and can never be counted or promoted.
- **Dashboard:** a "Real vs felt — the anxiety premium" panel now renders trembling_count
  history as bars (the real side — also the first trend view of the headline number)
  against the feel lines' z toward their alarm direction, with amber columns marking days
  when feeling runs hot (feel z ≥ 2) while every instrument reads calm — the anxiety
  premium, visible. Earlier same-day fixes: stale tier-1 lists in README/resonance modal
  corrected, comparator disclosed, calibrating qualifier added to the headline.
- The founding question's two halves are now both on the page.

### Round 7 — 2026-07-22 (the scale estimator; a miss, and a correction)

Triggered by a 15-day miss, reviewed against 31 days of history. The instrument read
**0 / 4 every day from 07-07 to 07-22** while the US–Iran ceasefire collapsed, the IRGC
closed the Strait of Hormuz, the Houthis declared a naval blockade of Saudi Arabia and
Brent reached $91. The miss is logged in `annotations.csv` as a permanent record.

**Diagnosis — mostly coverage, partly calibration, and the premise was wrong.**
The working premise going in was "the |z|>3 rule over-fires 26x" (7.8% observed against
0.3% nominal). That is wrong: 0.3% is the tail of a *standard normal*, but a z built from a
finite window has its own, much fatter null distribution that depends on window size.
Measured by simulation against the shipped code: **|z|>3 under MAD occurs 5.3% of the time
at n=10 and 0.56% at n=90 with nothing happening.** True over-firing was ~1.5–3x, not 26x —
and the threshold could not be raised anyway, because two adjudicated REAL events (the FAA
nine-airport ground stop of 07-21, and the 07-18 Northeast storms) had already scored
−2.70 and −2.80 and been missed *at* 3.0.

**Shipped: MAD → Rousseeuw-Croux Qn** in `core/normalize.py`. Same 50% breakdown point and
the same collapse condition, but unbiased on short windows (MAD measures ~0.91 sigma at
n=10; Qn ~1.00) with about half the sampling variance. Null exceedance at |z|>3 falls to
2.7% / 1.2% / 0.36% at n=10 / 20 / 90. Replayed over all 341 scored rows the tremble rate
goes 7.3% → 6.5%; `em_corp_oas` 9.1% → 0%; the adjudicated `grid_frequency` artifact of
07-12 is suppressed while 07-17 survives; and **the adjudicated real `flights` event of
07-22 is recovered, −2.695 → −3.014.** Forward only; every series carries a seam here.

**Shipped: the RMS fallback is gone.** When the robust scale collapsed, scoring fell
through to a median-centred RMS with breakdown point 0 — on the real `sofr_iorb_spread`
window of 07-02 it manufactured z = 5.262 from a 3bp integer move. No spread now returns
None, as the stated rule always said it should. Costs zero z-scores on the existing record.

**Shipped: a test suite** (`tests/test_normalize.py`, run in CI before any row is written)
and a **CI failure alarm** — a persistently failing run stopped the daily commit, and
GitHub disables a cron workflow after 60 days without repository activity, so the
instrument could have switched itself off with nobody told.

**Corrected:** the `gdelt_tone` annotation of 07-21 defended a tremble with a weekday
control computed on a *different row*. The trembling row scored a Sunday observation whose
own-weekday z is ≈ −1.05; the genuine weekday signal was the next row, at −4.31 sd, which
did not tremble. The instrument trembled on the artifact and stayed silent on the real day.

**Reliability, first data-backed reading** (tremble rate over scored rows, MAD basis, and
see limit 4 above — none of these n are large enough to adjudicate, they are recorded to
accumulate): `sofr_iorb_spread` 30% (n=10), `grid_frequency` 9.5% (21), `cnh_cny` 9.5% (21),
`em_corp_oas` 9.1% (11), `vix` 7.3% (178), `capital_premium` 4.8% (21), `cn_flights` 4.8%
(21), `flights` 4.8% (21), `credit_spread` 0% (11), `gnss_interference` 0% (19).
No promotions. `grid_frequency` is **blocked from tier-1** pending re-measurement under Qn.

**Investigated and deliberately NOT built** (each rejected on evidence, recorded so it is
not silently re-litigated):
- *A Gulf region for `flights`* — probed all three keyless ADS-B aggregators at seven Gulf
  points: 6–15 airborne over Dubai, 14–28 Doha, 10–21 Hormuz; the deduplicated union of
  eight 250nm circles covering the whole peninsula is **35 aircraft**, against ~950 in the
  single W/C Europe circle. Dubai swung 14→15→11→6→13 within fourteen minutes. A sensor
  with ±50% snapshot noise cannot see the −14% move the Hormuz closure actually produced.
  Free community ADS-B does not instrument the Gulf. Recorded as a permanent limitation.
- *Regionalizing `gnss_interference` onto a Hormuz box* — backtested on 95 days of real
  GPSJam files. A box at 25–38N/44–62E does fire (z ≈ +3.2/+3.8/+3.3 across the episode),
  but **moving its southern edge by one degree destroys the detection entirely** (24–38N
  gives 2.0/2.1/1.8), and its 90-day baseline spans a ~10x growth in the sampling frame
  (139 active cells / 3,570 aircraft in April against 555 / 36,416 in July) — the same
  sensor-inflation artifact that forced the `net_outages` v2 break. A tier-1 reading that
  depends on where a human drew a rectangle is worse than an honestly empty slot. Deferred.

**Still open, carried to round 8:** the level-vs-change limit (1 above) — the deepest
finding of the review and unaddressed; harvesting the full DAILY PortWatch series (the
fetcher currently discards 6 of every 7 observations it already downloads, which is the
real reason `chokepoint_breadth` could not score through the Hormuz closure); a per-line
`status` so "cannot score" stops reading identically to "calm"; the weekly cycle on the
GDELT feel lines; `grid_frequency`'s daily-maximum statistic; vendoring Chart.js.

### Round 7.1 — 2026-07-22 (tier-1 swap; the status column; PortWatch rebuilt)

**Tier-1 swap: `gnss_interference` → tier 2, `net_outages` → tier 1.**
The GPS line kept a primary slot while being structurally unable to do its job:
it sums every h3 cell on earth into one ratio, so a regional jamming campaign is
diluted by global traffic. Through the July Gulf escalation it read 0.47% and
z = −0.12 while the airspace over Iran and the Hormuz approaches ran near 16%.
Its Reach was scored 3 (global) — the honest score for a *global average* is 1,
because it responds to nowhere in particular. Regionalizing it was investigated
and deferred this round (see 7.0), so the slot is better spent.

Candidates were ranked on the data, not on preference. The freshness rule (≤ ~2
days) eliminated `chokepoint_breadth` (10d), `port_throughput` (10d) and
`sofr_iorb_spread` (2.5d) outright. Of the five survivors, first-difference
correlation against the three remaining tier-1 lines eliminated `em_corp_oas`
as **redundant** (r = +0.74 against credit_spread — it is another credit
spread); `capital_premium` and `cn_flights` duplicate the domains cnh_cny and
flights already cover, at Reach 1; `grid_frequency` is orthogonal (max |r| =
0.22) but is Nordic-only and was blocked from tier-1 this round on its
statistic. `net_outages` is the only candidate that is GLOBAL, zero-lag, and a
domain no other line watches — and it is the only change available that widens
an instrument whose other three lines are EU/US/China-specific. A country going
dark leaks either a deliberate shutdown or an infrastructure collapse; both are
disorder, and both are invisible to every other line here.

**This promotion is PROVISIONAL and breaks the round-7 bar, deliberately and on
the record.** The v2 series has ~13 observations, far short of the 60 scored
readings this same round set as the promotion standard. It is taken because the
alternative — leaving a slot occupied by a line proven unable to see its own
domain — is worse, and because the status column now makes the weakness legible
on the page rather than hidden. **Pre-committed review at 60 scored readings
(~late September 2026):** if the tremble rate's Wilson lower bound exceeds 2%,
or the line proves to track IODA's detector coverage rather than the world, it
goes back to tier-2 and the slot runs empty and disclosed. Also fixed as a
precondition: the fetcher now records WHICH countries are dark, because a count
alone makes a tremble unattributable and every tremble here must be answerable.

**The `status` column.** Every row now carries one of `scoring` / `warming-up` /
`stale` / `dark` / `no-spread`, and `summary.csv` gains `blind_count` and
`scoring_count`. A line reporting nothing was previously in one of six very
different states, all rendered as an empty z-score — which is exactly how a
strait closing went unnoticed for fifteen days: the only line watching it COULD
NOT SCORE, and that looked identical to calm. The dashboard's denominator is now
the number of instruments that could actually answer, so "0 of 4" can become
"0 of 3 · 1 line cannot score (not the same as calm)". Historical rows were
migrated by DERIVING status from what each row already said — dark from an empty
value, stale from its own note, scoring from a present z — never by re-scoring.

**PortWatch rebuilt (series v2, both trade lines).** The fetcher asked for the
newest available day and kept one row, so on six days out of seven it
re-recorded a reading it already held. PortWatch is a COMPLETE DAILY series
published weekly in seven-day batches: the fetcher was downloading the whole
week and discarding six sevenths of it. That, not the publication lag, is why
these lines held 6 distinct observations in 31 days and could not score at all.
v2 reads the observation exactly 10 days back — one new observation per
collection day — and both lines were seeded from the source's own archive
(`tools/seed_portwatch.py`, the `vix` precedent, replayed strictly in order so
no row is judged against its own future). Result: 6 distinct observations → 190
scored, with tremble rates of 2.1% and 1.1%. Every seeded row says in its note
that it was computed retroactively and was never a live detection.

**What this does NOT fix, stated plainly:** it does not close the Hormuz gap.
The reading is a 28-strait TOTAL and Hormuz is one or two percent of it — on the
day the strait closed this line moved UP. The alarm-direction tremble it does
record (observation 07-10, z = −4.63) comes from elsewhere in the basket. Seeing
a single strait needs a per-strait breadth COUNT, which is opened as a tier-3
candidate rather than built this round: it would be a second series break on a
line already broken today. Also noted: PortWatch REVISES history — the service
now serves 2,133 transits for observation 07-12 where the v1 record captured
2,137.

### Round 8 — 2026-07-23 (tier-2 red/blue divergence; cn_flights retired)

A diverge-then-adversarial round: six blue-team domain sweeps proposed candidates
(each required to probe a real free source), then every candidate ran through a
red-team attack and a neutral judge. Outcome: **16 rejected, 1 adjustment, zero
added.** A harsh screen is the honest one — the failure to fund is the finding.

**Acted on — RETIRE `cn_flights`** (structurally confounded, not underperforming;
do not re-litigate as "needs more readings"). Its alarm direction is *down*, and
its dominant confound — a community ADS-B feeder dropping offline — pushes the
count *down too*, so the sensor is collinear with its own failure and can never
separate "China grounded its metros" from "a Beijing receiver rebooted." Verified
live on the 32-row history: 2026-07-20 read Beijing=0 (physically impossible for a
metro), total 33, z=−2.41 in the alarm direction — a feeder outage wearing the
costume of an airspace collapse; Beijing then sat at 0/3/1/2 aircraft for four
straight days. The only tremble ever recorded (07-10, z=+6.07) was benign-direction
(coverage coming *on*). More data cannot cure a collinearity, and a normalization
cannot either (the dropout is per-metro and no keyless same-frame denominator is
exposed). A broken sensor pointed in the alarm direction is worse than an empty
slot — it manufactures the exact false "China air-traffic collapse" the instrument
exists to suppress. CSV archived to `data/archive/cn_flights_retired.csv`; the 8th
watchlist slot is now **open and disclosed** (the screen found nothing worth
filling it with).

**Why nothing was added — the pattern.** Almost every "new domain" candidate was
plumbing-clean (keyless, daily, fresh, real numbers) and died on the GUARD GATE:
they were free-floating physical or market-clearing reads dressed as guarded
equilibria. River gauges (`rhine_kaub`, a Mississippi stage), a Brazilian
reservoir level (`br_hydro_reserve`), French power net-exchange and nuclear
availability (`fr_net_exchange`, `fr_nuclear`), GB interconnector flows — in each,
nothing self-interested defends the level and pushes it back when it drifts;
scarcity or market coupling moving the number is arbitrage/weather succeeding, not
a guard being overpowered. That is the VIX/GDELT signature, and it fails the gate
categorically — no accumulation of readings converts a weather gauge into a
tension indicator. Two candidates passed the guard gate and still died on the
project's own statistics: `sofr99_dispersion` (SOFR99−SOFR is quantized to integer
basis points, so Qn=0 and the row is STATUS_FLAT on ~23% of windows — it literally
cannot score in the calm regime, failure mode #5 in terminal form) and
`taiwan_strait_transits` (an AIS gap-then-backfill artifact fires a false −7 to −11
"blockade" z on calm days, and it re-taps the weekly PortWatch pipeline).

**Adjustments screened and REJECTED (kept as-is, with the reason on record):**
- `grid_frequency` daily-max → minutes-outside-band: the duration statistic reads
  structurally zero on 41% of days at the honest ±100 mHz limit (failure mode #5),
  destroys the keyless Statnett fallback (a 60s snapshot can't compute a daily
  duration), and forces a baseline reset. The mild right-skew of the max (2 up-
  trembles in 32 rows) is the lesser evil. A skew-aware one-sided z on the existing
  max is the better idea, but it is a different, unbuilt change.
- `gnss_interference` regional-breadth: the ratio (hot/eligible) form does NOT
  divide out coverage growth — ADS-B feeders densify preferentially in already-hot
  theatres, so the breadth statistic drifts +43% over 24 months from the sampling
  frame alone (failure mode #1, the exact reason it was demoted in r7). Stays a
  global line.
- `chokepoint_per_strait_breadth`: the proposed volume gate (median ≥ 40) deletes
  Bab el-Mandeb, Panama, and Hormuz — the very straits the line exists to watch —
  from the panel. Rejected; `chokepoint_breadth` stays the 28-strait total.
- `capital_premium` keep-as-orthogonal: a label-only rebuttal that answered only
  one of the two demotion grounds; no change.

**Biggest gap still unaddressed** (unchanged from r7): the LEVEL-vs-CHANGE limit.
A rolling z is a change detector, so a sustained crisis reads calm once it sits
inside its own baseline — and notably, most of the rejected candidates fail *worse*
on exactly this axis (a heatwave-driven nuclear depression, a multi-week drought,
a year-long net-importer flip all go blind mid-crisis). Widening coverage does not
address it; only a level reference would, and that remains a deliberate open
question rather than a build.
