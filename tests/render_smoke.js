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
function el(id) {
  if (made[id]) return made[id];
  const node = {
    id, _html: "", _text: "", hidden: false, className: "", dataset: {},
    style: { setProperty() {}, removeProperty() {}, getPropertyValue: () => "" }, classList: { add() {}, remove() {}, toggle() {} },
    appendChild() {}, setAttribute() {}, removeAttribute() {},
    addEventListener() {}, getContext: () => ({}),
    set innerHTML(v) { this._html = String(v); }, get innerHTML() { return this._html; },
    set textContent(v) { this._text = String(v); }, get textContent() { return this._text; },
    set onclick(f) { this._onclick = f; }, get onclick() { return this._onclick; },
  };
  return (made[id] = node);
}
global.document = {
  documentElement: {}, body: el("body"),
  getElementById: el, createElement: () => el("tmp-" + Math.random()),
  querySelectorAll: () => [], querySelector: () => null, addEventListener() {},
  get cookie() { return ""; }, set cookie(v) {},
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

(0, eval)(js + "\n;globalThis.__P={LINES,covModal,resoModal,lineModal,render,load};");
const {LINES,covModal,resoModal,lineModal,render,load}=globalThis.__P;

(async () => {
  try {
  await load();
  for (const lang of ["en", "zh"]) {
    global.document.cookie = "tremor_lang=" + lang;
    try { render(); } catch (e) { errors.push(`render(${lang}): ${e.stack || e}`); }
  }
  // exercise every modal builder, in both languages
  for (const lang of ["en", "zh"]) {
    try { covModal(lang); resoModal(lang); } catch (e) { errors.push(`modal(${lang}): ${e.stack || e}`); }
    for (const L of LINES) {
      try { lineModal(L, lang); } catch (e) { errors.push(`lineModal(${L.id},${lang}): ${e.stack || e}`); }
    }
  }
  await new Promise(r => setTimeout(r, 50));
  if (errors.length) { console.log("FAILURES:\n" + errors.join("\n\n")); process.exit(1); }
  console.log("render OK in both languages; no runtime errors");
  console.log("  headline:", el("count-n").textContent, "/", el("count-of").textContent);
  console.log("  label   :", el("count-label").innerHTML.replace(/<[^>]+>/g, "").trim());
  console.log("  coverage:", el("coverage").innerHTML.replace(/<[^>]+>/g, "").trim().slice(0, 110));
  } catch (e) { console.log("HARNESS FAILURE: " + (e && e.stack || e)); process.exit(1); }
})();
