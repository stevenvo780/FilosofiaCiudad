/* ============================================================
   von_thunen.js — Visualización animada: Anillos de von Thünen
   Contrato: window.VIZ['von_thunen'] = { titulo, mount(container, opts) }
   mount() → { pause, resume, destroy }
   Sin dependencias externas. Classic script (no ES modules).
   ============================================================ */

(function () {
  'use strict';

  window.VIZ = window.VIZ || {};

  /* ── Paleta ─────────────────────────────────────────────── */
  var PAL = {
    bg:       '#0e1a2b',
    text:     '#e8e6e1',
    amber:    '#e0a458',    // Cultivo A interior
    blue:     '#4a90d9',    // Cultivo B exterior
    void:     '#1a2840',    // Zona sin renta
    gridLine: 'rgba(232,230,225,0.08)',
    radarBg:  'rgba(14,26,43,0.55)',
    overlay:  'rgba(14,26,43,0.92)',
    crosshair:'rgba(224,164,88,0.85)',
    rA:       '#e0a458',
    rB:       '#4a90d9',
    envelope: '#f0e6d0',
    dstar:    '#ff6b6b'
  };

  /* ── Easing ─────────────────────────────────────────────── */
  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
  function easeOutQuad(t) { return 1 - (1 - t) * (1 - t); }
  function lerp(a, b, t) { return a + (b - a) * t; }

  /* ── Inyectar estilos del overlay (una sola vez) ─────────── */
  var _stylesInjected = false;
  function injectStyles() {
    if (_stylesInjected) return;
    _stylesInjected = true;
    var s = document.createElement('style');
    s.id = 'vt-overlay-styles';
    s.textContent = [
      '.vt-overlay{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;',
      'justify-content:center;background:rgba(14,26,43,0.92);',
      'font-family:"Inter","Segoe UI",system-ui,sans-serif;color:#e8e6e1;}',

      '.vt-panel{position:relative;background:#0e1a2b;border:1px solid rgba(224,164,88,0.35);',
      'border-radius:12px;padding:32px 36px 28px;max-width:680px;width:90%;',
      'box-shadow:0 24px 64px rgba(0,0,0,0.7);}',

      '.vt-close{position:absolute;top:14px;right:18px;background:none;border:none;',
      'color:#e8e6e1;font-size:22px;cursor:pointer;line-height:1;opacity:0.7;}',
      '.vt-close:hover{opacity:1;}',

      '.vt-panel h2{margin:0 0 6px;font-size:1.15rem;font-weight:700;color:#e0a458;',
      'letter-spacing:0.02em;}',

      '.vt-panel .vt-subtitle{font-size:0.8rem;opacity:0.55;margin:0 0 20px;',
      'font-style:italic;}',

      '.vt-formula{background:rgba(224,164,88,0.08);border-left:3px solid #e0a458;',
      'padding:10px 14px;border-radius:0 6px 6px 0;font-family:monospace;',
      'font-size:0.9rem;margin-bottom:18px;letter-spacing:0.01em;}',

      '.vt-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;',
      'margin-bottom:18px;font-size:0.82rem;}',

      '.vt-kv{display:flex;flex-direction:column;gap:2px;}',
      '.vt-kv .k{opacity:0.5;font-size:0.72rem;text-transform:uppercase;',
      'letter-spacing:0.06em;}',
      '.vt-kv .v{font-weight:600;color:#e0a458;}',

      '.vt-sujetos{margin-top:14px;}',
      '.vt-sujetos h3{font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;',
      'opacity:0.5;margin:0 0 8px;}',

      '.vt-sujeto-row{display:flex;align-items:center;gap:8px;',
      'margin-bottom:5px;font-size:0.82rem;}',
      '.vt-sujeto-row .sname{flex:0 0 120px;opacity:0.75;}',
      '.vt-pips{display:flex;gap:3px;}',
      '.vt-pip{width:16px;height:16px;border-radius:3px;display:flex;',
      'align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;}',
      '.vt-pip.ok{background:rgba(74,144,80,0.4);color:#7ed694;}',
      '.vt-pip.fail{background:rgba(180,60,60,0.35);color:#e07070;}',

      '.vt-costos{margin-top:16px;font-size:0.78rem;opacity:0.65;',
      'border-top:1px solid rgba(232,230,225,0.1);padding-top:12px;}',
      '.vt-costos span{color:#e0a458;font-weight:600;}'
    ].join('');
    document.head.appendChild(s);
  }

  /* ── Panel overlay con datos del JSON ───────────────────── */
  function buildOverlay(data, onClose) {
    injectStyles();
    var overlay = document.createElement('div');
    overlay.className = 'vt-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');

    var panel = document.createElement('div');
    panel.className = 'vt-panel';

    /* Cerrar con Escape */
    function escHandler(e) {
      if (e.key === 'Escape') close();
    }
    document.addEventListener('keydown', escHandler);

    function close() {
      document.removeEventListener('keydown', escHandler);
      overlay.remove();
      if (onClose) onClose();
    }

    /* Botón X */
    var btn = document.createElement('button');
    btn.className = 'vt-close';
    btn.innerHTML = '&times;';
    btn.setAttribute('aria-label', 'Cerrar');
    btn.onclick = close;
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) close();
    });

    /* ── Contenido ── */
    var p = data.panel || {};
    var ver = data.verificaciones || {};
    var rendIA = data.rendimiento_ia || {};
    var costos = data.costos_vias || {};

    /* Recalcular d* desde datos canónicos (nunca hard-code en JS) */
    var dStar = data.frontera_anillo_d_star_km;
    var rentaDstar = data.renta_en_d_star;
    var d0A = data.radios_cero ? data.radios_cero.A : ver.d0_A;
    var d0B = data.radios_cero ? data.radios_cero.B : ver.d0_B;
    var slopeA = data.pendientes ? data.pendientes.A : ver.pendiente_A;
    var slopeB = data.pendientes ? data.pendientes.B : ver.pendiente_B;

    var costoSonnet = costos['claude-sonnet']
      ? (costos['claude-sonnet'].costo_usd_rango
          ? '$' + costos['claude-sonnet'].costo_usd_rango[0].toFixed(2)
            + '–$' + costos['claude-sonnet'].costo_usd_rango[1].toFixed(2)
          : 'n/d')
      : 'n/d';
    var costoOpus = costos['claude-opus']
      ? (costos['claude-opus'].costo_usd_rango
          ? '$' + costos['claude-opus'].costo_usd_rango[0].toFixed(2)
            + '–$' + costos['claude-opus'].costo_usd_rango[1].toFixed(2)
          : 'n/d')
      : 'n/d';

    panel.innerHTML = [
      '<h2>Anillos de von Thünen — Panel de datos</h2>',
      '<p class="vt-subtitle">' + (p.autor || '') + ' (' + (p.anio || '') + ')</p>',

      '<div class="vt-formula">' +
        'R(d) = y·(p−c) − y·f·d &nbsp;|&nbsp; envolvente: max(R<sub>A</sub>, R<sub>B</sub>, 0)' +
      '</div>',

      '<div class="vt-grid">',
        '<div class="vt-kv"><span class="k">Pendiente A</span>',
          '<span class="v">' + slopeA.toFixed(1) + ' $/km</span></div>',
        '<div class="vt-kv"><span class="k">Pendiente B</span>',
          '<span class="v">' + slopeB.toFixed(1) + ' $/km</span></div>',
        '<div class="vt-kv"><span class="k">Radio cero d₀_A</span>',
          '<span class="v">' + d0A.toFixed(1) + ' km</span></div>',
        '<div class="vt-kv"><span class="k">Radio cero d₀_B</span>',
          '<span class="v">' + d0B.toFixed(1) + ' km</span></div>',
        '<div class="vt-kv"><span class="k">Frontera d*</span>',
          '<span class="v" style="color:#ff6b6b">' + dStar.toFixed(1) + ' km</span></div>',
        '<div class="vt-kv"><span class="k">Renta en d*</span>',
          '<span class="v" style="color:#ff6b6b">' + rentaDstar.toFixed(0) + ' $/ha</span></div>',
        '<div class="vt-kv"><span class="k">Anillo interior</span>',
          '<span class="v" style="color:#e0a458">Cultivo A (intensivo)</span></div>',
        '<div class="vt-kv"><span class="k">Anillo exterior</span>',
          '<span class="v" style="color:#4a90d9">Cultivo B (extensivo)</span></div>',
      '</div>'
    ].join('');

    /* Rendimiento IA */
    var sujetoOrder = ['qwen2.5:3b','qwen3:14b','gpt-oss:20b','qwen3:32b','claude-sonnet','claude-opus'];
    var sujetoLabels = {
      'qwen2.5:3b':'Qwen 2.5·3b','qwen3:14b':'Qwen 3·14b',
      'gpt-oss:20b':'GPT-OSS·20b','qwen3:32b':'Qwen 3·32b',
      'claude-sonnet':'Sonnet','claude-opus':'Opus'
    };
    var sDiv = document.createElement('div');
    sDiv.className = 'vt-sujetos';
    sDiv.innerHTML = '<h3>Rendimiento IA — von Thünen (n34–36)</h3>';

    sujetoOrder.forEach(function (s) {
      var dat = rendIA[s];
      if (!dat) return;
      var row = document.createElement('div');
      row.className = 'vt-sujeto-row';
      var pips = dat.preguntas.map(function (q) {
        var ok = q.veredicto === 'CORRECTO';
        return '<div class="vt-pip ' + (ok ? 'ok' : 'fail') + '" title="n' + q.n + ': ' + q.veredicto + '">' +
               (ok ? '✓' : '✗') + '</div>';
      }).join('');
      row.innerHTML = '<span class="sname">' + (sujetoLabels[s] || s) + '</span>' +
                      '<div class="vt-pips">' + pips + '</div>' +
                      '<span style="font-size:0.75rem;opacity:0.55;margin-left:6px">' +
                      dat.aciertos + '/' + dat.total + '</span>';
      sDiv.appendChild(row);
    });

    /* Nota difícil */
    var nota = document.createElement('p');
    nota.style.cssText = 'font-size:0.74rem;opacity:0.5;margin:8px 0 0;font-style:italic;';
    nota.textContent = 'La teoría MÁS DIFÍCIL para los modelos locales. Pregunta d₀_B=16 fallada por casi todos los locales.';
    sDiv.appendChild(nota);

    /* Costos por vía (resumen) */
    var cosDiv = document.createElement('div');
    cosDiv.className = 'vt-costos';
    var pyLocal = costos['python_local'];
    cosDiv.innerHTML = 'Costo por vía (total experimento): ' +
      (pyLocal ? 'Python local <span>$' + (pyLocal.costo_usd || 0).toExponential(2) + '</span> · ' : '') +
      'Sonnet API <span>' + costoSonnet + '</span> · ' +
      'Opus API <span>' + costoOpus + '</span>';

    /* Ensamble */
    panel.appendChild(btn);
    panel.appendChild(sDiv);
    panel.appendChild(cosDiv);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    /* Focus trap */
    btn.focus();
  }

  /* ════════════════════════════════════════════════════════
     ANIMACIÓN PRINCIPAL
     Estado: SWEEP → PAUSE → FADE → SWEEP (loop perpetuo)
     ════════════════════════════════════════════════════════ */

  /* Convierte distancia km → radio en píxeles del panel izquierdo */
  function kmToR(km, maxKm, radius) {
    return (km / maxKm) * radius;
  }

  window.VIZ['von_thunen'] = {
    titulo: 'Los anillos de renta barren el campo',

    mount: function (container, opts) {
      opts = opts || {};
      var compact = !!opts.compact;

      /* ── Reduced-motion: mostrar fallback estático ── */
      var prefersReduced = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      /* ── Canvas setup ── */
      var dpr = window.devicePixelRatio || 1;
      var W = compact ? 800 : 1200;
      var H = compact ? 534 : 800;

      var canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:pointer;' +
                             'background:' + PAL.bg + ';border-radius:8px;';
      canvas.setAttribute('role', 'img');
      canvas.setAttribute('aria-label',
        'Animación interactiva de los anillos de von Thünen. Haz clic para más información.');
      container.style.background = PAL.bg;
      container.appendChild(canvas);

      var ctx = canvas.getContext('2d');

      /* Resize handler */
      function resize() {
        var rect = container.getBoundingClientRect();
        var cw = rect.width  || W;
        var ch = rect.height || H;
        canvas.width  = cw * dpr;
        canvas.height = ch * dpr;
        canvas.style.width  = cw + 'px';
        canvas.style.height = ch + 'px';
        ctx.scale(dpr, dpr);
        /* Recompute layout metrics */
        computeLayout(cw, ch);
      }

      /* ── Layout metrics (recalculados en resize) ── */
      var LAY = {};
      function computeLayout(cw, ch) {
        var pad = compact ? 16 : 24;
        LAY.cw = cw; LAY.ch = ch; LAY.pad = pad;
        /* Panel izquierdo: plano espacial */
        LAY.leftW = cw * 0.46;
        LAY.leftH = ch;
        LAY.cx = LAY.leftW / 2;
        LAY.cy = ch / 2;
        LAY.maxKm = 18;
        LAY.mapRadius = Math.min(LAY.leftW, ch) * 0.42;
        /* Panel derecho: gráfico R(d) */
        LAY.rightX  = LAY.leftW + pad;
        LAY.rightW  = cw - LAY.leftW - pad * 2;
        LAY.rightH  = ch;
        /* Gráfico interior */
        var gpad = compact ? { t: 36, r: 16, b: 44, l: 50 }
                           : { t: 48, r: 20, b: 52, l: 60 };
        LAY.gpad = gpad;
        LAY.gx = LAY.rightX + gpad.l;
        LAY.gy = gpad.t;
        LAY.gw = LAY.rightW - gpad.l - gpad.r;
        LAY.gh = ch - gpad.t - gpad.b;
        LAY.maxD = 18;
        LAY.maxR = 65;
      }
      computeLayout(W, H);

      /* ── Datos que usaremos en render (cargados vía fetch) ── */
      var DATA = null;

      /* ── Estado de animación ── */
      var PHASES = { SWEEP: 0, PAUSE: 1, FADE: 2 };
      var phase = PHASES.SWEEP;
      var sweepProgress = 0;   // 0..1 → ángulo del radar 0..maxKm
      var fadeAlpha = 1;       // 1=visible, 0=invisible (para FADE out)
      var pauseTimer = 0;      // ms acumulados en PAUSE
      var PAUSE_DURATION = 1500;
      var FADE_DURATION  = 600;
      var SWEEP_DURATION = 3200;

      var lastTs = null;
      var rafId = null;
      var paused = false;
      var destroyed = false;

      /* Partículas del radar (rastros luminosos) */
      var radarParticles = [];
      function emitRadarParticle(angle, r, km) {
        /* color según cultivo dominante en este radio */
        var col = km <= 4 ? PAL.amber : (km <= 16 ? PAL.blue : PAL.void);
        radarParticles.push({
          x: LAY.cx + Math.cos(angle) * r,
          y: LAY.cy + Math.sin(angle) * r,
          r: 2.5,
          alpha: 0.7,
          color: col
        });
        if (radarParticles.length > 180) radarParticles.shift();
      }

      /* ════════════════════════════════════════════════════
         RENDER
         ════════════════════════════════════════════════════ */
      function render(ts) {
        if (destroyed) return;
        if (paused) { rafId = requestAnimationFrame(render); return; }

        var dt = lastTs !== null ? Math.min(ts - lastTs, 50) : 16;
        lastTs = ts;

        /* ── Avance de estado ── */
        if (phase === PHASES.SWEEP) {
          sweepProgress = Math.min(sweepProgress + dt / SWEEP_DURATION, 1);
          if (sweepProgress >= 1) {
            phase = PHASES.PAUSE;
            pauseTimer = 0;
          }
        } else if (phase === PHASES.PAUSE) {
          pauseTimer += dt;
          if (pauseTimer >= PAUSE_DURATION) {
            phase = PHASES.FADE;
            fadeAlpha = 1;
          }
        } else if (phase === PHASES.FADE) {
          fadeAlpha = Math.max(0, fadeAlpha - dt / FADE_DURATION);
          if (fadeAlpha <= 0) {
            /* Reset */
            phase = PHASES.SWEEP;
            sweepProgress = 0;
            radarParticles = [];
            fadeAlpha = 1;
          }
        }

        var alpha = (phase === PHASES.FADE) ? fadeAlpha : 1;

        /* ── Limpiar ── */
        ctx.clearRect(0, 0, LAY.cw, LAY.ch);

        /* Fondo global */
        ctx.fillStyle = PAL.bg;
        ctx.fillRect(0, 0, LAY.cw, LAY.ch);

        /* Divisor vertical */
        ctx.save();
        ctx.globalAlpha = 0.18;
        ctx.strokeStyle = PAL.text;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 6]);
        ctx.beginPath();
        ctx.moveTo(LAY.leftW, 0);
        ctx.lineTo(LAY.leftW, LAY.ch);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        /* ── Panel izquierdo: plano espacial ── */
        drawSpatialPanel(alpha);

        /* ── Panel derecho: gráfico R(d) ── */
        if (DATA) drawGraphPanel(alpha);

        rafId = requestAnimationFrame(render);
      }

      /* ─────────────────────────────────────────────────────
         Panel izquierdo: mapa concéntrico con barrido radar
         ───────────────────────────────────────────────────── */
      function drawSpatialPanel(alpha) {
        ctx.save();
        ctx.globalAlpha = alpha;

        var cx = LAY.cx, cy = LAY.cy;
        var R = LAY.mapRadius;
        var maxKm = LAY.maxKm;

        /* ── Anillos rellenos según sweepProgress ── */
        /* Se revelan como sectores circulares conforme avanza el radar */
        /* Ángulo del radar: empieza en -π/2 (arriba) y barre 2π */
        var sweepAngle = -Math.PI / 2 + sweepProgress * Math.PI * 2;

        /* Dibujar anillos como capas del más exterior al más interior */
        /* Para cada punto del plano circular, calcular si ha sido revelado */
        /* Técnica: dibujar la zona revelada con clip de "pastel" */

        /* --- Zona revelada = sector de 0 a sweepAngle --- */
        ctx.save();

        /* Clip al sector revelado (ángulo desde -π/2 hasta sweepAngle) */
        if (phase === PHASES.SWEEP) {
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.arc(cx, cy, R + 4, -Math.PI / 2, sweepAngle, false);
          ctx.closePath();
          ctx.clip();
        }
        /* En PAUSE y FADE: clip completo (todo revelado) */

        /* Anillo exterior B (B extensivo, 4-16 km, azul) */
        ctx.beginPath();
        ctx.arc(cx, cy, kmToR(16, maxKm, R), 0, Math.PI * 2);
        ctx.fillStyle = PAL.blue;
        ctx.globalAlpha = alpha * 0.28;
        ctx.fill();

        /* Anillo interior A (A intensivo, 0-4 km, ámbar) */
        ctx.beginPath();
        ctx.arc(cx, cy, kmToR(4, maxKm, R), 0, Math.PI * 2);
        ctx.fillStyle = PAL.amber;
        ctx.globalAlpha = alpha * 0.45;
        ctx.fill();

        ctx.restore();

        /* ── Círculos de referencia (grid) ── */
        ctx.globalAlpha = alpha;
        [4, 8, 12, 16].forEach(function (km) {
          var r = kmToR(km, maxKm, R);
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, Math.PI * 2);
          ctx.strokeStyle = km === 4 ? PAL.dstar : PAL.gridLine;
          ctx.lineWidth = km === 4 ? 1.5 : 0.8;
          ctx.setLineDash(km === 4 ? [5, 4] : []);
          ctx.stroke();
          ctx.setLineDash([]);
          /* Etiqueta km */
          if (km <= 16) {
            ctx.fillStyle = PAL.text;
            ctx.globalAlpha = alpha * 0.35;
            ctx.font = (compact ? '9' : '10') + 'px "Inter",sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(km + 'km', cx + r + 2, cy - 3);
          }
          ctx.globalAlpha = alpha;
        });

        /* ── Partículas del rastro radar ── */
        if (phase === PHASES.SWEEP) {
          /* Emitir partículas en el frente del radar */
          var frontKm = sweepProgress * maxKm;
          for (var k = 0; k < 3; k++) {
            var km = frontKm * (0.15 + k * 0.28);
            var r = kmToR(km, maxKm, R);
            emitRadarParticle(sweepAngle, r, km);
          }
        }
        radarParticles.forEach(function (p) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fillStyle = p.color;
          ctx.globalAlpha = p.alpha * alpha * 0.6;
          ctx.fill();
          p.alpha *= 0.94;
        });
        ctx.globalAlpha = alpha;

        /* ── Línea del radar (aguja fina) ── */
        if (phase === PHASES.SWEEP) {
          var radarLen = R * 1.05;
          ctx.save();
          /* Gradiente de la aguja */
          var grd = ctx.createLinearGradient(
            cx, cy,
            cx + Math.cos(sweepAngle) * radarLen,
            cy + Math.sin(sweepAngle) * radarLen
          );
          grd.addColorStop(0, 'rgba(232,230,225,0)');
          grd.addColorStop(0.5, 'rgba(232,230,225,0.55)');
          grd.addColorStop(1, 'rgba(232,230,225,0.95)');
          ctx.strokeStyle = grd;
          ctx.lineWidth = compact ? 1.2 : 1.5;
          ctx.globalAlpha = alpha;
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(
            cx + Math.cos(sweepAngle) * radarLen,
            cy + Math.sin(sweepAngle) * radarLen
          );
          ctx.stroke();

          /* Estela del radar (sector translúcido detrás de la aguja) */
          var sweepBack = 0.22; /* radianes de cola */
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.arc(cx, cy, radarLen, sweepAngle - sweepBack, sweepAngle, false);
          ctx.closePath();
          var grdSweep = ctx.createRadialGradient(cx, cy, 0, cx, cy, radarLen);
          grdSweep.addColorStop(0, 'rgba(232,230,225,0.0)');
          grdSweep.addColorStop(1, 'rgba(224,164,88,0.08)');
          ctx.fillStyle = grdSweep;
          ctx.globalAlpha = alpha;
          ctx.fill();
          ctx.restore();
        }

        /* ── Marcador d* = 4 km ── */
        if (phase !== PHASES.SWEEP || sweepProgress > 0.25) {
          var dStarAlpha = phase === PHASES.SWEEP
            ? Math.max(0, (sweepProgress - 0.25) / 0.12)
            : 1;
          dStarAlpha = Math.min(1, dStarAlpha);

          /* Pulso en d* */
          var dStarR = kmToR(4, maxKm, R);
          var pulseT = (phase === PHASES.PAUSE) ? ((pauseTimer % 1200) / 1200) : 0;
          if (phase === PHASES.PAUSE) {
            ctx.beginPath();
            ctx.arc(cx, cy, dStarR + pulseT * 14, 0, Math.PI * 2);
            ctx.strokeStyle = PAL.dstar;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = alpha * dStarAlpha * (1 - pulseT) * 0.6;
            ctx.stroke();
            ctx.globalAlpha = alpha;
          }

          /* Etiqueta d* */
          ctx.save();
          ctx.globalAlpha = alpha * dStarAlpha;
          ctx.fillStyle = PAL.dstar;
          ctx.font = 'bold ' + (compact ? '10' : '12') + 'px "Inter",sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText('d*=4 km', cx + dStarR + 6, cy - dStarR * 0.15);
          ctx.restore();
        }

        /* ── Punto central (mercado) ── */
        ctx.beginPath();
        ctx.arc(cx, cy, compact ? 5 : 7, 0, Math.PI * 2);
        var grdCenter = ctx.createRadialGradient(cx, cy, 0, cx, cy, 7);
        grdCenter.addColorStop(0, '#ffffff');
        grdCenter.addColorStop(1, PAL.amber);
        ctx.fillStyle = grdCenter;
        ctx.globalAlpha = alpha;
        ctx.fill();

        /* Etiqueta "Mercado" */
        ctx.fillStyle = PAL.text;
        ctx.globalAlpha = alpha * 0.7;
        ctx.font = (compact ? '10' : '11') + 'px "Inter",sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Mercado', cx, cy + (compact ? 16 : 20));

        /* ── Título panel izquierdo ── */
        ctx.fillStyle = PAL.text;
        ctx.globalAlpha = alpha * 0.55;
        ctx.font = (compact ? '10' : '11') + 'px "Inter",sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Plano espacial (vista superior)', cx, LAY.pad + 14);

        /* ── Leyenda anillos ── */
        var legY = LAY.ch - LAY.pad - 8;
        var legX = cx - 80;
        ctx.globalAlpha = alpha * 0.8;
        [[PAL.amber, 0.45, 'A intensivo (0–4 km)'],
         [PAL.blue,  0.28, 'B extensivo (4–16 km)']].forEach(function (item, i) {
          ctx.fillStyle = item[0];
          ctx.globalAlpha = alpha * (item[1] + 0.3);
          ctx.fillRect(legX + i * 130, legY - 9, 12, 12);
          ctx.fillStyle = PAL.text;
          ctx.globalAlpha = alpha * 0.65;
          ctx.font = (compact ? '9' : '10') + 'px "Inter",sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText(item[2], legX + i * 130 + 16, legY);
        });

        ctx.restore();
      }

      /* ─────────────────────────────────────────────────────
         Panel derecho: gráfico R(d)
         ───────────────────────────────────────────────────── */
      function drawGraphPanel(alpha) {
        if (!DATA) return;
        ctx.save();
        ctx.globalAlpha = alpha;

        var gx = LAY.gx, gy = LAY.gy, gw = LAY.gw, gh = LAY.gh;
        var maxD = LAY.maxD, maxR = LAY.maxR;
        var series = DATA.series;
        var d_vals = series.d_values_km;

        /* ── Mapeo coordenadas ── */
        function toX(d) { return gx + (d / maxD) * gw; }
        function toY(R) { return gy + gh - (Math.max(0, R) / maxR) * gh; }

        /* ── Fondo zona A y B (pintados progresivamente según sweep) ── */
        var sweepKm = sweepProgress * maxD;
        var dStarKm = DATA.frontera_anillo_d_star_km; /* 4 */
        var d0B = DATA.radios_cero.B; /* 16 */

        /* Zona A (0..min(sweepKm, dStar)) */
        if (sweepKm > 0) {
          var xA0 = toX(0), xA1 = toX(Math.min(sweepKm, dStarKm));
          ctx.fillStyle = PAL.amber;
          ctx.globalAlpha = alpha * 0.08;
          ctx.fillRect(xA0, gy, xA1 - xA0, gh);
        }
        /* Zona B (dStar..min(sweepKm, d0B)) */
        if (sweepKm > dStarKm) {
          var xB0 = toX(dStarKm), xB1 = toX(Math.min(sweepKm, d0B));
          ctx.fillStyle = PAL.blue;
          ctx.globalAlpha = alpha * 0.07;
          ctx.fillRect(xB0, gy, xB1 - xB0, gh);
        }
        ctx.globalAlpha = alpha;

        /* ── Ejes ── */
        ctx.strokeStyle = PAL.text;
        ctx.globalAlpha = alpha * 0.3;
        ctx.lineWidth = 1;
        /* eje x */
        ctx.beginPath();
        ctx.moveTo(gx, gy + gh);
        ctx.lineTo(gx + gw, gy + gh);
        ctx.stroke();
        /* eje y */
        ctx.beginPath();
        ctx.moveTo(gx, gy);
        ctx.lineTo(gx, gy + gh);
        ctx.stroke();

        /* Grid horizontal */
        ctx.setLineDash([3, 5]);
        [0, 15, 30, 45, 60].forEach(function (r) {
          var y = toY(r);
          ctx.beginPath();
          ctx.moveTo(gx, y);
          ctx.lineTo(gx + gw, y);
          ctx.globalAlpha = alpha * 0.1;
          ctx.stroke();
          /* Tick labels */
          ctx.fillStyle = PAL.text;
          ctx.globalAlpha = alpha * 0.4;
          ctx.font = (compact ? '9' : '10') + 'px "Inter",sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(r, gx - 5, y + 3);
        });
        ctx.setLineDash([]);

        /* Grid vertical */
        [0, 4, 8, 12, 16, 18].forEach(function (d) {
          var x = toX(d);
          ctx.beginPath();
          ctx.moveTo(x, gy);
          ctx.lineTo(x, gy + gh);
          ctx.strokeStyle = d === 4 ? PAL.dstar : PAL.gridLine;
          ctx.lineWidth = d === 4 ? 1.2 : 0.7;
          ctx.setLineDash(d === 4 ? [4, 4] : [3, 5]);
          ctx.globalAlpha = d === 4 ? alpha * 0.6 : alpha * 0.1;
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = PAL.text;
          ctx.globalAlpha = alpha * 0.4;
          ctx.font = (compact ? '9' : '10') + 'px "Inter",sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(d, x, gy + gh + 14);
        });
        ctx.globalAlpha = alpha;

        /* ── Etiquetas de ejes ── */
        ctx.fillStyle = PAL.text;
        ctx.globalAlpha = alpha * 0.5;
        ctx.font = (compact ? '10' : '11') + 'px "Inter",sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('d (km)', gx + gw / 2, gy + gh + (compact ? 30 : 36));
        ctx.save();
        ctx.translate(gx - (compact ? 38 : 44), gy + gh / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = 'center';
        ctx.fillText('R ($/ha)', 0, 0);
        ctx.restore();
        ctx.globalAlpha = alpha;

        /* ── Título panel derecho ── */
        ctx.fillStyle = PAL.text;
        ctx.globalAlpha = alpha * 0.55;
        ctx.font = (compact ? '10' : '11') + 'px "Inter",sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Función de renta R(d)', gx + gw / 2, gy - (compact ? 20 : 26));

        /* ── Trazar curvas según sweepProgress ── */
        var nReveal = Math.min(
          d_vals.length,
          Math.ceil(sweepProgress * (d_vals.length - 1)) + 1
        );

        /* R_A */
        ctx.beginPath();
        var started = false;
        for (var i = 0; i < nReveal; i++) {
          var x = toX(d_vals[i]), y = toY(series.R_A[i]);
          if (!started) { ctx.moveTo(x, y); started = true; }
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = PAL.rA;
        ctx.lineWidth = compact ? 1.8 : 2.2;
        ctx.globalAlpha = alpha * 0.9;
        ctx.stroke();

        /* R_B */
        ctx.beginPath();
        started = false;
        for (var j = 0; j < nReveal; j++) {
          var xb = toX(d_vals[j]), yb = toY(series.R_B[j]);
          if (!started) { ctx.moveTo(xb, yb); started = true; }
          else ctx.lineTo(xb, yb);
        }
        ctx.strokeStyle = PAL.rB;
        ctx.lineWidth = compact ? 1.8 : 2.2;
        ctx.globalAlpha = alpha * 0.9;
        ctx.stroke();

        /* Envolvente (gruesa, punteada) */
        ctx.beginPath();
        started = false;
        for (var k = 0; k < nReveal; k++) {
          var xe = toX(d_vals[k]), ye = toY(series.envolvente[k]);
          if (!started) { ctx.moveTo(xe, ye); started = true; }
          else ctx.lineTo(xe, ye);
        }
        ctx.strokeStyle = PAL.envelope;
        ctx.lineWidth = compact ? 2.4 : 3.0;
        ctx.setLineDash([6, 5]);
        ctx.globalAlpha = alpha * 0.75;
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = alpha;

        /* ── Etiquetas de curvas (aparecen cuando el sweep llega al final) ── */
        if (sweepProgress > 0.85 || phase !== PHASES.SWEEP) {
          var labAlpha = phase === PHASES.SWEEP
            ? Math.min(1, (sweepProgress - 0.85) / 0.1) : 1;
          ctx.save();
          ctx.globalAlpha = alpha * labAlpha;
          var fs = (compact ? 10 : 12) + 'px "Inter",sans-serif';
          ctx.font = 'bold ' + fs;

          /* R_A label al inicio */
          ctx.fillStyle = PAL.rA;
          ctx.textAlign = 'left';
          ctx.fillText('R_A', toX(0.3), toY(series.R_A[0]) - 6);

          /* R_B label */
          ctx.fillStyle = PAL.rB;
          ctx.fillText('R_B', toX(0.3), toY(series.R_B[0]) + 14);

          /* Envolvente label en mitad */
          ctx.fillStyle = PAL.envelope;
          ctx.globalAlpha = alpha * labAlpha * 0.75;
          ctx.font = (compact ? 9 : 10) + 'px "Inter",sans-serif';
          ctx.fillText('envolvente', toX(7), toY(series.envolvente[7]) - 8);

          ctx.restore();
        }

        /* ── Punto de cruce d* = 4 km ── */
        var dStarRevealProgress = phase === PHASES.SWEEP
          ? Math.max(0, (sweepProgress - 0.22) / 0.1)
          : 1;
        dStarRevealProgress = Math.min(1, dStarRevealProgress);

        if (dStarRevealProgress > 0) {
          var dStarX = toX(dStarKm);
          var dStarY = toY(DATA.renta_en_d_star); /* 36 */

          /* Flash / pulso en PAUSE */
          var flashAlpha = dStarRevealProgress;
          if (phase === PHASES.PAUSE) {
            var pulse = Math.abs(Math.sin((pauseTimer / 800) * Math.PI));
            flashAlpha = 0.6 + 0.4 * pulse;
          }

          /* Punto de cruce */
          ctx.save();
          ctx.globalAlpha = alpha * flashAlpha;
          ctx.beginPath();
          ctx.arc(dStarX, dStarY, compact ? 5 : 7, 0, Math.PI * 2);
          ctx.fillStyle = PAL.dstar;
          ctx.fill();

          /* Anillo externo del pulso */
          if (phase === PHASES.PAUSE) {
            var pulseR = 7 + pulse * 10;
            ctx.beginPath();
            ctx.arc(dStarX, dStarY, pulseR, 0, Math.PI * 2);
            ctx.strokeStyle = PAL.dstar;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = alpha * (1 - pulse) * 0.6;
            ctx.stroke();
          }
          ctx.restore();

          /* Etiqueta d* */
          ctx.save();
          ctx.globalAlpha = alpha * flashAlpha;
          ctx.fillStyle = PAL.dstar;
          ctx.font = 'bold ' + (compact ? 10 : 12) + 'px "Inter",sans-serif';
          ctx.textAlign = 'left';
          ctx.fillText('d*=4 km', dStarX + 8, dStarY - 5);
          ctx.fillStyle = PAL.text;
          ctx.globalAlpha = alpha * flashAlpha * 0.65;
          ctx.font = (compact ? 9 : 10) + 'px "Inter",sans-serif';
          ctx.fillText('R=' + DATA.renta_en_d_star.toFixed(0), dStarX + 8, dStarY + 11);
          ctx.restore();

          /* Línea vertical hacia eje x */
          ctx.save();
          ctx.globalAlpha = alpha * dStarRevealProgress * 0.4;
          ctx.setLineDash([4, 4]);
          ctx.strokeStyle = PAL.dstar;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(dStarX, dStarY);
          ctx.lineTo(dStarX, gy + gh);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.restore();
        }

        /* ── Leyenda R_A / R_B (esquina superior derecha) ── */
        if (sweepProgress > 0.88 || phase !== PHASES.SWEEP) {
          var lfa = phase === PHASES.SWEEP ? Math.min(1, (sweepProgress - 0.88) / 0.08) : 1;
          ctx.save();
          ctx.globalAlpha = alpha * lfa;
          var legX2 = gx + gw - (compact ? 68 : 90);
          var legY2 = gy + (compact ? 12 : 16);
          [[PAL.rA, 'A: pendiente ' + DATA.pendientes.A.toFixed(0)],
           [PAL.rB, 'B: pendiente ' + DATA.pendientes.B.toFixed(0)]].forEach(function (item, i) {
            ctx.strokeStyle = item[0];
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(legX2, legY2 + i * 16);
            ctx.lineTo(legX2 + 16, legY2 + i * 16);
            ctx.stroke();
            ctx.fillStyle = PAL.text;
            ctx.globalAlpha = alpha * lfa * 0.7;
            ctx.font = (compact ? 9 : 10) + 'px "Inter",sans-serif';
            ctx.textAlign = 'left';
            ctx.fillText(item[1], legX2 + 20, legY2 + i * 16 + 3);
            ctx.globalAlpha = alpha * lfa;
          });
          ctx.restore();
        }

        ctx.restore();
      }

      /* ── Fallback estático para prefers-reduced-motion ── */
      function renderStatic() {
        /* Usar los datos si ya están cargados, de lo contrario esperar */
        if (!DATA) return;
        ctx.clearRect(0, 0, LAY.cw, LAY.ch);
        ctx.fillStyle = PAL.bg;
        ctx.fillRect(0, 0, LAY.cw, LAY.ch);
        /* Simular fin de sweep */
        sweepProgress = 1;
        phase = PHASES.PAUSE;
        pauseTimer = 0;
        drawSpatialPanel(1);
        drawGraphPanel(1);
      }

      /* ── Fetch datos ── */
      function loadData() {
        /* Path relativo: ../datos/von_thunen.json desde /viz/ */
        var basePath = (function () {
          var scripts = document.getElementsByTagName('script');
          for (var i = 0; i < scripts.length; i++) {
            var src = scripts[i].src || '';
            if (src.indexOf('von_thunen.js') !== -1) {
              return src.replace('viz/von_thunen.js', '');
            }
          }
          return './';
        })();

        fetch(basePath + 'datos/von_thunen.json')
          .then(function (r) { return r.json(); })
          .then(function (d) {
            DATA = d;
            if (prefersReduced) renderStatic();
          })
          .catch(function (e) {
            console.warn('[von_thunen.js] No se pudo cargar von_thunen.json:', e);
          });
      }

      /* ── Resize observer ── */
      var ro = null;
      if (window.ResizeObserver) {
        ro = new ResizeObserver(function () {
          resize();
          if (prefersReduced && DATA) renderStatic();
        });
        ro.observe(container);
      }
      resize();

      /* ── IntersectionObserver: auto-pausa fuera del viewport ── */
      var io = null;
      if (window.IntersectionObserver) {
        io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (!destroyed) {
              paused = !e.isIntersecting;
              if (!paused && !prefersReduced && rafId === null) {
                lastTs = null;
                rafId = requestAnimationFrame(render);
              }
            }
          });
        }, { threshold: 0.1 });
        io.observe(container);
      }

      /* ── Pausa con document.hidden ── */
      function handleVisibility() {
        if (!destroyed) {
          paused = document.hidden;
        }
      }
      document.addEventListener('visibilitychange', handleVisibility);

      /* ── Click: abrir overlay ── */
      canvas.addEventListener('click', function () {
        if (DATA) buildOverlay(DATA, null);
      });

      /* ── Iniciar animación ── */
      loadData();
      if (!prefersReduced) {
        rafId = requestAnimationFrame(render);
      }

      /* ── API pública ── */
      return {
        pause: function () { paused = true; },
        resume: function () {
          if (destroyed) return;
          paused = false;
          if (!prefersReduced && rafId === null) {
            lastTs = null;
            rafId = requestAnimationFrame(render);
          }
        },
        destroy: function () {
          destroyed = true;
          paused = true;
          if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
          if (ro) { ro.disconnect(); ro = null; }
          if (io) { io.disconnect(); io = null; }
          document.removeEventListener('visibilitychange', handleVisibility);
          canvas.remove();
        }
      };
    }
  };

}());
