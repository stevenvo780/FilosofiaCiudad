/* ════════════════════════════════════════════════════════════════════════
   ambient.js — Capa ambiental del deck Yuk Hui
   ────────────────────────────────────────────────────────────────────────
   Registra window.AMBIENT = {
     mount(container, { variante, ...params }) -> { pause, resume, destroy }
   }

   Variantes disponibles:
     flujo_vital  · bucle  · horizonte  · pulso_datos  · ascua  · deriva

   Paleta exclusiva del proyecto:
     BG     #0e1a2b   TEXTO  #e8e6e1   ACENTO  #e0a458
     AMBER  #efc88a   VERDE  #3ecf9a   ROJO    #e07a68
     AZUL   #5fa8e0   LINEA  #243248

   Contrato:
     mount() -> { pause(), resume(), destroy() }

   Física:
     • easing universal: cubic-bezier(.2,.7,.2,1) — idéntico al deck
     • velocidades: 0.05 – 0.40 px/frame (escaladas por DPR)
     • prefers-reduced-motion → frame estático, sin rAF
     • document.hidden → auto-pausa
     • compact:true (móvil) → ~40 % menos partículas
     • cap global ≤ 60 partículas/instancia
   ════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── Paleta ──────────────────────────────────────────────────────────── */
  var P = {
    BG:    '#0e1a2b',
    TEXTO: '#e8e6e1',
    ACENTO:'#e0a458',
    AMBER: '#efc88a',
    VERDE: '#3ecf9a',
    ROJO:  '#e07a68',
    AZUL:  '#5fa8e0',
    LINEA: '#243248',
  };

  /* ── Helpers de color ────────────────────────────────────────────────── */
  function hexToRgb(h) {
    var r = parseInt(h.slice(1,3),16);
    var g = parseInt(h.slice(3,5),16);
    var b = parseInt(h.slice(5,7),16);
    return [r,g,b];
  }
  function lerpRgb(a, b, t) {
    return [
      Math.round(a[0] + (b[0]-a[0])*t),
      Math.round(a[1] + (b[1]-a[1])*t),
      Math.round(a[2] + (b[2]-a[2])*t)
    ];
  }
  function rgba(hex, a) {
    var c = hexToRgb(hex);
    return 'rgba('+c[0]+','+c[1]+','+c[2]+','+a.toFixed(3)+')';
  }
  function rgbArr(arr, a) {
    return 'rgba('+arr[0]+','+arr[1]+','+arr[2]+','+a.toFixed(3)+')';
  }

  /* ── prefers-reduced-motion ──────────────────────────────────────────── */
  var REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Creador de canvas de fondo ──────────────────────────────────────── */
  function makeCanvas(container) {
    var cv = document.createElement('canvas');
    cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;display:block;';
    container.appendChild(cv);
    return cv;
  }

  /* ── Resize con DPR correcto ─────────────────────────────────────────── */
  function resizeCanvas(cv) {
    var dpr = window.devicePixelRatio || 1;
    var W = cv.clientWidth  || cv.parentElement && cv.parentElement.clientWidth  || 800;
    var H = cv.clientHeight || cv.parentElement && cv.parentElement.clientHeight || 600;
    if (cv.width !== W*dpr || cv.height !== H*dpr) {
      cv.width  = W * dpr;
      cv.height = H * dpr;
      var ctx = cv.getContext('2d');
      ctx.setTransform(1,0,0,1,0,0);
      ctx.scale(dpr, dpr);
    }
    return { W: W, H: H, dpr: dpr };
  }

  /* ── API base para animaciones ───────────────────────────────────────── */
  function makeLoop(tickFn, cv) {
    var paused  = false;
    var dead    = false;
    var rafId   = null;

    function onVisible() { paused = document.hidden; }
    document.addEventListener('visibilitychange', onVisible);

    var resObs = null;
    if (typeof ResizeObserver !== 'undefined' && cv) {
      resObs = new ResizeObserver(function() { resizeCanvas(cv); });
      resObs.observe(cv.parentElement || cv);
    }

    function frame(ts) {
      if (dead) return;
      rafId = requestAnimationFrame(frame);
      if (paused) return;
      tickFn(ts);
    }

    if (!REDUCED) {
      rafId = requestAnimationFrame(frame);
    }

    return {
      pause:   function() { paused = true; },
      resume:  function() { paused = false; },
      destroy: function() {
        dead = true;
        if (rafId) cancelAnimationFrame(rafId);
        document.removeEventListener('visibilitychange', onVisible);
        if (resObs) resObs.disconnect();
        if (cv && cv.parentElement) cv.parentElement.removeChild(cv);
      }
    };
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 1 — flujo_vital
     Bergson: élan vital vs. automatismo mecánico.
     Retícula fija (mecánico) + partículas orgánicas curl-noise (vital).
  ════════════════════════════════════════════════════════════════════ */
  function mountFlujoVital(container, opts) {
    var densidad   = opts.densidad   || 28;   // baja18/media28/alta40
    var opPart     = opts.opacidad   || 0.14;
    var opGrid     = opts.opReticula || 0.05;
    var speed      = opts.velocidad  || 0.25;
    if (opts.compact) densidad = Math.max(10, Math.floor(densidad * 0.6));
    densidad = Math.min(densidad, 60);

    var cv  = makeCanvas(container);
    var ctx = cv.getContext('2d');

    /* Campo de flow-noise precomputado (Perlin-lite 2D) */
    var FIELD_W = 32, FIELD_H = 32;
    var field = new Float32Array(FIELD_W * FIELD_H * 2); // [ax, ay, ax, ay ...]
    (function buildField() {
      // Gradientes aleatorios tipo Perlin simplificado
      var seed = [];
      for (var i = 0; i < (FIELD_W+1)*(FIELD_H+1); i++) {
        var a = Math.random() * Math.PI * 2;
        seed.push([Math.cos(a), Math.sin(a)]);
      }
      function g(ix, iy) { return seed[(iy*(FIELD_W+1)+ix)]; }
      function fade(t) { return t*t*t*(t*(t*6-15)+10); }
      function lerp(a, b, t) { return a + (b-a)*t; }
      function dot(gv, dx, dy) { return gv[0]*dx + gv[1]*dy; }

      for (var fy = 0; fy < FIELD_H; fy++) {
        for (var fx = 0; fx < FIELD_W; fx++) {
          var nx = fx / FIELD_W, ny = fy / FIELD_H;
          // bilinear Perlin
          var X0 = fx, Y0 = fy;
          var dx = nx * FIELD_W - X0;
          var dy = ny * FIELD_H - Y0;
          var u = fade(dx), v = fade(dy);
          var n00 = dot(g(X0,Y0),       dx,     dy    );
          var n10 = dot(g(X0+1,Y0),     dx-1,   dy    );
          var n01 = dot(g(X0,Y0+1),     dx,     dy-1  );
          var n11 = dot(g(X0+1,Y0+1),   dx-1,   dy-1  );
          var nx0 = lerp(n00, n10, u);
          var nx1 = lerp(n01, n11, u);
          var val = lerp(nx0, nx1, v);
          // campo curl: ángulo de flujo
          var angle = val * Math.PI * 2.8;
          var idx = (fy * FIELD_W + fx) * 2;
          field[idx]   = Math.cos(angle);
          field[idx+1] = Math.sin(angle);
        }
      }
    }());

    function sampleField(px, py, W, H) {
      var nx = (px / W) * (FIELD_W - 1);
      var ny = (py / H) * (FIELD_H - 1);
      var x0 = Math.floor(nx)|0, y0 = Math.floor(ny)|0;
      x0 = Math.max(0, Math.min(FIELD_W-2, x0));
      y0 = Math.max(0, Math.min(FIELD_H-2, y0));
      var tx = nx - x0, ty = ny - y0;
      var i00 = (y0*FIELD_W + x0)*2;
      var i10 = (y0*FIELD_W + x0+1)*2;
      var i01 = ((y0+1)*FIELD_W + x0)*2;
      var i11 = ((y0+1)*FIELD_W + x0+1)*2;
      var ax = (1-tx)*(1-ty)*field[i00]   + tx*(1-ty)*field[i10]
             + (1-tx)*ty*field[i01]        + tx*ty*field[i11];
      var ay = (1-tx)*(1-ty)*field[i00+1] + tx*(1-ty)*field[i10+1]
             + (1-tx)*ty*field[i01+1]     + tx*ty*field[i11+1];
      return [ax, ay];
    }

    /* Espaciado de la retícula */
    var GRID_STEP = 52;  // px lógicos

    /* Partículas */
    var TRAIL = 5;
    var RGB_VERDE  = hexToRgb(P.VERDE);
    var RGB_ACENTO = hexToRgb(P.ACENTO);

    function makeParticle(W, H) {
      var edge = (Math.random() * 4)|0;
      var x, y;
      if (edge === 0) { x = Math.random()*W; y = 0; }
      else if (edge === 1) { x = W; y = Math.random()*H; }
      else if (edge === 2) { x = Math.random()*W; y = H; }
      else { x = 0; y = Math.random()*H; }
      return {
        x: x, y: y,
        age: 0,
        life: 280 + Math.random()*200,
        trail: [],
        speed: speed * (0.7 + Math.random()*0.6)
      };
    }

    var particles = [];
    var dim = resizeCanvas(cv);
    for (var i = 0; i < densidad; i++) particles.push(makeParticle(dim.W, dim.H));

    /* Nudo de retícula más cercano */
    function nearestNode(x, y) {
      return [
        Math.round(x / GRID_STEP) * GRID_STEP,
        Math.round(y / GRID_STEP) * GRID_STEP
      ];
    }

    function drawStatic() {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);
      // Retícula estática
      ctx.strokeStyle = rgba(P.LINEA, opGrid);
      ctx.lineWidth = 0.5;
      for (var gx = 0; gx < W; gx += GRID_STEP) {
        ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke();
      }
      for (var gy = 0; gy < H; gy += GRID_STEP) {
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
      }
      // Partículas estáticas (puntos simples)
      for (var pi = 0; pi < particles.length; pi++) {
        var p = particles[pi];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.8, 0, Math.PI*2);
        ctx.fillStyle = rgba(P.VERDE, opPart);
        ctx.fill();
      }
    }

    if (REDUCED) { drawStatic(); return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } }; }

    var lastTs = 0;
    var SNAP_FRAMES = {}; // frame de snap por índice de partícula

    function tick(ts) {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      var dt = Math.min(ts - lastTs, 80);
      lastTs = ts;

      ctx.clearRect(0, 0, W, H);

      /* Retícula */
      ctx.strokeStyle = rgba(P.LINEA, opGrid);
      ctx.lineWidth = 0.5;
      for (var gx = 0; gx < W; gx += GRID_STEP) {
        ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, H); ctx.stroke();
      }
      for (var gy = 0; gy < H; gy += GRID_STEP) {
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
      }

      /* Partículas */
      for (var pi = 0; pi < particles.length; pi++) {
        var p = particles[pi];
        p.age++;

        /* Trail */
        p.trail.push([p.x, p.y]);
        if (p.trail.length > TRAIL) p.trail.shift();

        /* Muerto → reciclar */
        if (p.age > p.life || p.x < -20 || p.x > W+20 || p.y < -20 || p.y > H+20) {
          particles[pi] = makeParticle(W, H);
          SNAP_FRAMES[pi] = 0;
          continue;
        }

        /* Color por edad: verde → acento */
        var t = p.age / p.life;
        var col = lerpRgb(RGB_VERDE, RGB_ACENTO, t);

        /* Dibujar trail */
        for (var ti = 0; ti < p.trail.length; ti++) {
          var alpha = opPart * (ti+1)/p.trail.length * 0.5;
          ctx.beginPath();
          ctx.arc(p.trail[ti][0], p.trail[ti][1], 1.2, 0, Math.PI*2);
          ctx.fillStyle = rgbArr(col, alpha);
          ctx.fill();
        }

        /* Punto principal */
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.8, 0, Math.PI*2);
        ctx.fillStyle = rgbArr(col, opPart);
        ctx.fill();

        /* Detectar cruce de línea de retícula → micro-snap */
        var snapping = SNAP_FRAMES[pi] > 0;
        if (!snapping) {
          var nx = Math.round(p.x / GRID_STEP) * GRID_STEP;
          var ny = Math.round(p.y / GRID_STEP) * GRID_STEP;
          if (Math.abs(p.x - nx) < p.speed * 2 && Math.abs(p.y - ny) < p.speed * 2) {
            SNAP_FRAMES[pi] = 1; // 1 frame de snap
            p.x += (nx - p.x) * 0.7;
            p.y += (ny - p.y) * 0.7;
            continue;
          }
        } else {
          SNAP_FRAMES[pi] = 0;
        }

        /* Movimiento curl-noise */
        var dir = sampleField(p.x, p.y, W, H);
        p.x += dir[0] * p.speed;
        p.y += dir[1] * p.speed;
      }
    }

    return makeLoop(tick, cv);
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 2 — bucle
     Wiener/Simondon/Kant: retroalimentación.
     Lazo cerrado + punto luminoso que recorre el lazo.
  ════════════════════════════════════════════════════════════════════ */
  function mountBucle(container, opts) {
    var numPuntos  = opts.numPuntos  || 2;
    var periodo    = (opts.periodo   || 7) * 1000; // ms
    var opPath     = opts.opPath     || 0.06;
    var opPunto    = opts.opPunto    || 0.22;
    if (opts.compact) numPuntos = 1;

    var cv  = makeCanvas(container);
    var ctx = cv.getContext('2d');

    /* Precalcular puntos del lazo Bézier (óvalo con cruce) */
    var STEPS = 300;
    var pathPts = null;

    function buildPath(W, H) {
      var cx = W/2, cy = H/2;
      var rx = Math.min(W, H) * 0.28;
      var ry = Math.min(W, H) * 0.18;
      /* Lazo tipo figura-8 aplanada: dos elipses que se cruzan */
      pathPts = [];
      for (var i = 0; i <= STEPS; i++) {
        var a = (i / STEPS) * Math.PI * 2;
        /* Lemniscata de Bernoulli escalada suavemente */
        var denom = 1 + Math.sin(a)*Math.sin(a);
        var x = cx + rx * Math.cos(a) / denom;
        var y = cy + ry * Math.sin(a) * Math.cos(a) / denom;
        pathPts.push([x, y]);
      }
    }

    function getPt(progress) {
      if (!pathPts) return [0,0];
      var idx = ((progress % 1) * STEPS)|0;
      return pathPts[idx];
    }

    /* Pulso: escala en el nodo de cruce */
    var pulseT  = 0;       // progreso en el pulso (0 = sin pulso)
    var pulsing = false;
    var PULSE_DUR = 400;   // ms
    var lastPulseProgress = -1;

    function drawStatic(W, H) {
      if (!pathPts) buildPath(W, H);
      ctx.clearRect(0, 0, W, H);
      ctx.beginPath();
      ctx.moveTo(pathPts[0][0], pathPts[0][1]);
      for (var i = 1; i < pathPts.length; i++) ctx.lineTo(pathPts[i][0], pathPts[i][1]);
      ctx.closePath();
      ctx.strokeStyle = rgba(P.AZUL, opPath);
      ctx.lineWidth = 1;
      ctx.stroke();
      // Punto estático en inicio
      var pt = pathPts[0];
      ctx.beginPath(); ctx.arc(pt[0], pt[1], 3.5, 0, Math.PI*2);
      ctx.fillStyle = rgba(P.AMBER, opPunto);
      ctx.fill();
    }

    if (REDUCED) {
      var d0 = resizeCanvas(cv);
      buildPath(d0.W, d0.H);
      drawStatic(d0.W, d0.H);
      return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } };
    }

    var startTs = null;

    function tick(ts) {
      if (!startTs) startTs = ts;
      var dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      if (!pathPts || pathPts.length === 0) buildPath(W, H);

      ctx.clearRect(0, 0, W, H);

      /* Lazo */
      ctx.beginPath();
      ctx.moveTo(pathPts[0][0], pathPts[0][1]);
      for (var i = 1; i < pathPts.length; i++) ctx.lineTo(pathPts[i][0], pathPts[i][1]);
      ctx.closePath();
      ctx.strokeStyle = rgba(P.AZUL, opPath);
      ctx.lineWidth = 1;
      ctx.stroke();

      /* Puntos */
      for (var p = 0; p < numPuntos; p++) {
        var offset = p / numPuntos;
        var progress = ((ts - startTs) / periodo + offset) % 1;

        /* Detectar cruce (progreso ~0 o ~0.5 = nodo de cruce de la lemniscata) */
        if (Math.abs(progress - 0.5) < 0.008 && Math.abs(lastPulseProgress - progress) > 0.05) {
          pulsing = true;
          pulseT  = ts;
          lastPulseProgress = progress;
        }

        var pt = getPt(progress);
        var scale = 1;
        if (pulsing && p === 0) {
          var pdt = ts - pulseT;
          if (pdt < PULSE_DUR) {
            /* cubic-bezier(.2,.7,.2,1) aproximado */
            var tN = pdt / PULSE_DUR;
            scale = 1 + 0.3 * Math.sin(tN * Math.PI);
          } else {
            pulsing = false;
          }
        }

        var r = 3.5 * scale;
        /* Halo */
        var grad = ctx.createRadialGradient(pt[0], pt[1], 0, pt[0], pt[1], 10 * scale);
        grad.addColorStop(0, rgba(P.AMBER, opPunto));
        grad.addColorStop(1, rgba(P.AMBER, 0));
        ctx.beginPath(); ctx.arc(pt[0], pt[1], 10*scale, 0, Math.PI*2);
        ctx.fillStyle = grad; ctx.fill();

        /* Punto */
        ctx.beginPath(); ctx.arc(pt[0], pt[1], r, 0, Math.PI*2);
        ctx.fillStyle = rgba(P.AMBER, opPunto + 0.04);
        ctx.fill();

        /* Onda concéntrica en el pulso */
        if (pulsing && p === 0) {
          var wdt = ts - pulseT;
          var wt  = wdt / PULSE_DUR;
          var wr  = wt * 22;
          var wa  = opPath * (1 - wt) * 1.8;
          if (wa > 0) {
            ctx.beginPath(); ctx.arc(pt[0], pt[1], wr, 0, Math.PI*2);
            ctx.strokeStyle = rgba(P.AZUL, wa);
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
    }

    return makeLoop(tick, cv);
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 3 — horizonte
     Dreyfus/Heidegger: significatividad contextual.
     Nodos en deriva + líneas que aparecen por proximidad.
  ════════════════════════════════════════════════════════════════════ */
  function mountHorizonte(container, opts) {
    var numNodos   = opts.numNodos   || 20;
    var opNodos    = opts.opNodos    || 0.16;
    var opLineasMax= opts.opLineas   || 0.13;
    var velDrift   = opts.velocidad  || 0.12;
    if (opts.compact) numNodos = Math.max(10, Math.floor(numNodos * 0.6));
    numNodos = Math.min(numNodos, 40);

    var cv  = makeCanvas(container);
    var ctx = cv.getContext('2d');
    var dim = resizeCanvas(cv);

    /* Índice de nodo foco (cambia cada ~5s) */
    var focusIdx = 0;
    var lastFocusChange = 0;
    var FOCUS_INTERVAL = 5000;

    function makeNodo(W, H) {
      var a = Math.random() * Math.PI * 2;
      var s = velDrift * (0.4 + Math.random() * 0.6);
      return {
        x: Math.random() * W,
        y: Math.random() * H,
        vx: Math.cos(a) * s,
        vy: Math.sin(a) * s,
        r: 1.5 + Math.random()
      };
    }

    var nodos = [];
    for (var i = 0; i < numNodos; i++) nodos.push(makeNodo(dim.W, dim.H));

    function drawStatic() {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      var umbral = Math.min(W,H) * 0.22;
      ctx.clearRect(0, 0, W, H);
      for (var a = 0; a < nodos.length; a++) {
        for (var b = a+1; b < nodos.length; b++) {
          var dx = nodos[a].x - nodos[b].x;
          var dy = nodos[a].y - nodos[b].y;
          var dist = Math.sqrt(dx*dx+dy*dy);
          if (dist < umbral) {
            var alpha = opLineasMax * (1 - dist/umbral);
            ctx.beginPath();
            ctx.moveTo(nodos[a].x, nodos[a].y);
            ctx.lineTo(nodos[b].x, nodos[b].y);
            ctx.strokeStyle = rgba(P.AZUL, alpha);
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      for (var ni = 0; ni < nodos.length; ni++) {
        var n = nodos[ni];
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI*2);
        ctx.fillStyle = ni === focusIdx ? rgba(P.ACENTO, opNodos+0.06) : rgba(P.TEXTO, opNodos);
        ctx.fill();
      }
    }

    if (REDUCED) { drawStatic(); return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } }; }

    function tick(ts) {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      var umbral = Math.min(W,H) * 0.22;

      /* Cambiar foco */
      if (ts - lastFocusChange > FOCUS_INTERVAL) {
        focusIdx = (focusIdx + 1 + Math.floor(Math.random()*(nodos.length-1))) % nodos.length;
        lastFocusChange = ts;
      }

      ctx.clearRect(0, 0, W, H);

      /* Líneas */
      for (var a = 0; a < nodos.length; a++) {
        for (var b = a+1; b < nodos.length; b++) {
          var dx = nodos[a].x - nodos[b].x;
          var dy = nodos[a].y - nodos[b].y;
          var dist = Math.sqrt(dx*dx+dy*dy);
          if (dist < umbral) {
            var alpha = opLineasMax * (1 - dist/umbral);
            /* Nodo foco: prioriza conexiones (más brillante) */
            if (a === focusIdx || b === focusIdx) alpha = Math.min(opLineasMax, alpha * 1.4);
            ctx.beginPath();
            ctx.moveTo(nodos[a].x, nodos[a].y);
            ctx.lineTo(nodos[b].x, nodos[b].y);
            ctx.strokeStyle = rgba(P.AZUL, alpha);
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      /* Nodos */
      for (var ni = 0; ni < nodos.length; ni++) {
        var n = nodos[ni];
        var isFocus = ni === focusIdx;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * (isFocus ? 1.5 : 1), 0, Math.PI*2);
        ctx.fillStyle = isFocus ? rgba(P.ACENTO, opNodos+0.06) : rgba(P.TEXTO, opNodos);
        ctx.fill();

        /* Movimiento browniano amortiguado */
        /* Amortiguado: pequeña perturbación aleatoria por frame */
        n.vx += (Math.random()-0.5) * 0.01;
        n.vy += (Math.random()-0.5) * 0.01;
        /* Límite de velocidad */
        var spd = Math.sqrt(n.vx*n.vx + n.vy*n.vy);
        var maxSpd = velDrift * 1.2;
        if (spd > maxSpd) { n.vx *= maxSpd/spd; n.vy *= maxSpd/spd; }
        n.x += n.vx;
        n.y += n.vy;

        /* Rebote en bordes */
        if (n.x < 0) { n.x = 0; n.vx *= -1; }
        else if (n.x > W) { n.x = W; n.vx *= -1; }
        if (n.y < 0) { n.y = 0; n.vy *= -1; }
        else if (n.y > H) { n.y = H; n.vy *= -1; }
      }
    }

    return makeLoop(tick, cv);
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 4 — pulso_datos
     Datos discretos latiendo en el perímetro.
     Franja de ticks cuantizados con onda de luz.
  ════════════════════════════════════════════════════════════════════ */
  function mountPulsoDatos(container, opts) {
    var pistas      = opts.pistas    || 4;
    var periodo     = (opts.periodo  || 5) * 1000; // ms
    var opBase      = opts.opBase    || 0.07;
    var opPico      = opts.opPico    || 0.18;
    var altoFranja  = opts.alto      || 0.10; // fracción de la altura contenedor
    var ticks       = opts.ticks     || 32;
    if (opts.compact) { pistas = Math.max(2, pistas-1); ticks = Math.max(20, ticks-8); }

    /* Canvas anclado sólo a la franja inferior */
    var cv = document.createElement('canvas');
    cv.style.cssText = 'position:absolute;left:0;bottom:0;width:100%;pointer-events:none;display:block;';
    container.appendChild(cv);

    var ctx = cv.getContext('2d');

    function sizeFranja() {
      var dpr = window.devicePixelRatio || 1;
      var W = container.clientWidth  || 800;
      var Hc= container.clientHeight || 600;
      var H = Math.round(Hc * altoFranja);
      if (cv.width !== W*dpr || cv.height !== H*dpr) {
        cv.width  = W * dpr;
        cv.height = H * dpr;
        cv.style.height = H + 'px';
        ctx.setTransform(1,0,0,1,0,0);
        ctx.scale(dpr, dpr);
      }
      return { W:W, H:H };
    }

    function drawFrame(progress) {
      var dim = sizeFranja();
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);

      var pistaH = H / (pistas + 1);
      var tickW  = 2;
      var gap    = (W - ticks * tickW) / (ticks + 1);

      /* Posición de la onda: 0..1 → 0..W */
      var waveX = progress * W;

      for (var pi = 0; pi < pistas; pi++) {
        var cy = pistaH * (pi + 1);
        for (var ti = 0; ti < ticks; ti++) {
          var tx = gap + ti * (tickW + gap);
          /* Distancia a la onda (cuantizada — sin interpolación) */
          var distW = Math.abs(tx - waveX);
          var waveR = W * 0.06;
          var inWave = distW < waveR;
          var alpha  = inWave ? opPico : opBase;
          var color  = inWave ? P.VERDE : P.AZUL;

          ctx.fillStyle = rgba(color, alpha);
          /* Altura del tick: cuantizada (3 niveles) */
          var th;
          if (inWave)     th = 3;
          else if (ti % 4 === 0) th = 2;
          else           th = 1;
          ctx.fillRect(tx, cy - th, tickW, th*2);
        }
      }
    }

    if (REDUCED) {
      sizeFranja();
      drawFrame(0.3);
      return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } };
    }

    var startTs = null;

    function tick(ts) {
      if (!startTs) startTs = ts;
      var progress = ((ts - startTs) % periodo) / periodo;
      drawFrame(progress);
    }

    var paused  = false;
    var dead    = false;
    var rafId   = null;

    function onVisible() { paused = document.hidden; }
    document.addEventListener('visibilitychange', onVisible);

    var resObs = null;
    if (typeof ResizeObserver !== 'undefined') {
      resObs = new ResizeObserver(function() { sizeFranja(); });
      resObs.observe(container);
    }

    function frame(ts) {
      if (dead) return;
      rafId = requestAnimationFrame(frame);
      if (paused) return;
      tick(ts);
    }
    rafId = requestAnimationFrame(frame);

    return {
      pause:   function() { paused = true; },
      resume:  function() { paused = false; },
      destroy: function() {
        dead = true;
        if (rafId) cancelAnimationFrame(rafId);
        document.removeEventListener('visibilitychange', onVisible);
        if (resObs) resObs.disconnect();
        if (cv.parentElement) cv.parentElement.removeChild(cv);
      }
    };
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 5 — ascua
     Costos: partículas-brasa que caen y se consumen.
  ════════════════════════════════════════════════════════════════════ */
  function mountAscua(container, opts) {
    var densidad     = opts.densidad || 12; // baja12/media20
    var gravedad     = opts.gravedad || 0.18;
    var viento       = opts.viento   || 0.05;
    var opNac        = opts.opNac    || 0.18;
    var opExt        = 0;
    var vida         = (opts.vida    || 4) * 1000; // ms → frames equiv.
    var zonaDeadW    = opts.zonaDeadW || 0.64; // fracción del ancho reservada al centro
    if (opts.compact) densidad = Math.max(6, Math.floor(densidad * 0.6));
    densidad = Math.min(densidad, 40);

    var cv  = makeCanvas(container);
    var ctx = cv.getContext('2d');

    var RGB_ACENTO = hexToRgb(P.ACENTO);
    var RGB_ROJO   = hexToRgb(P.ROJO);

    function makeAscua(W, H) {
      /* Nace en franja lateral (evita zona muerta central) */
      var deadL = W * (1 - zonaDeadW) / 2;
      var deadR = W - deadL;
      var x;
      if (Math.random() < 0.5) {
        x = Math.random() * deadL;                  // franja izquierda
      } else {
        x = deadR + Math.random() * deadL;           // franja derecha
      }
      return {
        x: x,
        y: -4,
        vx: (Math.random()-0.5) * viento * 4,
        vy: gravedad * (0.5 + Math.random() * 0.8),
        r: 1.5 + Math.random() * 1.5,
        born: null,
        life: vida * (0.8 + Math.random() * 0.4)
      };
    }

    var dim = resizeCanvas(cv);
    var ascuas = [];
    for (var i = 0; i < densidad; i++) {
      var a = makeAscua(dim.W, dim.H);
      a.born = -Math.random() * a.life; // distribuir en el tiempo
      ascuas.push(a);
    }

    function drawStatic() {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);
      for (var ai = 0; ai < ascuas.length; ai++) {
        var asc = ascuas[ai];
        var t = 0.3 + Math.random() * 0.4;
        var col = lerpRgb(RGB_ACENTO, RGB_ROJO, t);
        var op = opNac * (1 - t * 0.6);
        ctx.beginPath(); ctx.arc(asc.x, asc.y > 0 ? asc.y : H*0.2, asc.r, 0, Math.PI*2);
        ctx.fillStyle = rgbArr(col, op);
        ctx.fill();
      }
    }

    if (REDUCED) { drawStatic(); return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } }; }

    function tick(ts) {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);

      for (var ai = 0; ai < ascuas.length; ai++) {
        var asc = ascuas[ai];
        if (asc.born === null) asc.born = ts;
        var age = ts - asc.born;

        /* Reciclar */
        if (age > asc.life || asc.y > H * 0.8) {
          var nu = makeAscua(W, H);
          nu.born = ts;
          ascuas[ai] = nu;
          continue;
        }

        /* Progreso 0..1 */
        var t = age / asc.life;
        /* Se extingue al 60% de altura (muere antes de llegar al centro) */
        var yFrac = asc.y / H;
        var extFrac = Math.min(t, yFrac / 0.6);
        var alpha = opNac * (1 - extFrac);
        if (alpha <= 0.002) { continue; }

        var col = lerpRgb(RGB_ACENTO, RGB_ROJO, extFrac);
        ctx.beginPath(); ctx.arc(asc.x, asc.y, asc.r, 0, Math.PI*2);
        ctx.fillStyle = rgbArr(col, alpha);
        ctx.fill();

        /* Física */
        asc.vx += (Math.random()-0.5) * viento * 0.4;
        asc.vy += gravedad * 0.05;
        asc.x  += asc.vx;
        asc.y  += asc.vy;
      }
    }

    return makeLoop(tick, cv);
  }

  /* ════════════════════════════════════════════════════════════════════
     VARIANTE 6 — deriva
     Ciudad nocturna desde arriba: luces que derivan lentamente.
  ════════════════════════════════════════════════════════════════════ */
  function mountDeriva(container, opts) {
    var numLuces   = opts.numLuces  || 45;
    var velDeriva  = opts.velocidad || 0.08;  // px/frame
    var opLuces    = opts.opLuces   || 0.11;
    var opAvenidas = opts.opAvenidas|| 0.16;
    var sinAvenidas= opts.sinAvenidas || false;
    if (opts.compact) numLuces = Math.max(20, Math.floor(numLuces * 0.6));
    numLuces = Math.min(numLuces, 80);

    var cv  = makeCanvas(container);
    var ctx = cv.getContext('2d');
    var dim = resizeCanvas(cv);

    var RGB_AMBER = hexToRgb(P.AMBER);
    var RGB_AZUL  = hexToRgb(P.AZUL);

    /* Dirección de deriva: ligeramente diagonal */
    var dAngle = Math.PI * 0.18;
    var dVx = Math.cos(dAngle) * velDeriva;
    var dVy = Math.sin(dAngle) * velDeriva;

    function makeLuz(W, H, forcePos) {
      var x = forcePos ? forcePos[0] : Math.random() * W;
      var y = forcePos ? forcePos[1] : Math.random() * H;
      /* 5-10% parpadean */
      var blink = Math.random() < 0.08;
      /* Mayoría ámbar, minoría azul */
      var isAzul = Math.random() < 0.22;
      /* ¿Es avenida? (algo más brillante) */
      var isAvenida = false;
      return {
        x: x, y: y,
        r: 0.8 + Math.random() * 1.2,
        blink: blink,
        blinkPhase: Math.random() * Math.PI * 2,
        blinkPeriod: 3000 + Math.random() * 4000,
        isAzul: isAzul,
        isAvenida: isAvenida,
        op: opLuces
      };
    }

    var luces = [];
    /* Distribuir incluyendo ~2 "avenidas" (bandas más brillantes) */
    var avenidaYs = [0.32, 0.68];

    for (var i = 0; i < numLuces; i++) {
      var l = makeLuz(dim.W, dim.H);
      /* Si cae cerca de una avenida, hacerla brillante */
      if (!sinAvenidas) {
        for (var ai = 0; ai < avenidaYs.length; ai++) {
          var ayFrac = avenidaYs[ai];
          if (Math.abs(l.y / dim.H - ayFrac) < 0.06) {
            l.isAvenida = true;
            l.op = opAvenidas;
          }
        }
      }
      luces.push(l);
    }

    function drawStatic() {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);
      for (var li = 0; li < luces.length; li++) {
        var l = luces[li];
        var col = l.isAzul ? P.AZUL : P.AMBER;
        ctx.beginPath(); ctx.arc(l.x, l.y, l.r, 0, Math.PI*2);
        ctx.fillStyle = rgba(col, l.op);
        ctx.fill();
      }
    }

    if (REDUCED) { drawStatic(); return { pause:function(){}, resume:function(){}, destroy:function(){ if(cv.parentElement) cv.parentElement.removeChild(cv); } }; }

    function tick(ts) {
      dim = resizeCanvas(cv);
      var W = dim.W, H = dim.H;
      ctx.clearRect(0, 0, W, H);

      for (var li = 0; li < luces.length; li++) {
        var l = luces[li];

        /* Deriva */
        l.x += dVx;
        l.y += dVy;

        /* Reciclar cuando sale del borde */
        if (l.x > W + 20 || l.y > H + 20 || l.x < -20 || l.y < -20) {
          /* Reciclar en el borde opuesto */
          if (l.x > W + 20) l.x -= W + 40;
          if (l.y > H + 20) l.y -= H + 40;
          if (l.x < -20)    l.x += W + 40;
          if (l.y < -20)    l.y += H + 40;
        }

        /* Parpadeo */
        var op = l.op;
        if (l.blink) {
          var sin = Math.sin(ts / l.blinkPeriod * Math.PI * 2 + l.blinkPhase);
          op = l.op * (0.5 + 0.5 * (sin * 0.5 + 0.5));
        }

        var col = l.isAzul ? P.AZUL : P.AMBER;
        ctx.beginPath(); ctx.arc(l.x, l.y, l.r, 0, Math.PI*2);
        ctx.fillStyle = rgba(col, op);
        ctx.fill();
      }
    }

    return makeLoop(tick, cv);
  }

  /* ════════════════════════════════════════════════════════════════════
     MOUNT PRINCIPAL — despachador
  ════════════════════════════════════════════════════════════════════ */
  function mount(container, opts) {
    opts = opts || {};
    var variante = opts.variante || '';

    /* Asegurar position:relative en el contenedor */
    var pos = window.getComputedStyle(container).position;
    if (pos === 'static') container.style.position = 'relative';

    switch (variante) {
      case 'flujo_vital':  return mountFlujoVital(container, opts);
      case 'bucle':        return mountBucle(container, opts);
      case 'horizonte':    return mountHorizonte(container, opts);
      case 'pulso_datos':  return mountPulsoDatos(container, opts);
      case 'ascua':        return mountAscua(container, opts);
      case 'deriva':       return mountDeriva(container, opts);
      default:
        console.warn('[ambient.js] variante desconocida:', variante);
        return { pause:function(){}, resume:function(){}, destroy:function(){} };
    }
  }

  /* ── Registro global ──────────────────────────────────────────────────── */
  window.AMBIENT = { mount: mount };

}());
