/**
 * automata.js — Visualización animada del autómata celular de crecimiento urbano.
 *
 * Registro global:
 *   window.VIZ = window.VIZ || {};
 *   window.VIZ['automata'] = { titulo, mount(container, opts) }
 *
 * mount(container, opts) → { pause, resume, destroy }
 *
 * opts.compact  — boolean, reduce densidad para móvil
 * opts.dataUrl  — override de la URL del JSON (por defecto "../datos/automata.json")
 */

(function () {
  'use strict';

  /* ═══════════════════════════════════════════════════════════════════
     CONSTANTES DE PALETA Y ANIMACIÓN
  ═══════════════════════════════════════════════════════════════════ */
  var BG_COLOR       = '#0e1a2b';
  var ACCENT_COLOR   = '#e0a458';   // ámbar base
  var TEXT_COLOR     = '#e8e6e1';
  var PANEL_BG       = 'rgba(14,26,43,0.97)';
  var SETTLED_MIN    = 0.38;        // luminosidad mínima de celda asentada
  var SETTLED_MAX    = 0.62;        // luminosidad máxima
  var FLASH_FRAMES   = 18;          // frames que una celda nueva permanece brillante
  var STEP_INTERVAL  = 120;         // ms entre pasos del autómata
  var PAUSE_AFTER    = 1500;        // ms de pausa al completar 50 pasos
  var FADE_FRAMES    = 45;          // frames del fade de reset
  var GRID_SIZE      = 100;
  var N_STEPS        = 50;
  var P_BASE         = 0.001;
  var P_DIFUSION     = 1.0;
  var NUCLEUS_R      = 1;           // radio del núcleo: celdas [49..51] x [49..51]

  /* ═══════════════════════════════════════════════════════════════════
     UTILIDADES MATEMÁTICAS
  ═══════════════════════════════════════════════════════════════════ */

  /** LCG determinista (no requiere seed=7 canónico; es re-simulación ilustrativa) */
  function makePRNG(seed) {
    var s = (seed >>> 0) || 1;
    return function () {
      s = (Math.imul(1664525, s) + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  /** Convierte luminosidad [0,1] a color ámbar HSL */
  function amberColor(l) {
    // Ámbar: hue≈38, saturación alta
    return 'hsl(38,92%,' + Math.round(l * 100) + '%)';
  }

  /** Easing cúbico para fade */
  function easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /* ═══════════════════════════════════════════════════════════════════
     SIMULACIÓN SINCRÓNICA
  ═══════════════════════════════════════════════════════════════════ */

  /**
   * Ejecuta un paso síncrono del autómata sobre el buffer `grid` (Uint8Array).
   * Devuelve array de índices recién urbanizados.
   *
   * Regla fronteriza: p_i = 0 si k_i = 0 (sin nucleación espontánea).
   */
  function stepAutomata(grid, rng) {
    var newCells = [];
    var candidates = [];

    // Recopilar celdas no urbanas con al menos un vecino urbano
    for (var row = 0; row < GRID_SIZE; row++) {
      for (var col = 0; col < GRID_SIZE; col++) {
        var idx = row * GRID_SIZE + col;
        if (grid[idx] !== 0) continue; // ya urbana

        // Contar vecinos Moore-8 (frontera absorbente: borde = no vecino)
        var k = 0;
        for (var dr = -1; dr <= 1; dr++) {
          for (var dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            var r2 = row + dr, c2 = col + dc;
            if (r2 < 0 || r2 >= GRID_SIZE || c2 < 0 || c2 >= GRID_SIZE) continue;
            if (grid[r2 * GRID_SIZE + c2] !== 0) k++;
          }
        }

        if (k > 0) candidates.push({ idx: idx, k: k });
      }
    }

    // Aplicar regla estocástica sincrónica
    for (var i = 0; i < candidates.length; i++) {
      var c = candidates[i];
      var pi = P_BASE + P_DIFUSION * (c.k / 8);
      if (rng() < pi) {
        newCells.push(c.idx);
      }
    }

    // Actualizar grid
    for (var j = 0; j < newCells.length; j++) {
      grid[newCells[j]] = 1;
    }

    return newCells;
  }

  /* ═══════════════════════════════════════════════════════════════════
     FALLBACK ESTÁTICO (prefers-reduced-motion)
  ═══════════════════════════════════════════════════════════════════ */

  function renderFallback(container, data) {
    container.style.background = BG_COLOR;
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    container.style.fontFamily = 'system-ui,sans-serif';
    container.style.color = TEXT_COLOR;
    container.style.padding = '2rem';

    // Título
    var h2 = document.createElement('h2');
    h2.textContent = data.titulo;
    h2.style.cssText = 'color:' + ACCENT_COLOR + ';font-size:1.1rem;margin:0 0 1.5rem;text-align:center;';
    container.appendChild(h2);

    // 4 mini-grids estáticos
    var frames = data.fallback_frames || [
      { paso: 0, celdas: 9 }, { paso: 15, celdas: 253 },
      { paso: 30, celdas: 965 }, { paso: 50, celdas: 2672 }
    ];
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;margin-bottom:1.5rem;';
    container.appendChild(row);

    frames.forEach(function (fr) {
      var wrap = document.createElement('div');
      wrap.style.cssText = 'text-align:center;';

      var cv = document.createElement('canvas');
      var S = 80;
      cv.width = S; cv.height = S;
      cv.style.cssText = 'display:block;border:1px solid rgba(224,164,88,0.3);';
      wrap.appendChild(cv);

      var ctx = cv.getContext('2d');
      ctx.fillStyle = BG_COLOR;
      ctx.fillRect(0, 0, S, S);

      // Dibuja un disco aproximado proporcional a 'celdas'
      var frac = fr.celdas / (GRID_SIZE * GRID_SIZE);
      var r = Math.sqrt(frac / Math.PI) * S * 0.9;
      ctx.beginPath();
      ctx.arc(S / 2, S / 2, Math.max(r, 2), 0, Math.PI * 2);
      ctx.fillStyle = ACCENT_COLOR;
      ctx.fill();

      var lbl = document.createElement('div');
      lbl.style.cssText = 'font-size:0.65rem;color:' + ACCENT_COLOR + ';margin-top:0.3rem;';
      lbl.textContent = 'paso ' + fr.paso + ' (' + fr.celdas + ')';
      wrap.appendChild(lbl);
      row.appendChild(wrap);
    });

    // Sparkline celdas_urbanas_por_paso
    var sparkWrap = document.createElement('div');
    sparkWrap.style.cssText = 'width:100%;max-width:480px;';

    var sparkLbl = document.createElement('div');
    sparkLbl.style.cssText = 'font-size:0.7rem;opacity:0.7;margin-bottom:0.3rem;text-align:center;';
    sparkLbl.textContent = 'celdas urbanas por paso (9 → 2672)';
    sparkWrap.appendChild(sparkLbl);

    var sc = document.createElement('canvas');
    sc.width = 480; sc.height = 60;
    sc.style.cssText = 'width:100%;height:auto;';
    sparkWrap.appendChild(sc);
    container.appendChild(sparkWrap);

    var sctx = sc.getContext('2d');
    sctx.fillStyle = 'rgba(255,255,255,0.05)';
    sctx.fillRect(0, 0, 480, 60);

    var series = data.series.celdas_urbanas_por_paso;
    var maxV = Math.max.apply(null, series);
    sctx.beginPath();
    series.forEach(function (v, i) {
      var x = (i / (series.length - 1)) * 478 + 1;
      var y = 58 - (v / maxV) * 56;
      if (i === 0) sctx.moveTo(x, y); else sctx.lineTo(x, y);
    });
    sctx.strokeStyle = ACCENT_COLOR;
    sctx.lineWidth = 1.5;
    sctx.stroke();
  }

  /* ═══════════════════════════════════════════════════════════════════
     PANEL OVERLAY CON DATOS CANÓNICOS
  ═══════════════════════════════════════════════════════════════════ */

  // Inyecta CSS del panel una sola vez
  var _panelStyleInjected = false;
  function injectPanelStyles() {
    if (_panelStyleInjected) return;
    _panelStyleInjected = true;
    var style = document.createElement('style');
    style.id = 'viz-automata-styles';
    style.textContent = [
      '.viz-automata-overlay{',
        'position:fixed;inset:0;z-index:9999;',
        'background:rgba(5,12,22,0.82);',
        'display:flex;align-items:center;justify-content:center;',
        'backdrop-filter:blur(4px);',
        'animation:vizFadeIn 0.25s ease;',
      '}',
      '@keyframes vizFadeIn{from{opacity:0}to{opacity:1}}',
      '.viz-automata-panel{',
        'background:' + PANEL_BG + ';',
        'border:1px solid rgba(224,164,88,0.35);',
        'border-radius:10px;',
        'padding:1.8rem 2.2rem;',
        'max-width:680px;width:90vw;',
        'max-height:88vh;overflow-y:auto;',
        'font-family:system-ui,sans-serif;',
        'color:' + TEXT_COLOR + ';',
        'font-size:0.88rem;line-height:1.55;',
        'box-shadow:0 8px 40px rgba(0,0,0,0.6);',
      '}',
      '.viz-automata-panel h3{',
        'color:' + ACCENT_COLOR + ';',
        'margin:0 0 1rem;font-size:1rem;font-weight:700;',
        'border-bottom:1px solid rgba(224,164,88,0.25);',
        'padding-bottom:0.5rem;',
      '}',
      '.viz-automata-panel .vap-formula{',
        'background:rgba(224,164,88,0.1);',
        'border-left:3px solid ' + ACCENT_COLOR + ';',
        'padding:0.6rem 1rem;border-radius:0 6px 6px 0;',
        'font-family:monospace;font-size:0.9rem;',
        'margin:0.8rem 0;',
      '}',
      '.viz-automata-panel .vap-kv{display:flex;gap:0.5rem;margin:0.3rem 0;}',
      '.viz-automata-panel .vap-k{color:rgba(232,230,225,0.55);min-width:11rem;flex-shrink:0;}',
      '.viz-automata-panel .vap-v{color:' + TEXT_COLOR + ';font-weight:600;}',
      '.viz-automata-panel table{width:100%;border-collapse:collapse;margin:0.8rem 0;font-size:0.8rem;}',
      '.viz-automata-panel th{',
        'background:rgba(224,164,88,0.15);',
        'padding:0.35rem 0.6rem;text-align:left;',
        'color:' + ACCENT_COLOR + ';font-weight:600;',
      '}',
      '.viz-automata-panel td{',
        'padding:0.3rem 0.6rem;',
        'border-bottom:1px solid rgba(255,255,255,0.06);',
      '}',
      '.viz-automata-panel .vap-correct{color:#6fcf97;}',
      '.viz-automata-panel .vap-wrong{color:#eb5757;}',
      '.viz-automata-panel .vap-none{color:#f2994a;opacity:0.8;}',
      '.viz-automata-panel .vap-close-btn{',
        'position:absolute;top:1rem;right:1.2rem;',
        'background:none;border:none;',
        'color:rgba(232,230,225,0.5);',
        'font-size:1.4rem;cursor:pointer;line-height:1;',
        'transition:color 0.15s;',
      '}',
      '.viz-automata-panel .vap-close-btn:hover{color:' + ACCENT_COLOR + ';}',
      '.viz-automata-panel .vap-sparkline{display:block;width:100%;height:48px;margin-top:0.6rem;}',
      '.viz-automata-panel .vap-section{margin-top:1.2rem;}',
      '.viz-automata-panel .vap-badge{',
        'display:inline-block;',
        'background:rgba(224,164,88,0.18);',
        'border:1px solid rgba(224,164,88,0.4);',
        'border-radius:4px;padding:0.1rem 0.5rem;',
        'font-size:0.78rem;color:' + ACCENT_COLOR + ';',
        'margin-left:0.4rem;',
      '}',
    ].join('');
    document.head.appendChild(style);
  }

  function buildPanel(data, closeCallback) {
    injectPanelStyles();

    var overlay = document.createElement('div');
    overlay.className = 'viz-automata-overlay';

    var panel = document.createElement('div');
    panel.className = 'viz-automata-panel';
    panel.style.position = 'relative';

    // Close button
    var closeBtn = document.createElement('button');
    closeBtn.className = 'vap-close-btn';
    closeBtn.setAttribute('aria-label', 'Cerrar panel');
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', closeCallback);
    panel.appendChild(closeBtn);

    // Keyboard close
    function onKey(e) {
      if (e.key === 'Escape') { closeCallback(); document.removeEventListener('keydown', onKey); }
    }
    document.addEventListener('keydown', onKey);
    overlay._removeKey = function () { document.removeEventListener('keydown', onKey); };

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeCallback();
    });

    var p = data.panel;
    var par = data.parametros;
    var res = data.resultados_finales;

    // ── Título ──
    var h3 = document.createElement('h3');
    h3.textContent = 'Autómata celular · regla de transición';
    panel.appendChild(h3);

    // ── Fórmula ──
    var formula = document.createElement('div');
    formula.className = 'vap-formula';
    formula.innerHTML = 'p<sub>i</sub> = p<sub>base</sub> + p<sub>difusión</sub> × (k<sub>i</sub> / 8)' +
      '<br><span style="font-size:0.78rem;opacity:0.7;">' +
      'regla fronteriza: k<sub>i</sub> = 0 → p<sub>i</sub> = 0 (sin nucleación espontánea)</span>';
    panel.appendChild(formula);

    // ── Atribución ──
    function kv(k, v) {
      var d = document.createElement('div'); d.className = 'vap-kv';
      var dk = document.createElement('span'); dk.className = 'vap-k'; dk.textContent = k;
      var dv = document.createElement('span'); dv.className = 'vap-v'; dv.textContent = v;
      d.appendChild(dk); d.appendChild(dv); return d;
    }
    panel.appendChild(kv('Autores:', 'White & Engelen 1993 / Clarke 1997'));
    panel.appendChild(kv('Antecedente:', 'Tobler 1979 (geografía celular)'));
    panel.appendChild(kv('Rejilla:', par.grid_size + '×' + par.grid_size));
    panel.appendChild(kv('Núcleo inicial:', par.nucleo_tam + '×' + par.nucleo_tam + ' → ' + (par.nucleo_tam * par.nucleo_tam) + ' celdas'));
    panel.appendChild(kv('p_base:', par.p_base));
    panel.appendChild(kv('p_difusión:', par.p_difusion));
    panel.appendChild(kv('Semilla canónica:', par.semilla));

    // ── Validación ──
    var secVal = document.createElement('div'); secVal.className = 'vap-section';
    var h3v = document.createElement('h3'); h3v.textContent = 'Validación canónica (seed = 7)';
    secVal.appendChild(h3v);
    secVal.appendChild(kv('Celdas paso 50:', res.celdas_urbanas_paso_50 + '  ← valor emergente'));
    secVal.appendChild(kv('Conexidad (todos pasos):', '100%'));
    secVal.appendChild(kv('Compacidad isoperimétrica:', (res.compacidad_isoperimetrica_final).toFixed(3)));
    secVal.appendChild(kv('Dimensión fractal (d_f):', (res.dimension_fractal).toFixed(3) + '  (indicador secundario)'));
    panel.appendChild(secVal);

    // ── Sparkline ──
    var series = data.series.celdas_urbanas_por_paso;
    var sparkSec = document.createElement('div'); sparkSec.className = 'vap-section';
    var h3sp = document.createElement('h3');
    h3sp.textContent = 'Celdas urbanas por paso (9 → 2672)';
    sparkSec.appendChild(h3sp);

    var sparkCV = document.createElement('canvas');
    sparkCV.className = 'vap-sparkline';
    sparkCV.width = 600; sparkCV.height = 60;
    sparkSec.appendChild(sparkCV);
    panel.appendChild(sparkSec);

    // Render sparkline after append (so offsetWidth works)
    setTimeout(function () {
      var sctx = sparkCV.getContext('2d');
      var W = sparkCV.width, H = sparkCV.height;
      var maxV = Math.max.apply(null, series);
      sctx.fillStyle = 'rgba(255,255,255,0.04)';
      sctx.fillRect(0, 0, W, H);

      // area fill
      sctx.beginPath();
      series.forEach(function (v, i) {
        var x = (i / (series.length - 1)) * (W - 2) + 1;
        var y = (H - 4) - (v / maxV) * (H - 8);
        if (i === 0) sctx.moveTo(x, H - 2); else sctx.lineTo(x, y);
      });
      sctx.lineTo(W - 1, H - 2);
      sctx.closePath();
      sctx.fillStyle = 'rgba(224,164,88,0.12)';
      sctx.fill();

      // line
      sctx.beginPath();
      series.forEach(function (v, i) {
        var x = (i / (series.length - 1)) * (W - 2) + 1;
        var y = (H - 4) - (v / maxV) * (H - 8);
        if (i === 0) sctx.moveTo(x, y); else sctx.lineTo(x, y);
      });
      sctx.strokeStyle = ACCENT_COLOR;
      sctx.lineWidth = 2;
      sctx.stroke();

      // markers para 4 frames del fallback
      [0, 15, 30, 50].forEach(function (paso) {
        var v = series[paso];
        var x = (paso / (series.length - 1)) * (W - 2) + 1;
        var y = (H - 4) - (v / maxV) * (H - 8);
        sctx.beginPath();
        sctx.arc(x, y, 3, 0, Math.PI * 2);
        sctx.fillStyle = '#fff';
        sctx.fill();
      });
    }, 0);

    // ── Tabla rendimiento IAs en pregunta emergente n=6 ──
    var secIA = document.createElement('div'); secIA.className = 'vap-section';
    var h3ia = document.createElement('h3');
    h3ia.innerHTML = 'IAs vs. valor emergente 2672' +
      '<span class="vap-badge">0/6 correctas</span>';
    secIA.appendChild(h3ia);

    var intro = document.createElement('p');
    intro.style.cssText = 'font-size:0.78rem;opacity:0.7;margin:0 0 0.6rem;';
    intro.textContent =
      'Pregunta n=6 (tipo emergente): "¿cuántas celdas urbanas tras 50 pasos?" — ' +
      'ningún modelo acertó el valor determinista.';
    secIA.appendChild(intro);

    var table = document.createElement('table');
    var thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>Modelo</th><th>Respuesta</th><th>Veredicto</th></tr>';
    table.appendChild(thead);
    var tbody = document.createElement('tbody');

    var qEmerg = null;
    (p.preguntas_ia || []).forEach(function (q) { if (q.n === 6) qEmerg = q; });

    if (qEmerg) {
      var sujetos = ['qwen2.5:3b', 'qwen3:14b', 'gpt-oss:20b', 'qwen3:32b', 'claude-sonnet', 'claude-opus'];
      sujetos.forEach(function (suj) {
        var s = qEmerg.sujetos[suj];
        if (!s) return;
        var tr = document.createElement('tr');
        var vclass = s.veredicto === 'CORRECTO' ? 'vap-correct' :
                     s.veredicto === 'SIN_RESPUESTA' || s.veredicto.indexOf('SIN') !== -1 ? 'vap-none' : 'vap-wrong';
        var displayName = suj.replace('claude-', 'Claude ').replace('qwen', 'Qwen');
        tr.innerHTML =
          '<td>' + displayName + '</td>' +
          '<td style="font-family:monospace">' + (s.respuesta || '—').substring(0, 40) + '</td>' +
          '<td class="' + vclass + '">' + s.veredicto + '</td>';
        tbody.appendChild(tr);
      });
    }
    table.appendChild(tbody);
    secIA.appendChild(table);
    panel.appendChild(secIA);

    // ── Costos ──
    var secCost = document.createElement('div'); secCost.className = 'vap-section';
    var h3c = document.createElement('h3'); h3c.textContent = 'Costo por vía';
    secCost.appendChild(h3c);

    var costos = data.costos;
    if (costos && costos.python_local_automata) {
      var py = costos.python_local_automata;
      if (py.elapsed_s) {
        secCost.appendChild(kv('Python (esta simulación):', py.elapsed_s.toFixed(2) + ' s · ' +
          (py.energia_J ? py.energia_J.toFixed(1) + ' J · ' : '') +
          (py.costo_usd ? '$' + py.costo_usd.toExponential(2) + ' USD' : '')));
      }
    }
    if (costos && costos.por_via) {
      var vias = costos.por_via;
      var viaOrder = ['python_local', 'qwen2.5:3b', 'qwen3:14b', 'gpt-oss:20b', 'qwen3:32b', 'claude-sonnet', 'claude-opus'];
      viaOrder.forEach(function (via) {
        var v = vias[via];
        if (!v) return;
        if (via === 'python_local') return; // ya mostrado arriba
        var minV = typeof v.min === 'number' ? v.min : null;
        var maxV = typeof v.max === 'number' && v.max !== v.min ? v.max : null;
        if (minV === null) return;
        var txt = '$' + minV.toFixed(4) + (maxV ? '–$' + maxV.toFixed(4) : '') + ' USD (total exp.)';
        secCost.appendChild(kv(via + ':', txt));
      });
    }
    panel.appendChild(secCost);

    overlay.appendChild(panel);
    return overlay;
  }

  /* ═══════════════════════════════════════════════════════════════════
     MOTOR DE ANIMACIÓN PRINCIPAL
  ═══════════════════════════════════════════════════════════════════ */

  function mount(container, opts) {
    opts = opts || {};
    var compact = !!opts.compact;
    var dataUrl = opts.dataUrl || '../datos/automata.json';

    // Detectar prefers-reduced-motion
    var prefersReduced = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ── Canvas setup ─────────────────────────────────────────────── */
    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'display:block;position:absolute;inset:0;';
    /* No pisar un host posicionado en absolute/fixed: solo posicionar si está
       en flujo normal (static). Un host absolute ya sirve de contexto. */
    if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
    container.style.overflow = 'hidden';
    container.style.background = BG_COLOR;
    container.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;

    function resizeCanvas() {
      var W = container.clientWidth;
      var H = container.clientHeight;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width  = W + 'px';
      canvas.style.height = H + 'px';
      ctx.scale(dpr, dpr);
      return { W: W, H: H };
    }

    var dim = resizeCanvas();

    /* ── Estado de simulación ─────────────────────────────────────── */
    var grid     = new Uint8Array(GRID_SIZE * GRID_SIZE);
    var flashAge = new Int16Array(GRID_SIZE * GRID_SIZE); // >0 = frames restantes
    var settled  = new Float32Array(GRID_SIZE * GRID_SIZE); // luminosidad estable

    // Semilla del PRNG ilustrativo (varía por sesión para que cada run sea diferente)
    var rng = makePRNG(Date.now() & 0xFFFF);

    function initGrid() {
      grid.fill(0);
      flashAge.fill(0);
      settled.fill(0);
      // Núcleo 3×3 centrado
      var cx = Math.floor(GRID_SIZE / 2);
      var cy = Math.floor(GRID_SIZE / 2);
      for (var r = cx - NUCLEUS_R; r <= cx + NUCLEUS_R; r++) {
        for (var c = cy - NUCLEUS_R; c <= cy + NUCLEUS_R; c++) {
          grid[r * GRID_SIZE + c] = 1;
          settled[r * GRID_SIZE + c] = 0.55 + rng() * 0.1;
          flashAge[r * GRID_SIZE + c] = 0;
        }
      }
    }

    /* ── Control de tiempo del autómata ──────────────────────────── */
    var step         = 0;
    var lastStepTime = 0;
    var isPaused     = false;
    var isFading     = false;
    var fadeFrame    = 0;
    var inPauseAfterEnd = false;
    var pauseEndTime    = 0;

    /* ── Escalado visual ──────────────────────────────────────────── */
    // Tamaño de celda en píxeles lógicos
    function getCellSize() {
      var W = container.clientWidth;
      var H = container.clientHeight;
      // Queremos que la rejilla GRID_SIZE × GRID_SIZE quepa cómodamente
      var maxSide = Math.min(W, H) * (compact ? 0.82 : 0.88);
      return Math.max(1, maxSide / GRID_SIZE);
    }

    /* ── Render frame ─────────────────────────────────────────────── */
    function render(fadeAlpha) {
      var W = container.clientWidth;
      var H = container.clientHeight;
      var cs = getCellSize();
      var gridPx = cs * GRID_SIZE;
      var ox = (W - gridPx) / 2;   // offset x para centrar
      var oy = (H - gridPx) / 2;

      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = BG_COLOR;
      ctx.fillRect(0, 0, W, H);

      // Sutil borde/glow de la rejilla
      ctx.strokeStyle = 'rgba(224,164,88,0.06)';
      ctx.lineWidth = 1;
      ctx.strokeRect(ox - 0.5, oy - 0.5, gridPx + 1, gridPx + 1);

      // Dibuja celdas urbanas
      for (var i = 0; i < GRID_SIZE * GRID_SIZE; i++) {
        if (grid[i] === 0) continue;
        var row = Math.floor(i / GRID_SIZE);
        var col = i % GRID_SIZE;
        var x = ox + col * cs;
        var y = oy + row * cs;

        var l;
        if (flashAge[i] > 0) {
          // Celda recién urbanizada: pulso ámbar brillante
          var t = flashAge[i] / FLASH_FRAMES;
          l = 0.75 + t * 0.18; // 0.75..0.93
        } else {
          l = settled[i]; // luminosidad estable
        }

        ctx.fillStyle = 'hsl(38,90%,' + Math.round(l * 100) + '%)';
        // Pequeño gap entre celdas para que el retículo se perciba
        var gap = cs > 3 ? 0.6 : 0.2;
        ctx.fillRect(x + gap / 2, y + gap / 2, cs - gap, cs - gap);
      }

      // Overlay de fade si reset
      if (typeof fadeAlpha === 'number' && fadeAlpha > 0) {
        ctx.fillStyle = 'rgba(14,26,43,' + fadeAlpha + ')';
        ctx.fillRect(0, 0, W, H);
      }

      // HUD: paso actual y celdas
      var urbanCount = 0;
      for (var j = 0; j < grid.length; j++) { if (grid[j]) urbanCount++; }

      ctx.font = (compact ? '11px' : '13px') + ' monospace';
      ctx.fillStyle = 'rgba(224,164,88,0.7)';
      ctx.fillText('paso ' + step + '  ·  ' + urbanCount + ' celdas', ox + 6, oy + gridPx + 18);

      // Clic hint
      ctx.font = (compact ? '10px' : '11px') + ' system-ui';
      ctx.fillStyle = 'rgba(232,230,225,0.3)';
      ctx.fillText('clic → datos canónicos', ox + 6, oy - 8);
    }

    /* ── Loop RAF ─────────────────────────────────────────────────── */
    var rafId = null;

    function loop(now) {
      if (isPaused) { rafId = null; return; }

      rafId = requestAnimationFrame(loop);

      dim = resizeCanvas();

      // ── Fade de reset ──
      if (isFading) {
        fadeFrame++;
        var t = easeInOut(Math.min(fadeFrame / FADE_FRAMES, 1));
        render(t);
        if (fadeFrame >= FADE_FRAMES) {
          isFading = false;
          fadeFrame = 0;
          initGrid();
          step = 0;
          lastStepTime = now;
        }
        return;
      }

      // ── Pausa al finalizar ciclo ──
      if (inPauseAfterEnd) {
        render(0);
        if (now >= pauseEndTime) {
          inPauseAfterEnd = false;
          isFading = true;
          fadeFrame = 0;
        }
        return;
      }

      // ── Avance del autómata ──
      if (step <= N_STEPS && now - lastStepTime >= STEP_INTERVAL) {
        lastStepTime = now;

        if (step < N_STEPS) {
          // Envejecer flash
          for (var i = 0; i < flashAge.length; i++) {
            if (flashAge[i] > 0) flashAge[i]--;
          }

          var newCells = stepAutomata(grid, rng);
          for (var k = 0; k < newCells.length; k++) {
            var idx = newCells[k];
            flashAge[idx] = FLASH_FRAMES;
            // Asignar luminosidad de asentamiento aleatoria (variación sutil)
            settled[idx] = SETTLED_MIN + rng() * (SETTLED_MAX - SETTLED_MIN);
          }
          step++;
        } else {
          // Ciclo completo: pausa y luego fade
          inPauseAfterEnd = true;
          pauseEndTime = now + PAUSE_AFTER;
        }
      }

      // Bajar flash frame a frame (suavizado)
      for (var fi = 0; fi < flashAge.length; fi++) {
        // Ya se decrementó en el paso de avance; aquí solo render
      }

      render(0);
    }

    /* ── Datos y arranque ─────────────────────────────────────────── */
    var loadedData = null;
    var overlay    = null;

    fetch(dataUrl)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        loadedData = data;

        if (prefersReduced) {
          renderFallback(container, data);
          return;
        }

        initGrid();
        lastStepTime = performance.now();
        rafId = requestAnimationFrame(loop);
      })
      .catch(function (err) {
        console.warn('[automata.js] No se pudo cargar', dataUrl, err);
        // Arrancar de todos modos sin datos del panel
        if (!prefersReduced) {
          initGrid();
          lastStepTime = performance.now();
          rafId = requestAnimationFrame(loop);
        }
      });

    /* ── IntersectionObserver: auto-pausa fuera de viewport ──────── */
    var isVisible = true;
    var io = null;
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(function (entries) {
        isVisible = entries[0].isIntersecting;
        if (!isVisible && !isPaused) { pauseInternal(); }
        else if (isVisible && isPaused && !_manualPause) { resumeInternal(); }
      }, { threshold: 0.1 });
      io.observe(container);
    }

    /* document.hidden: pausar cuando la pestaña no es activa */
    function onVisibilityChange() {
      if (document.hidden) { pauseInternal(); }
      else if (!document.hidden && !_manualPause && isVisible) { resumeInternal(); }
    }
    document.addEventListener('visibilitychange', onVisibilityChange);

    var _manualPause = false;

    function pauseInternal() {
      isPaused = true;
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    }
    function resumeInternal() {
      if (isPaused) {
        isPaused = false;
        lastStepTime = performance.now();
        rafId = requestAnimationFrame(loop);
      }
    }

    /* ── Click → panel overlay ───────────────────────────────────── */
    canvas.style.cursor = 'pointer';
    canvas.addEventListener('click', function () {
      if (overlay) return; // ya abierto
      if (!loadedData) return;

      pauseInternal();
      _manualPause = true;

      overlay = buildPanel(loadedData, function () {
        if (overlay) {
          if (overlay._removeKey) overlay._removeKey();
          overlay.parentNode && overlay.parentNode.removeChild(overlay);
          overlay = null;
        }
        _manualPause = false;
        resumeInternal();
      });

      document.body.appendChild(overlay);
    });

    /* ── API pública ─────────────────────────────────────────────── */
    return {
      pause: function () {
        _manualPause = true;
        pauseInternal();
      },
      resume: function () {
        _manualPause = false;
        if (isVisible && !document.hidden) resumeInternal();
      },
      destroy: function () {
        pauseInternal();
        document.removeEventListener('visibilitychange', onVisibilityChange);
        if (io) io.disconnect();
        if (overlay) {
          if (overlay._removeKey) overlay._removeKey();
          overlay.parentNode && overlay.parentNode.removeChild(overlay);
          overlay = null;
        }
        if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
      }
    };
  }

  /* ═══════════════════════════════════════════════════════════════════
     REGISTRO GLOBAL
  ═══════════════════════════════════════════════════════════════════ */
  window.VIZ = window.VIZ || {};
  window.VIZ['automata'] = {
    titulo: 'La mancha urbana crece por contagio de borde',
    mount: mount
  };

})();
