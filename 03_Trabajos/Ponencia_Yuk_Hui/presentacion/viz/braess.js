/* braess.js — Visualización animada de la Paradoja de Braess
 * Registro global: window.VIZ['braess']
 * Contrato: mount(container, opts?) → { pause, resume, destroy }
 * Sin dependencias externas. Canvas propio con DPR correcto.
 */

window.VIZ = window.VIZ || {};

window.VIZ['braess'] = (function () {

  /* ─────────────────────────────────────────────────────────────────────
     PALETA Y CONSTANTES DE DISEÑO
  ───────────────────────────────────────────────────────────────────── */
  var PAL = {
    bg:       '#0e1a2b',
    text:     '#e8e6e1',
    amber:    '#e0a458',
    amberDim: '#a06820',
    blue:     '#5ba3d9',
    blueDim:  '#2d5580',
    green:    '#6bcf7f',
    red:      '#e05858',
    dim:      '#3a4e66',
    dimEdge:  '#1e3045',
  };

  /* ─────────────────────────────────────────────────────────────────────
     ESTILOS DEL PANEL OVERLAY (inyectados una sola vez)
  ───────────────────────────────────────────────────────────────────── */
  var PANEL_STYLE_ID = '__braess_panel_style__';
  function injectStyles() {
    if (document.getElementById(PANEL_STYLE_ID)) return;
    var s = document.createElement('style');
    s.id = PANEL_STYLE_ID;
    s.textContent = [
      '.__braess_overlay{position:fixed;inset:0;z-index:9000;display:flex;align-items:center;justify-content:center;background:rgba(14,26,43,0.88);backdrop-filter:blur(4px);}',
      '.__braess_panel{background:#0e1a2b;border:1px solid #2d4a6a;border-radius:10px;padding:28px 32px;max-width:620px;width:92%;max-height:88vh;overflow-y:auto;position:relative;color:#e8e6e1;font-family:"SF Mono","Fira Code","Consolas",monospace;font-size:13px;line-height:1.7;}',
      '.__braess_panel h2{margin:0 0 18px;font-size:17px;font-weight:700;color:#e0a458;letter-spacing:.03em;}',
      '.__braess_panel h3{margin:18px 0 6px;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:#5ba3d9;border-bottom:1px solid #1e3045;padding-bottom:4px;}',
      '.__braess_panel .kv{display:flex;justify-content:space-between;padding:3px 0;}',
      '.__braess_panel .kv .k{color:#a0b4c8;}',
      '.__braess_panel .kv .v{color:#e8e6e1;font-weight:600;}',
      '.__braess_panel .kv .v.hi{color:#e0a458;}',
      '.__braess_panel .kv .v.ok{color:#6bcf7f;}',
      '.__braess_panel .kv .v.err{color:#e05858;}',
      '.__braess_panel .sujeto-row{display:flex;align-items:center;gap:10px;padding:4px 0;border-bottom:1px solid #14263a;}',
      '.__braess_panel .sujeto-row:last-child{border-bottom:none;}',
      '.__braess_panel .sujeto-name{flex:0 0 130px;color:#a0b4c8;}',
      '.__braess_panel .pip{width:11px;height:11px;border-radius:50%;flex-shrink:0;}',
      '.__braess_panel .pip.ok{background:#6bcf7f;}',
      '.__braess_panel .pip.err{background:#e05858;}',
      '.__braess_panel .pip.warn{background:#e0a458;}',
      '.__braess_panel .nota{font-size:11px;color:#6a8099;margin-top:14px;border-top:1px solid #1e3045;padding-top:10px;}',
      '.__braess_close{position:absolute;top:14px;right:16px;background:none;border:none;color:#6a8099;font-size:20px;cursor:pointer;line-height:1;padding:2px 6px;}',
      '.__braess_close:hover{color:#e8e6e1;}',
    ].join('\n');
    document.head.appendChild(s);
  }

  /* ─────────────────────────────────────────────────────────────────────
     EASING
  ───────────────────────────────────────────────────────────────────── */
  function easeInOut(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }
  function easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }
  function clamp(x, lo, hi) {
    return x < lo ? lo : x > hi ? hi : x;
  }

  /* ─────────────────────────────────────────────────────────────────────
     LÓGICA PRINCIPAL: mount
  ───────────────────────────────────────────────────────────────────── */
  function mount(container, opts) {
    opts = opts || {};

    /* Prefers-reduced-motion → fallback estático */
    var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* Canvas */
    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'display:block;width:100%;height:100%;cursor:pointer;';
    container.style.position = container.style.position || 'relative';
    container.appendChild(canvas);

    var dpr = window.devicePixelRatio || 1;
    var W = 0, H = 0; // lógicos
    function resize() {
      var rect = container.getBoundingClientRect();
      W = rect.width  || 1200;
      H = rect.height || 800;
      canvas.width  = Math.round(W * dpr);
      canvas.height = Math.round(H * dpr);
    }
    resize();

    var ctx = canvas.getContext('2d');

    /* ── Estado de animación ─────────────────────────────────────── */
    var DATA = null;       // cargado por fetch
    var paused = false;
    var destroyed = false;
    var rafId = null;

    /* Fases del loop perpetuo:
       0 = FASE1 flujo estable (duración ~3 s)
       1 = TRANSICIÓN: atajo se ilumina (1 s)
       2 = FASE2 migración a R3 + congestión (3 s)
       3 = PAUSA en tiempo=80 (1.5 s)
       4 = FADE OUT atajo + reset (1 s)
    */
    var PHASE_DUR = [3000, 1000, 3000, 1500, 1000]; // ms
    var phase = 0;
    var phaseT = 0;    // tiempo dentro de la fase [0..1]
    var lastTs = null;

    /* Partículas */
    var particles = [];
    var NPART = opts.compact ? 18 : 32; // densidad calibrada

    /* ── Geometría de la red ──────────────────────────────────────── */
    function layout() {
      /* Nodos: Origen (I), A, B, Destino (Fin) */
      var cx = W * 0.5, cy = H * 0.5;
      var rw = W * 0.32, rh = H * 0.22;
      return {
        I:   { x: cx - rw, y: cy },
        A:   { x: cx,      y: cy - rh },
        B:   { x: cx,      y: cy + rh },
        Fin: { x: cx + rw, y: cy },
      };
    }

    /* ── Partícula ────────────────────────────────────────────────── */
    function Particle(route) {
      this.route = route;   // 'R1'|'R2'|'R3'
      this.t = Math.random(); // progresión [0,1] a lo largo de la ruta
      this.speed = 0;
      this.alpha = 1;
      this.size = opts.compact ? 2.5 : 3.2;
    }

    /* Devuelve la posición interpolada a lo largo de la ruta */
    Particle.prototype.pos = function (nodes, shortcutVisible) {
      var I = nodes.I, A = nodes.A, B = nodes.B, F = nodes.Fin;
      var t = this.t;
      if (this.route === 'R1') {
        /* I -> A -> Fin  (dos segmentos iguales) */
        if (t < 0.5) {
          var u = t * 2;
          return { x: I.x + (A.x - I.x) * u, y: I.y + (A.y - I.y) * u };
        } else {
          var u = (t - 0.5) * 2;
          return { x: A.x + (F.x - A.x) * u, y: A.y + (F.y - A.y) * u };
        }
      } else if (this.route === 'R2') {
        /* I -> B -> Fin */
        if (t < 0.5) {
          var u = t * 2;
          return { x: I.x + (B.x - I.x) * u, y: I.y + (B.y - I.y) * u };
        } else {
          var u = (t - 0.5) * 2;
          return { x: B.x + (F.x - B.x) * u, y: B.y + (F.y - B.y) * u };
        }
      } else {
        /* R3: I -> A -> B -> Fin  (tres segmentos iguales) */
        if (t < 1/3) {
          var u = t * 3;
          return { x: I.x + (A.x - I.x) * u, y: I.y + (A.y - I.y) * u };
        } else if (t < 2/3) {
          var u = (t - 1/3) * 3;
          return { x: A.x + (B.x - A.x) * u, y: A.y + (B.y - A.y) * u };
        } else {
          var u = (t - 2/3) * 3;
          return { x: B.x + (F.x - B.x) * u, y: B.y + (F.y - B.y) * u };
        }
      }
    };

    /* ── Inicializa partículas para FASE1 ─────────────────────────── */
    function initParticles_phase1() {
      particles = [];
      var half = Math.floor(NPART / 2);
      for (var i = 0; i < NPART; i++) {
        var p = new Particle(i < half ? 'R1' : 'R2');
        /* velocidad base: inversa al tiempo de tramo 65 → normalizar a ~0.18 */
        p.speed = 0.14 + Math.random() * 0.06;
        p.alpha = 1;
        particles.push(p);
      }
    }

    /* ── Inicializa partículas para FASE2 (todas a R3, más lentas) ── */
    function initParticles_phase2() {
      particles = [];
      /* Tiempo de tramo en FASE2 es 80: velocidad ~ 1/80 → más lento */
      var speedFactor = 65 / 80; // ~ 0.81× respecto a fase1
      for (var i = 0; i < NPART; i++) {
        var p = new Particle('R3');
        p.speed = (0.14 + Math.random() * 0.06) * speedFactor;
        p.alpha = 1;
        particles.push(p);
      }
    }

    /* ── RENDER ───────────────────────────────────────────────────── */
    function draw(ts) {
      if (!lastTs) lastTs = ts;
      var dt = Math.min(ts - lastTs, 50); // cap a 50 ms para no saltar
      lastTs = ts;

      if (!paused && DATA) {
        /* Avanza fase */
        phaseT += dt / PHASE_DUR[phase];
        if (phaseT >= 1) {
          phaseT = 0;
          phase = (phase + 1) % 5;
          /* Al entrar en FASE1: reiniciar partículas R1/R2 */
          if (phase === 0) initParticles_phase1();
          /* Al entrar en FASE2: convertir a R3 */
          if (phase === 2) initParticles_phase2();
        }

        /* Mueve partículas */
        var et = easeInOut(phaseT);
        for (var i = 0; i < particles.length; i++) {
          var p = particles[i];
          /* Durante TRANSICIÓN (phase=1): partículas R1/R2 van acabando
             y su alpha baja; en phase=4 también */
          if (phase === 1) {
            p.t += p.speed * (dt / 1000) * (1 - et * 0.5);
          } else if (phase === 4) {
            p.t += p.speed * (dt / 1000) * 0.5;
            p.alpha = Math.max(0, p.alpha - dt / 800);
          } else {
            p.t += p.speed * (dt / 1000);
          }
          if (p.t > 1) p.t -= 1;
        }
      }

      /* ── Canvas clear ─── */
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = PAL.bg;
      ctx.fillRect(0, 0, W, H);

      if (!DATA) {
        /* Loading */
        ctx.fillStyle = PAL.text;
        ctx.font = '14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('cargando datos…', W / 2, H / 2);
        ctx.restore();
        return;
      }

      var nodes = layout();

      /* ── Atajo visibilidad ───────────────────────────────────────── */
      /* shortcutAlpha: cuánto se ve el atajo A->B */
      var shortcutAlpha = 0;
      if (phase === 0) shortcutAlpha = 0;
      else if (phase === 1) shortcutAlpha = easeOut(phaseT);
      else if (phase === 2 || phase === 3) shortcutAlpha = 1;
      else if (phase === 4) shortcutAlpha = 1 - easeInOut(phaseT);

      /* ── Tiempo mostrado en el contador ─────────────────────────── */
      var displayTime;
      if (phase === 0) {
        displayTime = 65;
      } else if (phase === 1) {
        /* sube suavemente de 65 → 80 durante la transición */
        displayTime = 65 + 15 * easeInOut(phaseT);
      } else if (phase === 2) {
        displayTime = 65 + 15 * easeInOut(phaseT);
      } else if (phase === 3) {
        displayTime = 80;
      } else {
        /* phase 4: baja de 80 → 65 */
        displayTime = 80 - 15 * easeInOut(phaseT);
      }

      /* ── Dibujo de aristas ───────────────────────────────────────── */
      var edgeWidth = opts.compact ? 1.5 : 2;

      function drawEdge(from, to, color, alpha, width, dashed) {
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = color;
        ctx.lineWidth = width || edgeWidth;
        if (dashed) ctx.setLineDash([6, 6]);
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
        ctx.restore();
      }

      /* Congestión: en FASE2/3 los tramos I->A y B->Fin se saturan */
      var congestionA = 0; // I->A
      var congestionB = 0; // B->Fin
      if (phase === 2) {
        congestionA = easeOut(phaseT);
        congestionB = easeOut(phaseT);
      } else if (phase === 3) {
        congestionA = congestionB = 1;
      } else if (phase === 4) {
        congestionA = congestionB = 1 - easeInOut(phaseT);
      }

      /* Saturación visual: línea más gruesa + color */
      var edgeColorIA  = lerp_color(PAL.blue, PAL.red, congestionA);
      var edgeColorBFin = lerp_color(PAL.blue, PAL.red, congestionB);
      /* En FASE1 R1 (I->A) y R2 (B->Fin) son las congestionadas */
      /* En FASE2 cambia: I->A en R3 se congestiona, B->Fin también */

      /* Aristas base (R1 y R2) */
      var r1alpha = 1, r2alpha = 1;
      if (phase === 2 || phase === 3) { r1alpha = 0.18; r2alpha = 0.18; }
      if (phase === 4) { r1alpha = r2alpha = 0.18 + 0.82 * easeInOut(phaseT); }

      /* R1: I->A y A->Fin */
      drawEdge(nodes.I, nodes.A, edgeColorIA,  r1alpha, edgeWidth + congestionA * 2);
      drawEdge(nodes.A, nodes.Fin, PAL.blue,   r1alpha, edgeWidth);
      /* R2: I->B y B->Fin */
      drawEdge(nodes.I, nodes.B, PAL.blue,      r2alpha, edgeWidth);
      drawEdge(nodes.B, nodes.Fin, edgeColorBFin, r2alpha, edgeWidth + congestionB * 2);

      /* Atajo A->B */
      if (shortcutAlpha > 0.01) {
        var shortcutW = edgeWidth * 1.2;
        /* Glow: sombra ámbar cuando aparece */
        ctx.save();
        ctx.globalAlpha = shortcutAlpha * 0.35;
        ctx.strokeStyle = PAL.amber;
        ctx.lineWidth = shortcutW + 6;
        ctx.shadowColor = PAL.amber;
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.moveTo(nodes.A.x, nodes.A.y);
        ctx.lineTo(nodes.B.x, nodes.B.y);
        ctx.stroke();
        ctx.restore();

        drawEdge(nodes.A, nodes.B, PAL.amber, shortcutAlpha, shortcutW + 1.5);
      }

      /* ── Etiquetas de aristas ─────────────────────────────────────── */
      ctx.font = (opts.compact ? '10px' : '11px') + ' "SF Mono","Fira Code",monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      function edgeLabel(from, to, txt, col, alpha) {
        var mx = (from.x + to.x) / 2, my = (from.y + to.y) / 2;
        /* offset perpendicular */
        var dx = to.x - from.x, dy = to.y - from.y;
        var len = Math.sqrt(dx*dx + dy*dy) || 1;
        var nx = -dy / len, ny = dx / len;
        var off = opts.compact ? 12 : 14;
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = col;
        ctx.fillText(txt, mx + nx * off, my + ny * off);
        ctx.restore();
      }

      edgeLabel(nodes.I, nodes.A, 't=x/100', PAL.text, r1alpha * 0.8);
      edgeLabel(nodes.A, nodes.Fin, 't=45', PAL.text, r1alpha * 0.8);
      edgeLabel(nodes.I, nodes.B, 't=45', PAL.text, r2alpha * 0.8);
      edgeLabel(nodes.B, nodes.Fin, 't=x/100', PAL.text, r2alpha * 0.8);
      if (shortcutAlpha > 0.05) {
        edgeLabel(nodes.A, nodes.B, 't=0', PAL.amber, shortcutAlpha);
      }

      /* ── Nodos ─────────────────────────────────────────────────────── */
      var nodeR = opts.compact ? 20 : 26;
      function drawNode(pos, label, glow) {
        ctx.save();
        if (glow) {
          ctx.shadowColor = PAL.amber;
          ctx.shadowBlur = 12 * glow;
        }
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, nodeR, 0, Math.PI * 2);
        ctx.fillStyle = PAL.bg;
        ctx.fill();
        ctx.strokeStyle = glow ? PAL.amber : PAL.blue;
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = glow ? (0.5 + 0.5 * glow) : 1;
        ctx.stroke();
        ctx.restore();

        ctx.fillStyle = PAL.text;
        ctx.font = (opts.compact ? '12px' : '14px') + ' sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, pos.x, pos.y);
      }

      drawNode(nodes.I,   'O',   0);
      drawNode(nodes.A,   'A',   shortcutAlpha);
      drawNode(nodes.B,   'B',   shortcutAlpha);
      drawNode(nodes.Fin, 'D',   0);

      /* ── Partículas ────────────────────────────────────────────────── */
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var pos = p.pos(nodes, shortcutAlpha > 0.5);
        var col = (p.route === 'R3') ? PAL.amber : PAL.blue;

        ctx.save();
        ctx.globalAlpha = p.alpha;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.shadowColor = col;
        ctx.shadowBlur = 5;
        ctx.fill();
        ctx.restore();
      }

      /* ── Contador de tiempo ────────────────────────────────────────── */
      drawTimer(displayTime);

      /* ── Rótulo de fase ────────────────────────────────────────────── */
      drawPhaseLabel();

      /* ── Instrucción click ─────────────────────────────────────────── */
      drawClickHint();

      ctx.restore(); // dpr scale
    }

    /* ── Contador de tiempo estilo velocímetro ────────────────────── */
    function drawTimer(t) {
      var tw = opts.compact ? 120 : 160;
      var th = opts.compact ? 64 : 86;
      var tx = W - tw - 18, ty = 16;

      /* Fondo */
      ctx.save();
      ctx.fillStyle = 'rgba(14,26,43,0.85)';
      roundRect(ctx, tx, ty, tw, th, 8);
      ctx.fill();
      ctx.strokeStyle = (t > 70) ? PAL.amber : PAL.dim;
      ctx.lineWidth = 1;
      roundRect(ctx, tx, ty, tw, th, 8);
      ctx.stroke();

      /* Etiqueta */
      ctx.fillStyle = PAL.dim;
      ctx.font = (opts.compact ? '9px' : '10px') + ' monospace';
      ctx.textAlign = 'center';
      ctx.fillText('TIEMPO DE VIAJE', tx + tw / 2, ty + (opts.compact ? 14 : 18));

      /* Número */
      var numSize = opts.compact ? 28 : 38;
      ctx.font = 'bold ' + numSize + 'px "SF Mono","Fira Code",monospace';
      ctx.fillStyle = t > 70 ? PAL.amber : PAL.green;
      ctx.textAlign = 'center';
      ctx.fillText(t.toFixed(1), tx + tw / 2, ty + (opts.compact ? 42 : 56));

      /* Unidad */
      ctx.fillStyle = PAL.dim;
      ctx.font = (opts.compact ? '9px' : '10px') + ' monospace';
      ctx.fillText('min · N=4000', tx + tw / 2, ty + (opts.compact ? 56 : 74));

      ctx.restore();
    }

    /* ── Rótulo de la fase actual ─────────────────────────────────── */
    function drawPhaseLabel() {
      var labels = [
        '• Sin atajo — equilibrio estable',
        '▶ Nuevo atajo A→B disponible…',
        '⚠ Migración egoísta en curso',
        '✕ Paradoja: +15 min para todos',
        '↺ Reseteando…'
      ];
      var colors = [PAL.green, PAL.amber, PAL.amber, PAL.red, PAL.dim];

      ctx.save();
      ctx.font = (opts.compact ? '11px' : '13px') + ' monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = colors[phase];
      ctx.fillText(labels[phase], 16, H - 16);
      ctx.restore();
    }

    /* ── Instrucción de click ─────────────────────────────────────── */
    function drawClickHint() {
      ctx.save();
      ctx.font = (opts.compact ? '9px' : '10px') + ' monospace';
      ctx.textAlign = 'right';
      ctx.fillStyle = PAL.dim;
      ctx.fillText('click → panel técnico', W - 14, H - 16);
      ctx.restore();
    }

    /* ── Fallback estático ────────────────────────────────────────── */
    function drawStatic() {
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.fillStyle = PAL.bg;
      ctx.fillRect(0, 0, W, H);

      if (!DATA) {
        ctx.fillStyle = PAL.text;
        ctx.font = '13px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('prefers-reduced-motion: datos no cargados', W/2, H/2);
        ctx.restore();
        return;
      }

      var nodes = layout();

      /* Dos diagramas lado a lado */
      var savedNodes = nodes;
      function drawDiagram(offsetX, label, showShortcut, time, fluxR1, fluxR2, fluxR3) {
        ctx.save();
        ctx.translate(offsetX, 0);

        /* Aristas */
        ctx.strokeStyle = PAL.blue;
        ctx.lineWidth = 1.5;
        function seg(a, b) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
        seg(nodes.I, nodes.A); seg(nodes.A, nodes.Fin);
        seg(nodes.I, nodes.B); seg(nodes.B, nodes.Fin);
        if (showShortcut) {
          ctx.strokeStyle = PAL.amber;
          ctx.lineWidth = 2;
          seg(nodes.A, nodes.B);
        }

        /* Flujos */
        function fluxLabel(from, to, val) {
          var mx = (from.x + to.x)/2, my = (from.y + to.y)/2;
          ctx.fillStyle = PAL.text;
          ctx.font = '11px monospace';
          ctx.textAlign = 'center';
          ctx.fillText('x=' + val, mx, my - 6);
        }
        fluxLabel(nodes.I, nodes.A, fluxR1);
        fluxLabel(nodes.A, nodes.Fin, fluxR1);
        fluxLabel(nodes.I, nodes.B, fluxR2);
        fluxLabel(nodes.B, nodes.Fin, fluxR2);

        /* Nodos */
        function nd(p, l) {
          ctx.beginPath(); ctx.arc(p.x, p.y, 22, 0, Math.PI*2);
          ctx.fillStyle = PAL.bg; ctx.fill();
          ctx.strokeStyle = PAL.blue; ctx.lineWidth=1.5; ctx.stroke();
          ctx.fillStyle = PAL.text; ctx.font='13px sans-serif';
          ctx.textAlign='center'; ctx.textBaseline='middle';
          ctx.fillText(l, p.x, p.y);
        }
        nd(nodes.I,'O'); nd(nodes.A,'A'); nd(nodes.B,'B'); nd(nodes.Fin,'D');

        /* Título + tiempo */
        ctx.fillStyle = PAL.text;
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(label, nodes.I.x + (nodes.Fin.x - nodes.I.x)/2, nodes.I.y - 60);

        ctx.font = 'bold 28px monospace';
        ctx.fillStyle = showShortcut ? PAL.amber : PAL.green;
        ctx.fillText(time + ' min', nodes.I.x + (nodes.Fin.x - nodes.I.x)/2, nodes.I.y + 60);

        ctx.restore();
      }

      var shiftX = W * 0.02;
      drawDiagram(-shiftX, 'Sin atajo', false, '65', 2000, 2000, 0);
      drawDiagram(shiftX,  'Con atajo A→B', true, '80', 0, 0, 4000);

      /* Barra comparativa */
      var bx = W/2 - 80, by = H * 0.82, bw = 160, bh = 28;
      ctx.fillStyle = PAL.green;
      ctx.fillRect(bx, by, bw * 0.6, bh);
      ctx.fillStyle = PAL.amber;
      ctx.fillRect(bx + bw * 0.6, by, bw * 0.4, bh);
      ctx.fillStyle = PAL.text;
      ctx.font = '11px monospace'; ctx.textAlign = 'center';
      ctx.fillText('65 vs 80 — Δ = +15', W/2, by - 8);

      ctx.restore();
    }

    /* ── Loop de animación ────────────────────────────────────────── */
    function loop(ts) {
      if (destroyed) return;
      draw(ts);
      rafId = requestAnimationFrame(loop);
    }

    /* ── IntersectionObserver (pausa cuando fuera de viewport) ─────── */
    var io = null;
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { if (paused) resume(); }
          else { if (!paused) pause(); }
        });
      }, { threshold: 0.1 });
      io.observe(container);
    }

    /* document.hidden */
    function onVisibility() {
      if (document.hidden) pause(); else resume();
    }
    document.addEventListener('visibilitychange', onVisibility);

    /* ── Resize observer ─────────────────────────────────────────── */
    var ro = null;
    if ('ResizeObserver' in window) {
      ro = new ResizeObserver(function () { resize(); });
      ro.observe(container);
    }

    /* ── Carga de datos ──────────────────────────────────────────── */
    /* Ruta relativa desde viz/braess.js hacia datos/braess.json;
       el fetch se hace desde el contexto del documento, así que
       usamos una ruta relativa al script si es posible o detectamos. */
    function dataUrl() {
      /* Intenta ubicar el script actual para inferir la ruta base */
      var scripts = document.querySelectorAll('script[src]');
      for (var i = 0; i < scripts.length; i++) {
        var src = scripts[i].src;
        if (src.indexOf('braess.js') !== -1) {
          return src.replace('viz/braess.js', 'datos/braess.json');
        }
      }
      /* Fallback: relativo al documento */
      return 'datos/braess.json';
    }

    fetch(dataUrl())
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (d) {
        DATA = d;
        initParticles_phase1();
      })
      .catch(function (e) {
        console.warn('[braess.js] fetch error:', e);
        /* Continúa con datos mínimos hard-coded como fallback */
        DATA = {
          titulo_corto: 'Abrir una via empeora el trafico de todos',
          parametros: { N: 4000, capacidad: 100, t_fijo: 45 },
          equilibrio_sin_atajo: { flujo_R1: 2000, flujo_R2: 2000, tiempo: 65, wardrop_ok: true },
          equilibrio_con_atajo: { flujo_R3: 4000, flujo_R1: 0, flujo_R2: 0, tiempo: 80 },
          validacion: { delta_tiempo: 15, paradoja_confirmada: true },
          rendimiento_ia: {},
          costos: {}
        };
        initParticles_phase1();
      });

    /* ── Arranca ─────────────────────────────────────────────────── */
    if (prefersReduced) {
      /* Fallback: render estático único (no anima) */
      fetch(dataUrl()).then(function(r){ return r.json(); }).then(function(d){
        DATA = d;
        ctx.save(); ctx.scale(dpr, dpr);
        drawStatic();
        ctx.restore();
      }).catch(function(){ DATA = {}; drawStatic(); });
      /* No arranca RAF */
    } else {
      rafId = requestAnimationFrame(loop);
    }

    /* ── Panel overlay de datos canónicos ─────────────────────────── */
    injectStyles();
    var overlayEl = null;

    function openPanel() {
      if (overlayEl) return;
      if (!DATA) return;

      var d = DATA;
      var sin = d.equilibrio_sin_atajo || {};
      var con = d.equilibrio_con_atajo || {};
      var val = d.validacion || {};
      var ren = d.rendimiento_ia || {};
      var costos = d.costos || {};

      /* Números computados en JS — nunca hard-coded en el HTML */
      var t_sin = sin.tiempo || 65;
      var t_con = con.tiempo || 80;
      var delta  = val.delta_tiempo || (t_con - t_sin);
      var N      = (d.parametros || {}).N || 4000;

      function kv(k, v, cls) {
        return '<div class="kv"><span class="k">' + k + '</span><span class="v ' + (cls||'') + '">' + v + '</span></div>';
      }

      /* Tabla de rendimiento por sujeto (preguntas n10–n12) */
      var sujetosRows = '';
      var sujetos = Object.keys(ren);
      if (sujetos.length === 0) sujetos = [];
      sujetos.forEach(function(s) {
        var info = ren[s];
        var pqs = info.preguntas || [];
        var pips = pqs.map(function(q) {
          var cls = q.correcto ? 'ok' : (q.veredicto === 'SIN_RESPUESTA*' ? 'warn' : 'err');
          return '<span class="pip ' + cls + '" title="n' + q.n + ' (' + q.tipo + '): ' + (q.correcto?'✓':'✗') + '"></span>';
        }).join('');
        var ex = info.exactitud !== undefined ? (info.exactitud * 100).toFixed(0) + '%' : '?';
        sujetosRows += '<div class="sujeto-row"><span class="sujeto-name">' + s + '</span>' + pips + '<span style="margin-left:auto;color:#a0b4c8">' + ex + '</span></div>';
      });

      /* Costos por vía */
      var costosRows = '';
      var ckeys = Object.keys(costos);
      ckeys.forEach(function(m) {
        var c = costos[m];
        var cval = c.costo_usd;
        var cstr = (typeof cval === 'number') ? ('$' + cval.toFixed(4)) : '—';
        var tipo = c.tipo === 'api' ? ' (API)' : ' (local)';
        costosRows += kv(m + tipo, cstr, c.tipo === 'api' ? 'hi' : '');
      });

      var html = [
        '<button class="__braess_close" id="__braess_close_btn">✕</button>',
        '<h2>Paradoja de Braess · panel técnico</h2>',

        '<h3>Red y parámetros</h3>',
        kv('N viajeros', N),
        kv('t(x) congestionado', 'x / ' + (d.parametros||{}).capacidad),
        kv('t fijo', (d.parametros||{}).t_fijo + ' min'),
        kv('Atajo A→B', 't = 0'),

        '<h3>Equilibrio de Wardrop</h3>',
        kv('Criterio', 'todas las rutas usadas tienen igual tiempo'),
        kv('Sin atajo — flujo R1/R2', sin.flujo_R1 + ' / ' + sin.flujo_R2),
        kv('Sin atajo — tiempo equilibrio', t_sin.toFixed(1) + ' min', 'ok'),
        kv('Wardrop sin atajo ✓', sin.wardrop_ok ? 'verdadero' : 'falso', sin.wardrop_ok ? 'ok' : 'err'),
        kv('Con atajo — flujo R3 (I→A→B→D)', con.flujo_R3),
        kv('Con atajo — tiempo equilibrio', t_con.toFixed(1) + ' min', 'hi'),
        kv('Wardrop con atajo ✓', con.wardrop_activas_ok ? 'verdadero' : 'falso', con.wardrop_activas_ok ? 'ok' : 'err'),

        '<h3>La paradoja</h3>',
        kv('Δ tiempo = ' + t_con + ' − ' + t_sin, '+' + delta.toFixed(1) + ' min', 'hi'),
        kv('Paradoja confirmada', val.paradoja_confirmada ? 'SÍ' : 'NO', val.paradoja_confirmada ? 'hi' : 'err'),
        kv('Referencia', 'Braess 1968 / Wardrop 1952'),

        '<h3>Rendimiento IA (n10–n12, teoría Braess)</h3>',
        '<div style="font-size:10px;color:#6a8099;margin-bottom:6px">● ok &nbsp; ● err &nbsp; ● sin resp.</div>',
        sujetosRows || '<div style="color:#6a8099">sin datos</div>',

        costosRows ? '<h3>Costo por vía</h3>' + costosRows : '',

        '<div class="nota">Equilibrio de usuario de Wardrop: ningún conductor puede mejorar su tiempo cambiando de ruta. La paradoja de Braess demuestra que agregar infraestructura puede empeorar el tiempo de todos los usuarios en equilibrio no-cooperativo.</div>',
        '<div class="nota">Datos computados en JS a partir de <code>datos/braess.json</code>.</div>',
      ].join('');

      overlayEl = document.createElement('div');
      overlayEl.className = '__braess_overlay';
      overlayEl.innerHTML = '<div class="__braess_panel">' + html + '</div>';
      document.body.appendChild(overlayEl);

      function close() {
        if (overlayEl) { overlayEl.remove(); overlayEl = null; }
      }
      document.getElementById('__braess_close_btn').addEventListener('click', close);
      overlayEl.addEventListener('click', function(e) {
        if (e.target === overlayEl) close();
      });
      function onKey(e) {
        if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); }
      }
      document.addEventListener('keydown', onKey);
    }

    canvas.addEventListener('click', openPanel);

    /* ── API pública ─────────────────────────────────────────────── */
    function pause() {
      paused = true;
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    }
    function resume() {
      if (paused && !destroyed && !prefersReduced) {
        paused = false;
        lastTs = null;
        rafId = requestAnimationFrame(loop);
      }
    }
    function destroy() {
      destroyed = true;
      if (rafId) cancelAnimationFrame(rafId);
      if (io) io.disconnect();
      if (ro) ro.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
      canvas.removeEventListener('click', openPanel);
      canvas.remove();
      if (overlayEl) { overlayEl.remove(); overlayEl = null; }
    }

    return { pause: pause, resume: resume, destroy: destroy };
  }

  /* ─────────────────────────────────────────────────────────────────────
     UTILIDADES
  ───────────────────────────────────────────────────────────────────── */
  function lerp_color(a, b, t) {
    /* a y b son strings hex '#rrggbb' */
    function parse(s) {
      var h = s.replace('#','');
      return [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)];
    }
    var ca = parse(a), cb = parse(b);
    var r = Math.round(ca[0] + (cb[0]-ca[0])*t);
    var g = Math.round(ca[1] + (cb[1]-ca[1])*t);
    var bv = Math.round(ca[2] + (cb[2]-ca[2])*t);
    return 'rgb('+r+','+g+','+bv+')';
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  /* ─────────────────────────────────────────────────────────────────────
     REGISTRO
  ───────────────────────────────────────────────────────────────────── */
  return {
    titulo: 'Paradoja de Braess — Abrir una vía empeora el tráfico de todos',
    mount: mount
  };

}());
