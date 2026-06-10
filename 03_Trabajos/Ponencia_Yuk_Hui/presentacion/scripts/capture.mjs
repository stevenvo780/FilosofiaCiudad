/* Smoke-test + captura de renders reales de los modelos con puppeteer.
   Requiere un servidor http sirviendo la carpeta presentacion en BASE_URL. */
import puppeteer from 'puppeteer';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS = resolve(__dirname, '..', 'assets');
const BASE = process.env.BASE_URL || 'http://localhost:8137/';

// slides 1-indexed 8..13 => indices 0-indexed 7..12
const MODELS = [
  { name: 'cellular-automata', idx: 7 },
  { name: 'schelling', idx: 8 },
  { name: 'space-syntax', idx: 9 },
  { name: 'physarum', idx: 10 },
  { name: 'agent-traffic', idx: 11 },
  { name: 'gravity', idx: 12 },
];

const errors = [];
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE.ERROR: ' + m.text()); });

await page.goto(BASE, { waitUntil: 'networkidle2', timeout: 30000 });
// esperar a que reveal y los modelos esten listos
await page.waitForFunction(
  () => window._deck && window.PonenciaSims && Object.keys(window.PonenciaSims).length >= 6,
  { timeout: 15000 }
);
const registered = await page.evaluate(() => Object.keys(window.PonenciaSims));
console.log('Modelos registrados:', registered.join(', '));

const report = [];
for (const m of MODELS) {
  await page.evaluate((i) => window._deck.slide(i, 0), m.idx);
  await sleep(4200); // dejar correr la animacion
  const info = await page.evaluate(() => {
    const slide = document.querySelector('.reveal .slides section.present');
    const stage = slide && slide.querySelector('.sim-stage');
    const canvas = stage && stage.querySelector('canvas');
    if (!canvas) return { canvas: false };
    // muestrear si hay pixeles no-vacios (render real)
    const c = document.createElement('canvas');
    c.width = 40; c.height = 40;
    const cx = c.getContext('2d');
    cx.drawImage(canvas, 0, 0, 40, 40);
    const d = cx.getImageData(0, 0, 40, 40).data;
    let nonBg = 0;
    for (let k = 0; k < d.length; k += 4) {
      // fondo ~ #0d1117 (13,17,23)
      if (Math.abs(d[k] - 13) + Math.abs(d[k+1] - 17) + Math.abs(d[k+2] - 23) > 40) nonBg++;
    }
    return { canvas: true, w: canvas.width, h: canvas.height, nonBgPct: Math.round(100 * nonBg / (40*40)) };
  });
  let shotOk = false;
  try {
    const stage = await page.$('.reveal .slides section.present .sim-stage');
    if (stage) { await stage.screenshot({ path: resolve(ASSETS, m.name + '.png') }); shotOk = true; }
  } catch (e) { errors.push('SHOT ' + m.name + ': ' + e.message); }
  report.push({ model: m.name, ...info, shot: shotOk });
  console.log(`  ${m.name}: canvas=${info.canvas} ${info.w||''}x${info.h||''} contenido=${info.nonBgPct ?? '?'}% shot=${shotOk}`);
}

await browser.close();
console.log('\n=== ERRORES (' + errors.length + ') ===');
errors.slice(0, 30).forEach(e => console.log(' - ' + e));
const bad = report.filter(r => !r.canvas || (r.nonBgPct ?? 0) < 3);
console.log('\n=== MODELOS SIN RENDER VISIBLE: ' + (bad.length ? bad.map(b=>b.model).join(', ') : 'ninguno') + ' ===');
process.exit(errors.length || bad.length ? 1 : 0);
