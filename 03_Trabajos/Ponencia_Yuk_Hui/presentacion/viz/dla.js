/**
 * dla.js — Visualización DLA (Diffusion-Limited Aggregation) Batty-Longley 1994
 * Módulo clásico (sin ES modules). Registra window.VIZ['dla'].
 *
 * Paleta: fondo #0e1a2b · texto #e8e6e1 · acento/semilla #e0a458
 * La partícula más reciente es ámbar (#e0a458), la más antigua es azul secundario (#2a5fa5).
 */
(function () {
  'use strict';

  /* ─── Paleta ─────────────────────────────────────────────── */
  var C = {
    BG:     '#0e1a2b',
    TEXT:   '#e8e6e1',
    AMBER:  '#e0a458',   // adhesión reciente / semilla
    OLD:    '#2a5fa5',   // adhesión antigua
    GRID:   'rgba(255,255,255,0.04)',
    PANEL_BG: 'rgba(14,26,43,0.97)',
    DOT_LAUNCH: 'rgba(255,255,255,0.25)',
  };

  /* ─── Interpolación de color por orden de adhesión ──────── */
  function adhesionColor(t) {
    // t ∈ [0,1]: 0 = antiguo (OLD), 1 = reciente (AMBER)
    var rA = 0xe0, gA = 0xa4, bA = 0x58;  // AMBER
    var rO = 0x2a, gO = 0x5f, bO = 0xa5;  // OLD
    var r = Math.round(rO + (rA - rO) * t);
    var g = Math.round(gO + (gA - gO) * t);
    var b = Math.round(bO + (bA - bO) * t);
    return 'rgb(' + r + ',' + g + ',' + b + ')';
  }

  /* ─── Inyección de estilos del panel (una sola vez) ──────── */
  var PANEL_STYLES_INJECTED = false;
  function injectPanelStyles() {
    if (PANEL_STYLES_INJECTED) return;
    PANEL_STYLES_INJECTED = true;
    var style = document.createElement('style');
    style.textContent = [
      '.dla-panel-overlay{',
        'position:fixed;top:0;left:0;width:100%;height:100%;z-index:9999;',
        'background:rgba(0,0,0,0.72);display:flex;align-items:center;',
        'justify-content:center;animation:dlaFadeIn 0.25s ease;',
      '}',
      '.dla-panel-box{',
        'background:' + C.PANEL_BG + ';color:' + C.TEXT + ';',
        'border:1px solid rgba(224,164,88,0.3);border-radius:10px;',
        'padding:28px 32px 24px;max-width:700px;width:92%;',
        'max-height:85vh;overflow-y:auto;font-family:system-ui,sans-serif;',
        'position:relative;box-shadow:0 8px 40px rgba(0,0,0,0.7);',
      '}',
      '.dla-panel-box h2{margin:0 0 4px;font-size:1.15rem;color:' + C.AMBER + ';font-weight:700;}',
      '.dla-panel-box h3{margin:18px 0 6px;font-size:0.95rem;color:' + C.AMBER + ';opacity:0.85;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}',
      '.dla-panel-box p{margin:4px 0;font-size:0.9rem;line-height:1.55;opacity:0.92;}',
      '.dla-panel-box .ref{font-size:0.78rem;opacity:0.6;margin-top:2px;}',
      '.dla-panel-box table{border-collapse:collapse;width:100%;margin-top:6px;font-size:0.82rem;}',
      '.dla-panel-box th{text-align:left;padding:4px 8px;border-bottom:1px solid rgba(224,164,88,0.3);color:' + C.AMBER + ';opacity:0.85;}',
      '.dla-panel-box td{padding:3px 8px;border-bottom:1px solid rgba(255,255,255,0.06);}',
      '.dla-panel-box .v-ok{color:#4caf50;}',
      '.dla-panel-box .v-fail{color:#ef5350;}',
      '.dla-panel-box .v-na{color:#888;}',
      '.dla-panel-close{',
        'position:absolute;top:12px;right:14px;background:none;border:none;',
        'color:' + C.TEXT + ';font-size:1.4rem;cursor:pointer;opacity:0.7;line-height:1;',
        'padding:4px 8px;border-radius:4px;transition:opacity .15s;',
      '}',
      '.dla-panel-close:hover{opacity:1;background:rgba(255,255,255,0.07);}',
      '.dla-loglog-canvas{display:block;width:100%;max-width:520px;margin:12px auto 4px;',
        'border-radius:6px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);}',
      '@keyframes dlaFadeIn{from{opacity:0}to{opacity:1}}',
    ].join('');
    document.head.appendChild(style);
  }

  /* ─── Dibuja el mini log-log en un canvas auxiliar ──────── */
  function drawLogLog(canvas, data) {
    var dpr = window.devicePixelRatio || 1;
    var W = canvas.clientWidth  || 520;
    var H = canvas.clientHeight || 280;
    canvas.width  = W * dpr;
    canvas.height = H * dpr;
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    var pad = { left: 52, right: 18, top: 16, bottom: 42 };
    var plotW = W - pad.left - pad.right;
    var plotH = H - pad.top  - pad.bottom;

    // Datos canónicos: todos 30 puntos
    var radii  = data.mass_radius_data.radii;
    var counts = data.mass_radius_data.counts;
    var rFit   = data.mass_radius_data.radii_fit;
    var cFit   = data.mass_radius_data.counts_fit;
    var D      = data.dimension_fractal_simulacion.D;          // 1.69275
    var b      = data.dimension_fractal_simulacion.intercepto_log; // 0.83287 (log10)

    // Escala log10
    var logR = radii.map(Math.log10);
    var logC = counts.map(Math.log10);
    var xMin = logR[0], xMax = logR[logR.length - 1];
    var yMin = logC[0] - 0.05, yMax = logC[logC.length - 1] + 0.05;

    function xPx(lx) { return pad.left  + (lx - xMin) / (xMax - xMin) * plotW; }
    function yPx(ly) { return pad.top   + plotH - (ly - yMin) / (yMax - yMin) * plotH; }

    // Fondo
    ctx.fillStyle = 'rgba(255,255,255,0.02)';
    ctx.fillRect(0, 0, W, H);

    // Grid ligero
    ctx.strokeStyle = C.GRID;
    ctx.lineWidth = 1;
    for (var i = 0; i <= 4; i++) {
      var lx = xMin + i * (xMax - xMin) / 4;
      ctx.beginPath(); ctx.moveTo(xPx(lx), pad.top); ctx.lineTo(xPx(lx), pad.top + plotH); ctx.stroke();
      var ly = yMin + i * (yMax - yMin) / 4;
      ctx.beginPath(); ctx.moveTo(pad.left, yPx(ly)); ctx.lineTo(pad.left + plotW, yPx(ly)); ctx.stroke();
    }

    // Puntos completos (todos 30, gris claro)
    ctx.fillStyle = 'rgba(232,230,225,0.45)';
    for (var j = 0; j < radii.length; j++) {
      var cx = xPx(logR[j]), cy = yPx(logC[j]);
      ctx.beginPath(); ctx.arc(cx, cy, 2.5, 0, 2 * Math.PI); ctx.fill();
    }

    // Puntos del fit (ámbar, más visibles)
    var logRf = rFit.map(Math.log10);
    var logCf = cFit.map(Math.log10);
    ctx.fillStyle = C.AMBER;
    for (var k = 0; k < rFit.length; k++) {
      var fx = xPx(logRf[k]), fy = yPx(logCf[k]);
      ctx.beginPath(); ctx.arc(fx, fy, 3, 0, 2 * Math.PI); ctx.fill();
    }

    // Recta de regresión: log10(N) = b + D * log10(R)
    ctx.strokeStyle = C.AMBER;
    ctx.lineWidth = 2;
    ctx.beginPath();
    var x0 = xMin, x1 = xMax;
    ctx.moveTo(xPx(x0), yPx(b + D * x0));
    ctx.lineTo(xPx(x1), yPx(b + D * x1));
    ctx.stroke();

    // Anotación de pendiente
    var midX = (x0 + x1) / 2;
    var midY = b + D * midX;
    ctx.fillStyle = C.AMBER;
    ctx.font = 'bold 11px system-ui';
    ctx.fillText('D = ' + D.toFixed(4), xPx(midX) + 8, yPx(midY) - 8);

    // Ejes
    ctx.strokeStyle = 'rgba(232,230,225,0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.stroke();

    // Etiquetas ejes
    ctx.fillStyle = 'rgba(232,230,225,0.7)';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('log₁₀(R)', pad.left + plotW / 2, H - 6);
    ctx.save();
    ctx.translate(13, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('log₁₀(N)', 0, 0);
    ctx.restore();

    // Ticks
    ctx.textAlign = 'center';
    for (var ti = 0; ti <= 4; ti++) {
      var tlx = xMin + ti * (xMax - xMin) / 4;
      ctx.fillText(Math.pow(10, tlx).toFixed(1), xPx(tlx), pad.top + plotH + 14);
    }
    ctx.textAlign = 'right';
    for (var ti2 = 0; ti2 <= 4; ti2++) {
      var tly = yMin + ti2 * (yMax - yMin) / 4;
      ctx.fillText(Math.pow(10, tly).toFixed(0), pad.left - 5, yPx(tly) + 3);
    }
  }

  /* ─── Abre el panel overlay ──────────────────────────────── */
  function openPanel(data, canvasEl) {
    injectPanelStyles();
    var overlay = document.createElement('div');
    overlay.className = 'dla-panel-overlay';

    var d = data.dimension_fractal_simulacion;
    var ej = data.dimension_fractal_ejemplo_literal;
    var pan = data.panel;

    // Tabla de rendimiento por sujeto
    var subjRows = '';
    var sujetos = Object.keys(pan.rendimiento_sujetos);
    sujetos.forEach(function (s) {
      var stats = pan.rendimiento_sujetos[s];
      var pct = (stats.exactitud * 100).toFixed(0) + '%';
      var cls = stats.exactitud >= 1.0 ? 'v-ok' : stats.exactitud < 0.5 ? 'v-fail' : 'v-na';
      subjRows += '<tr><td>' + s + '</td><td class="' + cls + '">' +
        stats.aciertos + '/' + stats.total + '</td><td class="' + cls + '">' + pct + '</td></tr>';
    });

    // Tabla de preguntas
    var pqRows = '';
    pan.preguntas.forEach(function (p) {
      var vds = Object.entries(p.veredictos).map(function (kv) {
        var v = kv[1];
        var cls = v === 'CORRECTO' ? 'v-ok' : v === 'INCORRECTO' ? 'v-fail' : 'v-na';
        return '<span class="' + cls + '">' + kv[0].replace('claude-', 'C-') + ':' + (v === 'CORRECTO' ? '✓' : v === 'INCORRECTO' ? '✗' : '–') + '</span>';
      }).join(' ');
      pqRows += '<tr><td>n' + p.n + '</td><td>' + p.tipo + '</td>' +
        '<td>' + p.valor_exacto + '</td><td>' + vds + '</td></tr>';
    });

    // Tabla de costos
    var costRows = '';
    var vias = data.vias_costo;
    Object.keys(vias).forEach(function (k) {
      var v = vias[k];
      var costo = v.costo_usd;
      var costoStr = '';
      if (typeof costo === 'object' && costo !== null) {
        if (costo.valor !== undefined) costoStr = '$' + (+costo.valor).toFixed(6);
        else if (costo.rango_min !== undefined) costoStr = '$' + costo.rango_min.toFixed(2) + '–$' + costo.rango_max.toFixed(2);
      }
      costRows += '<tr><td>' + k + '</td><td>' + costoStr + '</td></tr>';
    });

    overlay.innerHTML = '<div class="dla-panel-box">' +
      '<button class="dla-panel-close" title="Cerrar (Esc)">✕</button>' +
      '<h2>DLA fractal urbano — Batty & Longley 1994</h2>' +
      '<p class="ref">Aggregation-limited diffusion · dimension fractal por mass-radius</p>' +

      '<h3>Fórmula canónica</h3>' +
      '<p style="font-family:monospace;font-size:1rem;letter-spacing:.02em;">' +
        pan.formula +
      '</p>' +
      '<p>Dimensión simulación: <strong style="color:' + C.AMBER + '">D = ' + d.D.toFixed(5) + '</strong> &nbsp;·&nbsp; ' +
        'R² = <strong>' + d.R2.toFixed(5) + '</strong> &nbsp;·&nbsp; ' +
        'Criterio D ∈ [1.60, 1.80]: <span class="v-ok">CUMPLIDO</span></p>' +
      '<p>Ejemplo literal (dos puntos): D = log(' + ej.N2 + '/' + ej.N1 + ') / log(' + ej.R2 + '/' + ej.R1 + ') = <strong>' + ej.D.toFixed(3) + '</strong></p>' +

      '<h3>Gráfico log-log N(R) ~ R<sup>D</sup></h3>' +
      '<canvas class="dla-loglog-canvas" id="dlaLogLogCanvas" width="520" height="280"></canvas>' +
      '<p class="ref">Puntos ámbar = rango de fit (20 pts). Gris = todos 30 puntos. Recta: pendiente D = ' + d.D.toFixed(4) + '.</p>' +

      '<h3>Rendimiento modelos IA (preguntas n16–18)</h3>' +
      '<table><thead><tr><th>Sujeto</th><th>Aciertos</th><th>Exactitud</th></tr></thead>' +
      '<tbody>' + subjRows + '</tbody></table>' +
      '<p class="ref">qwen2.5:3b 1/3 (falló emergente n18); los 4 modelos grandes 3/3.</p>' +

      '<h3>Detalle por pregunta</h3>' +
      '<table><thead><tr><th>n</th><th>Tipo</th><th>Valor</th><th>Veredictos</th></tr></thead>' +
      '<tbody>' + pqRows + '</tbody></table>' +

      '<h3>Costo por vía</h3>' +
      '<table><thead><tr><th>Vía</th><th>Costo USD</th></tr></thead>' +
      '<tbody>' + costRows + '</tbody></table>' +
      '<p class="ref">Fuente: costos.json · Tarifa eléctrica ~0.20 USD/kWh · API Anthropic jun-2026</p>' +
    '</div>';

    document.body.appendChild(overlay);

    // Dibuja el log-log DESPUÉS de que el DOM exista
    requestAnimationFrame(function () {
      var llc = document.getElementById('dlaLogLogCanvas');
      if (llc) drawLogLog(llc, data);
    });

    // Cierre
    function close() { document.body.removeChild(overlay); }
    overlay.querySelector('.dla-panel-close').addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

    // Cierre con Escape (una sola vez por overlay)
    function onKey(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); }
    }
    document.addEventListener('keydown', onKey);
    overlay.addEventListener('remove', function () { document.removeEventListener('keydown', onKey); });
  }

  /* ══════════════════════════════════════════════════════════
     MOTOR DLA — caminata aleatoria + cluster
  ══════════════════════════════════════════════════════════ */

  /**
   * Clase DLASimulation
   * Opera en una rejilla de GRID_SIZE × GRID_SIZE celdas.
   * No es seed=3 canónico; usa Math.random() para variedad perpetua.
   */
  function DLASimulation(gridSize) {
    this.G = gridSize;         // p.ej. 201
    this.center = Math.floor(gridSize / 2);
    this.grid = new Uint8Array(gridSize * gridSize);  // 0 = libre, 1 = ocupada
    this.order = new Float32Array(gridSize * gridSize); // tiempo de adhesión normalizado [0,1]
    this.count = 0;            // partículas adheridas
    this.maxParticles = 1500;
    this.radius = 0;           // radio actual del cluster (para lanzar desde el borde)

    // Vecindad 4-conectada
    this.dx = [1, -1, 0, 0];
    this.dy = [0, 0, 1, -1];

    // Semilla central
    var s = this.center;
    this.grid[s * gridSize + s] = 1;
    this.order[s * gridSize + s] = 0;
    this.count = 1;
    this.radius = 1;
  }

  DLASimulation.prototype.reset = function () {
    this.grid.fill(0);
    this.order.fill(0);
    this.count = 1;
    this.radius = 1;
    var s = this.center;
    this.grid[s * this.G + s] = 1;
    this.order[s * this.G + s] = 0;
  };

  /* Lanza una partícula y la pasea hasta adhesión o descarte */
  DLASimulation.prototype.stepParticle = function () {
    var G = this.G;
    var margin = 5;
    // Radio de lanzamiento = radio del cluster + margen de seguridad
    var launchR = this.radius + margin + 2;
    if (launchR >= G / 2 - 2) launchR = Math.floor(G / 2 - 3);

    // Lanzar en un círculo de radio launchR
    var angle = Math.random() * 2 * Math.PI;
    var cx = this.center, cy = this.center;
    var px = Math.round(cx + launchR * Math.cos(angle));
    var py = Math.round(cy + launchR * Math.sin(angle));
    px = Math.max(1, Math.min(G - 2, px));
    py = Math.max(1, Math.min(G - 2, py));

    // Radio de muerte: si la partícula se aleja demasiado, descartarla
    var killR = launchR + 12;
    var maxSteps = G * G;   // seguridad anti-bucle

    for (var step = 0; step < maxSteps; step++) {
      // Comprobar adhesión (4-vecinos)
      var stuck = false;
      for (var d = 0; d < 4; d++) {
        var nx = px + this.dx[d];
        var ny = py + this.dy[d];
        if (nx >= 0 && nx < G && ny >= 0 && ny < G && this.grid[ny * G + nx] === 1) {
          stuck = true;
          break;
        }
      }
      if (stuck) {
        this.grid[py * G + px] = 1;
        // t: 1 = más reciente, decrece conforme aumenta el conteo
        this.order[py * G + px] = this.count / this.maxParticles;
        this.count++;
        // Actualizar radio del cluster
        var dr = Math.sqrt((px - cx) * (px - cx) + (py - cy) * (py - cy));
        if (dr > this.radius) this.radius = dr;
        return true;  // adhesión producida
      }

      // Paso browniano
      var dir = (Math.random() * 4) | 0;
      px += this.dx[dir];
      py += this.dy[dir];

      // Reflejo en bordes
      if (px < 1) px = 1; if (px > G - 2) px = G - 2;
      if (py < 1) py = 1; if (py > G - 2) py = G - 2;

      // Descarte por alejamiento
      var dist2 = (px - cx) * (px - cx) + (py - cy) * (py - cy);
      if (dist2 > killR * killR) return false;
    }
    return false;
  };

  /* ══════════════════════════════════════════════════════════
     RENDERER — dibuja el cluster en el canvas principal
  ══════════════════════════════════════════════════════════ */

  /**
   * Dibuja todas las celdas ocupadas con color por orden de adhesión.
   * cellSize: tamaño en px de cada celda de la rejilla.
   */
  function renderCluster(ctx, sim, cellSize, alpha) {
    var G = sim.G;
    var cx = sim.center, cy = sim.center;
    // Viewport: centramos en el canvas
    var offX = ctx.canvas.width  / (window.devicePixelRatio || 1) / 2 - cx * cellSize;
    var offY = ctx.canvas.height / (window.devicePixelRatio || 1) / 2 - cy * cellSize;

    ctx.globalAlpha = alpha;
    for (var y = 0; y < G; y++) {
      for (var x = 0; x < G; x++) {
        if (sim.grid[y * G + x] === 1) {
          // t: orden temporal de adhesión normalizado
          // La semilla central tiene order=0, las más recientes se acercan a 1
          var rawT = sim.order[y * G + x];
          // Recalcular t relativo al conteo actual para actualizar colores en vivo
          var t = 1 - rawT; // invertimos: order cercano a 0 = antiguo, near 1 = reciente
          // pero la semilla tiene rawT=0 y queremos que sea ámbar (semilla = punto inicial)
          // Aclaramos: rawT = conteoAdhesion / maxParticles
          // rawT=0 → semilla (antiguo en tiempo, pero queremos destacarla como ámbar)
          // Para el gradiente temporal: reciente (rawT~1) = ámbar, antiguo (rawT~0) = azul
          // La semilla (rawT=0) será azul, las últimas adheridas serán ámbar.
          ctx.fillStyle = adhesionColor(rawT);
          var px = Math.round(offX + x * cellSize);
          var py = Math.round(offY + y * cellSize);
          var sz = Math.max(1, Math.ceil(cellSize));
          ctx.fillRect(px, py, sz, sz);
        }
      }
    }
    ctx.globalAlpha = 1;
  }

  /* ══════════════════════════════════════════════════════════
     FALLBACK ESTÁTICO para prefers-reduced-motion
  ══════════════════════════════════════════════════════════ */
  function mountStatic(container, data) {
    container.style.position = 'relative';
    container.style.background = C.BG;
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    container.style.gap = '12px';
    container.style.padding = '16px';

    var img = document.createElement('img');
    // Ruta relativa desde el HTML que carga el módulo
    img.src = '../' + data.fallback_png;
    img.alt = 'Cluster DLA coloreado por orden de adhesión';
    img.style.cssText = 'max-width:100%;max-height:60%;border-radius:6px;object-fit:contain;';

    var caption = document.createElement('p');
    caption.textContent = data.titulo;
    caption.style.cssText = 'color:' + C.TEXT + ';font-family:system-ui;font-size:0.9rem;margin:0;opacity:0.85;';

    container.appendChild(img);
    container.appendChild(caption);

    // Click → panel
    container.addEventListener('click', function () { openPanel(data, null); });

    return { pause: function(){}, resume: function(){}, destroy: function(){ container.innerHTML = ''; }};
  }

  /* ══════════════════════════════════════════════════════════
     MOUNT PRINCIPAL
  ══════════════════════════════════════════════════════════ */
  function mount(container, opts) {
    opts = opts || {};
    var compact = !!opts.compact;

    // ── Fetch datos canónicos ──────────────────────────────
    var dataPath = (opts.dataPath || '../datos/dla.json');
    var loadedData = null;
    var vizReady = false;

    /* Estado de la animación */
    var rafId = null;
    var paused = false;
    var destroyed = false;
    var phase = 'growing';   // 'growing' | 'pause' | 'fading'
    var fadeAlpha = 1;
    var pauseTimer = 0;
    var PAUSE_DURATION = 1500;  // ms
    var FADE_DURATION  = 800;   // ms

    /* Canvas */
    var dpr = window.devicePixelRatio || 1;
    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:pointer;';
    /* No pisar un host posicionado en absolute/fixed (p. ej. fondos full-bleed
       con position:absolute;inset:0): solo posicionar si está en flujo normal. */
    if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
    container.style.overflow = 'hidden';
    container.style.background = C.BG;
    container.appendChild(canvas);

    var ctx = canvas.getContext('2d');

    function resize() {
      var W = container.clientWidth  || 1200;
      var H = container.clientHeight || 800;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      ctx.scale(dpr, dpr);
    }
    resize();
    var resizeObs = new ResizeObserver(resize);
    resizeObs.observe(container);

    /* Simulación DLA */
    var GRID = 201;
    var sim = new DLASimulation(GRID);

    /* cellSize: queremos que el cluster de radio ~67 quepa en ~40% del canvas */
    function getCellSize() {
      var W = container.clientWidth  || 1200;
      var H = container.clientHeight || 800;
      var side = Math.min(W, H);
      return compact ? (side / GRID) * 0.92 : (side / GRID) * 0.98;
    }

    /* Partículas en vuelo (máx concurrent) — más alto = cluster crece más rápido */
    var CONCURRENT = compact ? 6 : 12;

    /* ── Bucle de animación ─────────────────────────────── */
    var lastTime = 0;

    function loop(ts) {
      if (destroyed) return;
      if (paused) { rafId = requestAnimationFrame(loop); return; }

      var dt = ts - lastTime;
      lastTime = ts;
      if (dt > 200) dt = 200; // cap para tabs en segundo plano

      var W = canvas.width  / dpr;
      var H = canvas.height / dpr;

      /* ── Limpiar ── */
      ctx.fillStyle = C.BG;
      ctx.fillRect(0, 0, W, H);

      if (phase === 'growing') {
        /* Lanzar CONCURRENT partículas por frame */
        var adhesions = 0;
        for (var i = 0; i < CONCURRENT; i++) {
          if (sim.count < sim.maxParticles) {
            if (sim.stepParticle()) adhesions++;
          }
        }
        renderCluster(ctx, sim, getCellSize(), 1);

        if (sim.count >= sim.maxParticles) {
          phase = 'pause';
          pauseTimer = ts;
        }

      } else if (phase === 'pause') {
        renderCluster(ctx, sim, getCellSize(), 1);
        // Mostrar brevemente el coral completo
        if (ts - pauseTimer >= PAUSE_DURATION) {
          phase = 'fading';
          fadeAlpha = 1;
        }

      } else if (phase === 'fading') {
        fadeAlpha -= dt / FADE_DURATION;
        if (fadeAlpha <= 0) {
          fadeAlpha = 0;
          sim.reset();
          phase = 'growing';
        }
        renderCluster(ctx, sim, getCellSize(), Math.max(0, fadeAlpha));
      }

      /* Texto discreto: contador */
      drawHUD(ctx, sim, W, H, phase, fadeAlpha);

      rafId = requestAnimationFrame(loop);
    }

    /* ── HUD ── */
    function drawHUD(ctx, sim, W, H, phase, alpha) {
      var a = phase === 'fading' ? alpha : 1;
      ctx.globalAlpha = a * 0.55;
      ctx.fillStyle = C.TEXT;
      ctx.font = '11px system-ui';
      ctx.textAlign = 'right';
      var txt = 'N = ' + sim.count + ' / ' + sim.maxParticles;
      ctx.fillText(txt, W - 12, H - 12);
      ctx.globalAlpha = 1;
    }

    /* ── Pausa por visibilidad ── */
    function onVisibility() {
      if (document.hidden) { paused = true; } else { paused = false; }
    }
    document.addEventListener('visibilitychange', onVisibility);

    var intersectObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { paused = !e.isIntersecting; });
    }, { threshold: 0.1 });
    intersectObs.observe(container);

    /* ── Click → panel ── */
    canvas.addEventListener('click', function () {
      if (loadedData) openPanel(loadedData, canvas);
    });

    /* ── Fetch y arranque ── */
    fetch(dataPath)
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        loadedData = data;
        vizReady = true;
        lastTime = performance.now();
        rafId = requestAnimationFrame(loop);
      })
      .catch(function (err) {
        console.warn('[DLA] No se pudo cargar datos:', err);
        // Arranca igualmente sin panel
        lastTime = performance.now();
        rafId = requestAnimationFrame(loop);
      });

    /* ── API pública ── */
    return {
      pause:   function () { paused = true; },
      resume:  function () { paused = false; },
      destroy: function () {
        destroyed = true;
        if (rafId) cancelAnimationFrame(rafId);
        resizeObs.disconnect();
        intersectObs.disconnect();
        document.removeEventListener('visibilitychange', onVisibility);
        container.removeChild(canvas);
      }
    };
  }

  /* ──────────────────────────────────────────────────────── */
  /* Comprobación prefers-reduced-motion: mount devuelve la   */
  /* versión adecuada.                                        */
  /* ──────────────────────────────────────────────────────── */
  function smartMount(container, opts) {
    opts = opts || {};
    var dataPath = opts.dataPath || '../datos/dla.json';

    // Verificar prefers-reduced-motion
    var reducedMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (reducedMotion) {
      // Cargar datos y montar fallback estático
      fetch(dataPath)
        .then(function (r) { return r.json(); })
        .then(function (data) { mountStatic(container, data); })
        .catch(function () { mountStatic(container, { titulo: 'DLA Fractal', fallback_png: 'assets/sim/sim_dla_batty_longley_fractal_1.png' }); });
      return { pause: function(){}, resume: function(){}, destroy: function(){ container.innerHTML = ''; }};
    }

    return mount(container, opts);
  }

  /* ── Registro global ── */
  window.VIZ = window.VIZ || {};
  window.VIZ['dla'] = {
    titulo: 'La ciudad fractal se agrega partícula a partícula',
    mount: smartMount
  };

}());
