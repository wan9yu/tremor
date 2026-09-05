// Execute the dashboard's real render path against the real CSVs, in both
// languages, plus every modal builder — then again against a synthetic
// fixture DATA that exercises every status core/normalize.py can write to a
// row, plus the tier-2 gap-chip run (T21).
//
// The dashboard is a single 40k-character inline script with no build step, so a
// syntax check is all it used to get — and a syntax check cannot see a
// temporal-dead-zone read, a missing i18n key, or a modal that throws on one
// line out of fifteen. Exactly that shipped once: a `const` read four lines
// before its declaration, which threw on every render. The real CSVs are
// whatever the record happens to hold today, so they cannot be relied on to
// cover every status on every run (`stale`, say, is rare) — the fixture pass
// is what guarantees every status is actually exercised, every run.
//
// Usage:  node tests/render_smoke.js
const fs = require("fs"), path = require("path");
const REPO = path.dirname(__dirname);

const html = fs.readFileSync(path.join(REPO, "docs/index.html"), "utf8");
const js = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).join("\n");

const made = {};
// createElement()'d nodes that got appendChild()'d in during the render just
// finished; reset per language below so a language's sweep only sees its own
// appended content, not the previous language's leftovers.
let appendedNodes = [];
function el(id) {
  if (made[id]) return made[id];
  const node = {
    id, _html: "", _text: "", hidden: false, className: "", dataset: {},
    style: { setProperty() {}, removeProperty() {}, getPropertyValue: () => "" }, classList: { add() {}, remove() {}, toggle() {} },
    appendChild(child) { appendedNodes.push(child); return child; },
    setAttribute() {}, removeAttribute() {},
    addEventListener() {}, getContext: () => ({}),
    set innerHTML(v) { this._html = String(v); }, get innerHTML() { return this._html; },
    set textContent(v) { this._text = String(v); }, get textContent() { return this._text; },
    set onclick(f) { this._onclick = f; }, get onclick() { return this._onclick; },
  };
  return (made[id] = node);
}
// A real cookie jar: `document.cookie = "k=v[;attrs]"` sets ONE cookie (browser
// semantics -- trailing attributes like path=/max-age are parsed off and
// ignored, other cookies are untouched), and the getter returns the
// accumulated "k1=v1; k2=v2" string. The old stub always returned "", so
// getLang()/getRange() (docs/index.html) always fell back to their defaults
// and the zh render path never actually executed.
let cookieJar = {};
global.document = {
  documentElement: {}, body: el("body"),
  getElementById: el, createElement: () => el("tmp-" + Math.random()),
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {},
  get cookie() { return Object.entries(cookieJar).map(([k, v]) => `${k}=${v}`).join("; "); },
  set cookie(v) {
    const kv = String(v).split(";")[0];
    const eq = kv.indexOf("=");
    if (eq > -1) cookieJar[kv.slice(0, eq).trim()] = kv.slice(eq + 1).trim();
  },
};
global.window = { addEventListener() {}, matchMedia: () => ({ matches: false }) };
global.Chart = class { constructor() {} destroy() {} update() {} };
global.Chart.defaults = { font: {}, color: "", plugins: { legend: {} } };
global.fetch = async (url) => {
  const p = path.join(REPO, "docs", url);
  if (!fs.existsSync(p)) return { ok: false, status: 404, text: async () => "" };
  return { ok: true, status: 200, text: async () => fs.readFileSync(p, "utf8") };
};

const errors = [];
process.on("unhandledRejection", e => errors.push("unhandledRejection: " + (e && e.stack || e)));

// docs/index.html has no `setDATA` function -- DATA is a top-level `let`,
// reassigned by load(). Synthesize a setter in this same eval scope (it closes
// over the real `DATA` binding) and export it on globalThis.__P so T21's
// fixtures below can inject DATA directly, bypassing fetch/load().
(0, eval)(js + "\n;globalThis.__P={LINES,T,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load,setDATA:function(v){DATA=v;}};");
const {LINES,T,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load,setDATA}=globalThis.__P;

// Rendered text lives in two places: nodes looked up by id (`made`, mutated in
// place on every render -- so at sweep time, right after render(), they hold
// only this language's content) and nodes appendChild()'d in during render
// (`appendedNodes`, reset per language above each render() call). Today all
// three appendChild sites in docs/index.html happen to pass createElement()'d
// nodes, which are already registered in `made` too -- so `appendedNodes` is
// redundant with `made` right now. It's kept as defense-in-depth: it also
// catches a node appendChild()'d WITHOUT going through createElement (e.g. a
// clone or a text node), which `made` alone would miss.
function sweepForBadValues(lang) {
  const bits = [];
  for (const n of Object.values(made)) bits.push(n._text, n._html);
  for (const n of appendedNodes) bits.push(n._text, n._html);
  const all = bits.join("\n");
  if (all.includes("undefined")) errors.push(`rendered output (${lang}) contains the literal substring "undefined"`);
  if (all.includes("NaN")) errors.push(`rendered output (${lang}) contains the literal substring "NaN"`);
}

// T21: a synthetic DATA covering every status core/normalize.py can write to
// a row (scoring, warming-up, stale, dark, closed, no-spread) PLUS the new
// tier-2 gap-chip state docs/index.html:GAP_STATUSES/GAP_RUN_LOUD introduces
// -- a tier-2 line dark for >= GAP_RUN_LOUD consecutive collections must
// render a "NO DATA" gap chip, and (the boundary case) a tier-2 line dark for
// only ONE collection must NOT. Exercised via setDATA(), bypassing
// fetch/load() entirely, so this needs no network and no real CSVs.
//
// Every field a real parseCSV() row would carry is filled in explicitly
// (raw_value, z_score, trembling, direction, source_note, obs_date, status)
// -- a field silently left `undefined` would string-concatenate into the
// rendered HTML as the literal substring "undefined", which is exactly what
// sweepForBadValues() below is built to catch, so leaving one out would be
// invisible right up until it wasn't.
function fixtureRow(overrides) {
  return Object.assign({
    date: "", raw_value: "", z_score: "", trembling: "0", direction: "",
    source_note: "fixture row", obs_date: "", status: "scoring",
  }, overrides);
}
const FIXTURE_DATE = "2026-09-03";
function buildFixtureData() {
  const lines = {};
  // --- tier-1 (all four): one of each of scoring+trembling, scoring+calm,
  // closed, dark -- the tier-1 strip only branches on hasToday/isClosed, so
  // this is what exercises that branch, not the full statusLabel map (that
  // map is read only by the tier-2 watchlist below).
  lines.flights = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1000", z_score: "-3.5",
    trembling: "1", direction: "down", status: "scoring" })];               // alarm=down: fires
  lines.credit_spread = [fixtureRow({ date: FIXTURE_DATE, raw_value: "4.2", z_score: "0.4",
    trembling: "0", direction: "up", status: "scoring" })];                 // calm
  lines.cnh_cny = [fixtureRow({ date: FIXTURE_DATE, status: "closed",
    source_note: "no new observation: FX weekend, both legs frozen" })];
  lines.net_outages = [fixtureRow({ date: FIXTURE_DATE, status: "dark",
    source_note: "IODA request failed: timeout" })];
  // --- tier-2: the remaining statuses, plus the gap-chip run boundary ---
  lines.capital_premium = [fixtureRow({ date: FIXTURE_DATE, raw_value: "2.1", status: "warming-up" })];
  lines.grid_frequency = [fixtureRow({ date: FIXTURE_DATE, raw_value: "12", status: "no-spread" })];
  lines.gdelt = [fixtureRow({ date: FIXTURE_DATE, raw_value: "0.18", status: "stale",
    source_note: "[stale: observation already recorded]" })];
  lines.vix = [fixtureRow({ date: FIXTURE_DATE, status: "closed" })];
  lines.em_corp_oas = [fixtureRow({ date: FIXTURE_DATE, raw_value: "1.4", z_score: "0.2", status: "scoring" })];
  // ONE dark day: below GAP_RUN_LOUD (2) -- must render plain, not a gap chip.
  lines.space_weather = [
    fixtureRow({ date: "2026-09-02", raw_value: "3", z_score: "0.1", status: "scoring" }),
    fixtureRow({ date: FIXTURE_DATE, status: "dark", source_note: "NOAA SWPC request failed" }),
  ];
  // A dark run AT GAP_RUN_LOUD -- the hkma_aggr_balance scenario this task is
  // named for (dark 7 of its last 8 real collections as of this writing) --
  // must render the gap chip.
  lines.hkma_aggr_balance = [
    fixtureRow({ date: "2026-09-01", status: "dark", source_note: "HKMA HTTP 502" }),
    fixtureRow({ date: "2026-09-02", status: "dark", source_note: "HKMA request failed: ReadTimeout" }),
    fixtureRow({ date: FIXTURE_DATE, status: "dark", source_note: "HKMA HTTP 502" }),
  ];
  const summary = [{ date: FIXTURE_DATE, trembling_count: "1", dark_count: "1", blind_count: "0" }];
  return { summary, dates: [FIXTURE_DATE], lines, annotations: [], annoMap: new Map(), stuck: [] };
}

// T22 (Task 2): headline discloses adjudication + machine leans + episode-age.
// Three firing tier-1 lines, each exercising one new state, PLUS the
// precedence rule (a human annotation wins over a same-day machine lean) --
// flights carries BOTH an `artifact` annotation and a common-mode lean on the
// same day, and only the annotation's qualifier may surface.
const ADJ_DATE = "2026-09-10";
const ADJ_PREV_DATE = "2026-09-09";
function buildAdjFixtureData() {
  const lines = {
    // (a) adjudicated artifact -- AND a same-day common-mode lean that must
    // be suppressed by precedence (the lean's own evidence string is the
    // canary: it must never appear in the rendered output).
    flights: [fixtureRow({ date: ADJ_DATE, raw_value: "500", z_score: "-4.1",
      trembling: "1", direction: "down", status: "scoring" })],
    // (b) common-mode lean, no annotation at all -- the lean qualifier fires.
    net_outages: [fixtureRow({ date: ADJ_DATE, raw_value: "10", z_score: "5.0",
      trembling: "1", direction: "up", status: "scoring" })],
    // (c) a 2-day trembling run, no annotation, and an "ok" lean (must render
    // nothing -- only common-mode does).
    credit_spread: [
      fixtureRow({ date: ADJ_PREV_DATE, raw_value: "4.0", z_score: "3.2",
        trembling: "1", direction: "up", status: "scoring" }),
      fixtureRow({ date: ADJ_DATE, raw_value: "4.1", z_score: "3.4",
        trembling: "1", direction: "up", status: "scoring" }),
    ],
    // bystander: calm, present so all four tier-1 lines have a today row.
    cnh_cny: [fixtureRow({ date: ADJ_DATE, raw_value: "10", z_score: "0.1",
      trembling: "0", direction: "up", status: "scoring" })],
  };
  const annotations = [
    { date: ADJ_DATE, line: "flights", verdict: "artifact", note: "fixture: instrument artifact" },
  ];
  const leans = [
    { date: ADJ_DATE, line: "flights", lean: "common-mode", evidence: "MUST NOT RENDER: annotation wins" },
    { date: ADJ_DATE, line: "net_outages", lean: "common-mode", evidence: "7/7 synchronized" },
    { date: ADJ_DATE, line: "credit_spread", lean: "ok", evidence: "0/4 corroborated" },
  ];
  const summary = [{ date: ADJ_DATE, trembling_count: "3", dark_count: "0", blind_count: "0" }];
  return {
    summary, dates: [ADJ_PREV_DATE, ADJ_DATE], lines,
    annotations, annoMap: new Map(annotations.map(a => [a.line + "|" + a.date, a])),
    leans, leanMap: new Map(leans.map(r => [r.line + "|" + r.date, r])),
    stuck: [],
  };
}

// T23 (review fix): data/annotations.csv keys plenty of method/correction/
// retraction rows to the SAME (line,date) as a genuine verdict -- none of
// those three actually adjudicates a tremble, and 2026-09-04 net_outages
// carries both a retraction AND an artifact row for the same day. Two cases
// the T22 fixture above did not cover:
//   (d) a firing line with ONLY a same-day `method` annotation must still
//       disclose its common-mode lean and hatch its pill -- method is not an
//       adjudication, so this must read exactly like "no annotation at all".
//   (e) a (line,date) carrying BOTH a non-adjudicating row and an `artifact`
//       row, with the artifact row written FIRST and a later, non-adjudicating
//       `correction` row LAST -- a last-row-wins lookup (over ALL rows,
//       adjudicating or not) would wrongly return the correction and silently
//       drop the artifact qualifier; the fix must return the artifact row
//       regardless of position.
const ADJ2_DATE = "2026-09-11";
function buildAdjPrecedenceFixtureData() {
  const lines = {
    // (e): the artifact row is written BEFORE the correction row below.
    flights: [fixtureRow({ date: ADJ2_DATE, raw_value: "480", z_score: "-4.3",
      trembling: "1", direction: "down", status: "scoring" })],
    // (d): method only -- no adjudication.
    net_outages: [fixtureRow({ date: ADJ2_DATE, raw_value: "12", z_score: "5.5",
      trembling: "1", direction: "up", status: "scoring" })],
    // bystanders: calm, present so all four tier-1 lines have a today row.
    credit_spread: [fixtureRow({ date: ADJ2_DATE, raw_value: "3.0", z_score: "0.2",
      trembling: "0", direction: "up", status: "scoring" })],
    cnh_cny: [fixtureRow({ date: ADJ2_DATE, raw_value: "10", z_score: "0.1",
      trembling: "0", direction: "up", status: "scoring" })],
  };
  const annotations = [
    { date: ADJ2_DATE, line: "flights", verdict: "artifact", note: "fixture: artifact, written FIRST" },
    { date: ADJ2_DATE, line: "net_outages", verdict: "method", note: "fixture: methodology note -- not a verdict on today's tremble" },
    { date: ADJ2_DATE, line: "flights", verdict: "correction", note: "fixture: a later, non-adjudicating row -- must NOT shadow the artifact row above" },
  ];
  const leans = [
    { date: ADJ2_DATE, line: "net_outages", lean: "common-mode", evidence: "12/12 synchronized" },
  ];
  const summary = [{ date: ADJ2_DATE, trembling_count: "2", dark_count: "0", blind_count: "0" }];
  return {
    summary, dates: [ADJ2_DATE], lines,
    annotations, annoMap: new Map(annotations.map(a => [a.line + "|" + a.date, a])),
    leans, leanMap: new Map(leans.map(r => [r.line + "|" + r.date, r])),
    stuck: [],
  };
}

(async () => {
  try {
  await load();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    appendedNodes = [];
    try { render(); sweepForBadValues(lang); } catch (e) { errors.push(`render(${lang}): ${e.stack || e}`); }
  }
  // exercise every modal builder, in both languages
  for (const lang of ["en", "zh"]) {
    try { covModal(lang); resoModal(lang); levelModal(lang); } catch (e) { errors.push(`modal(${lang}): ${e.stack || e}`); }
    for (const L of LINES) {
      try { lineModal(L, lang); } catch (e) { errors.push(`lineModal(${L.id},${lang}): ${e.stack || e}`); }
      // openTier2Modal is only ever invoked (in docs/index.html) for tier-2
      // lines, and it side-effects through openModal() rather than returning
      // html, so it needs DATA (already loaded above) and a real tier-2 row.
      if ((L.tier || 1) === 2) {
        try { openTier2Modal(L, lang); } catch (e) { errors.push(`openTier2Modal(${L.id},${lang}): ${e.stack || e}`); }
      }
    }
  }
  // T21: drive the fixture DATA through the real render path, both languages
  // -- every normalize status plus the tier-2 gap-chip run, and no crash / no
  // undefined / no NaN for any of them.
  const fixture = buildFixtureData();
  const fixtureSummary = fixture.summary[fixture.summary.length - 1];
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(fixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("fixture-" + lang);
      // summary <-> page firing-count binding: the headline "N" the page
      // shows is read straight off summary.csv's own trembling_count column
      // (count-n's textContent), so a fixture summary row and a fresh count
      // over its own tier-1 rows must imply the SAME N -- this asserts the
      // page actually reads that column rather than silently drifting from it.
      const shownN = el("count-n").textContent;
      if (shownN !== fixtureSummary.trembling_count) {
        errors.push(`fixture(${lang}): headline shows ${shownN}, but the fixture's `
          + `summary row implies trembling_count=${fixtureSummary.trembling_count}`);
      }
      // gap chip: exactly the GAP_RUN_LOUD+ dark line (hkma_aggr_balance)
      // renders one -- the single-dark-day line (space_weather) must not.
      const gapItems = appendedNodes.filter(n => (n.className || "").includes("wl-gap"));
      if (gapItems.length !== 1) {
        errors.push(`fixture(${lang}): expected exactly 1 tier-2 gap chip `
          + `(hkma_aggr_balance's dark run), found ${gapItems.length}`);
      } else if (!/NO DATA|无数据/.test(gapItems[0]._html)) {
        errors.push(`fixture(${lang}): gap chip did not carry the "dark" statusLabel text: ${gapItems[0]._html}`);
      }
      // blind chip: warming-up (capital_premium) and no-spread (grid_frequency).
      // wl-blind is an inline <span> INSIDE the item's innerHTML (unlike
      // wl-gap, which also marks the outer wl-item node's own className), so
      // this greps the rendered markup rather than filtering by className.
      const blindItems = appendedNodes.filter(n => (n._html || "").includes('class="wl-blind"'));
      if (blindItems.length !== 2) {
        errors.push(`fixture(${lang}): expected exactly 2 BLIND watchlist items `
          + `(warming-up + no-spread), found ${blindItems.length}`);
      }
    } catch (e) { errors.push(`fixture render(${lang}): ${e.stack || e}`); }
    // exercise the modal builders against the fixture too, tier-1 and tier-2.
    try { covModal(lang); resoModal(lang); levelModal(lang); } catch (e) { errors.push(`fixture modal(${lang}): ${e.stack || e}`); }
    for (const id of Object.keys(fixture.lines)) {
      const L = LINES.find(x => x.id === id);
      if (!L) continue;
      try { lineModal(L, lang); } catch (e) { errors.push(`fixture lineModal(${id},${lang}): ${e.stack || e}`); }
      if ((L.tier || 1) === 2) {
        try { openTier2Modal(L, lang); } catch (e) { errors.push(`fixture openTier2Modal(${id},${lang}): ${e.stack || e}`); }
      }
    }
  }

  // T22: adjudication/lean/run disclosure (Task 2), both languages -- the
  // headline integer must not move, precedence must hold (flights' lean
  // evidence must never surface once it is annotated), and all three new
  // qualifiers plus the strip's pill-hatch must actually render.
  const adjFixture = buildAdjFixtureData();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(adjFixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("adj-" + lang);
      const Tl = T[lang];
      const shownN = el("count-n").textContent;
      if (shownN !== "3") {
        errors.push(`adj(${lang}): headline shows ${shownN}, expected 3 -- `
          + `the integer must never move for a disclosure qualifier`);
      }
      const labelHtml = el("count-label").innerHTML;
      if (!labelHtml.includes(Tl.verdictLabel.artifact)) {
        errors.push(`adj(${lang}): missing the artifact-adjudication qualifier for flights`);
      }
      const leanCore = Tl.leanNote("", "7/7 synchronized").replace(" · ", "");
      if (!labelHtml.includes(leanCore)) {
        errors.push(`adj(${lang}): missing the common-mode machine-lean qualifier for net_outages`);
      }
      const suppressedLeanCore = Tl.leanNote("", "MUST NOT RENDER: annotation wins").replace(" · ", "");
      if (labelHtml.includes(suppressedLeanCore)) {
        errors.push(`adj(${lang}): precedence violated -- flights' machine lean rendered `
          + `even though it carries a human annotation`);
      }
      const runCore = Tl.runNote("", 2).replace(" · ", "");
      if (!labelHtml.includes(runCore)) {
        errors.push(`adj(${lang}): missing the 2-day trembling-run qualifier for credit_spread`);
      }
      // strip pill hatch: TIER1 order is [flights, credit_spread, cnh_cny,
      // net_outages] -- flights (artifact) and net_outages (common-mode lean)
      // must carry the "adjudicated" hatch class; credit_spread (run only,
      // "ok" lean) must not.
      const instNodes = appendedNodes.filter(n => n.className === "inst");
      if (instNodes.length !== 4) {
        errors.push(`adj(${lang}): expected 4 tier-1 strip chips, found ${instNodes.length}`);
      } else {
        if (!/class="pill trembling adjudicated"/.test(instNodes[0]._html))
          errors.push(`adj(${lang}): flights' pill missing the adjudicated hatch class`);
        if (/adjudicated/.test(instNodes[1]._html))
          errors.push(`adj(${lang}): credit_spread's pill wrongly carries the adjudicated hatch class`);
        if (!/class="pill trembling adjudicated"/.test(instNodes[3]._html))
          errors.push(`adj(${lang}): net_outages' pill missing the adjudicated hatch class`);
      }
    } catch (e) { errors.push(`adj render(${lang}): ${e.stack || e}`); }
  }

  // T23 (review fix): method-only annotation must not suppress the lean/pill
  // (case d), and an adjudicating row must win regardless of row order among
  // duplicates for the same (line,date) (case e).
  const adj2Fixture = buildAdjPrecedenceFixtureData();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    setDATA(adj2Fixture);
    appendedNodes = [];
    try {
      render();
      sweepForBadValues("adj2-" + lang);
      const Tl = T[lang];
      const shownN = el("count-n").textContent;
      if (shownN !== "2") {
        errors.push(`adj2(${lang}): headline shows ${shownN}, expected 2 -- `
          + `the integer must never move for a disclosure qualifier`);
      }
      const labelHtml = el("count-label").innerHTML;
      // (d) net_outages carries only a `method` annotation -- not an
      // adjudication -- so its common-mode lean must still surface.
      const leanCore = Tl.leanNote("", "12/12 synchronized").replace(" · ", "");
      if (!labelHtml.includes(leanCore)) {
        errors.push(`adj2(${lang}): a same-day METHOD annotation wrongly suppressed `
          + `net_outages' common-mode lean qualifier (method must not act as an adjudication)`);
      }
      // (e) flights carries an `artifact` row written FIRST and a `correction`
      // row written LAST for the same (line,date) -- the artifact qualifier
      // must still render (a last-row-over-ALL-rows lookup would miss it).
      if (!labelHtml.includes(Tl.verdictLabel.artifact)) {
        errors.push(`adj2(${lang}): flights' artifact adjudication was shadowed by a later, `
          + `non-adjudicating (correction) row for the same (line,date) -- `
          + `the adjudicating row must win regardless of order`);
      }
      // strip pill hatch: TIER1 order is [flights, credit_spread, cnh_cny,
      // net_outages] -- flights (artifact, order-independent) and
      // net_outages (method-only + common-mode lean) must both hatch.
      const instNodes = appendedNodes.filter(n => n.className === "inst");
      if (instNodes.length !== 4) {
        errors.push(`adj2(${lang}): expected 4 tier-1 strip chips, found ${instNodes.length}`);
      } else {
        if (!/class="pill trembling adjudicated"/.test(instNodes[0]._html))
          errors.push(`adj2(${lang}): flights' pill missing the adjudicated hatch class `
            + `(shadowed by the later correction row?)`);
        if (!/class="pill trembling adjudicated"/.test(instNodes[3]._html))
          errors.push(`adj2(${lang}): net_outages' pill missing the adjudicated hatch class `
            + `(a method annotation must not block the common-mode lean's hatch)`);
      }
    } catch (e) { errors.push(`adj2 render(${lang}): ${e.stack || e}`); }
  }

  await new Promise(r => setTimeout(r, 50));
  if (errors.length) { console.log("FAILURES:\n" + errors.join("\n\n")); process.exit(1); }
  console.log("render OK in both languages; no runtime errors, no undefined/NaN");
  console.log("  headline:", el("count-n").textContent, "/", el("count-of").textContent);
  console.log("  label   :", el("count-label").innerHTML.replace(/<[^>]+>/g, "").trim());
  console.log("  coverage:", el("coverage").innerHTML.replace(/<[^>]+>/g, "").trim().slice(0, 110));
  } catch (e) { console.log("HARNESS FAILURE: " + (e && e.stack || e)); process.exit(1); }
})();
