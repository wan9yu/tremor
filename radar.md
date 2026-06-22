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

4-8-16 is a steady-state target, not a forced cut: a line is never demoted without
evidence. Rubric scores are 0–3; computed metrics show `—` until there is enough
history (~20 days).

---

## Tier 1 — primary  (5 / 4 · over capacity, see log)

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | Orthog | note |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|---|
| flights | airspace (EU/US/JP) | 3 | 3 | 2 | — | — | — | archetype side-channel; semi-global |
| credit_spread | financial (US→global) | 3 | 3 | 3 | — | — | — | global bellwether; locked |
| capital_premium | capital controls (Korea) | 2 | 3 | 1 | — | — | — | national; demotion candidate |
| grid_frequency | infrastructure (Nordic) | 2 | 3 | 1 | — | — | — | regional; demotion candidate |
| cnh_cny | capital controls (China) | 2 | 3 | 2 | — | — | — | national but globally weighty |

## Tier 2 — watchlist  (2 / 8)

| indicator | domain | Lev | Guard | Reach | Reliab | Respons | note |
|---|---|:--:|:--:|:--:|:--:|:--:|---|
| cn_flights | airspace (China) | 3 | 3 | 1 | — | — | sparse ADS-B coverage; observing if signal survives |
| gdelt | attention (global) | 1 | 0 | 3 | — | — | no guard → can never reach tier-1; "felt vs real" contrast only |

## Tier 3 — candidate ideas  (5 / 16 · under target, fills over rounds)

All must clear the cadence gate (daily-persistent or daily-aggregated). Sorted by readiness.

| candidate | domain | hypothesis (guard → leaking hand) | Lev | Guard | Reach | data source (free, daily) |
|---|---|---|:--:|:--:|:--:|---|
| chokepoint_transit | trade | trade economics + the canal authorities keep ships flowing → a drop in Suez/Hormuz/Panama transits leaks blockade, war, drought, attack | 3 | 3 | 3 | ✅ **IMF PortWatch** `Daily_Chokepoints_Data` (Suez 26–39/day now — already depressed by Red Sea) |
| sofr_stress | financial | the Fed defends the policy rate → a SOFR spike leaks dollar-funding seizure (cf. Sept 2019 repo) | 3 | 3 | 3 | ✅ FRED `SOFR` (key in CI) |
| net_outages | infrastructure | ISPs/states defend routing → a spike in national internet outages leaks censorship, war, cable cuts | 2 | 2 | 3 | ✅ **IODA** (Georgia Tech), keyless |
| ar_blue | capital controls | the central bank burns reserves to defend the official peso → a blue-dollar premium leaks capital flight, controls, devaluation | 2 | 3 | 1 | ✅ dolarapi (premium ~0% now) |
| ve_parallel | capital controls | same as ar_blue, Venezuela → a parallel-rate gap leaks hyperinflation / controls | 2 | 3 | 1 | ✅ ve.dolarapi (parallel ~768/USD) |

The two 3/3/3 candidates (chokepoint_transit, sofr_stress) are **global, strongly guarded,
high-leverage, daily, free** — stronger on the rubric than the three national/regional tier-1
lines. They are the top build targets: once they accumulate history they can challenge for
tier-1.

### Rejected
| candidate | reason |
|---|---|
| stablecoin_peg | **fails the cadence gate** — depegs are intraday-transient (recover in minutes–hours), so a once-daily snapshot aliases past the event. Would need an intraday daily-min source. |

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
