/* Genera build/ponencia-yuk-hui.pptx — versión estática y elegante de la ponencia,
   con esquemas vectoriales de los 6 modelos. Ejecutar: npm run pptx */

import PptxGenJS from 'pptxgenjs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { existsSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, '..', 'build', 'ponencia-yuk-hui.pptx');

// ---- Paleta (idéntica al tema web) ----
const C = {
  bg: '0D1117', bg2: '161B26', grid: '222B3A', line: '2A3344',
  ink: 'E8E6DF', muted: '8A93A3', agua: '3B82C4', verde: '5CAB73',
  amber: 'E0A44E', rojo: 'E0524A', mixto: 'D97A3D', industrial: '7B8FA6',
  cian: '2DD4BF', violeta: 'A78BFA', calle: 'CDD6E3',
};
const FONT = 'Arial';           // PPTX portable (no depende de fuentes web)
const SERIF = 'Georgia';

const pptx = new PptxGenJS();
pptx.defineLayout({ name: 'W', width: 13.333, height: 7.5 });
pptx.layout = 'W';
pptx.author = 'Steven Vallejo';
pptx.title = 'El límite de la IA y el objeto epistémico del urbanismo computacional';

// PRNG determinista (build reproducible)
let _s = 1337;
const rnd = () => { _s = (_s * 1103515245 + 12345) & 0x7fffffff; return _s / 0x7fffffff; };

// ---- Helpers ----
function slide(bg = C.bg) {
  const s = pptx.addSlide();
  s.background = { color: bg };
  return s;
}
function kicker(s, txt, color = C.cian) {
  s.addText(txt.toUpperCase(), {
    x: 0.7, y: 0.55, w: 12, h: 0.4, fontFace: FONT, fontSize: 13, bold: true,
    color, charSpacing: 3, align: 'left',
  });
}
function title(s, txt, opts = {}) {
  s.addText(txt, {
    x: 0.7, y: 0.95, w: 12, h: 1.3, fontFace: SERIF, fontSize: opts.size || 40,
    color: C.ink, bold: true, align: 'left', ...opts,
  });
}
function lead(s, runs, y = 2.5, opts = {}) {
  s.addText(runs, {
    x: 0.7, y, w: opts.w || 12, h: opts.h || 1.0, fontFace: FONT, fontSize: opts.size || 20,
    color: C.ink, align: 'left', lineSpacingMultiple: 1.15, ...opts,
  });
}
function card(s, x, y, w, h, head, body, accent = C.cian) {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, fill: { color: C.bg2 }, line: { color: C.line, width: 1 }, rectRadius: 0.1,
  });
  s.addShape(pptx.ShapeType.rect, { x, y: y + 0.18, w: 0.07, h: h - 0.36, fill: { color: accent } });
  s.addText(head, {
    x: x + 0.28, y: y + 0.18, w: w - 0.5, h: 0.5, fontFace: FONT, fontSize: 15, bold: true,
    color: accent, align: 'left',
  });
  s.addText(body, {
    x: x + 0.28, y: y + 0.72, w: w - 0.5, h: h - 0.9, fontFace: FONT, fontSize: 13,
    color: C.ink, align: 'left', lineSpacingMultiple: 1.1, valign: 'top',
  });
}
function pullquote(s, runs, y, accent = C.cian) {
  s.addShape(pptx.ShapeType.rect, { x: 0.7, y, w: 0.08, h: 1.0, fill: { color: accent } });
  s.addText(runs, {
    x: 1.0, y: y - 0.05, w: 11.3, h: 1.1, fontFace: SERIF, fontSize: 22, italic: true,
    color: C.ink, align: 'left', lineSpacingMultiple: 1.1, valign: 'middle',
  });
}
function footer(s, n) {
  s.addText('Yuk Hui · El límite de la IA y el objeto epistémico del urbanismo · Filosofía de la Ciudad',
    { x: 0.7, y: 7.05, w: 11, h: 0.3, fontFace: FONT, fontSize: 9, color: C.muted, align: 'left' });
  s.addText(String(n), { x: 12.4, y: 7.05, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 9, color: C.muted, align: 'right' });
}
// área del esquema (panel) a la derecha
function stage(s, x = 7.05, y = 2.2, w = 5.55, h = 4.3) {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, fill: { color: '0B0E14' }, line: { color: C.line, width: 1 }, rectRadius: 0.08,
  });
  return { x, y, w, h };
}

// ================= ESQUEMAS DE MODELOS (formas nativas) =================
function diagCA(s, a) {
  const cols = 22, rows = 16, pad = 0.18;
  const cw = (a.w - pad * 2) / cols, ch = (a.h - pad * 2) / rows;
  const cx = cols / 2, cy = rows / 2;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const d = Math.hypot(i - cx, j - cy);
    const p = Math.max(0, 1 - d / 9) + (rnd() - 0.5) * 0.35;
    let col = null;
    if (p > 0.85) col = C.rojo; else if (p > 0.45) col = C.amber; else if (p > 0.28) col = C.mixto;
    if (col) s.addShape(pptx.ShapeType.rect, {
      x: a.x + pad + i * cw, y: a.y + pad + j * ch, w: cw - 0.02, h: ch - 0.02, fill: { color: col },
    });
  }
  legend(s, a, [['Núcleo (CBD)', C.rojo], ['Urbanizado', C.amber], ['En desarrollo', C.mixto]]);
}
function diagSchelling(s, a) {
  const cols = 20, rows = 14, pad = 0.2;
  const cw = (a.w - pad * 2) / cols, ch = (a.h - pad * 2) / rows;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    if (rnd() < 0.1) continue; // vacío
    // segregación: dos bloques con ruido
    const left = i < cols / 2 + Math.sin(j) * 2;
    const col = (left ? rnd() < 0.85 : rnd() < 0.15) ? C.cian : C.amber;
    s.addShape(pptx.ShapeType.ellipse, {
      x: a.x + pad + i * cw + cw * 0.12, y: a.y + pad + j * ch + ch * 0.12,
      w: cw * 0.72, h: ch * 0.72, fill: { color: col },
    });
  }
  legend(s, a, [['Grupo A', C.cian], ['Grupo B', C.amber], ['Vacío', C.grid]]);
}
function diagNetwork(s, a, highlight = true) {
  const n = 16; const pts = [];
  for (let i = 0; i < n; i++) pts.push({
    x: a.x + 0.4 + rnd() * (a.w - 0.8), y: a.y + 0.4 + rnd() * (a.h - 0.9),
  });
  // aristas a vecinos cercanos
  const edges = [];
  for (let i = 0; i < n; i++) {
    const d = pts.map((p, j) => ({ j, d: Math.hypot(p.x - pts[i].x, p.y - pts[i].y) }))
      .filter(o => o.j !== i).sort((u, v) => u.d - v.d).slice(0, 2);
    d.forEach(o => edges.push([i, o.j]));
  }
  edges.forEach(([i, j], k) => {
    const hot = highlight && k % 5 === 0;
    s.addShape(pptx.ShapeType.line, {
      x: Math.min(pts[i].x, pts[j].x), y: Math.min(pts[i].y, pts[j].y),
      w: Math.abs(pts[i].x - pts[j].x) || 0.001, h: Math.abs(pts[i].y - pts[j].y) || 0.001,
      line: { color: hot ? C.rojo : C.industrial, width: hot ? 3 : 1.25,
        beginArrowType: 'none', endArrowType: 'none' },
      flipH: (pts[i].x > pts[j].x) !== (pts[i].y > pts[j].y) ? false : true,
    });
  });
  pts.forEach((p, i) => s.addShape(pptx.ShapeType.ellipse, {
    x: p.x - 0.07, y: p.y - 0.07, w: 0.14, h: 0.14,
    fill: { color: i % 4 === 0 ? C.cian : C.calle }, line: { color: C.bg, width: 1 },
  }));
  legend(s, a, [['Calle integradora', C.rojo], ['Calle', C.industrial], ['Intersección', C.calle]]);
}
function diagPhysarum(s, a) {
  // nodos urbanos
  const nodes = [[0.22, 0.3], [0.5, 0.18], [0.8, 0.32], [0.3, 0.68], [0.68, 0.72], [0.5, 0.5]];
  const P = nodes.map(([u, v]) => ({ x: a.x + 0.3 + u * (a.w - 0.6), y: a.y + 0.3 + v * (a.h - 0.7) }));
  // red orgánica: conectar al centro y vecinos
  const conn = [[5, 0], [5, 1], [5, 2], [5, 3], [5, 4], [0, 1], [1, 2], [3, 4], [0, 3], [2, 4]];
  conn.forEach(([i, j]) => s.addShape(pptx.ShapeType.line, {
    x: Math.min(P[i].x, P[j].x), y: Math.min(P[i].y, P[j].y),
    w: Math.abs(P[i].x - P[j].x) || 0.001, h: Math.abs(P[i].y - P[j].y) || 0.001,
    line: { color: C.cian, width: 2, transparency: 35 },
    flipV: (P[i].x > P[j].x) !== (P[i].y > P[j].y),
  }));
  P.forEach(p => s.addShape(pptx.ShapeType.ellipse, {
    x: p.x - 0.11, y: p.y - 0.11, w: 0.22, h: 0.22, fill: { color: C.amber }, line: { color: C.bg, width: 1 },
  }));
  legend(s, a, [['Centro urbano', C.amber], ['Red emergente', C.cian]]);
}
function diagTraffic(s, a) {
  const pad = 0.35; const gx = 5, gy = 4;
  const xs = Array.from({ length: gx }, (_, i) => a.x + pad + i * (a.w - pad * 2) / (gx - 1));
  const ys = Array.from({ length: gy }, (_, j) => a.y + pad + j * (a.h - pad * 2.2) / (gy - 1));
  const cols = [C.verde, C.verde, C.amber, C.rojo];
  // horizontales y verticales con color por "congestión"
  ys.forEach((y) => s.addShape(pptx.ShapeType.line, {
    x: xs[0], y, w: xs[gx - 1] - xs[0], h: 0.001,
    line: { color: cols[Math.floor(rnd() * 4)], width: 3.5 },
  }));
  xs.forEach((x) => s.addShape(pptx.ShapeType.line, {
    x, y: ys[0], w: 0.001, h: ys[gy - 1] - ys[0],
    line: { color: cols[Math.floor(rnd() * 4)], width: 3.5 },
  }));
  // vehículos
  for (let k = 0; k < 14; k++) s.addShape(pptx.ShapeType.ellipse, {
    x: xs[0] + rnd() * (xs[gx - 1] - xs[0]) - 0.04, y: ys[Math.floor(rnd() * gy)] - 0.04,
    w: 0.09, h: 0.09, fill: { color: C.ink },
  });
  legend(s, a, [['Fluido', C.verde], ['Lento', C.amber], ['Congestión', C.rojo]]);
}
function diagGravity(s, a) {
  const centers = [
    { u: 0.3, v: 0.35, m: 0.34 }, { u: 0.72, v: 0.28, m: 0.26 }, { u: 0.55, v: 0.66, m: 0.30 },
    { u: 0.2, v: 0.72, m: 0.18 }, { u: 0.82, v: 0.62, m: 0.2 },
  ].map(c => ({ x: a.x + 0.4 + c.u * (a.w - 0.8), y: a.y + 0.4 + c.v * (a.h - 0.9), m: c.m }));
  for (let i = 0; i < centers.length; i++) for (let j = i + 1; j < centers.length; j++) {
    const d = Math.hypot(centers[i].x - centers[j].x, centers[i].y - centers[j].y);
    const flow = (centers[i].m * centers[j].m) / (d * d);
    const w = Math.min(5, Math.max(0.6, flow * 14));
    s.addShape(pptx.ShapeType.line, {
      x: Math.min(centers[i].x, centers[j].x), y: Math.min(centers[i].y, centers[j].y),
      w: Math.abs(centers[i].x - centers[j].x) || 0.001, h: Math.abs(centers[i].y - centers[j].y) || 0.001,
      line: { color: C.cian, width: w, transparency: 30 },
      flipV: (centers[i].x > centers[j].x) !== (centers[i].y > centers[j].y),
    });
  }
  centers.forEach(c => s.addShape(pptx.ShapeType.ellipse, {
    x: c.x - c.m * 0.9, y: c.y - c.m * 0.9, w: c.m * 1.8, h: c.m * 1.8,
    fill: { color: C.amber }, line: { color: C.rojo, width: 1.5 },
  }));
  legend(s, a, [['Centro (masa)', C.amber], ['Flujo T_ij', C.cian]]);
}
function legend(s, a, items) {
  let x = a.x + 0.25;
  const y = a.y + a.h - 0.42;
  items.forEach(([label, col]) => {
    s.addShape(pptx.ShapeType.ellipse, { x, y: y + 0.05, w: 0.14, h: 0.14, fill: { color: col } });
    s.addText(label, { x: x + 0.2, y, w: 2.1, h: 0.3, fontFace: FONT, fontSize: 10, color: C.muted, align: 'left' });
    x += 0.28 + Math.min(2.0, 0.13 * label.length + 0.5);
  });
}

// model slide template — usa una captura REAL del modelo si existe; si no, el esquema vectorial
function modelSlide(n, kick, ttl, accent, claim, source, tag, imgFileOrDrawer) {
  const s = slide('0B0E14');
  kicker(s, kick, accent);
  title(s, ttl, { size: 33 });
  s.addText(claim, {
    x: 0.7, y: 2.3, w: 5.9, h: 2.0, fontFace: FONT, fontSize: 18, color: C.ink,
    align: 'left', lineSpacingMultiple: 1.2, valign: 'top',
  });
  s.addText(source, { x: 0.7, y: 4.5, w: 5.9, h: 0.6, fontFace: FONT, fontSize: 13, color: C.muted, italic: true, align: 'left' });
  s.addShape(pptx.ShapeType.roundRect, { x: 0.7, y: 5.4, w: 5.9, h: 0.6, fill: { color: C.bg2 }, line: { color: accent, width: 1 }, rectRadius: 0.1 });
  s.addText(tag, { x: 0.85, y: 5.4, w: 5.6, h: 0.6, fontFace: FONT, fontSize: 13, color: accent, align: 'left', valign: 'middle' });
  const a = stage(s);
  if (typeof imgFileOrDrawer === 'string') {
    const imgPath = resolve(__dirname, '..', 'assets', imgFileOrDrawer);
    if (existsSync(imgPath)) {
      s.addImage({ path: imgPath, x: a.x + 0.1, y: a.y + 0.1,
        w: a.w - 0.2, h: a.h - 0.2, sizing: { type: 'contain', w: a.w - 0.2, h: a.h - 0.2 } });
    }
  } else if (typeof imgFileOrDrawer === 'function') {
    imgFileOrDrawer(s, a);
  }
  s.addText('▶ versión interactiva en vivo en la web', { x: a.x, y: a.y + a.h + 0.12, w: a.w, h: 0.3, fontFace: FONT, fontSize: 10, color: C.muted, align: 'center' });
  footer(s, n);
  return s;
}

// ============================ DIAPOSITIVAS ============================
// 1 · Portada
{
  const s = slide(C.bg);
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.18, h: 7.5, fill: { color: C.cian } });
  s.addText('FILOSOFÍA DE LA CIUDAD · UNIDAD URBAN AI', {
    x: 0.9, y: 1.4, w: 11, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.cian, charSpacing: 3,
  });
  s.addText([
    { text: 'El límite de la IA\n', options: { color: C.ink } },
    { text: 'y el objeto epistémico\n', options: { color: C.cian } },
    { text: 'del urbanismo computacional', options: { color: C.ink } },
  ], { x: 0.9, y: 2.1, w: 11.5, h: 2.6, fontFace: SERIF, fontSize: 46, bold: true, align: 'left', lineSpacingMultiple: 1.05 });
  s.addText([
    { text: 'Una lectura de Yuk Hui — “Sobre el límite de la inteligencia artificial”\n', options: { color: C.ink, fontSize: 18 } },
    { text: 'en Fragmentar el futuro. Ensayos sobre tecnodiversidad (Caja Negra, 2020), pp. 163-191', options: { color: C.muted, fontSize: 14, italic: true } },
  ], { x: 0.9, y: 5.0, w: 11, h: 1.0, fontFace: FONT, align: 'left', lineSpacingMultiple: 1.2 });
  s.addText('Steven Vallejo · 12 de junio de 2026', { x: 0.9, y: 6.3, w: 11, h: 0.4, fontFace: FONT, fontSize: 14, color: C.muted });
}

// 2 · La IA es asombrosa
{
  const s = slide(); kicker(s, 'Concedamos lo evidente', C.cian);
  title(s, 'La IA es asombrosa — como asistente');
  card(s, 0.7, 2.3, 3.85, 2.3, 'Aplana curvas de aprendizaje', 'Lo que exigía meses de oficio —programar un modelo, leer un paper denso, montar una visualización— hoy toma horas.', C.cian);
  card(s, 4.74, 2.3, 3.85, 2.3, 'Acelera la creación', 'Prototipa, traduce, depura, documenta. Es un multiplicador de productividad intelectual.', C.amber);
  card(s, 8.78, 2.3, 3.85, 2.3, 'Democratiza el acceso', 'Baja la barrera de entrada a técnicas que antes pertenecían solo a especialistas.', C.violeta);
  pullquote(s, [{ text: 'No vengo a negar su poder. Vengo a preguntar ', options: {} }, { text: 'qué clase de poder es', options: { color: C.cian } }, { text: '.', options: {} }], 5.4);
  footer(s, 2);
}

// 3 · Pero esto es Filosofía de la Ciudad
{
  const s = slide(); kicker(s, 'El giro de la pregunta', C.amber);
  title(s, 'Pero esto es Filosofía de la Ciudad');
  lead(s, [{ text: 'La pregunta del ingeniero es ', options: {} }, { text: '¿qué puede hacer la IA?', options: { italic: true, color: C.muted } }, { text: '  La del filósofo es otra:', options: {} }], 2.35);
  pullquote(s, [{ text: '¿Cuál es el objeto epistémico del urbanismo? ¿Qué produce conocimiento sobre la ciudad?', options: {} }], 3.3, C.amber);
  lead(s, [{ text: 'La trampa de época: confundir el ', options: {} }, { text: 'acelerador', options: { color: C.cian } }, { text: ' (la IA) con el ', options: {} }, { text: 'objeto', options: { color: C.amber } }, { text: ' (el modelo del mundo urbano).', options: {} }], 5.0);
  footer(s, 3);
}

// 4 · Yuk Hui / el límite
{
  const s = slide(); kicker(s, 'El texto', C.cian);
  title(s, 'Yuk Hui y la pregunta por el límite');
  lead(s, [{ text: 'Hui no pregunta qué no puede hacer la IA —esa pregunta envejece con cada modelo nuevo—. Pregunta cómo ', options: {} }, { text: 'pensar el límite', options: { color: C.cian } }, { text: ' de una inteligencia que parece absorber toda función humana cuantificable.', options: {} }], 2.3, { w: 6.0, h: 2.2 });
  pullquote(s, [{ text: 'El límite no es frontera técnica fija: es político y cosmológico.', options: {} }], 4.9);
  card(s, 7.0, 2.3, 5.6, 2.2, 'La pregunta decisiva', '¿Qué tipo de MUNDO produce la IA cuando convierte la ciudad en datos computables?', C.cian);
  footer(s, 4);
}

// 5 · Bergson + cibernética
{
  const s = slide(); kicker(s, 'Genealogía del límite · I', C.cian);
  title(s, 'Inteligencia exteriorizada y recursividad');
  card(s, 0.7, 2.3, 5.9, 2.5, 'Bergson', 'La inteligencia es homo faber: fabrica herramientas, exterioriza. Tensión entre lo mecánico (automatismo) y lo vital (la duración). La IA exterioriza y desborda la intención humana.', C.amber);
  card(s, 6.74, 2.3, 5.9, 2.5, 'Cibernética (Wiener)', 'Ciencia del control y la comunicación. La retroalimentación hace que la máquina se regule a sí misma. Nace la máquina recursiva: la herramienta que se aplica a sí misma.', C.cian);
  pullquote(s, [{ text: 'De la herramienta al sistema autónomo. Pero, ¿basta la recursividad para tener fines propios?', options: {} }], 5.5);
  footer(s, 5);
}

// 6 · Kant/Simondon + Dreyfus/Heidegger
{
  const s = slide(); kicker(s, 'Genealogía del límite · II — el núcleo', C.rojo);
  title(s, 'Lo que a la IA le falta');
  card(s, 0.7, 2.3, 5.9, 2.4, 'Kant / Simondon — juicio reflexionante', 'Juicio determinante: dada la regla, subsumir el caso (la IA lo hace de maravilla). Reflexionante: dado el caso, inventar la regla y darse el fin. La IA optimiza fines dados; no se los da.', C.violeta);
  card(s, 6.74, 2.3, 5.9, 2.4, 'Dreyfus / Heidegger — mundo', 'El mundo no es un conjunto de datos: es un horizonte de significatividad. Comprender es captar relevancia y contexto, no calcular. La IA no tiene mundo.', C.amber);
  pullquote(s, [{ text: 'El límite: la IA computa dentro de un mundo y unos fines que no son suyos. Calcula; no significa.', options: {} }], 5.4, C.rojo);
  footer(s, 6);
}

// 7 · El giro empírico
{
  const s = slide('0B0E14'); kicker(s, 'El giro empírico', C.cian);
  title(s, 'Los cálculos de verdad del urbanismo no se hacen con súper-IAs', { size: 32 });
  lead(s, [{ text: 'Se hacen con modelos de cómputo sistémico: reglas locales, teoría de grafos, optimización, dinámica de agentes. Décadas anteriores a la IA generativa.', options: {} }], 2.7);
  lead(s, [{ text: 'Lo que sigue son ', options: {} }, { text: 'seis modelos reales', options: { color: C.cian } }, { text: '. Ninguno es IA. Cada uno es un objeto epistémico: produce conocimiento sobre la ciudad.', options: {} }], 3.9);
  lead(s, [{ text: 'La IA, a lo sumo, me ayudó a montarlos más rápido. Eso es justamente la tesis.', options: { color: C.muted, italic: true, size: 16 } }], 5.2);
  footer(s, 7);
}

// 8-13 · Modelos
modelSlide(8, 'Modelo 1 · Emergencia', 'Autómata celular — crecimiento urbano', C.amber,
  'La mancha urbana emerge de reglas locales: difusión en bordes, chispazos espontáneos, atracción por vías. Sin plan central, sin IA.',
  'Familia SLEUTH — usado en planeación real para proyectar expansión.',
  'ontología: ciudad como proceso celular', 'cellular-automata.png');
modelSlide(9, 'Modelo 2 · Micro → Macro', 'Segregación de Schelling', C.cian,
  'Preferencias locales leves producen segregación macro. Nadie la diseña: emerge. El modelo revela una verdad estructural invisible a la intuición.',
  'Schelling, 1971 — Nobel de Economía. Cero IA.',
  'epistemología: experimento mental ejecutable', 'schelling.png');
modelSlide(10, 'Modelo 3 · Teoría de grafos', 'Sintaxis espacial — centralidad de la red', C.rojo,
  'La calle como grafo. La intermediación (betweenness) predice dónde habrá comercio, flujo, vida urbana. La estructura, no la apariencia, manda.',
  'Hillier & Hanson, The Social Logic of Space.',
  'ontología: ciudad como red de relaciones', 'space-syntax.png');
modelSlide(11, 'Modelo 4 · Optimización distribuida', 'Physarum — red de transporte emergente', C.cian,
  'Miles de agentes-feromona conectan centros urbanos en una red casi-óptima. Un moho reproduce la red ferroviaria de Tokio. Cómputo sin cerebro.',
  'Tero et al., Science 2010.',
  'ontología: ciudad como organismo / flujo', 'physarum.png');
modelSlide(12, 'Modelo 5 · Microsimulación', 'Tráfico basado en agentes', C.amber,
  'Cada vehículo enruta y avanza; la congestión emerge de la interacción. Así se evalúan semáforos, peajes y trazados antes de construirlos.',
  'MATSim, SUMO — estándar en planeación de transporte.',
  'técnica: ciudad como sistema dinámico', 'agent-traffic.png');
modelSlide(13, 'Modelo 6 · Geografía cuantitativa', 'Modelo gravitacional de interacción', C.violeta,
  'El flujo entre dos centros ∝ masas / distancia^β. Modela migración, comercio, viajes. Arrastra un centro y los flujos se recalculan.',
  'Wilson, 1970 — geografía cuantitativa clásica.',
  'epistemología: la fórmula como objeto', 'gravity.png');

// 14 · Análisis ontológico
{
  const s = slide(); kicker(s, 'Análisis · I', C.amber);
  title(s, 'Ontológico: cada modelo funda un mundo');
  lead(s, [{ text: 'Ningún modelo es neutral. Cada uno enuncia una ontología de la ciudad:', options: {} }], 2.2, { h: 0.5 });
  s.addTable([
    [{ text: 'Modelo', options: { bold: true, color: C.cian } }, { text: 'La ciudad es…', options: { bold: true, color: C.cian } }, { text: 'Ilumina / oculta', options: { bold: true, color: C.cian } }],
    ['Autómata celular', 'proceso / mancha', 'morfología · borra al habitante'],
    ['Schelling', 'agregado de decisiones', 'segregación · simplifica el deseo'],
    ['Sintaxis espacial', 'red de relaciones', 'flujo · ignora el sentido'],
    ['Physarum / gravedad', 'organismo / campo de fuerzas', 'eficiencia · naturaliza lo político'],
  ], {
    x: 0.7, y: 2.8, w: 11.9, colW: [3.2, 4.0, 4.7], fontFace: FONT, fontSize: 14, color: C.ink,
    border: { type: 'solid', color: C.line, pt: 1 }, fill: { color: C.bg2 }, rowH: 0.5, valign: 'middle',
  });
  pullquote(s, [{ text: 'Esto es la cosmotécnica de Hui: toda técnica produce un cosmos. El modelo no describe la ciudad: la instaura.', options: {} }], 5.7, C.amber);
  footer(s, 14);
}

// 15 · Análisis técnico
{
  const s = slide(); kicker(s, 'Análisis · II', C.cian);
  title(s, 'Técnico: ¿qué son, en rigor, estos cálculos?');
  card(s, 0.7, 2.3, 5.9, 2.3, 'Los modelos urbanos', 'Sistemas dinámicos discretos · teoría de grafos · optimización · emergencia. Mecanismos transparentes: la regla ES la explicación.', C.cian);
  card(s, 6.74, 2.3, 5.9, 2.3, 'La IA / ML', 'Aproximación estadística de funciones sobre datos. Correlación opaca: predice sin explicar. Acelera, ajusta, genera código.', C.rojo);
  pullquote(s, [{ text: 'La IA construye el modelo más rápido. El modelo ES el conocimiento. No confundas al albañil con la casa.', options: {} }], 5.3, C.cian);
  footer(s, 15);
}

// 16 · Análisis epistémico
{
  const s = slide(); kicker(s, 'Análisis · III — la tesis', C.violeta);
  title(s, 'Epistémico: la IA es acelerador, no sujeto');
  card(s, 0.7, 2.3, 3.85, 2.3, 'Objeto epistémico', 'El modelo de cómputo sistémico. Lo que porta fines, ontología y mundo.', C.amber);
  card(s, 4.74, 2.3, 3.85, 2.3, 'Rol de la IA', 'Acelerador epistémico: aplana la curva de construir esos modelos. Instrumento, no fuente.', C.cian);
  card(s, 8.78, 2.3, 3.85, 2.3, 'El límite (Hui)', 'Sin mundo ni juicio reflexionante, la IA no puede ser el objeto: no se da los fines del urbanismo.', C.violeta);
  pullquote(s, [{ text: 'El objeto epistémico del urbanismo no es la IA. Son los cálculos de orden sistémico — y la IA solo ayuda a parirlos ágilmente.', options: {} }], 5.4, C.violeta);
  footer(s, 16);
}

// 17 · Cosmotécnica / tecnodiversidad
{
  const s = slide(); kicker(s, 'Hui, hasta el final', C.cian);
  title(s, '¿Qué ciudad produce cada cálculo?');
  lead(s, [{ text: 'Si cada modelo instaura un cosmos, elegir modelo es un acto político y cosmológico —no técnico—.', options: {} }], 2.2, { h: 0.7 });
  card(s, 0.7, 3.1, 5.9, 2.1, 'Tecnodiversidad', 'Frente a la monocultura del “optimizar todo”: pluralidad de modelos, de cosmotécnicas, de mundos urbanos posibles.', C.cian);
  card(s, 6.74, 3.1, 5.9, 2.1, 'Desde el Sur', '¿Cómo se ven nuestras ciudades latinoamericanas —informales, vivas— bajo modelos pensados para otra cosmología? ¿Qué modelos nos faltan?', C.amber);
  footer(s, 17);
}

// 18 · Preguntas y cierre
{
  const s = slide(C.bg); kicker(s, 'Para discutir', C.cian);
  title(s, 'Tres preguntas');
  s.addText([
    { text: '1.  Si la IA no tiene mundo, ¿qué mundo produce al gobernar la ciudad por datos?\n\n', options: {} },
    { text: '2.  ¿El “límite” en Hui es técnico o político?\n\n', options: {} },
    { text: '3.  ¿Qué cosmotécnica urbana latinoamericana estamos dejando de computar?', options: {} },
  ], { x: 0.7, y: 2.3, w: 11.8, h: 2.2, fontFace: FONT, fontSize: 22, color: C.ink, lineSpacingMultiple: 1.1, align: 'left' });
  pullquote(s, [{ text: 'La IA aplana la curva de aprendizaje. Pero elegir qué ciudad calcular sigue siendo, y será, nuestro.', options: {} }], 5.3);
  s.addText('Gracias. · Steven Vallejo · Filosofía de la Ciudad · 2026', { x: 0.7, y: 6.6, w: 11, h: 0.4, fontFace: FONT, fontSize: 13, color: C.muted });
}

await pptx.writeFile({ fileName: OUT });
console.log('PPTX generado:', OUT);
