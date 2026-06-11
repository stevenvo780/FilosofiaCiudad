/**
 * christaller.js  —  Visualizacion animada de la tesselacion hexagonal de Christaller (k=3)
 * Registro global: window.VIZ['christaller']
 *
 * Contrato de mount(container, opts):
 *   - Crea un canvas propio adaptado al container (devicePixelRatio correcto)
 *   - Carga datos/christaller.json via fetch relativo
 *   - Anima un loop perpetuo: construccion jerarquica grande→pequeño, pausa, fade inverso
 *   - Se auto-pausa con IntersectionObserver y document.hidden
 *   - Respeta prefers-reduced-motion mostrando frame estatico
 *   - Click abre panel overlay con datos canonicos del JSON
 *   - Devuelve { pause, resume, destroy }
 */

(function () {
  'use strict';

  window.VIZ = window.VIZ || {};

  // ─── Paleta ──────────────────────────────────────────────────────────────
  var PALETTE = {
    bg:     '#0e1a2b',
    amber:  '#e0a458',
    text:   '#e8e6e1',
    dim:    '#4a6080',
    panel:  'rgba(14,26,43,0.97)',
    accent: '#e0a458'
  };

  // Colores por nivel (4 → 1): del mas grande al mas pequeño
  var LEVEL_COLORS = [
    null,               // índice 0 sin uso
    'rgba(224,164,88,0.55)',  // nivel 1 — los 18 pequeños
    'rgba(224,164,88,0.70)',  // nivel 2 — los 6 medios
    'rgba(224,164,88,0.82)',  // nivel 3 — los 2 grandes
    'rgba(224,164,88,0.95)'   // nivel 4 — el hexagono mayor
  ];
  var LEVEL_STROKE = [
    null,
    'rgba(224,164,88,0.35)',
    'rgba(224,164,88,0.50)',
    'rgba(224,164,88,0.65)',
    'rgba(224,164,88,0.90)'
  ];
  var DOT_RADIUS   = [null, 2.5, 4.5, 7, 11]; // radio del punto central por nivel

  // ─── Utilidades ──────────────────────────────────────────────────────────

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function easeOutQuad(t) {
    return 1 - (1 - t) * (1 - t);
  }

  /** Dibuja un hexagono regular centrado en (cx,cy) con radio r (punta-a-lado). */
  function hexPath(ctx, cx, cy, r) {
    ctx.beginPath();
    for (var i = 0; i < 6; i++) {
      var angle = Math.PI / 6 + (Math.PI / 3) * i; // flat-top
      var x = cx + r * Math.cos(angle);
      var y = cy + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
  }

  /** Inyecta los estilos del panel overlay una sola vez en el documento. */
  var _stylesInjected = false;
  function injectPanelStyles() {
    if (_stylesInjected) return;
    _stylesInjected = true;
    var style = document.createElement('style');
    style.textContent = [
      '.chr-overlay{position:fixed;top:0;left:0;width:100%;height:100%;',
      'background:rgba(14,26,43,0.88);z-index:9000;display:flex;',
      'align-items:center;justify-content:center;',
      'animation:chr-fadein 0.25s ease}',
      '@keyframes chr-fadein{from{opacity:0}to{opacity:1}}',
      '.chr-panel{background:#0e1a2b;border:1px solid rgba(224,164,88,0.4);',
      'border-radius:8px;padding:32px 36px;max-width:640px;width:90%;',
      'color:#e8e6e1;font-family:system-ui,sans-serif;font-size:14px;line-height:1.6;',
      'position:relative;max-height:90vh;overflow-y:auto}',
      '.chr-panel h2{margin:0 0 12px;color:#e0a458;font-size:1.15em;font-weight:600}',
      '.chr-panel h3{margin:16px 0 6px;color:#e0a458;font-size:0.95em;font-weight:600;',
      'text-transform:uppercase;letter-spacing:0.08em}',
      '.chr-panel p{margin:4px 0}',
      '.chr-panel .chr-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px;',
      'margin:6px 0}',
      '.chr-panel .chr-row{display:flex;justify-content:space-between;',
      'border-bottom:1px solid rgba(224,164,88,0.1);padding:3px 0}',
      '.chr-panel .chr-val{color:#e0a458;font-variant-numeric:tabular-nums}',
      '.chr-panel .chr-nota{font-size:0.82em;color:#8fa8c0;margin-top:10px;',
      'border-left:2px solid rgba(224,164,88,0.3);padding-left:10px}',
      '.chr-close{position:absolute;top:12px;right:16px;background:none;',
      'border:none;color:#8fa8c0;font-size:22px;cursor:pointer;line-height:1}',
      '.chr-close:hover{color:#e0a458}',
      '.chr-table{width:100%;border-collapse:collapse;font-size:0.88em;margin-top:6px}',
      '.chr-table th{color:#8fa8c0;font-weight:400;text-align:left;',
      'padding:3px 8px 3px 0;border-bottom:1px solid rgba(224,164,88,0.2)}',
      '.chr-table td{padding:3px 8px 3px 0;border-bottom:1px solid rgba(224,164,88,0.08)}',
      '.chr-table .ok{color:#6ec06e}.chr-table .fail{color:#e06060}'
    ].join('');
    document.head.appendChild(style);
  }

  // ─── Renderizado del panel de datos ──────────────────────────────────────

  function buildPanelHTML(data) {
    var m   = data.meta;
    var par = data.parametros;
    var cr  = data.criterio_validacion;
    var s   = data.series;
    var ia  = data.experimento_ia;

    // Tabla de rendimiento IA
    var sujetos = Object.keys(ia.rendimiento_por_sujeto);
    var tablaRows = sujetos.map(function (suj) {
      var r = ia.rendimiento_por_sujeto[suj];
      var pct = (r.exactitud * 100).toFixed(0) + '%';
      var cls = r.aciertos === r.total ? 'ok' : (r.aciertos > 0 ? '' : 'fail');
      return '<tr><td>' + suj + '</td><td class="' + cls + '">' +
        r.aciertos + '/' + r.total + '</td><td class="' + cls + '">' + pct + '</td></tr>';
    }).join('');

    // Tabla de niveles
    var nivelRows = s.niveles.map(function (n, i) {
      return '<tr><td>Nivel ' + n + '</td><td class="chr-val">' +
        s.num_lugares_por_nivel[i] + '</td><td class="chr-val">' +
        s.areas_km2_por_nivel[i].toFixed(2) + '</td><td class="chr-val">' +
        s.radios_km_por_nivel[i].toFixed(2) + '</td></tr>';
    }).join('');

    // Costos: solo vias relevantes (no el desglose largo de python_local)
    var costosHTML = '';
    if (data.costos) {
      var viaKeys = Object.keys(data.costos).filter(function (k) {
        return k !== 'python_local' || true; // incluir todas
      });
      var costRows = viaKeys.map(function (via) {
        var v = data.costos[via];
        var costoStr = '—';
        if (v.costo_usd) {
          var c = v.costo_usd;
          if (typeof c === 'object') {
            if (c.valor !== undefined) costoStr = '$' + (typeof c.valor === 'number' ? c.valor.toFixed(4) : c.valor);
            else if (c.rango_min !== undefined) costoStr = '$' + c.rango_min.toFixed(4) + '–$' + c.rango_max.toFixed(4);
          } else {
            costoStr = '$' + Number(c).toFixed(4);
          }
        }
        var aciertos = (v.aciertos && v.aciertos.valor !== undefined)
          ? v.aciertos.valor + '/' + (v.aciertos.total || '?')
          : '—';
        return '<tr><td>' + via + '</td><td class="chr-val">' + costoStr +
          '</td><td>' + aciertos + '</td></tr>';
      }).join('');
      costosHTML = '<h3>Costo por via (experimento completo)</h3>' +
        '<table class="chr-table"><thead><tr><th>Via</th><th>Costo USD</th><th>Aciertos</th></tr></thead>' +
        '<tbody>' + costRows + '</tbody></table>';
    }

    return '<button class="chr-close" aria-label="Cerrar">&#x2715;</button>' +
      '<h2>' + m.titulo + '</h2>' +
      '<p style="color:#8fa8c0;font-size:0.88em">' + m.autor + ' &middot; ' + m.anio + ' &middot; ' + m.campo + '</p>' +

      '<h3>Principio de mercado k=3</h3>' +
      '<p>Cada lugar central de orden <em>n+1</em> sirve</p>' +
      '<p style="text-align:center;color:#e0a458;font-size:1.1em">1 + 6&times;(1/3) = <strong>3</strong> areas de orden <em>n</em></p>' +
      '<p>Area hexagonal: <span style="color:#e0a458">A = (3&radic;3/2)&middot;r&sup2;</span></p>' +

      '<h3>Jerarquia de 4 niveles</h3>' +
      '<table class="chr-table"><thead><tr><th>Nivel</th><th>N.&ordm; lugares</th><th>Area (km&sup2;)</th><th>Radio (km)</th></tr></thead>' +
      '<tbody>' + nivelRows + '</tbody></table>' +

      '<h3>Validacion</h3>' +
      '<div class="chr-grid">' +
      '<div class="chr-row"><span>Razones de area</span><span class="chr-val">[' + cr.razones_areas.join(', ') + ']</span></div>' +
      '<div class="chr-row"><span>Error area base</span><span class="chr-val">' + cr.area_base_error_km2.toFixed(2) + ' km&sup2;</span></div>' +
      '<div class="chr-row"><span>Area base</span><span class="chr-val">' + cr.area_base_km2.toFixed(2) + ' km&sup2;</span></div>' +
      '<div class="chr-row"><span>Area nivel 4</span><span class="chr-val">' + cr.area_nivel4_km2.toFixed(2) + ' km&sup2;</span></div>' +
      '</div>' +

      '<h3>Rendimiento IA (preguntas n13–n15)</h3>' +
      '<table class="chr-table"><thead><tr><th>Sujeto</th><th>Aciertos</th><th>%</th></tr></thead>' +
      '<tbody>' + tablaRows + '</tbody></table>' +

      costosHTML +

      '<p class="chr-nota">' + m.nota_historica + '</p>';
  }

  // ─── Motor de animacion ───────────────────────────────────────────────────

  /**
   * AnimState gestiona el estado continuo del loop de animacion.
   *
   * Fases del loop:
   *   0  BUILD  — aparecen los hexagonos de nivel 4 → 1 en cascada
   *   1  HOLD   — malla completa visible ~1.5 s
   *   2  FADE   — desvanece de nivel 1 → 4 (inverso al build)
   *   3  GAP    — breve pausa oscura antes de reiniciar
   */
  function AnimState(data, W, H, compact) {
    this.data    = data;
    this.W       = W;
    this.H       = H;
    this.compact = compact;

    // Escala: los centros estan en km; el hexagono nivel-4 tiene radio ~51.96 km
    // Queremos que quepa con margen en el canvas
    var marginFactor = compact ? 0.38 : 0.43;
    var maxR_km = data.series.radios_km_por_nivel[3]; // nivel 4 = indice 3
    this.scale = (Math.min(W, H) * marginFactor) / maxR_km;

    // Origen en el centro del canvas
    this.ox = W / 2;
    this.oy = H / 2;

    this.reset();
  }

  AnimState.prototype.reset = function () {
    this.phase     = 0;    // 0=BUILD 1=HOLD 2=FADE 3=GAP
    this.phaseT    = 0;    // tiempo normalizado [0,1] dentro de la fase actual
    this.lastTime  = null;

    // Duracion de cada fase en ms
    // BUILD: tiempo total para los 4 niveles (con stagger entre niveles)
    this.BUILD_TOTAL = 3200;
    this.HOLD_MS     = 1600;  // pausa con malla completa
    this.FADE_TOTAL  = 2200;
    this.GAP_MS      = 380;

    // Para cada nivel, fraccion del BUILD_TOTAL en que comienza a aparecer
    //   nivel 4: 0.00, nivel 3: 0.22, nivel 2: 0.44, nivel 1: 0.64
    this.levelStart  = [null, 0.64, 0.44, 0.22, 0.00];  // indice 1..4
    this.levelEnd    = [null, 1.00, 0.72, 0.52, 0.32];

    // Para el FADE inverso (nivel 1 → 4):
    this.fadeStart   = [null, 0.00, 0.28, 0.52, 0.74];
    this.fadeEnd     = [null, 0.30, 0.58, 0.82, 1.00];

    // Alpha global (para GAP → BUILD fade-in, FADE → GAP fade-out)
    this.globalAlpha = 1.0;
  };

  /**
   * Avanza el estado y dibuja un frame.
   * Devuelve true si sigue vivo.
   */
  AnimState.prototype.tick = function (ctx, ts) {
    if (this.lastTime === null) this.lastTime = ts;
    var dt = ts - this.lastTime;
    this.lastTime = ts;

    // Limitar dt para evitar saltos tras tab-switch
    if (dt > 200) dt = 200;

    switch (this.phase) {
      case 0: // BUILD
        this.phaseT += dt / this.BUILD_TOTAL;
        if (this.phaseT >= 1) {
          this.phaseT = 1;
          this.phase  = 1;
          this._holdAccum = 0;
        }
        break;
      case 1: // HOLD
        this._holdAccum = (this._holdAccum || 0) + dt;
        if (this._holdAccum >= this.HOLD_MS) {
          this.phase  = 2;
          this.phaseT = 0;
        }
        break;
      case 2: // FADE
        this.phaseT += dt / this.FADE_TOTAL;
        if (this.phaseT >= 1) {
          this.phaseT = 1;
          this.phase  = 3;
          this._gapAccum = 0;
        }
        break;
      case 3: // GAP
        this._gapAccum = (this._gapAccum || 0) + dt;
        if (this._gapAccum >= this.GAP_MS) {
          this.reset();
        }
        break;
    }

    this._draw(ctx);
  };

  AnimState.prototype._levelAlpha = function (level) {
    var t = this.phaseT;
    if (this.phase === 0) {
      // BUILD: aparece de nivel 4 a nivel 1
      var s = this.levelStart[level];
      var e = this.levelEnd[level];
      if (t <= s) return 0;
      if (t >= e) return 1;
      return easeInOutCubic((t - s) / (e - s));
    }
    if (this.phase === 1) return 1;
    if (this.phase === 2) {
      // FADE: desaparece de nivel 1 a nivel 4
      var fs = this.fadeStart[level];
      var fe = this.fadeEnd[level];
      if (t <= fs) return 1;
      if (t >= fe) return 0;
      return 1 - easeInOutCubic((t - fs) / (fe - fs));
    }
    // GAP
    return 0;
  };

  AnimState.prototype._draw = function (ctx) {
    var W = this.W, H = this.H;
    ctx.clearRect(0, 0, W, H);

    // Fondo
    ctx.fillStyle = PALETTE.bg;
    ctx.fillRect(0, 0, W, H);

    var sc = this.scale;
    var ox = this.ox, oy = this.oy;
    var data = this.data;

    // Dibujar niveles de 4 (mayor) a 1 (menor), para que los pequenos queden encima
    for (var lv = 4; lv >= 1; lv--) {
      var alpha = this._levelAlpha(lv);
      if (alpha <= 0) continue;

      var centros = data.centros_generados['nivel_' + lv];
      var r_km    = data.series.radios_km_por_nivel[lv - 1]; // niveles 1-indexed
      var r_px    = r_km * sc;

      ctx.globalAlpha = alpha;

      // Hexagonos
      ctx.strokeStyle = LEVEL_STROKE[lv];
      ctx.fillStyle   = 'transparent';
      ctx.lineWidth   = lv === 4 ? 1.5 : (lv === 3 ? 1.2 : (lv === 2 ? 0.9 : 0.6));

      for (var i = 0; i < centros.length; i++) {
        var cx = ox + centros[i][0] * sc;
        var cy = oy - centros[i][1] * sc; // eje Y invertido en canvas
        hexPath(ctx, cx, cy, r_px);
        ctx.stroke();
      }

      // Puntos centrales (lugares centrales)
      var dotR = DOT_RADIUS[lv];
      if (this.compact) dotR *= 0.8;
      ctx.fillStyle = LEVEL_COLORS[lv];

      for (var j = 0; j < centros.length; j++) {
        var px = ox + centros[j][0] * sc;
        var py = oy - centros[j][1] * sc;
        ctx.beginPath();
        ctx.arc(px, py, dotR, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalAlpha = 1;
    }

    // Etiqueta sutil en corner
    ctx.globalAlpha = 0.32;
    ctx.fillStyle = PALETTE.text;
    ctx.font = (this.compact ? '9px' : '11px') + ' system-ui, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Christaller k=3', W - 12, H - 12);
    ctx.textAlign = 'left';
    ctx.globalAlpha = 1;
  };

  // ─── Frame estatico (prefers-reduced-motion / fallback) ──────────────────

  function drawStaticFrame(ctx, data, W, H, compact) {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = PALETTE.bg;
    ctx.fillRect(0, 0, W, H);

    var sc;
    var maxR_km = data.series.radios_km_por_nivel[3];
    var marginFactor = compact ? 0.38 : 0.43;
    sc = (Math.min(W, H) * marginFactor) / maxR_km;

    var ox = W * (compact ? 0.50 : 0.40);
    var oy = H / 2;

    for (var lv = 4; lv >= 1; lv--) {
      var centros = data.centros_generados['nivel_' + lv];
      var r_km    = data.series.radios_km_por_nivel[lv - 1];
      var r_px    = r_km * sc;

      ctx.strokeStyle = LEVEL_STROKE[lv];
      ctx.lineWidth   = lv === 4 ? 1.5 : (lv === 3 ? 1.2 : (lv === 2 ? 0.9 : 0.6));
      for (var i = 0; i < centros.length; i++) {
        hexPath(ctx, ox + centros[i][0] * sc, oy - centros[i][1] * sc, r_px);
        ctx.stroke();
      }

      var dotR = DOT_RADIUS[lv];
      if (compact) dotR *= 0.8;
      ctx.fillStyle = LEVEL_COLORS[lv];
      for (var j = 0; j < centros.length; j++) {
        ctx.beginPath();
        ctx.arc(ox + centros[j][0] * sc, oy - centros[j][1] * sc, dotR, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Barras logaritmicas (fallback)
    if (!compact) {
      var barX = W * 0.72;
      var barAreaW = W * 0.24;
      var barAreaH = H * 0.72;
      var barAreaY = H * 0.14;
      var niv = data.series.niveles;
      var nums = data.series.num_lugares_por_nivel;
      var maxLog = Math.log10(nums[0] + 1);
      var barW = (barAreaW / niv.length) * 0.6;
      var spacing = barAreaW / niv.length;

      ctx.fillStyle = 'rgba(224,164,88,0.18)';
      ctx.fillRect(barX - 8, barAreaY - 8, barAreaW + 16, barAreaH + 24);

      ctx.fillStyle = PALETTE.text;
      ctx.globalAlpha = 0.5;
      ctx.font = '10px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Lugares por nivel', barX + barAreaW / 2, barAreaY - 14);
      ctx.globalAlpha = 1;

      for (var k = 0; k < niv.length; k++) {
        var bh = (Math.log10(nums[k] + 1) / maxLog) * barAreaH;
        var bx = barX + k * spacing + (spacing - barW) / 2;
        var by = barAreaY + barAreaH - bh;

        var alphaBar = 0.4 + 0.6 * (k / (niv.length - 1));
        ctx.fillStyle = 'rgba(224,164,88,' + alphaBar + ')';
        ctx.fillRect(bx, by, barW, bh);

        ctx.fillStyle = PALETTE.amber;
        ctx.globalAlpha = 0.8;
        ctx.font = '11px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(nums[k], bx + barW / 2, by - 4);

        ctx.fillStyle = PALETTE.dim;
        ctx.globalAlpha = 0.6;
        ctx.font = '9px system-ui';
        ctx.fillText('N' + niv[k], bx + barW / 2, barAreaY + barAreaH + 14);
        ctx.globalAlpha = 1;
      }
    }

    ctx.fillStyle = PALETTE.text;
    ctx.globalAlpha = 0.32;
    ctx.font = '11px system-ui, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Christaller k=3', W - 12, H - 12);
    ctx.globalAlpha = 1;
    ctx.textAlign = 'left';
  }

  // ─── mount ────────────────────────────────────────────────────────────────

  window.VIZ['christaller'] = {
    titulo: 'La teselacion hexagonal se autoconstruye',

    mount: function (container, opts) {
      opts = opts || {};
      var compact = !!opts.compact;
      var prefersReduced = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      injectPanelStyles();

      // Canvas
      var canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:pointer';
      container.style.position = container.style.position || 'relative';
      container.appendChild(canvas);

      var dpr = window.devicePixelRatio || 1;
      var W, H;

      function resize() {
        var rect = container.getBoundingClientRect();
        W = rect.width  || container.offsetWidth  || 1200;
        H = rect.height || container.offsetHeight || 800;
        canvas.width  = W * dpr;
        canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        if (anim) { anim.W = W; anim.H = H; anim.scale = computeScale(); anim.ox = W/2; anim.oy = H/2; }
      }

      var ctx = canvas.getContext('2d');

      function computeScale() {
        if (!_data) return 1;
        var maxR_km = _data.series.radios_km_por_nivel[3];
        var mf = compact ? 0.38 : 0.43;
        return (Math.min(W, H) * mf) / maxR_km;
      }

      var _data  = null;
      var anim   = null;
      var rafId  = null;
      var paused = false;

      // ── Auto-pausa ────────────────────────────────────────────────────────
      var observer = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          if (!paused) _startRAF();
        } else {
          _stopRAF();
        }
      }, { threshold: 0.1 });
      observer.observe(canvas);

      function _onVisChange() {
        if (document.hidden) _stopRAF(); else { if (!paused) _startRAF(); }
      }
      document.addEventListener('visibilitychange', _onVisChange);

      function _startRAF() {
        if (rafId !== null) return;
        if (!_data) return;
        if (prefersReduced) return; // nunca anima en reduced-motion
        rafId = requestAnimationFrame(_loop);
      }

      function _stopRAF() {
        if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
      }

      function _loop(ts) {
        if (paused || !_data) { rafId = null; return; }
        if (anim) anim.tick(ctx, ts);
        rafId = requestAnimationFrame(_loop);
      }

      // ── Panel overlay ─────────────────────────────────────────────────────
      var _panel = null;

      function openPanel() {
        if (_panel || !_data) return;
        _panel = document.createElement('div');
        _panel.className = 'chr-overlay';
        _panel.setAttribute('role', 'dialog');
        _panel.setAttribute('aria-modal', 'true');

        var inner = document.createElement('div');
        inner.className = 'chr-panel';
        inner.innerHTML = buildPanelHTML(_data);
        _panel.appendChild(inner);
        document.body.appendChild(_panel);

        // Cerrar con botón X
        inner.querySelector('.chr-close').addEventListener('click', closePanel);
        // Cerrar con click en overlay (fuera del panel)
        _panel.addEventListener('click', function (e) {
          if (e.target === _panel) closePanel();
        });
        // Cerrar con Escape
        document.addEventListener('keydown', _escClose);

        // Foco al panel para accesibilidad
        inner.setAttribute('tabindex', '-1');
        inner.focus();
      }

      function closePanel() {
        if (!_panel) return;
        document.removeEventListener('keydown', _escClose);
        document.body.removeChild(_panel);
        _panel = null;
      }

      function _escClose(e) {
        if (e.key === 'Escape') closePanel();
      }

      canvas.addEventListener('click', openPanel);

      // ── Carga de datos via fetch relativo ────────────────────────────────
      // Resuelve la URL relativa a la ubicacion de este script
      function resolveDataURL() {
        var scripts = document.querySelectorAll('script[src]');
        var base = '';
        for (var i = 0; i < scripts.length; i++) {
          if (scripts[i].src.indexOf('christaller.js') !== -1) {
            base = scripts[i].src.replace('christaller.js', '');
            break;
          }
        }
        // Fallback: subir un nivel desde viz/ hacia datos/
        if (!base) base = './viz/';
        return base.replace(/viz\/$/, '') + 'datos/christaller.json';
      }

      resize();

      // Dibujar fondo inmediatamente mientras carga
      ctx.fillStyle = PALETTE.bg;
      ctx.fillRect(0, 0, W, H);

      fetch(resolveDataURL())
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(function (data) {
          _data = data;
          resize(); // recalcular con datos

          if (prefersReduced) {
            // Frame estatico sin animacion
            drawStaticFrame(ctx, _data, W, H, compact);
          } else {
            anim = new AnimState(_data, W, H, compact);
            _startRAF();
          }
        })
        .catch(function (err) {
          // Fallback: texto de error en canvas
          ctx.fillStyle = PALETTE.bg;
          ctx.fillRect(0, 0, W, H);
          ctx.fillStyle = PALETTE.amber;
          ctx.font = '14px system-ui';
          ctx.textAlign = 'center';
          ctx.fillText('christaller.json no encontrado: ' + err.message, W / 2, H / 2);
          console.warn('[VIZ/christaller] fetch error:', err);
        });

      // ── Resize observer (si disponible) ──────────────────────────────────
      var _ro = null;
      if (typeof ResizeObserver !== 'undefined') {
        _ro = new ResizeObserver(function () {
          resize();
          if (prefersReduced && _data) drawStaticFrame(ctx, _data, W, H, compact);
        });
        _ro.observe(container);
      }

      // ── API publica ───────────────────────────────────────────────────────
      return {
        pause: function () {
          paused = true;
          _stopRAF();
        },
        resume: function () {
          paused = false;
          if (_data && !prefersReduced) _startRAF();
        },
        destroy: function () {
          _stopRAF();
          document.removeEventListener('visibilitychange', _onVisChange);
          document.removeEventListener('keydown', _escClose);
          observer.disconnect();
          if (_ro) _ro.disconnect();
          if (_panel) { document.body.removeChild(_panel); _panel = null; }
          if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
          _data = null;
          anim  = null;
        }
      };
    }
  };

})();
