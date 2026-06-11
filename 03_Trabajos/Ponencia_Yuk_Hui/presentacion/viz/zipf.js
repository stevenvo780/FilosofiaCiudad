/* ============================================================
 * viz/zipf.js  —  Ley de Zipf: 100 ciudades cayendo a la recta
 * Registro global: window.VIZ['zipf']
 * Sin dependencias externas. ES5-compatible con alguna ES6 puntual.
 * ============================================================ */

window.VIZ = window.VIZ || {};

(function () {

  /* ---- paleta ------------------------------------------- */
  var C = {
    bg:        '#0e1a2b',
    grid:      'rgba(255,255,255,0.06)',
    axis:      'rgba(255,255,255,0.25)',
    label:     '#8eacc8',
    text:      '#e8e6e1',
    amber:     '#e0a458',    // recta ideal
    amberDim:  'rgba(224,164,88,0.18)',
    blue:      '#5ba4d4',    // recta empírica
    blueDim:   'rgba(91,164,212,0.15)',
    dotIdeal:  '#e0a458',
    dotEmp:    '#5ba4d4',
    overlay:   'rgba(14,26,43,0.96)'
  };

  /* ---- easing ------------------------------------------- */
  function easeInOutCubic(t) {
    return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2,3)/2;
  }
  function easeOutQuart(t) {
    return 1 - Math.pow(1-t, 4);
  }

  /* ---- utilidades log-log ------------------------------- */
  // Convierte (rango, poblacion) → coordenadas canvas
  // margen en px aplicado afuera
  function logX(r, xMin, xMax, w) {
    return (Math.log10(r) - xMin) / (xMax - xMin) * w;
  }
  function logY(p, yMin, yMax, h) {
    return h - (Math.log10(p) - yMin) / (yMax - yMin) * h;
  }

  /* ============================================================
   * FUNCIÓN PRINCIPAL: mount
   * ============================================================ */
  function mount(container, opts) {
    opts = opts || {};
    var compact = !!opts.compact;

    /* --- canvas ------------------------------------------- */
    var dpr = window.devicePixelRatio || 1;
    var canvas = document.createElement('canvas');
    canvas.style.display = 'block';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    container.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var W = 0, H = 0; // lógico (css px)

    function resize() {
      W = container.clientWidth  || 1200;
      H = container.clientHeight || 800;
      canvas.width  = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    resize();
    var resizeObs = new ResizeObserver(resize);
    resizeObs.observe(container);

    /* --- márgenes dinámicos ------------------------------- */
    function margins() {
      var f = compact ? 0.75 : 1;
      return {
        l: Math.round(64*f), r: Math.round(32*f),
        t: Math.round(40*f), b: Math.round(56*f)
      };
    }

    /* --- estado de la animación -------------------------- */
    var DATA = null;       // se llena tras fetch
    var rafId = null;
    var paused = false;
    var hidden = false;

    // Fases: 'scatter'→'settle'→'pause'→'fade'→'scatter'...
    var PHASE_DUR = {
      scatter: 400,   // ms que los puntos están dispersos
      settle:  2200,  // ms del deslizamiento (easing)
      pause:   1500,  // ms con ambas rectas visibles
      fade:    700    // ms de fade-out antes de volver a scatter
    };
    var phase = 'scatter';
    var phaseStart = null;
    var globalAlpha = 1;   // para fade

    // prefiere-reduced-motion: sólo fallback estático
    var prefersReduced = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* --- partículas --------------------------------------- */
    // Cada partícula tiene posición scattered y posición target (Zipf ideal o empírico)
    // group: 0 = ideal, 1 = empírico
    var N = 100;
    var particles = [];

    // Semilla determinista para reproducibilidad visual
    function seededRand(seed) {
      var s = seed;
      return function() {
        s = (s * 1664525 + 1013904223) & 0xffffffff;
        return (s >>> 0) / 4294967296;
      };
    }

    function initParticles() {
      particles = [];
      var rng = seededRand(42);
      for (var i = 0; i < N; i++) {
        particles.push({
          idx: i,          // índice 0-99
          group: i < 50 ? 0 : 1,  // 0=ideal, 1=empírico
          // posición scattered (normalizada 0-1 en espacio log)
          sx: rng(),
          sy: rng(),
          // phase offset para que no lleguen todos a la vez
          delay: rng() * 0.45,
          // tamaño del punto
          r: compact ? 2.5 : 3.5
        });
      }
    }

    /* ---- rango log-log ----------------------------------- */
    var LOG_X_MIN = 0;        // log10(1)
    var LOG_X_MAX = 2;        // log10(100)
    var LOG_Y_MIN = 3.8;      // log10(~6300)
    var LOG_Y_MAX = 6.2;      // log10(~1.6M)

    /* ---- proyectar un punto al canvas ------------------- */
    function project(logR, logP, mg) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;
      return {
        x: mg.l + (logR - LOG_X_MIN) / (LOG_X_MAX - LOG_X_MIN) * pw,
        y: mg.t + (1 - (logP - LOG_Y_MIN) / (LOG_Y_MAX - LOG_Y_MIN)) * ph
      };
    }

    /* ---- target de cada partícula ----------------------- */
    function targetPos(p, mg) {
      if (!DATA) return { x: W/2, y: H/2 };
      var city = p.group === 0
        ? DATA.ciudades[p.idx]
        : DATA.ciudades_empiricas[p.idx];
      return project(Math.log10(city.r), Math.log10(city.p), mg);
    }

    /* ---- posición scattered de cada partícula ----------- */
    function scatterPos(p, mg) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;
      // Extender la zona de dispersión más allá del área del plot
      return {
        x: mg.l + (p.sx * pw * 1.2) - pw * 0.1,
        y: mg.t + (p.sy * ph * 1.2) - ph * 0.1
      };
    }

    /* ============================================================
     * DIBUJADO
     * ============================================================ */

    function drawBackground() {
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, W, H);
    }

    function drawGrid(mg) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;
      ctx.strokeStyle = C.grid;
      ctx.lineWidth = 0.5;

      // Líneas verticales: log10(r) = 0,1,2 y subdivisiones
      var xTicks = [1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100];
      xTicks.forEach(function(r) {
        var lx = Math.log10(r);
        if (lx < LOG_X_MIN || lx > LOG_X_MAX) return;
        var x = mg.l + (lx - LOG_X_MIN)/(LOG_X_MAX - LOG_X_MIN)*pw;
        ctx.beginPath();
        ctx.moveTo(x, mg.t);
        ctx.lineTo(x, mg.t + ph);
        ctx.stroke();
      });

      // Líneas horizontales
      var yTicks = [10000,20000,50000,100000,200000,500000,1000000];
      yTicks.forEach(function(p) {
        var lp = Math.log10(p);
        if (lp < LOG_Y_MIN || lp > LOG_Y_MAX) return;
        var y = mg.t + (1-(lp-LOG_Y_MIN)/(LOG_Y_MAX-LOG_Y_MIN))*ph;
        ctx.beginPath();
        ctx.moveTo(mg.l, y);
        ctx.lineTo(mg.l + pw, y);
        ctx.stroke();
      });
    }

    function drawAxes(mg) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;
      ctx.strokeStyle = C.axis;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(mg.l, mg.t);
      ctx.lineTo(mg.l, mg.t + ph);
      ctx.lineTo(mg.l + pw, mg.t + ph);
      ctx.stroke();
    }

    function drawAxisLabels(mg) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;
      var fs = compact ? 10 : 12;
      ctx.fillStyle = C.label;
      ctx.font = fs + 'px "Courier New", monospace';
      ctx.textAlign = 'center';

      // X ticks
      [1,2,5,10,20,50,100].forEach(function(r) {
        var lx = Math.log10(r);
        if (lx < LOG_X_MIN || lx > LOG_X_MAX) return;
        var x = mg.l + (lx-LOG_X_MIN)/(LOG_X_MAX-LOG_X_MIN)*pw;
        ctx.fillText(r, x, mg.t + ph + 18);
      });

      // Y ticks
      ctx.textAlign = 'right';
      [10000,50000,100000,500000,1000000].forEach(function(p) {
        var lp = Math.log10(p);
        if (lp < LOG_Y_MIN || lp > LOG_Y_MAX) return;
        var y = mg.t + (1-(lp-LOG_Y_MIN)/(LOG_Y_MAX-LOG_Y_MIN))*ph;
        var label = p >= 1000000 ? '1M' :
                    p >= 100000 ? (p/1000|0)+'k' :
                    (p/1000|0)+'k';
        ctx.fillText(label, mg.l - 8, y + 4);
      });

      // Títulos de ejes
      var fsTitle = compact ? 11 : 13;
      ctx.font = fsTitle + 'px sans-serif';
      ctx.fillStyle = C.text;
      ctx.textAlign = 'center';
      ctx.fillText('Rango (log)', mg.l + pw/2, mg.t + ph + (compact ? 38 : 44));

      ctx.save();
      ctx.translate(compact ? 14 : 18, mg.t + ph/2);
      ctx.rotate(-Math.PI/2);
      ctx.fillText('Población (log)', 0, 0);
      ctx.restore();
    }

    /* Dibuja la recta de referencia en el espacio log-log */
    function drawLine(slope, intercept, color, alpha, mg, label, dashed) {
      var pw = W - mg.l - mg.r;
      var ph = H - mg.t - mg.b;

      // Calcular dos puntos en los extremos del eje X
      var x0log = LOG_X_MIN, x1log = LOG_X_MAX;
      var y0log = intercept + slope * x0log;
      var y1log = intercept + slope * x1log;

      // Clamp al rango Y visible
      var clampPt = function(lx, ly) {
        return {
          x: mg.l + (lx-LOG_X_MIN)/(LOG_X_MAX-LOG_X_MIN)*pw,
          y: mg.t + (1-(ly-LOG_Y_MIN)/(LOG_Y_MAX-LOG_Y_MIN))*ph
        };
      };

      var p0 = clampPt(x0log, y0log);
      var p1 = clampPt(x1log, y1log);

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = color;
      ctx.lineWidth = compact ? 1.5 : 2;
      if (dashed) ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // Etiqueta junto a la recta (extremo derecho)
      if (label && alpha > 0.3) {
        var lx = Math.log10(80);
        var ly = intercept + slope * lx;
        var lpt = clampPt(lx, ly);
        ctx.fillStyle = color;
        ctx.font = (compact ? 10 : 12) + 'px "Courier New", monospace';
        ctx.textAlign = 'left';
        ctx.fillText(label, lpt.x + 6, lpt.y - 4);
      }
      ctx.restore();
    }

    /* Dibuja la etiqueta de métricas (pendiente, R²) que cuenta */
    function drawMetrics(t_settle, alpha_lines, mg) {
      // t_settle: 0→1, progreso del asentamiento
      var slope_ideal   = DATA.ajuste_log_log.pendiente;
      var r2_ideal      = DATA.ajuste_log_log.r_cuadrado;
      var slope_emp     = DATA.ajuste_log_log_empirico.pendiente;
      var r2_emp        = DATA.ajuste_log_log_empirico.r_cuadrado;

      // Los valores "cuentan" desde 0 a su valor final conforme t_settle avanza
      var s_i  = slope_ideal  * easeOutQuart(t_settle);
      var r2_i = r2_ideal     * easeOutQuart(t_settle);
      var s_e  = slope_emp    * easeOutQuart(t_settle);
      var r2_e = r2_emp       * easeOutQuart(t_settle);

      var fs = compact ? 11 : 13;
      var x = W - (compact ? 140 : 180);
      var y = mg.t + (compact ? 18 : 24);
      var lh = fs + 6;

      ctx.save();
      ctx.globalAlpha = alpha_lines;
      ctx.font = 'bold ' + fs + 'px "Courier New", monospace';

      // Ideal
      ctx.fillStyle = C.amber;
      ctx.textAlign = 'left';
      ctx.fillText('Ideal  q=1.000', x, y);
      ctx.font = fs + 'px "Courier New", monospace';
      ctx.fillText('  β = ' + s_i.toFixed(4), x, y + lh);
      ctx.fillText('  R² = ' + r2_i.toFixed(4), x, y + lh*2);

      // Empírico
      ctx.font = 'bold ' + fs + 'px "Courier New", monospace';
      ctx.fillStyle = C.blue;
      ctx.fillText('Empírico q=0.85', x, y + lh*3.5);
      ctx.font = fs + 'px "Courier New", monospace';
      ctx.fillText('  β = ' + s_e.toFixed(4), x, y + lh*4.5);
      ctx.fillText('  R² = ' + r2_e.toFixed(4), x, y + lh*5.5);

      ctx.restore();
    }

    /* Dibuja los 100 puntos con su posición interpolada */
    function drawParticles(mg, progress, phase_name, fade_alpha) {
      if (!DATA) return;

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var spos = scatterPos(p, mg);
        var tpos = targetPos(p, mg);

        var px, py, alpha;

        if (phase_name === 'scatter') {
          px = spos.x; py = spos.y;
          alpha = 0.65 + p.idx % 5 * 0.05;
        } else if (phase_name === 'settle') {
          // Cada punto tiene su propio delay
          var localT = Math.max(0, Math.min(1,
            (progress - p.delay) / (1 - p.delay)));
          var ease = easeInOutCubic(localT);
          px = spos.x + (tpos.x - spos.x) * ease;
          py = spos.y + (tpos.y - spos.y) * ease;
          alpha = 0.4 + ease * 0.55;
        } else if (phase_name === 'pause') {
          px = tpos.x; py = tpos.y;
          alpha = 0.95;
        } else { // fade
          px = tpos.x; py = tpos.y;
          alpha = 0.95 * (1 - progress);
        }

        alpha *= fade_alpha;

        var color = p.group === 0 ? C.dotIdeal : C.dotEmp;
        var r = p.r;

        // Halo suave
        var grad = ctx.createRadialGradient(px, py, 0, px, py, r * 2.5);
        grad.addColorStop(0, color.replace(')', ',0.35)').replace('rgb', 'rgba'));
        grad.addColorStop(1, 'transparent');
        // Fallback simple para colores hex
        ctx.save();
        ctx.globalAlpha = alpha * 0.3;
        ctx.fillStyle = p.group === 0 ? C.amberDim : C.blueDim;
        ctx.beginPath();
        ctx.arc(px, py, r * 3, 0, Math.PI*2);
        ctx.fill();

        // Punto principal
        ctx.globalAlpha = alpha;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI*2);
        ctx.fill();
        ctx.restore();
      }
    }

    /* ============================================================
     * FALLBACK ESTÁTICO (prefers-reduced-motion)
     * ============================================================ */
    function drawStatic() {
      if (!DATA) return;
      var mg = margins();

      drawBackground();
      drawGrid(mg);
      drawAxes(mg);
      drawAxisLabels(mg);

      // Dibujar todos los puntos en su posición final
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var tpos = targetPos(p, mg);
        ctx.fillStyle = p.group === 0 ? C.dotIdeal : C.dotEmp;
        ctx.globalAlpha = 0.85;
        ctx.beginPath();
        ctx.arc(tpos.x, tpos.y, p.r, 0, Math.PI*2);
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLine(DATA.ajuste_log_log.pendiente,
               DATA.ajuste_log_log.intercepto,
               C.amber, 1, mg, 'β=−1.000  R²=1.000', false);
      drawLine(DATA.ajuste_log_log_empirico.pendiente,
               DATA.ajuste_log_log_empirico.intercepto,
               C.blue, 1, mg, 'β=−0.857  R²=0.987', true);

      drawAxisLabels(mg);
      drawMetrics(1, 1, mg);
      drawTitle(mg);
    }

    function drawTitle(mg) {
      if (!DATA) return;
      var fs = compact ? 13 : 16;
      ctx.save();
      ctx.fillStyle = C.text;
      ctx.font = 'bold ' + fs + 'px sans-serif';
      ctx.textAlign = 'center';
      ctx.globalAlpha = 0.9;
      ctx.fillText(DATA.titulo || 'Ley de Zipf: rango–tamaño',
        mg.l + (W - mg.l - mg.r)/2, mg.t - (compact ? 10 : 14));
      ctx.restore();
    }

    /* ============================================================
     * LOOP DE ANIMACIÓN
     * ============================================================ */
    function tick(ts) {
      if (paused || hidden || !DATA) {
        rafId = requestAnimationFrame(tick);
        return;
      }

      if (phaseStart === null) phaseStart = ts;
      var elapsed = ts - phaseStart;

      var mg = margins();

      drawBackground();
      drawGrid(mg);
      drawAxes(mg);

      /* --- progreso de fase ------------------------------ */
      var dur = PHASE_DUR[phase];
      var t = Math.min(elapsed / dur, 1);

      /* Cuándo mostrar las rectas (sólo en settle/pause/fade) */
      var lineAlpha = 0;
      var metricT = 0;
      var fade_alpha = 1;

      if (phase === 'settle') {
        lineAlpha = easeOutQuart(t);
        metricT = easeOutQuart(t);
      } else if (phase === 'pause') {
        lineAlpha = 1;
        metricT = 1;
      } else if (phase === 'fade') {
        lineAlpha = 1 - easeInOutCubic(t);
        metricT = 1 - easeInOutCubic(t);
        fade_alpha = 1 - easeInOutCubic(t);
      }

      /* Dibujar rectas */
      drawLine(DATA.ajuste_log_log.pendiente,
               DATA.ajuste_log_log.intercepto,
               C.amber, lineAlpha, mg, null, false);
      drawLine(DATA.ajuste_log_log_empirico.pendiente,
               DATA.ajuste_log_log_empirico.intercepto,
               C.blue, lineAlpha * 0.85, mg, null, true);

      /* Dibujar partículas */
      drawParticles(mg, t, phase, fade_alpha);

      /* Etiquetas de ejes (encima de los puntos) */
      drawAxisLabels(mg);

      /* Métricas */
      if (lineAlpha > 0.01) drawMetrics(metricT, lineAlpha, mg);

      /* Leyenda de los dos grupos */
      if (lineAlpha > 0.05) drawLegend(mg, lineAlpha);

      /* Título */
      drawTitle(mg);

      /* --- transición de fase ---------------------------- */
      if (elapsed >= dur) {
        phaseStart = ts;
        if (phase === 'scatter') {
          phase = 'settle';
        } else if (phase === 'settle') {
          phase = 'pause';
        } else if (phase === 'pause') {
          phase = 'fade';
        } else { // fade
          phase = 'scatter';
          // Re-inicializar posiciones scattered con nueva semilla aleatoria
          reinitScatter();
        }
      }

      rafId = requestAnimationFrame(tick);
    }

    function drawLegend(mg, alpha) {
      var x = mg.l + 8;
      var y = mg.t + (compact ? 14 : 18);
      var fs = compact ? 10 : 12;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.font = fs + 'px "Courier New", monospace';

      ctx.fillStyle = C.amber;
      ctx.beginPath();
      ctx.arc(x, y, compact ? 4 : 5, 0, Math.PI*2);
      ctx.fill();
      ctx.fillStyle = C.text;
      ctx.textAlign = 'left';
      ctx.fillText('Sistema ideal (q=1)', x + 10, y + 4);

      var y2 = y + fs + 8;
      ctx.fillStyle = C.blue;
      ctx.beginPath();
      ctx.arc(x, y2, compact ? 4 : 5, 0, Math.PI*2);
      ctx.fill();
      ctx.fillStyle = C.text;
      ctx.fillText('Sistema empírico (q=0.85)', x + 10, y2 + 4);
      ctx.restore();
    }

    /* Regenera posiciones scattered con aleatoriedad real */
    function reinitScatter() {
      for (var i = 0; i < particles.length; i++) {
        particles[i].sx = Math.random();
        particles[i].sy = Math.random();
        // Variar delay también
        particles[i].delay = Math.random() * 0.45;
      }
    }

    /* ============================================================
     * CARGA DE DATOS y ARRANQUE
     * ============================================================ */
    var dataUrl = (opts.dataPath || '../datos/zipf.json');

    fetch(dataUrl)
      .then(function(r) { return r.json(); })
      .then(function(d) {
        DATA = d;
        initParticles();
        if (prefersReduced) {
          drawStatic();
        } else {
          rafId = requestAnimationFrame(tick);
        }
      })
      .catch(function(err) {
        console.error('[VIZ:zipf] Error cargando datos:', err);
        // Dibujar mensaje de error
        drawBackground();
        ctx.fillStyle = C.text;
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Error cargando datos: ' + err.message, W/2, H/2);
      });

    /* ============================================================
     * AUTO-PAUSA con IntersectionObserver y visibilitychange
     * ============================================================ */
    var intersecting = true;
    var observer = new IntersectionObserver(function(entries) {
      intersecting = entries[0].isIntersecting;
      hidden = !intersecting || document.hidden;
    }, { threshold: 0.1 });
    observer.observe(container);

    function onVisibility() {
      hidden = document.hidden || !intersecting;
    }
    document.addEventListener('visibilitychange', onVisibility);

    /* ============================================================
     * PANEL OVERLAY al hacer CLICK
     * ============================================================ */
    var PANEL_STYLE_ID = 'viz-zipf-panel-styles';

    function injectPanelStyles() {
      if (document.getElementById(PANEL_STYLE_ID)) return;
      var el = document.createElement('style');
      el.id = PANEL_STYLE_ID;
      el.textContent = [
        '.vz-overlay{position:fixed;inset:0;background:rgba(14,26,43,0.92);',
        'display:flex;align-items:center;justify-content:center;z-index:9999;',
        'backdrop-filter:blur(4px);}',
        '.vz-panel{background:#0e1a2b;border:1px solid rgba(224,164,88,0.35);',
        'border-radius:10px;padding:28px 32px;max-width:540px;width:90%;',
        'max-height:82vh;overflow-y:auto;color:#e8e6e1;font-family:sans-serif;',
        'position:relative;box-shadow:0 8px 40px rgba(0,0,0,0.7);}',
        '.vz-panel h2{margin:0 0 6px;font-size:1.15rem;color:#e0a458;}',
        '.vz-panel .vz-subtitle{font-size:0.8rem;color:#8eacc8;margin-bottom:18px;}',
        '.vz-panel .vz-formula{font-family:"Courier New",monospace;',
        'background:rgba(255,255,255,0.05);border-left:3px solid #e0a458;',
        'padding:8px 14px;border-radius:4px;font-size:1rem;margin-bottom:16px;}',
        '.vz-panel table{border-collapse:collapse;width:100%;font-size:0.82rem;}',
        '.vz-panel th{text-align:left;color:#8eacc8;font-weight:normal;',
        'padding:3px 8px 3px 0;border-bottom:1px solid rgba(255,255,255,0.08);}',
        '.vz-panel td{padding:4px 8px 4px 0;vertical-align:top;}',
        '.vz-panel .vz-correct{color:#56c96a;}.vz-panel .vz-wrong{color:#e05a5a;}',
        '.vz-panel .vz-badge{display:inline-block;padding:1px 6px;border-radius:3px;',
        'font-size:0.75rem;font-family:"Courier New",monospace;}',
        '.vz-panel .vz-amber{color:#e0a458;}.vz-panel .vz-blue{color:#5ba4d4;}',
        '.vz-close{position:absolute;top:12px;right:16px;background:none;',
        'border:none;color:#8eacc8;font-size:1.4rem;cursor:pointer;',
        'line-height:1;padding:0;}',
        '.vz-close:hover{color:#e8e6e1;}',
        '.vz-section{margin-top:14px;border-top:1px solid rgba(255,255,255,0.08);',
        'padding-top:12px;}',
        '.vz-section h3{margin:0 0 8px;font-size:0.88rem;color:#8eacc8;',
        'text-transform:uppercase;letter-spacing:0.08em;}',
        '.vz-row{display:flex;gap:20px;margin-bottom:8px;}',
        '.vz-stat{flex:1;}.vz-stat .vz-val{font-size:1.3rem;font-weight:bold;}',
        '.vz-stat .vz-lbl{font-size:0.73rem;color:#8eacc8;}'
      ].join('');
      document.head.appendChild(el);
    }

    function buildPanelHTML() {
      if (!DATA) return '<p>Datos no cargados.</p>';
      var p = DATA.panel;
      var sim = DATA.ajuste_log_log;
      var emp = DATA.ajuste_log_log_empirico;
      var ver = DATA.verificacion;

      // Recalcular P(4) canónico desde los parámetros (nunca hardcoded del JSON directo)
      var P1 = DATA.parametros.P1;
      var q  = DATA.parametros.q;
      var P4 = (P1 / Math.pow(4, q)).toFixed(0);

      // Filas de rendimiento
      var rows = '';
      var sujetos = Object.keys(p.rendimiento_por_sujeto || {});
      sujetos.forEach(function(s) {
        var d = p.rendimiento_por_sujeto[s];
        var aciertosLabel = d.aciertos + '/' + d.total;
        var pct = (d.exactitud * 100).toFixed(0) + '%';
        var cls = d.exactitud >= 1 ? 'vz-correct' : (d.exactitud > 0.5 ? '' : 'vz-wrong');
        var pregs = (d.por_pregunta || []).map(function(pq) {
          var v = pq.veredicto;
          var ok = v === 'CORRECTO';
          return '<span class="vz-badge ' + (ok?'vz-correct':'vz-wrong') + '">' +
            'n' + pq.n + (ok ? ' ✓' : ' ✗') + '</span>';
        }).join(' ');
        rows += '<tr>' +
          '<td style="font-family:monospace;font-size:0.8rem">' + s + '</td>' +
          '<td class="' + cls + '">' + aciertosLabel + ' (' + pct + ')</td>' +
          '<td>' + pregs + '</td>' +
          '</tr>';
      });

      // Filas de costos
      var costRows = '';
      var vias = p.costos_vias || {};
      Object.keys(vias).forEach(function(via) {
        var v = vias[via];
        var costoStr = '';
        if (v.costo_usd && typeof v.costo_usd === 'object') {
          if (v.costo_usd.rango_min !== undefined) {
            costoStr = '$' + v.costo_usd.rango_min.toFixed(3) +
              '–$' + v.costo_usd.rango_max.toFixed(3);
          } else {
            costoStr = '$' + Number(v.costo_usd.valor || 0).toExponential(2);
          }
        } else if (v.costo_usd !== undefined) {
          costoStr = '$' + Number(v.costo_usd).toFixed(4);
        }
        var acc = (v.aciertos !== undefined)
          ? v.aciertos + '/' + v.total : '—';
        costRows += '<tr>' +
          '<td style="font-family:monospace;font-size:0.77rem">' + via + '</td>' +
          '<td>' + costoStr + '</td>' +
          '<td>' + acc + '</td>' +
          '</tr>';
      });

      return [
        '<button class="vz-close" id="vz-close-btn" title="Cerrar (Esc)">&#x2715;</button>',
        '<h2>Ley de Zipf &mdash; Rango &amp; Tamaño</h2>',
        '<div class="vz-subtitle">Zipf (1949) &mdash; Gabaix (1999)</div>',
        '<div class="vz-formula">' + p.formula + ' &nbsp;&nbsp; log P = log P₁ &minus; q·log r</div>',
        '<div class="vz-row">',
          '<div class="vz-stat">',
            '<div class="vz-val vz-amber">&minus;1.0000</div>',
            '<div class="vz-lbl">pendiente ideal (q=1)</div>',
          '</div>',
          '<div class="vz-stat">',
            '<div class="vz-val vz-amber">' + sim.r_cuadrado.toFixed(4) + '</div>',
            '<div class="vz-lbl">R² sistema ideal</div>',
          '</div>',
          '<div class="vz-stat">',
            '<div class="vz-val vz-blue">' + emp.pendiente.toFixed(4) + '</div>',
            '<div class="vz-lbl">pendiente empírica (q=0.85)</div>',
          '</div>',
          '<div class="vz-stat">',
            '<div class="vz-val vz-blue">' + emp.r_cuadrado.toFixed(4) + '</div>',
            '<div class="vz-lbl">R² sistema empírico</div>',
          '</div>',
        '</div>',
        '<div class="vz-stat" style="margin-bottom:12px">',
          '<div class="vz-val" style="font-size:1.05rem">',
            'P(4) = P₁/4^q = ' + Number(P1).toLocaleString() + '/4¹ = <strong>' +
            Number(P4).toLocaleString() + '</strong>',
          '</div>',
          '<div class="vz-lbl">Verificación canónica (rango 4)</div>',
        '</div>',
        '<div class="vz-section">',
          '<h3>Rendimiento por sujeto IA (n37–39)</h3>',
          '<table><thead><tr>',
            '<th>Sujeto</th><th>Aciertos</th><th>Detalle</th>',
          '</tr></thead><tbody>' + rows + '</tbody></table>',
          '<div style="font-size:0.75rem;color:#8eacc8;margin-top:6px">',
            'n37: P(4)=250 000 &nbsp;|&nbsp; n38: q=1 &nbsp;|&nbsp; n39: pendiente emergente=−1.000',
          '</div>',
        '</div>',
        '<div class="vz-section">',
          '<h3>Costo por vía (experimento completo)</h3>',
          '<table><thead><tr>',
            '<th>Vía</th><th>Costo USD</th><th>Aciertos</th>',
          '</tr></thead><tbody>' + costRows + '</tbody></table>',
        '</div>',
        '<div class="vz-section" style="font-size:0.77rem;color:#8eacc8">',
          p.nota_canon || '',
        '</div>'
      ].join('');
    }

    var overlayEl = null;

    function openPanel() {
      if (overlayEl) return;
      injectPanelStyles();
      paused = true;

      overlayEl = document.createElement('div');
      overlayEl.className = 'vz-overlay';

      var panel = document.createElement('div');
      panel.className = 'vz-panel';
      panel.innerHTML = buildPanelHTML();
      overlayEl.appendChild(panel);
      document.body.appendChild(overlayEl);

      var closeBtn = document.getElementById('vz-close-btn');
      if (closeBtn) closeBtn.onclick = closePanel;

      overlayEl.addEventListener('click', function(e) {
        if (e.target === overlayEl) closePanel();
      });
    }

    function closePanel() {
      if (!overlayEl) return;
      document.body.removeChild(overlayEl);
      overlayEl = null;
      paused = false;
    }

    function onKey(e) {
      if (e.key === 'Escape' && overlayEl) closePanel();
    }
    document.addEventListener('keydown', onKey);

    canvas.addEventListener('click', openPanel);
    canvas.style.cursor = 'pointer';

    /* ============================================================
     * API PÚBLICA
     * ============================================================ */
    function pause()  { paused = true;  }
    function resume() {
      paused = false;
      if (!rafId) rafId = requestAnimationFrame(tick);
    }
    function destroy() {
      if (rafId) cancelAnimationFrame(rafId);
      observer.disconnect();
      resizeObs.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      document.removeEventListener('keydown', onKey);
      canvas.removeEventListener('click', openPanel);
      if (overlayEl) { document.body.removeChild(overlayEl); overlayEl = null; }
      container.removeChild(canvas);
    }

    return { pause: pause, resume: resume, destroy: destroy };
  }

  /* ============================================================
   * REGISTRO EN window.VIZ
   * ============================================================ */
  window.VIZ['zipf'] = {
    titulo: 'Cien ciudades cayendo a la ley de potencias',
    mount: mount
  };

})();
