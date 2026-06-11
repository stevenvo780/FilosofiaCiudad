/**
 * schelling.js — Visualización animada del modelo de segregación de Schelling
 * Loop perpetuo: mezcla aleatoria → cristalización de clusters → pausa → fade → reset
 *
 * Registro global: window.VIZ['schelling']
 * Contrato mount(container, opts) → { pause, resume, destroy }
 */

(function () {
  'use strict';

  window.VIZ = window.VIZ || {};

  // ─── Paleta ───────────────────────────────────────────────────────────────
  var COLOR_ROJO   = '#e0a458';  // ámbar cálido (grupo A)
  var COLOR_AZUL   = '#4a90d9';  // azul secundario (grupo B)
  var COLOR_BG     = '#0e1a2b';  // fondo marino oscuro
  var COLOR_TEXT   = '#e8e6e1';  // texto claro
  var COLOR_ACCENT = '#e0a458';  // acento para cifras

  // ─── Parámetros de simulación ─────────────────────────────────────────────
  var N         = 50;    // rejilla N×N
  var FRAC_A    = 0.45;  // fracción grupo rojo/ámbar
  var FRAC_B    = 0.45;  // fracción grupo azul
  var UMBRAL_T  = 0.30;  // umbral de satisfacción

  // ─── Parámetros de animación ──────────────────────────────────────────────
  var TICKS_PER_SEC  = 8;          // velocidad lógica de la simulación
  var PAUSE_MS       = 1500;       // pausa al converger
  var FADE_MS        = 800;        // duración del fade-out/in

  // ─── Estilos del panel lateral ────────────────────────────────────────────
  var PANEL_STYLES_ID = '__viz_schelling_panel_styles';

  function injectPanelStyles() {
    if (document.getElementById(PANEL_STYLES_ID)) return;
    var s = document.createElement('style');
    s.id = PANEL_STYLES_ID;
    s.textContent = [
      '.__sch-overlay{position:fixed;inset:0;background:rgba(14,26,43,0.85);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px);}',
      '.__sch-panel{background:#0e1a2b;border:1px solid rgba(224,164,88,0.35);border-radius:12px;color:#e8e6e1;font-family:system-ui,sans-serif;font-size:13px;line-height:1.55;max-width:680px;width:calc(100% - 40px);max-height:90vh;overflow-y:auto;padding:28px 32px;box-shadow:0 20px 60px rgba(0,0,0,0.7);}',
      '.__sch-panel h2{margin:0 0 4px;font-size:1.25rem;color:#e0a458;font-weight:700;}',
      '.__sch-panel h3{margin:18px 0 6px;font-size:.95rem;text-transform:uppercase;letter-spacing:.08em;color:#e0a458;opacity:.75;font-weight:600;}',
      '.__sch-panel p{margin:4px 0;}',
      '.__sch-panel .formula{background:rgba(224,164,88,0.1);border-left:3px solid #e0a458;padding:8px 12px;border-radius:0 6px 6px 0;font-family:monospace;font-size:12px;color:#f0d090;margin:8px 0;}',
      '.__sch-panel .badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;margin-left:6px;}',
      '.__sch-panel .badge-ok{background:rgba(72,200,120,0.2);color:#48c878;}',
      '.__sch-panel .badge-fail{background:rgba(220,80,80,0.2);color:#e05050;}',
      '.__sch-panel .badge-none{background:rgba(180,180,180,0.15);color:#aaa;}',
      '.__sch-panel .kpi-row{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0;}',
      '.__sch-panel .kpi{background:rgba(255,255,255,0.04);border-radius:8px;padding:10px 16px;min-width:110px;text-align:center;}',
      '.__sch-panel .kpi .val{font-size:1.5rem;font-weight:700;color:#e0a458;}',
      '.__sch-panel .kpi .lbl{font-size:11px;opacity:.65;margin-top:2px;}',
      '.__sch-panel table{width:100%;border-collapse:collapse;margin:8px 0;font-size:12px;}',
      '.__sch-panel th{padding:5px 8px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);color:#e0a458;font-weight:600;}',
      '.__sch-panel td{padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.05);}',
      '.__sch-panel .close-btn{position:absolute;top:16px;right:20px;background:none;border:none;color:#e8e6e1;font-size:22px;cursor:pointer;line-height:1;padding:4px;opacity:.7;transition:opacity .2s;}',
      '.__sch-panel .close-btn:hover{opacity:1;}',
      '.__sch-sparkline{display:block;margin:6px 0;}',
      '.__sch-panel .ref{font-size:11px;opacity:.5;margin-top:16px;border-top:1px solid rgba(255,255,255,0.07);padding-top:10px;}',
      '.__sch-panel .cost-note{font-size:11px;opacity:.6;font-style:italic;}'
    ].join('');
    document.head.appendChild(s);
  }

  // ─── Utilidades ───────────────────────────────────────────────────────────

  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  // Pseudo-RNG (mulberry32) para que los resets sean reproducibles pero variados
  function makePRNG(seed) {
    var s = seed >>> 0;
    return function () {
      s += 0x6D2B79F5;
      var t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ─── Núcleo de simulación Schelling ───────────────────────────────────────
  // Estado: Int8Array de largo N*N, valores: 0=vacío, 1=grupo A, 2=grupo B

  function initGrid(rng) {
    var total = N * N;
    var nA    = Math.round(total * FRAC_A);
    var nB    = Math.round(total * FRAC_B);
    var grid  = new Int8Array(total);

    // Llenar con A y B, resto vacío
    for (var i = 0; i < nA; i++) grid[i] = 1;
    for (var i = nA; i < nA + nB; i++) grid[i] = 2;
    // Fisher-Yates shuffle
    for (var i = total - 1; i > 0; i--) {
      var j = (rng() * (i + 1)) | 0;
      var tmp = grid[i]; grid[i] = grid[j]; grid[j] = tmp;
    }
    return grid;
  }

  // Devuelve índices de vecinos Moore-8 (frontera toroidal)
  function mooreNeighbors(idx) {
    var row = (idx / N) | 0;
    var col = idx % N;
    var nb  = new Int32Array(8);
    var k   = 0;
    for (var dr = -1; dr <= 1; dr++) {
      for (var dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        var r = (row + dr + N) % N;
        var c = (col + dc + N) % N;
        nb[k++] = r * N + c;
      }
    }
    return nb;
  }

  // Caché de vecindades (se construye una sola vez)
  var NEIGHBOR_CACHE = null;
  function getNeighborCache() {
    if (NEIGHBOR_CACHE) return NEIGHBOR_CACHE;
    NEIGHBOR_CACHE = new Array(N * N);
    for (var i = 0; i < N * N; i++) {
      NEIGHBOR_CACHE[i] = mooreNeighbors(i);
    }
    return NEIGHBOR_CACHE;
  }

  // Fracción de vecinos del mismo grupo para el agente en idx
  function fraccionMismoGrupo(grid, nb, idx) {
    var self = grid[idx];
    if (self === 0) return 1; // vacío: siempre satisfecho
    var mismo = 0, total = 0;
    for (var k = 0; k < 8; k++) {
      var v = grid[nb[k]];
      if (v !== 0) {
        total++;
        if (v === self) mismo++;
      }
    }
    return total === 0 ? 1 : mismo / total;
  }

  // Un tick de simulación: mueve agentes insatisfechos a celdas vacías
  // Devuelve { nInsatisfechos, fracMedia }
  function stepSimulation(grid, rng) {
    var cache  = getNeighborCache();
    var total  = N * N;
    var vacias = [];
    var insatisfechos = [];

    for (var i = 0; i < total; i++) {
      if (grid[i] === 0) {
        vacias.push(i);
      } else {
        if (fraccionMismoGrupo(grid, cache[i], i) < UMBRAL_T) {
          insatisfechos.push(i);
        }
      }
    }

    // Barajar insatisfechos y vacías
    for (var i = insatisfechos.length - 1; i > 0; i--) {
      var j = (rng() * (i + 1)) | 0;
      var t = insatisfechos[i]; insatisfechos[i] = insatisfechos[j]; insatisfechos[j] = t;
    }
    for (var i = vacias.length - 1; i > 0; i--) {
      var j = (rng() * (i + 1)) | 0;
      var t = vacias[i]; vacias[i] = vacias[j]; vacias[j] = t;
    }

    // Mover cada insatisfecho a una celda vacía al azar
    var moved = Math.min(insatisfechos.length, vacias.length);
    for (var k = 0; k < moved; k++) {
      var src = insatisfechos[k];
      var dst = vacias[k];
      grid[dst] = grid[src];
      grid[src] = 0;
    }

    // Calcular fracción media de mismo grupo (solo agentes)
    var sumFrac = 0, nAgentes = 0;
    for (var i = 0; i < total; i++) {
      if (grid[i] !== 0) {
        sumFrac += fraccionMismoGrupo(grid, cache[i], i);
        nAgentes++;
      }
    }
    var fracMedia = nAgentes > 0 ? sumFrac / nAgentes : 0;

    return { nInsatisfechos: insatisfechos.length, fracMedia: fracMedia };
  }

  // ─── Renderizado canvas ───────────────────────────────────────────────────

  // Interpola color hex entre fondo y color de grupo
  function hexToRGB(hex) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    return [r, g, b];
  }

  var RGB_BG   = hexToRGB(COLOR_BG);
  var RGB_ROJO = hexToRGB(COLOR_ROJO);
  var RGB_AZUL = hexToRGB(COLOR_AZUL);

  function blendColor(rgb, alpha) {
    var r = Math.round(lerp(RGB_BG[0], rgb[0], alpha));
    var g = Math.round(lerp(RGB_BG[1], rgb[1], alpha));
    var b = Math.round(lerp(RGB_BG[2], rgb[2], alpha));
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  // Dibuja la rejilla en el canvas; alpha controla la opacidad global (fade)
  function drawGrid(ctx, grid, cellW, cellH, alpha) {
    var total = N * N;
    for (var i = 0; i < total; i++) {
      var g = grid[i];
      if (g === 0) continue;
      var col = i % N;
      var row = (i / N) | 0;
      var x = col * cellW;
      var y = row * cellH;
      var rgb = g === 1 ? RGB_ROJO : RGB_AZUL;
      ctx.fillStyle = blendColor(rgb, alpha);
      // Puntos ligeramente más pequeños que la celda para ver el tejido
      var pad = cellW > 6 ? 0.8 : 0.3;
      ctx.fillRect(x + pad, y + pad, cellW - pad * 2, cellH - pad * 2);
    }
  }

  // Dibuja la curva de fracción en la parte inferior del canvas
  function drawCurve(ctx, W, H, histFrac, fracActual, alpha) {
    var chartH   = Math.round(H * 0.18);
    var chartY   = H - chartH - 4;
    var chartX   = Math.round(W * 0.05);
    var chartW   = Math.round(W * 0.42);
    var maxPts   = 30; // puntos máximos visibles

    // Fondo semitransparente
    ctx.save();
    ctx.globalAlpha = alpha * 0.7;
    ctx.fillStyle = 'rgba(14,26,43,0.75)';
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(chartX - 4, chartY - 4, chartW + 8, chartH + 12, 6)
                  : ctx.rect(chartX - 4, chartY - 4, chartW + 8, chartH + 12);
    ctx.fill();
    ctx.globalAlpha = alpha;

    // Etiquetas
    ctx.fillStyle = COLOR_TEXT;
    ctx.font = '10px system-ui,sans-serif';
    ctx.globalAlpha = alpha * 0.5;
    ctx.fillText('fracción mismo grupo', chartX, chartY - 6);
    ctx.globalAlpha = alpha;

    var pts = histFrac.concat([fracActual]);
    if (pts.length > maxPts) pts = pts.slice(pts.length - maxPts);

    var n = pts.length;
    if (n < 2) { ctx.restore(); return; }

    // Línea de referencia 0.70
    ctx.strokeStyle = 'rgba(224,164,88,0.25)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    var yRef = chartY + chartH - (0.70 - 0.45) / (1.0 - 0.45) * chartH;
    ctx.beginPath();
    ctx.moveTo(chartX, yRef);
    ctx.lineTo(chartX + chartW, yRef);
    ctx.stroke();
    ctx.setLineDash([]);

    // Línea principal
    ctx.strokeStyle = COLOR_ACCENT;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (var k = 0; k < n; k++) {
      var px = chartX + (k / (n - 1)) * chartW;
      var py = chartY + chartH - clamp((pts[k] - 0.45) / (1.0 - 0.45), 0, 1) * chartH;
      k === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Punto final con valor
    var lastX = chartX + chartW;
    var lastY = chartY + chartH - clamp((fracActual - 0.45) / (1.0 - 0.45), 0, 1) * chartH;
    ctx.fillStyle = COLOR_ACCENT;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  // Dibuja el número flotante que late al converger
  function drawPulseNumber(ctx, W, H, value, pulse) {
    var size = 28 + pulse * 8;
    ctx.save();
    ctx.globalAlpha = 0.85 + pulse * 0.15;
    ctx.font = 'bold ' + size.toFixed(1) + 'px system-ui,sans-serif';
    ctx.fillStyle = COLOR_ACCENT;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    // Sombra suave
    ctx.shadowColor = COLOR_ACCENT;
    ctx.shadowBlur = 12 + pulse * 8;
    ctx.fillText(value.toFixed(4), W * 0.75, H * 0.88);
    ctx.shadowBlur = 0;
    ctx.font = '12px system-ui,sans-serif';
    ctx.globalAlpha = 0.55;
    ctx.fillText('fracción final', W * 0.75, H * 0.88 + size / 2 + 4);
    ctx.restore();
  }

  // ─── Sparkline del historial canónico ─────────────────────────────────────

  function buildSparklineSVG(histFrac, w, h) {
    var n   = histFrac.length;
    var min = 0.45, max = 1.0;
    var pts = histFrac.map(function (v, i) {
      var x = (i / (n - 1)) * (w - 4) + 2;
      var y = h - 2 - ((v - min) / (max - min)) * (h - 4);
      return x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
    return '<svg width="' + w + '" height="' + h + '" class="__sch-sparkline" style="overflow:visible">'
      + '<polyline points="' + pts + '" fill="none" stroke="' + COLOR_ACCENT + '" stroke-width="1.8"/>'
      + '<circle cx="' + ((n - 1) / (n - 1) * (w - 4) + 2).toFixed(1) + '" cy="'
      + (h - 2 - ((histFrac[n - 1] - min) / (max - min)) * (h - 4)).toFixed(1) + '" r="3" fill="' + COLOR_ACCENT + '"/>'
      + '</svg>';
  }

  // ─── Panel overlay (click) ─────────────────────────────────────────────────

  function buildPanelHTML(data) {
    var p = data.panel;
    var sujetos = ['qwen2.5:3b', 'qwen3:14b', 'gpt-oss:20b', 'qwen3:32b', 'claude-sonnet', 'claude-opus'];
    var veredictoLabels = { 'CORRECTO': 'ok', 'INCORRECTO': 'fail', 'SIN_RESPUESTA*': 'none' };

    // Sparkline SVG
    var spark = buildSparklineSVG(data.historial_frac_mismo_grupo, 220, 44);

    // Tabla de sujetos por pregunta
    var tHead = '<tr><th>Modelo</th><th>n28 frac=0.714</th><th>n29 vacías=250</th><th>n30 emergente 0.7507</th><th>Aciertos</th></tr>';
    var tRows = sujetos.map(function (s) {
      var short = s.replace('claude-', '').replace('qwen', 'q').replace('gpt-oss', 'gpt');
      var q28 = (data.detalle_preguntas[0] && data.detalle_preguntas[0].sujetos[s]) || {};
      var q29 = (data.detalle_preguntas[1] && data.detalle_preguntas[1].sujetos[s]) || {};
      var q30 = (data.detalle_preguntas[2] && data.detalle_preguntas[2].sujetos[s]) || {};
      var r   = (data.rendimiento_sujetos && data.rendimiento_sujetos[s]) || {};

      function badge(v) {
        var cls = veredictoLabels[v] || 'none';
        var sym = cls === 'ok' ? '✓' : cls === 'fail' ? '✗' : '–';
        return '<span class="badge badge-' + cls + '">' + sym + '</span>';
      }
      var highlight = s === 'claude-sonnet' ? ' style="background:rgba(224,164,88,0.07)"' : '';
      return '<tr' + highlight + '><td><strong>' + s + '</strong></td>'
        + '<td>' + badge(q28.veredicto) + '</td>'
        + '<td>' + badge(q29.veredicto) + '</td>'
        + '<td>' + badge(q30.veredicto) + ' <span style="font-size:10px;opacity:.6">'
        + (q30.respuesta ? q30.respuesta.replace('Respuesta final: ', '') : '—') + '</span></td>'
        + '<td style="text-align:center;font-weight:700">' + (r.aciertos || 0) + '/3</td>'
        + '</tr>';
    }).join('');

    // Costos
    var costRows = '';
    var vias = data.costos || {};
    var viaOrder = ['python_local', 'qwen2.5:3b', 'qwen3:14b', 'gpt-oss:20b', 'qwen3:32b', 'claude-sonnet', 'claude-opus'];
    viaOrder.forEach(function (v) {
      if (!vias[v]) return;
      var c = vias[v];
      var cStr = '';
      if (c.valor !== undefined && c.valor !== 'no_medido') {
        cStr = '$' + Number(c.valor).toExponential(3);
      } else if (c.rango_min !== undefined) {
        cStr = '$' + c.rango_min.toFixed(4) + ' – $' + c.rango_max.toFixed(4);
      } else {
        cStr = 'no medido';
      }
      costRows += '<tr><td>' + v + '</td><td style="text-align:right">' + cStr + '</td></tr>';
    });

    return '<div style="position:relative">'
      + '<button class="close-btn" data-action="close" aria-label="Cerrar">×</button>'
      + '<h2>Segregación de Schelling <small style="font-weight:400;font-size:.8em;opacity:.7">(1971)</small></h2>'
      + '<p style="opacity:.65;font-size:12px">' + p.descripcion + '</p>'
      + '<div class="formula">satisfecho(i) : f<sub>i</sub> = vecinos_mismo / vecinos_ocupados ≥ T = 0.30</div>'

      + '<h3>Resultados canónicos (seed=42, 50×50, T=0.3)</h3>'
      + '<div class="kpi-row">'
      + '<div class="kpi"><div class="val">' + p.fraccion_inicial_real.toFixed(4) + '</div><div class="lbl">fracción inicial</div></div>'
      + '<div class="kpi"><div class="val" style="color:#48c878">' + p.fraccion_final_real.toFixed(4) + '</div><div class="lbl">fracción final</div></div>'
      + '<div class="kpi"><div class="val">' + p.iteracion_convergencia + '</div><div class="lbl">iteraciones</div></div>'
      + '<div class="kpi"><div class="val">' + p.n_insatisfechos_final + '</div><div class="lbl">insatisfechos final</div></div>'
      + '</div>'
      + '<p style="font-size:11px;opacity:.6">Criterio: fracción_final &gt; 0.70 → <span style="color:#48c878;font-weight:700">SUPERADO (0.7507)</span></p>'

      + '<h3>Trayectoria fracción mismo grupo (canónica, 15 valores)</h3>'
      + spark
      + '<p style="font-size:10px;opacity:.5;margin:0">0.501 → 0.591 → … → 0.7507 (convergencia en paso 14)</p>'

      + '<h3>Rendimiento de los 6 modelos IA (3 preguntas)</h3>'
      + '<table><thead>' + tHead + '</thead><tbody>' + tRows + '</tbody></table>'
      + '<p class="cost-note">Solo claude-sonnet acertó el valor emergente 0.7507. claude-opus respondió ~0.85 (error &gt; tolerancia ±0.05).</p>'

      + '<h3>Costo total por vía (USD)</h3>'
      + '<table><thead><tr><th>Vía</th><th style="text-align:right">Costo USD</th></tr></thead><tbody>'
      + costRows + '</tbody></table>'

      + '<p class="ref">' + p.referencia + '</p>'
      + '</div>';
  }

  function openPanel(data, container) {
    injectPanelStyles();
    var overlay = document.createElement('div');
    overlay.className = '__sch-overlay';
    var panel = document.createElement('div');
    panel.className = '__sch-panel';
    panel.innerHTML = buildPanelHTML(data);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    function close() {
      overlay.style.transition = 'opacity .25s';
      overlay.style.opacity = '0';
      setTimeout(function () { overlay.remove(); }, 260);
      document.removeEventListener('keydown', onKey);
    }

    function onKey(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay || (e.target.dataset && e.target.dataset.action === 'close')) {
        close();
      }
    });
  }

  // ─── Máquina de estados de animación ─────────────────────────────────────
  // Estados: 'running' | 'pausing' | 'fading_out' | 'fading_in'

  function createSimState(seedOffset) {
    var rng  = makePRNG(0x9E3779B9 + (seedOffset | 0) * 0x517CC1B7);
    var grid = initGrid(rng);
    return { grid: grid, rng: rng, histFrac: [], tick: 0, nIns: 9999 };
  }

  // ─── mount ────────────────────────────────────────────────────────────────

  window.VIZ['schelling'] = {
    titulo: 'La segregación que nadie eligió',

    mount: function (container, opts) {
      opts = opts || {};
      var compact = !!opts.compact;

      // ── Reduced-motion: fallback estático ────────────────────────────────
      var prefersReduced = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      // ── Canvas ────────────────────────────────────────────────────────────
      var canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:100%;';
      container.style.background = COLOR_BG;
      container.appendChild(canvas);
      var ctx = canvas.getContext('2d');

      var dpr = window.devicePixelRatio || 1;

      function resize() {
        var W = container.clientWidth  || 1200;
        var H = container.clientHeight || 800;
        canvas.width  = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width  = W + 'px';
        canvas.style.height = H + 'px';
        ctx.scale(dpr, dpr);
      }
      resize();

      var resizeObs = new ResizeObserver(resize);
      resizeObs.observe(container);

      // ── Estado ────────────────────────────────────────────────────────────
      var data       = null;       // datos JSON cargados
      var simState   = null;
      var seedOffset = 0;

      var phase      = 'fading_in'; // arranca en fade-in desde negro
      var phaseT     = 0;           // ms transcurridos en la fase actual
      var lastTs     = null;
      var rafId      = null;
      var paused     = false;
      var destroyed  = false;

      // Acumulador de tiempo para ticks de simulación
      var tickAccum  = 0;
      var tickMs     = 1000 / TICKS_PER_SEC;

      // Historial para la curva de la viz (no el canónico)
      var vizHistFrac = [];
      var vizFracActual = 0.5;
      var vizConverged = false;

      // Para el latido del número
      var pulsePhase = 0;

      // ── Carga de datos ────────────────────────────────────────────────────
      var dataPath = (function () {
        // Detecta ruta relativa al script
        var scripts = document.querySelectorAll('script[src*="schelling"]');
        if (scripts.length) {
          var src = scripts[scripts.length - 1].src;
          return src.replace('viz/schelling.js', 'datos/schelling.json')
                    .replace('viz\\schelling.js', 'datos/schelling.json');
        }
        return '../datos/schelling.json';
      })();

      fetch(dataPath)
        .then(function (r) { return r.json(); })
        .then(function (d) { data = d; })
        .catch(function (e) { console.warn('[VIZ/schelling] No se pudo cargar schelling.json:', e); });

      // ── Inicializar primera simulación ────────────────────────────────────
      simState = createSimState(seedOffset);
      vizHistFrac = [];
      vizFracActual = 0.5;
      vizConverged = false;

      // ── Fallback estático ─────────────────────────────────────────────────
      if (prefersReduced) {
        // Dibuja un frame estático con la curva completa si hay datos
        function drawFallback() {
          var W = canvas.width / dpr, H = canvas.height / dpr;
          ctx.clearRect(0, 0, W, H);
          ctx.fillStyle = COLOR_BG;
          ctx.fillRect(0, 0, W, H);

          // Rejilla mezclada (estado inicial) — lado izquierdo
          var rngF = makePRNG(42);
          var gridF = initGrid(rngF);
          var cW = (W * 0.42) / N, cH = (H * 0.85) / N;
          ctx.save();
          ctx.translate(W * 0.02, H * 0.08);
          drawGrid(ctx, gridF, cW, cH, 1);
          ctx.restore();

          // Rejilla segregada: 14 pasos de simulación
          var rngSeg = makePRNG(42);
          var gridSeg = initGrid(rngSeg);
          for (var i = 0; i < 14; i++) stepSimulation(gridSeg, rngSeg);
          ctx.save();
          ctx.translate(W * 0.52, H * 0.08);
          drawGrid(ctx, gridSeg, cW, cH, 1);
          ctx.restore();

          // Curva completa
          if (data) {
            drawCurve(ctx, W, H, data.historial_frac_mismo_grupo, data.resultados.fraccion_final, 1);
          }

          // Cifra anotada
          ctx.fillStyle = COLOR_ACCENT;
          ctx.font = 'bold 36px system-ui,sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText('0.7507', W * 0.75, H * 0.5);
          ctx.font = '13px system-ui,sans-serif';
          ctx.fillStyle = COLOR_TEXT;
          ctx.fillText('fracción final', W * 0.75, H * 0.5 + 26);
        }
        drawFallback();
        // Redibujar si llegan los datos
        var fallbackWait = setInterval(function () {
          if (data || destroyed) { clearInterval(fallbackWait); if (data) drawFallback(); }
        }, 200);

        // Click para panel
        canvas.style.cursor = 'pointer';
        function onClickFallback() { if (data) openPanel(data, container); }
        canvas.addEventListener('click', onClickFallback);

        return {
          pause:   function () {},
          resume:  function () {},
          destroy: function () {
            destroyed = true;
            clearInterval(fallbackWait);
            canvas.removeEventListener('click', onClickFallback);
            resizeObs.disconnect();
            canvas.remove();
          }
        };
      }

      // ── Loop de animación principal ───────────────────────────────────────

      function startNewCycle() {
        seedOffset++;
        simState = createSimState(seedOffset);
        vizHistFrac = [];
        vizFracActual = 0.5;
        vizConverged = false;
        pulsePhase = 0;
        phase  = 'fading_in';
        phaseT = 0;
      }

      function frame(ts) {
        if (destroyed) return;
        if (paused) { rafId = requestAnimationFrame(frame); return; }

        var dt = lastTs ? Math.min(ts - lastTs, 100) : 0; // cap 100ms para tabs en 2do plano
        lastTs = ts;
        phaseT += dt;

        var W = canvas.width / dpr, H = canvas.height / dpr;
        var cellW = W / N, cellH = H / N;

        // ── Lógica de fase ──────────────────────────────────────────────────
        if (phase === 'fading_in') {
          // Primeros ticks de simulación mientras aparece
          tickAccum += dt;
          while (tickAccum >= tickMs && !vizConverged) {
            tickAccum -= tickMs;
            var result = stepSimulation(simState.grid, simState.rng);
            vizHistFrac.push(vizFracActual);
            vizFracActual = result.fracMedia;
            simState.tick++;
            if (result.nInsatisfechos === 0) {
              vizConverged = true;
            }
          }
          if (phaseT >= FADE_MS) {
            phase  = 'running';
            phaseT = 0;
          }
        } else if (phase === 'running') {
          tickAccum += dt;
          while (tickAccum >= tickMs && !vizConverged) {
            tickAccum -= tickMs;
            var result = stepSimulation(simState.grid, simState.rng);
            vizHistFrac.push(vizFracActual);
            vizFracActual = result.fracMedia;
            simState.tick++;
            if (result.nInsatisfechos === 0) {
              vizConverged = true;
            }
          }
          if (vizConverged) {
            phase  = 'pausing';
            phaseT = 0;
            pulsePhase = 0;
          }
        } else if (phase === 'pausing') {
          // El número late; simulación quieta
          pulsePhase = (phaseT / 600) * Math.PI * 2; // latido suave ~1.6s por ciclo
          if (phaseT >= PAUSE_MS) {
            phase  = 'fading_out';
            phaseT = 0;
          }
        } else if (phase === 'fading_out') {
          if (phaseT >= FADE_MS) {
            startNewCycle();
          }
        }

        // ── Render ──────────────────────────────────────────────────────────
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = COLOR_BG;
        ctx.fillRect(0, 0, W, H);

        // Alpha global según fase
        var alpha = 1;
        if (phase === 'fading_in') {
          alpha = clamp(phaseT / FADE_MS, 0, 1);
          // Easing suave (ease-out cubic)
          alpha = 1 - Math.pow(1 - alpha, 3);
        } else if (phase === 'fading_out') {
          alpha = clamp(1 - phaseT / FADE_MS, 0, 1);
          alpha = Math.pow(alpha, 2); // ease-in
        }

        // Rejilla
        drawGrid(ctx, simState.grid, cellW, cellH, alpha);

        // Curva de fracción (abajo-izquierda)
        drawCurve(ctx, W, H, vizHistFrac, vizFracActual, alpha);

        // Número latiente durante pausa
        if (phase === 'pausing' || (phase === 'fading_out' && phaseT < 300)) {
          var pulse = Math.max(0, Math.sin(pulsePhase + phaseT / 600 * Math.PI * 2));
          var fadeAlpha = phase === 'fading_out' ? clamp(1 - phaseT / 300, 0, 1) : 1;
          ctx.save();
          ctx.globalAlpha = fadeAlpha;
          drawPulseNumber(ctx, W, H, vizFracActual, pulse * 0.5);
          ctx.restore();
        }

        // Indicador de iteración (esquina superior derecha)
        ctx.save();
        ctx.globalAlpha = alpha * 0.45;
        ctx.fillStyle = COLOR_TEXT;
        ctx.font = (compact ? '10px' : '11px') + ' system-ui,sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('iter ' + simState.tick + '  T=' + UMBRAL_T, W - 12, 20);
        ctx.restore();

        rafId = requestAnimationFrame(frame);
      }

      rafId = requestAnimationFrame(frame);

      // ── IntersectionObserver: pausa fuera de viewport ─────────────────────
      var visible = true;
      var iObs = new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        if (!visible) { paused = true; }
        else if (!document.hidden) { paused = false; lastTs = null; }
      }, { threshold: 0.05 });
      iObs.observe(container);

      // ── Pausa en tab oculto ────────────────────────────────────────────────
      function onVisChange() {
        if (document.hidden) { paused = true; }
        else if (visible) { paused = false; lastTs = null; }
      }
      document.addEventListener('visibilitychange', onVisChange);

      // ── Click: abrir panel ────────────────────────────────────────────────
      canvas.style.cursor = 'pointer';
      function onClick() {
        if (data) openPanel(data, container);
      }
      canvas.addEventListener('click', onClick);

      // ── API pública ────────────────────────────────────────────────────────
      return {
        pause: function () { paused = true; },
        resume: function () {
          if (!document.hidden && visible) { paused = false; lastTs = null; }
        },
        destroy: function () {
          destroyed = true;
          cancelAnimationFrame(rafId);
          document.removeEventListener('visibilitychange', onVisChange);
          canvas.removeEventListener('click', onClick);
          iObs.disconnect();
          resizeObs.disconnect();
          canvas.remove();
        }
      };
    }
  };

})();
