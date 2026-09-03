// Execute the dashboard's real render path against the real CSVs, in both
// languages, plus every modal builder.
//
// The dashboard is a single 40k-character inline script with no build step, so a
// syntax check is all it used to get — and a syntax check cannot see a
// temporal-dead-zone read, a missing i18n key, or a modal that throws on one
// line out of fifteen. Exactly that shipped once: a `const` read four lines
// before its declaration, which threw on every render.
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
// over the real `DATA` binding) and export it on globalThis.__P purely for
// T21's fixtures to inject DATA directly, bypassing fetch/load(). Nothing in
// this file calls it, so it's left out of the local destructure below.
(0, eval)(js + "\n;globalThis.__P={LINES,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load,setDATA:function(v){DATA=v;}};");
const {LINES,covModal,resoModal,lineModal,levelModal,openTier2Modal,render,load}=globalThis.__P;

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
  await new Promise(r => setTimeout(r, 50));
  if (errors.length) { console.log("FAILURES:\n" + errors.join("\n\n")); process.exit(1); }
  console.log("render OK in both languages; no runtime errors, no undefined/NaN");
  console.log("  headline:", el("count-n").textContent, "/", el("count-of").textContent);
  console.log("  label   :", el("count-label").innerHTML.replace(/<[^>]+>/g, "").trim());
  console.log("  coverage:", el("coverage").innerHTML.replace(/<[^>]+>/g, "").trim().slice(0, 110));
  } catch (e) { console.log("HARNESS FAILURE: " + (e && e.stack || e)); process.exit(1); }
})();
