#!/usr/bin/env node
/*
 * Backtest for the net-salary calculator in index-1.html.
 *
 * Loads the actual calculation functions straight out of index-1.html
 * (no re-typing of the formulas) and checks them against an
 * independently written reference implementation across a wide range
 * of gross salaries and bracket boundaries, plus a handful of
 * full end-to-end scenarios (credit points, pension, oleh chadash).
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const htmlPath = path.join(__dirname, '..', 'index-1.html');
const html = fs.readFileSync(htmlPath, 'utf8');

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) throw new Error('Could not find <script> block in index-1.html');

const cutMarker = 'function calculate(){';
const cutIdx = scriptMatch[1].indexOf(cutMarker);
if (cutIdx === -1) throw new Error('Could not find calculate() to isolate pure functions');
const pureSource = scriptMatch[1].slice(0, cutIdx);

const sandbox = {};
vm.createContext(sandbox);
// top-level `const`/`let` bindings aren't exposed as properties of the
// vm context's global object, so re-export them explicitly.
vm.runInContext(
  pureSource + '\nthis.POINT_VALUE = POINT_VALUE; this.brackets = brackets;',
  sandbox,
  { filename: 'index-1.html (extracted)' }
);

const { calcIncomeTax, calcBLHealth, POINT_VALUE, brackets } = sandbox;

// --- Independent reference implementation (written separately, not copied) ---
function refIncomeTax(gross) {
  const edges = [0, 7010, 10060, 16150, 22440, 46690, 60130, Infinity];
  const rates = [0.10, 0.14, 0.20, 0.31, 0.35, 0.47, 0.50];
  let tax = 0;
  for (let i = 0; i < rates.length; i++) {
    const lo = edges[i], hi = edges[i + 1];
    if (gross <= lo) break;
    tax += (Math.min(gross, hi) - lo) * rates[i];
  }
  return tax;
}

function refBLHealth(gross) {
  const lowCap = 7122, highCap = 49030;
  const low = Math.min(gross, lowCap);
  const high = Math.max(0, Math.min(gross, highCap) - lowCap);
  return { bl: low * 0.004 + high * 0.07, health: low * 0.031 + high * 0.05 };
}

function refNet(gross, { points = 2.25, oleh = false, pensionPct = 0 } = {}) {
  const tax = oleh ? 0 : Math.max(0, refIncomeTax(gross) - points * 242);
  const { bl, health } = refBLHealth(gross);
  const pension = gross * (pensionPct / 100);
  return gross - tax - bl - health - pension;
}

const EPS = 0.01; // agam tolerance for floating point noise
let failures = [];
let checked = 0;

function approxEqual(a, b) {
  return Math.abs(a - b) < EPS;
}

// 1) Sweep across a dense range of gross salaries, including every bracket
//    boundary (and the shekel just below/above each one), plus the NII caps.
const boundaries = [0, 1, 100, 7009, 7010, 7011, 7122, 7123, 10059, 10060, 10061,
  16149, 16150, 16151, 22439, 22440, 22441, 46689, 46690, 46691, 49029, 49030, 49031,
  60129, 60130, 60131, 75000, 100000, 250000];
const sweep = [];
for (let g = 0; g <= 100000; g += 137) sweep.push(g);
const grossValues = Array.from(new Set([...boundaries, ...sweep])).sort((a, b) => a - b);

for (const gross of grossValues) {
  checked++;
  const tax = calcIncomeTax(gross);
  const refTax = refIncomeTax(gross);
  if (!approxEqual(tax, refTax)) {
    failures.push(`calcIncomeTax(${gross}) = ${tax} but reference = ${refTax}`);
  }

  checked++;
  const { bl, health } = calcBLHealth(gross);
  const ref = refBLHealth(gross);
  if (!approxEqual(bl, ref.bl) || !approxEqual(health, ref.health)) {
    failures.push(`calcBLHealth(${gross}) = {bl:${bl}, health:${health}} but reference = {bl:${ref.bl}, health:${ref.health}}`);
  }
}

// 2) Sanity invariants that should hold regardless of the exact numbers.
for (const gross of grossValues) {
  checked++;
  const tax = calcIncomeTax(gross);
  if (tax < 0) failures.push(`calcIncomeTax(${gross}) is negative: ${tax}`);
  if (gross > 0 && tax > gross) failures.push(`calcIncomeTax(${gross}) exceeds gross: ${tax}`);

  checked++;
  const { bl, health } = calcBLHealth(gross);
  if (bl < 0 || health < 0) failures.push(`calcBLHealth(${gross}) negative: bl=${bl}, health=${health}`);
}

// 3) Monotonicity: net-of-tax-and-NII should never decrease as gross rises
//    (marginal rates coded are all < 100%, so take-home should keep rising).
let prevAfterTaxNII = -Infinity;
for (const gross of grossValues) {
  checked++;
  const tax = calcIncomeTax(gross);
  const { bl, health } = calcBLHealth(gross);
  const afterTaxNII = gross - tax - bl - health;
  if (afterTaxNII < prevAfterTaxNII - EPS) {
    failures.push(`Non-monotonic take-home at gross=${gross}: ${afterTaxNII} < previous ${prevAfterTaxNII}`);
  }
  prevAfterTaxNII = afterTaxNII;
}

// 4) End-to-end scenarios (mirrors the wiring in calculate(), independently
//    recomputed) for representative profiles.
const scenarios = [
  { label: 'Single, no credits beyond base, 5000 gross', gross: 5000, points: 2.25 },
  { label: 'Single, 15000 gross, base credits', gross: 15000, points: 2.25 },
  { label: 'Woman + academic, 15000 gross', gross: 15000, points: 2.25 + 0.5 + 1 },
  { label: 'Woman, 2 young kids, 12000 gross', gross: 12000, points: 2.25 + 0.5 + 2 * 2.5 },
  { label: 'Discharged soldier, 8000 gross', gross: 8000, points: 2.25 + 2 },
  { label: 'High earner, 70000 gross', gross: 70000, points: 2.25 },
  { label: 'Oleh chadash, 20000 gross (full exemption)', gross: 20000, oleh: true },
  { label: 'With 6% pension, 15000 gross', gross: 15000, points: 2.25, pensionPct: 6 },
];

const results = [];
for (const s of scenarios) {
  checked++;
  const tax = s.oleh ? 0 : Math.max(0, calcIncomeTax(s.gross) - (s.points ?? 2.25) * POINT_VALUE);
  const { bl, health } = calcBLHealth(s.gross);
  const pension = s.gross * ((s.pensionPct ?? 0) / 100);
  const net = s.gross - tax - bl - health - pension;
  const expectedNet = refNet(s.gross, { points: s.points ?? 2.25, oleh: !!s.oleh, pensionPct: s.pensionPct ?? 0 });
  if (!approxEqual(net, expectedNet)) {
    failures.push(`Scenario "${s.label}": net=${net} but reference=${expectedNet}`);
  }
  results.push({ label: s.label, gross: s.gross, tax: Math.round(tax), bl: Math.round(bl), health: Math.round(health), pension: Math.round(pension), net: Math.round(net) });
}

// --- Report ---
console.log(`Backtest: ${checked} checks across ${grossValues.length} gross-salary points + ${scenarios.length} scenarios\n`);
console.log('Scenario results:');
for (const r of results) {
  console.log(`  ${r.label.padEnd(45)} gross=${String(r.gross).padStart(6)}  tax=${String(r.tax).padStart(6)}  bl=${String(r.bl).padStart(5)}  health=${String(r.health).padStart(5)}  pension=${String(r.pension).padStart(5)}  net=${String(r.net).padStart(6)}`);
}

console.log('');
if (failures.length === 0) {
  console.log(`PASS — all ${checked} checks matched the independent reference implementation (tolerance ${EPS}).`);
  process.exit(0);
} else {
  console.log(`FAIL — ${failures.length} mismatch(es):`);
  for (const f of failures.slice(0, 50)) console.log('  - ' + f);
  if (failures.length > 50) console.log(`  ... and ${failures.length - 50} more`);
  process.exit(1);
}
