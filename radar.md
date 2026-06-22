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

## Tier 3 — candidate ideas  (4 / 16 · under target, fills over rounds)

| candidate | hypothesis (guard → leaking hand) | Lev | Guard | Reach | data source | source free? |
|---|---|:--:|:--:|:--:|---|---|
| stablecoin_peg | issuer reserves + arbitrage hold USDT≈$1 → a break leaks crypto/dollar-liquidity stress | 2 | 2 | 3 | Coinbase USDT-USD spot | ✅ verified keyless (USDT 0.9988 now) |
| sofr_stress | the Fed defends the policy rate → a SOFR spike leaks dollar-funding seizure (cf. Sept 2019 repo) | 3 | 3 | 3 | FRED `SOFR` | ✅ FRED (key already in CI) |
| chokepoint_transit | trade economics keep ships moving → a drop in Suez/Hormuz transits leaks blockade, war, drought | 3 | 2 | 3 | AIS (Suez/Hormuz) | ⚠️ no free source verified yet |
| net_outages | ISPs defend routing → a spike in national internet outages leaks censorship, war, cable cuts | 2 | 2 | 3 | Cloudflare Radar | ⚠️ needs auth token (not keyless) |

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
