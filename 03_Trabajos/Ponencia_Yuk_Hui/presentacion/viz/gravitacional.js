/**
 * gravitacional.js — Visualizacion animada del modelo gravitacional de flujos
 * Autor: generado por Claude Code para la ponencia Yuk Hui
 *
 * Uso:
 *   window.VIZ['gravitacional'].mount(containerElement, opts)
 *   => { pause, resume, destroy }
 *
 * opts.compact  : boolean — reduce densidad de particulas para movil
 */

window.VIZ = window.VIZ || {};

window.VIZ['gravitacional'] = (function () {

  /* ────────────────────────────────────────────
     ESTILOS GLOBALES (inyectados una sola vez)
     ──────────────────────────────────────────── */
  var _stylesInjected = false;
  function _injectStyles() {
    if (_stylesInjected) return;
    _stylesInjected = true;
    var s = document.createElement('style');
    s.textContent = [
      '.grav-overlay{',
        'position:absolute;top:0;left:0;width:100%;height:100%;',
        'background:rgba(14,26,43,0.93);',
        'display:flex;align-items:center;justify-content:center;',
        'z-index:100;cursor:default;',
      '}',
      '.grav-panel{',
        'background:#0e1a2b;border:1px solid #e0a458;border-radius:8px;',
        'padding:28px 32px;max-width:520px;width:90%;',
        'color:#e8e6e1;font-family:"Georgia",serif;font-size:14px;line-height:1.7;',
        'position:relative;box-shadow:0 0 40px rgba(224,164,88,0.25);',
      '}',
      '.grav-panel h2{',
        'color:#e0a458;font-size:17px;margin:0 0 14px 0;letter-spacing:.5px;',
      '}',
      '.grav-panel h3{',
        'color:#e0a458;font-size:13px;margin:16px 0 6px 0;',
        'text-transform:uppercase;letter-spacing:.8px;',
      '}',
      '.grav-panel .formula{',
        'font-family:"Courier New",monospace;font-size:15px;',
        'background:rgba(224,164,88,0.08);border-left:3px solid #e0a458;',
        'padding:8px 12px;margin:10px 0;color:#e0a458;',
      '}',
      '.grav-panel table{',
        'width:100%;border-collapse:collapse;font-size:12px;margin-top:6px;',
      '}',
      '.grav-panel th{',
        'color:#e0a458;padding:4px 8px;text-align:left;',
        'border-bottom:1px solid rgba(224,164,88,0.3);',
      '}',
      '.grav-panel td{',
        'padding:3px 8px;border-bottom:1px solid rgba(255,255,255,0.06);',
      '}',
      '.grav-panel td.v-ok{color:#7ecb8e;}',
      '.grav-panel td.v-fail{color:#e07070;}',
      '.grav-panel .close-btn{',
        'position:absolute;top:12px;right:14px;',
        'background:none;border:none;color:#e0a458;',
        'font-size:20px;cursor:pointer;line-height:1;padding:0;',
      '}',
      '.grav-panel .close-btn:hover{color:#fff;}',
      '.grav-panel .nota-val{',
        'font-size:11px;color:rgba(232,230,225,0.55);margin-top:4px;',
      '}',
    ].join('');
    document.head.appendChild(s);
  }

  /* ────────────────────────────────────────────
     HELPERS MATEMATICOS
     ──────────────────────────────────────────── */

  /** Calcula T_ij = G * Pi * Pj / d^c desde los parametros canonicos del JSON */
  function computeT(G, Pi, Pj, d, c) {
    return G * Pi * Pj / Math.pow(d, c);
  }

  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeInOut(t) { return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; }

  /* ────────────────────────────────────────────
     FUNCION PRINCIPAL mount()
     ──────────────────────────────────────────── */
  function mount(container, opts) {
    opts = opts || {};

    _injectStyles();

    /* Detectar prefers-reduced-motion — si activo, mostramos fallback estatico */
    var reducedMotion = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* Canvas adaptado al container con devicePixelRatio */
    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:pointer;';
    /* No pisar un host posicionado en absolute/fixed (p. ej. fondos full-bleed
       con position:absolute;inset:0): solo posicionar si está en flujo normal. */
    if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
    container.style.overflow = 'hidden';
    container.appendChild(canvas);

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;

    var W = 0, H = 0;  // dimensiones logicas (CSS px)
    var data = null;   // JSON cargado

    /* ── Estado de animacion ── */
    var rafId = null;
    var paused = false;
    var destroyed = false;
    var lastTime = 0;
    var syncTimer = 0;       // contador para el fundido de sincronizacion cada ~6s
    var syncFade = 0;        // 0..1 — opacidad del fundido

    /* ── Pool de particulas por par ── */
    /* Cada par (i,j) mantiene su propio array de particulas con progreso 0..1 */
    var pairs = [];          // se construye en initScene()

    /* ── overlay del panel ── */
    var overlay = null;

    /* ── Variables de escena ── */
    var zones = [];          // { x, y, r, color, label, pop }  en px canvas logico
    var margin = { left: 0, top: 0, scale: 1 };

    /* ── Resize ── */
    function resize() {
      var rect = container.getBoundingClientRect();
      W = rect.width  || 800;
      H = rect.height || 600;
      canvas.width  = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
      canvas.style.width  = W + 'px';
      canvas.style.height = H + 'px';
      if (data) buildScene();
    }

    var resizeObserver = new ResizeObserver(function () { resize(); });
    resizeObserver.observe(container);

    /* ── IntersectionObserver — auto-pausa fuera del viewport ── */
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.intersectionRatio < 0.01) {
          paused = true;
        } else if (!destroyed) {
          paused = false;
          if (!rafId) startLoop();
        }
      });
    }, { threshold: 0.01 });
    io.observe(container);

    /* ── Pausa cuando la pestaña se oculta ── */
    function onVisChange() {
      if (document.hidden) {
        paused = true;
      } else {
        paused = false;
        if (!rafId && !destroyed) startLoop();
      }
    }
    document.addEventListener('visibilitychange', onVisChange);

    /* ── Clic para abrir panel ── */
    canvas.addEventListener('click', function () {
      if (data) openPanel();
    });

    /* ───────────────────────────────────────────
       CARGA DE DATOS
       ─────────────────────────────────────────── */
    var dataUrl = (function () {
      /* Calcula la ruta relativa a datos/gravitacional.json
         buscando el script en la pagina, o usando una ruta heuristica */
      var scripts = document.querySelectorAll('script[src]');
      for (var i = 0; i < scripts.length; i++) {
        var src = scripts[i].src;
        if (src && src.indexOf('gravitacional.js') !== -1) {
          return src.replace('viz/gravitacional.js', 'datos/gravitacional.json');
        }
      }
      return '../datos/gravitacional.json';  // fallback relativo
    })();

    fetch(dataUrl)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        data = d;
        resize();
        if (reducedMotion) {
          drawFallback();
        } else {
          initParticles();
          startLoop();
        }
      })
      .catch(function (err) {
        console.warn('[gravitacional.js] No se pudo cargar datos:', err);
        /* Fallback sin datos: usar valores hard-coded canonicos */
        data = _fallbackData();
        resize();
        if (reducedMotion) {
          drawFallback();
        } else {
          initParticles();
          startLoop();
        }
      });

    /* ───────────────────────────────────────────
       CONSTRUCCION DE ESCENA
       (mapa canonico: zona1=(0,0) zona2=(30,0) zona3=(0,40))
       ─────────────────────────────────────────── */
    function buildScene() {
      /* Coordenadas canonicas en unidades del modelo */
      var modelCoords = [[0, 0], [30, 0], [0, 40]];
      var pops = data.zonas.map(function (z) { return z.poblacion; });
      var maxPop = Math.max.apply(null, pops);

      /* Radio proporcional a sqrt(P): area proporcional a P */
      var baseR = Math.min(W, H) * 0.09;
      var radii = pops.map(function (p) { return baseR * Math.sqrt(p / maxPop); });

      /* Mapeo del espacio modelo -> px logicos con margen */
      var modelW = 30, modelH = 40;
      var padH = W * 0.12, padV = H * 0.12;
      var usableW = W - padH * 2;
      var usableH = H - padV * 2;
      var scale = Math.min(usableW / modelW, usableH / modelH);

      /* Centrar el triangulo */
      var cx = padH + (usableW - modelW * scale) / 2;
      var cy = padV + (usableH - modelH * scale) / 2;

      margin = { left: cx, top: cy, scale: scale };

      var colors = ['#4ab3f0', '#82d9a0', '#f0a84a'];
      var labels = ['Z1', 'Z2', 'Z3'];

      zones = data.zonas.map(function (z, i) {
        return {
          x: cx + modelCoords[i][0] * scale,
          /* Invertimos Y para que (0,0) quede abajo-izquierda en pantalla */
          y: cy + (modelH - modelCoords[i][1]) * scale,
          r: radii[i],
          color: colors[i],
          label: labels[i],
          pop: z.poblacion,
          id: z.id
        };
      });
    }

    /* ───────────────────────────────────────────
       INICIALIZACION DE PARTICULAS
       ─────────────────────────────────────────── */
    function initParticles() {
      pairs = [];
      if (!data || zones.length === 0) return;

      var G = data.panel.parametros.G;
      var c = data.panel.parametros.c;
      var compact = opts.compact;

      /* Calcular T para los tres pares */
      var pairDefs = [
        { i: 0, j: 1, d: data.distancias.d_12 },
        { i: 0, j: 2, d: data.distancias.d_13 },
        { i: 1, j: 2, d: data.distancias.d_23 }
      ];

      var Tmax = 0;
      pairDefs.forEach(function (pd) {
        pd.T = computeT(G, data.zonas[pd.i].poblacion, data.zonas[pd.j].poblacion, pd.d, c);
        if (pd.T > Tmax) Tmax = pd.T;
      });

      pairDefs.forEach(function (pd) {
        var ratio = pd.T / Tmax;           // 0..1 relativo al maximo
        /* Densidad: numero de particulas activas simultaneamente en este par */
        var baseDensity = compact ? 18 : 40;
        var n = Math.max(3, Math.round(baseDensity * Math.sqrt(ratio)));

        /* Velocidad proporcional a T (los rios mas densos tambien se mueven mas rapido) */
        var baseSpeed = 0.04;
        var speed = baseSpeed * (0.5 + 0.5 * ratio);  // 50..100% del maximo

        /* Grosor de linea: 1..4 px */
        var lineWidth = 0.5 + 3.0 * ratio;

        /* Color — mas calido cuanto mayor el flujo */
        var alpha = 0.25 + 0.45 * ratio;
        var lineColor = 'rgba(' + Math.round(lerp(60,220,ratio)) + ',' +
                                  Math.round(lerp(120,180,ratio)) + ',' +
                                  Math.round(lerp(200,80,ratio)) + ',' + alpha.toFixed(2) + ')';

        /* Particulas — distribuidas con offset uniforme para flujo continuo */
        var particles = [];
        for (var k = 0; k < n; k++) {
          particles.push({
            /* progreso 0..1: la posicion a lo largo del segmento i->j */
            t: k / n,
            /* cada particula va en una direccion (alternando o random) */
            dir: (k % 2 === 0) ? 1 : -1,
            /* pequeña oscilacion perpendicular para aspecto organico */
            phase: Math.random() * Math.PI * 2,
            phaseSpeed: 0.4 + Math.random() * 0.6,
            amp: (compact ? 1.5 : 3) * ratio,   // amplitud de wiggleo
            size: 1.2 + 1.8 * ratio * (0.7 + Math.random() * 0.6),
            opacity: 0.5 + 0.5 * Math.random()
          });
        }

        /* Fase de respiracion del grosor de linea */
        pairs.push({
          i: pd.i, j: pd.j,
          T: pd.T, ratio: ratio,
          n: n, speed: speed,
          lineWidth: lineWidth,
          lineColor: lineColor,
          particles: particles,
          breathPhase: Math.random() * Math.PI * 2,
          /* periodo de respiracion distinto por par — revela distintos ritmos */
          breathPeriod: 1.8 + 2.4 * (1 - ratio)
        });
      });
    }

    /* ───────────────────────────────────────────
       LOOP DE ANIMACION
       ─────────────────────────────────────────── */
    function startLoop() {
      if (rafId) return;
      lastTime = performance.now();
      rafId = requestAnimationFrame(tick);
    }

    function tick(now) {
      if (destroyed) { rafId = null; return; }
      rafId = requestAnimationFrame(tick);
      if (paused) return;

      var dt = Math.min((now - lastTime) / 1000, 0.05);  // segundos, capped a 50ms
      lastTime = now;

      update(dt, now / 1000);
      draw(now / 1000);
    }

    function update(dt, t) {
      /* Sincronizacion cada ~6s con fade suave */
      syncTimer += dt;
      var syncPeriod = 6.0;
      var fadeDuration = 0.4;  // segundos del fundido
      var syncPhase = syncTimer % syncPeriod;

      if (syncPhase < fadeDuration) {
        /* Fundido de salida al inicio del ciclo */
        syncFade = easeInOut(syncPhase / fadeDuration);
      } else if (syncPhase > syncPeriod - fadeDuration) {
        /* Fundido de entrada al final */
        syncFade = easeInOut((syncPeriod - syncPhase) / fadeDuration);
      } else {
        syncFade = 0;
      }

      /* Avanzar particulas */
      pairs.forEach(function (pair) {
        pair.particles.forEach(function (p) {
          p.t += p.dir * pair.speed * dt;
          p.phase += p.phaseSpeed * dt;
          /* Wrap en 0..1 para loop continuo sin reset duro */
          if (p.t > 1) p.t -= 1;
          if (p.t < 0) p.t += 1;
        });
        /* Respiracion del grosor */
        pair.breathPhase += (Math.PI * 2 / pair.breathPeriod) * dt;
      });
    }

    function draw(t) {
      /* Escalar al devicePixelRatio */
      ctx.save();
      ctx.scale(dpr, dpr);

      /* Fondo */
      ctx.fillStyle = '#0e1a2b';
      ctx.fillRect(0, 0, W, H);

      if (zones.length === 0) { ctx.restore(); return; }

      /* Overlay de sincronizacion (fundido negro suave) */
      if (syncFade > 0) {
        ctx.fillStyle = 'rgba(14,26,43,' + (syncFade * 0.6).toFixed(3) + ')';
        ctx.fillRect(0, 0, W, H);
      }

      /* ── Lineas de fondo (el canal de cada par) ── */
      pairs.forEach(function (pair) {
        var zA = zones[pair.i], zB = zones[pair.j];
        var breath = 1 + 0.18 * Math.sin(pair.breathPhase);

        ctx.beginPath();
        ctx.moveTo(zA.x, zA.y);
        ctx.lineTo(zB.x, zB.y);
        ctx.strokeStyle = pair.lineColor.replace(/[\d.]+\)$/, function (m) {
          return (parseFloat(m) * 0.35).toFixed(2) + ')';
        });
        ctx.lineWidth = pair.lineWidth * breath * 0.6;
        ctx.lineCap = 'round';
        ctx.stroke();
      });

      /* ── Particulas ── */
      pairs.forEach(function (pair) {
        var zA = zones[pair.i], zB = zones[pair.j];

        /* Vector perpendicular para el wiggleo */
        var dx = zB.x - zA.x, dy = zB.y - zA.y;
        var len = Math.sqrt(dx * dx + dy * dy);
        var nx = -dy / len, ny = dx / len;

        pair.particles.forEach(function (p) {
          var pt = p.t;
          var px = lerp(zA.x, zB.x, pt);
          var py = lerp(zA.y, zB.y, pt);

          /* Wiggleo organico */
          var wiggle = pair.ratio * p.amp * Math.sin(p.phase);
          px += nx * wiggle;
          py += ny * wiggle;

          /* Fade en los extremos del segmento — las particulas
             aparecen/desaparecen suavemente al entrar o salir de las zonas */
          var edgeFade = Math.min(pt / 0.12, 1) * Math.min((1 - pt) / 0.12, 1);
          var alpha = p.opacity * edgeFade * (1 - syncFade * 0.7);

          /* Halo glow */
          var rad = ctx.createRadialGradient(px, py, 0, px, py, p.size * 2.5);
          var baseColor = pair.lineColor.match(/rgba\((\d+),(\d+),(\d+)/);
          if (baseColor) {
            var r = baseColor[1], g = baseColor[2], b = baseColor[3];
            rad.addColorStop(0,   'rgba(' + r + ',' + g + ',' + b + ',' + (alpha * 0.9).toFixed(3) + ')');
            rad.addColorStop(0.4, 'rgba(' + r + ',' + g + ',' + b + ',' + (alpha * 0.4).toFixed(3) + ')');
            rad.addColorStop(1,   'rgba(' + r + ',' + g + ',' + b + ',0)');
          }
          ctx.beginPath();
          ctx.arc(px, py, p.size * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = rad;
          ctx.fill();

          /* Nucleo brillante */
          ctx.beginPath();
          ctx.arc(px, py, p.size * 0.5, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(255,255,255,' + (alpha * 0.85).toFixed(3) + ')';
          ctx.fill();
        });
      });

      /* ── Etiquetas de flujo sobre cada linea ── */
      if (W > 500) {
        pairs.forEach(function (pair) {
          var zA = zones[pair.i], zB = zones[pair.j];
          var mx = (zA.x + zB.x) / 2, my = (zA.y + zB.y) / 2;
          var tLabel = Math.round(pair.T);
          ctx.font = (W > 800 ? '11px' : '9px') + ' "Courier New", monospace';
          ctx.fillStyle = 'rgba(224,200,120,0.65)';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText('T=' + tLabel.toLocaleString(), mx, my - 10);
        });
      }

      /* ── Circulos de zonas ── */
      zones.forEach(function (z, i) {
        /* Glow externo */
        var glow = ctx.createRadialGradient(z.x, z.y, z.r * 0.7, z.x, z.y, z.r * 1.6);
        glow.addColorStop(0, z.color.replace(')', ',0.18)').replace('rgb', 'rgba'));
        glow.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.beginPath();
        ctx.arc(z.x, z.y, z.r * 1.6, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        /* Circulo relleno */
        var grad = ctx.createRadialGradient(z.x - z.r * 0.3, z.y - z.r * 0.3, 0, z.x, z.y, z.r);
        grad.addColorStop(0, lighten(z.color, 0.4));
        grad.addColorStop(1, z.color);
        ctx.beginPath();
        ctx.arc(z.x, z.y, z.r, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        /* Borde */
        ctx.beginPath();
        ctx.arc(z.x, z.y, z.r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        /* Etiqueta */
        ctx.font = 'bold ' + Math.max(10, Math.round(z.r * 0.55)) + 'px sans-serif';
        ctx.fillStyle = '#0e1a2b';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Z' + z.id, z.x, z.y);

        /* Poblacion debajo */
        ctx.font = Math.max(9, Math.round(z.r * 0.38)) + 'px sans-serif';
        ctx.fillStyle = 'rgba(232,230,225,0.7)';
        ctx.fillText((z.pop / 1000).toFixed(0) + 'k', z.x, z.y + z.r + 12);
      });

      /* ── Titulo ── */
      ctx.font = 'bold ' + (W > 700 ? '14' : '11') + 'px "Georgia", serif';
      ctx.fillStyle = 'rgba(224,164,88,0.75)';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText('Modelo Gravitacional de Flujos', 14, 10);

      /* ── Hint de click ── */
      ctx.font = '10px sans-serif';
      ctx.fillStyle = 'rgba(232,230,225,0.3)';
      ctx.textAlign = 'right';
      ctx.fillText('clic para datos', W - 10, H - 14);

      ctx.restore();
    }

    /* ───────────────────────────────────────────
       FALLBACK ESTATICO (prefers-reduced-motion)
       ─────────────────────────────────────────── */
    function drawFallback() {
      ctx.save();
      ctx.scale(dpr, dpr);

      ctx.fillStyle = '#0e1a2b';
      ctx.fillRect(0, 0, W, H);

      if (!data || zones.length === 0) { ctx.restore(); return; }

      /* Lineas proporcionales al flujo */
      var flowKeys = [
        { i: 0, j: 1, key: 'T_12' },
        { i: 0, j: 2, key: 'T_13' },
        { i: 1, j: 2, key: 'T_23' }
      ];
      var Tmax = Math.max(data.flujos.T_12, data.flujos.T_13, data.flujos.T_23);

      flowKeys.forEach(function (fk) {
        var zA = zones[fk.i], zB = zones[fk.j];
        var T = data.flujos[fk.key];
        var ratio = T / Tmax;
        ctx.beginPath();
        ctx.moveTo(zA.x, zA.y);
        ctx.lineTo(zB.x, zB.y);
        ctx.strokeStyle = 'rgba(224,164,88,' + (0.3 + 0.5 * ratio).toFixed(2) + ')';
        ctx.lineWidth = 1 + 5 * ratio;
        ctx.lineCap = 'round';
        ctx.stroke();
      });

      /* Zonas */
      zones.forEach(function (z) {
        ctx.beginPath();
        ctx.arc(z.x, z.y, z.r, 0, Math.PI * 2);
        ctx.fillStyle = z.color;
        ctx.fill();
        ctx.font = 'bold ' + Math.max(10, Math.round(z.r * 0.55)) + 'px sans-serif';
        ctx.fillStyle = '#0e1a2b';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Z' + z.id, z.x, z.y);
      });

      ctx.restore();
    }

    /* ───────────────────────────────────────────
       PANEL OVERLAY
       ─────────────────────────────────────────── */
    function openPanel() {
      if (overlay) return;
      /* Los numeros del panel se recalculan desde los datos del JSON */
      var d = data;
      var G = d.panel.parametros.G;
      var c = d.panel.parametros.c;
      var T12 = computeT(G, d.zonas[0].poblacion, d.zonas[1].poblacion, d.distancias.d_12, c);
      var T13 = computeT(G, d.zonas[0].poblacion, d.zonas[2].poblacion, d.distancias.d_13, c);
      var T23 = computeT(G, d.zonas[1].poblacion, d.zonas[2].poblacion, d.distancias.d_23, c);
      var sumaPares = T12 + T13 + T23;

      /* Rendimiento por sujeto IA en las preguntas de esta teoria */
      var sujetos = Object.keys(d.rendimiento_IA || {});
      var renRows = sujetos.map(function (s) {
        var ri = d.rendimiento_IA[s];
        var n24res = (d.preguntas_experimento || []).find(function (p) { return p.n === 24; });
        var n24suj = n24res && n24res.resultados && n24res.resultados[s];
        var correcto24 = n24suj && n24suj.veredicto === 'CORRECTO';
        return {
          sujeto: s,
          correctas: ri.correctas,
          total: ri.total,
          n24ok: correcto24
        };
      });

      overlay = document.createElement('div');
      overlay.className = 'grav-overlay';

      var cRecomp = d.panel.criterio_validacion.c_recuperado_regresion;

      var panelHTML = [
        '<div class="grav-panel">',
          '<button class="close-btn" aria-label="Cerrar">&times;</button>',
          '<h2>Modelo Gravitacional de Flujos Espaciales</h2>',
          '<p><strong>Autores:</strong> ' + d.panel.autor_principal + ' (' + d.panel.anio + ').',
          ' Raices: ' + d.panel.raices + '. Derivacion entropica: ' + d.panel.derivacion_entropica + '.</p>',
          '<div class="formula">T<sub>ij</sub> = G &middot; P<sub>i</sub> &middot; P<sub>j</sub> / d<sub>ij</sub><sup>c</sup></div>',
          '<p class="nota-val">c=' + c + ' (analogia newtoniana); G=' + G + '. Parametros canonicos del experimento.</p>',
          '<h3>Flujos calculados</h3>',
          '<table><thead><tr>',
            '<th>Par</th><th>T_ij</th><th>d (u.m.)</th><th>Ratio</th>',
          '</tr></thead><tbody>',
            '<tr><td>Z1–Z2</td><td>' + Math.round(T12).toLocaleString() + '</td><td>' + d.distancias.d_12 + '</td><td>' + (T12 / T13).toFixed(2) + '</td></tr>',
            '<tr><td>Z1–Z3 <small>(mayor)</small></td><td>' + Math.round(T13).toLocaleString() + '</td><td>' + d.distancias.d_13 + '</td><td>1.00</td></tr>',
            '<tr><td>Z2–Z3</td><td>' + Math.round(T23).toLocaleString() + '</td><td>' + d.distancias.d_23 + '</td><td>' + (T23 / T13).toFixed(2) + '</td></tr>',
            '<tr><td><strong>Suma pares</strong></td><td colspan="3"><strong>' + Math.round(sumaPares).toLocaleString() + '</strong></td></tr>',
          '</tbody></table>',
          '<p class="nota-val">Simetria T_ij=T_ji: <strong>' + (d.panel.criterio_validacion.simetria_ok ? 'OK' : 'FALLO') + '</strong>. ' +
            'c recuperado por regresion: <strong>' + (cRecomp ? cRecomp.toFixed(3) : 'N/A') + '</strong>.</p>',
          '<h3>Rendimiento sujetos IA (preguntas n22-24)</h3>',
          '<table><thead><tr>',
            '<th>Sujeto</th><th>Correctas/Total</th><th>n24 emergente</th>',
          '</tr></thead><tbody>',
          renRows.map(function (r) {
            return '<tr><td>' + r.sujeto + '</td>' +
              '<td>' + r.correctas + '/' + r.total + '</td>' +
              '<td class="' + (r.n24ok ? 'v-ok' : 'v-fail') + '">' +
              (r.n24ok ? '&#10003; OK' : '&#10007; Error') + '</td></tr>';
          }).join(''),
          '</tbody></table>',
          '<p class="nota-val">n24 (emergente, suma pares ' + Math.round(sumaPares).toLocaleString() + '): ',
          'qwen2.5:3b y qwen3:14b dan 8.6M y 4.3M (error: no suman pares distintos). ',
          'gpt-oss:20b, sonnet, opus: correctos.</p>',
        '</div>'
      ].join('');

      overlay.innerHTML = panelHTML;
      container.appendChild(overlay);

      /* Cerrar con el boton X */
      overlay.querySelector('.close-btn').addEventListener('click', closePanel);

      /* Cerrar al hacer clic fuera del panel */
      overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closePanel();
      });

      /* Cerrar con Escape */
      overlay._keyHandler = function (e) {
        if (e.key === 'Escape') closePanel();
      };
      document.addEventListener('keydown', overlay._keyHandler);
    }

    function closePanel() {
      if (!overlay) return;
      document.removeEventListener('keydown', overlay._keyHandler);
      overlay.parentNode && overlay.parentNode.removeChild(overlay);
      overlay = null;
    }

    /* ───────────────────────────────────────────
       DATOS FALLBACK (cuando el JSON no carga)
       ─────────────────────────────────────────── */
    function _fallbackData() {
      return {
        panel: {
          parametros: { G: 1.0, a: 1.0, b: 1.0, c: 2.0 },
          autor_principal: 'John Q. Stewart',
          anio: '1948',
          raices: 'Henry Carey (1858), G. K. Zipf (1946)',
          derivacion_entropica: 'Alan Wilson (1967)',
          criterio_validacion: {
            simetria_ok: true,
            c_recuperado_regresion: 2.0,
            tolerancia_05pct_ok: true
          }
        },
        zonas: [
          { id: 1, poblacion: 10000, posicion: [0, 0] },
          { id: 2, poblacion: 5000,  posicion: [30, 0] },
          { id: 3, poblacion: 20000, posicion: [0, 40] }
        ],
        distancias: { d_12: 30, d_13: 40, d_23: 50 },
        flujos: { T_12: 55555.56, T_13: 125000, T_23: 40000 },
        suma_pares: 220555.56,
        rendimiento_IA: {},
        preguntas_experimento: []
      };
    }

    /* ───────────────────────────────────────────
       UTILIDADES DE COLOR
       ─────────────────────────────────────────── */
    function lighten(hex, amount) {
      var r = parseInt(hex.slice(1,3),16);
      var g = parseInt(hex.slice(3,5),16);
      var b = parseInt(hex.slice(5,7),16);
      r = Math.min(255, Math.round(r + (255 - r) * amount));
      g = Math.min(255, Math.round(g + (255 - g) * amount));
      b = Math.min(255, Math.round(b + (255 - b) * amount));
      return 'rgb(' + r + ',' + g + ',' + b + ')';
    }

    /* ───────────────────────────────────────────
       API PUBLICA
       ─────────────────────────────────────────── */
    function pause()   { paused = true; }
    function resume()  {
      paused = false;
      if (!rafId && !destroyed) startLoop();
    }
    function destroy() {
      destroyed = true;
      paused = true;
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      resizeObserver.disconnect();
      io.disconnect();
      document.removeEventListener('visibilitychange', onVisChange);
      closePanel();
      if (canvas.parentNode) canvas.parentNode.removeChild(canvas);
    }

    return { pause: pause, resume: resume, destroy: destroy };
  }

  return {
    titulo: 'Ciudades que se atraen como masas',
    mount: mount
  };

})();
