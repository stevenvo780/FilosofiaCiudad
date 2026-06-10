(function () {
  /* -----------------------------------------------------------------------
   * PHYSARUM TRANSPORT NETWORK
   * Slime-mould (Physarum polycephalum) agent simulation — Jones algorithm.
   *
   * Each agent: senses pheromone at 3 angles (left/center/right) at a fixed
   * sensor distance, turns toward the strongest signal, steps forward, and
   * deposits pheromone.  The trail map decays and blurs every frame, creating
   * emergent near-optimal transport networks between food nodes.
   *
   * Food nodes = "urban centres" (amber #e0a44e) that continuously emit
   * pheromone.  The self-organising network connecting them mirrors the
   * Tokyo rail experiment (Tero et al., 2010): distributed optimisation
   * without any central planner or AI.
   * --------------------------------------------------------------------- */

  // ── Palette (SPEC.md) ──────────────────────────────────────────────────
  const C_BG      = '#0d1117';
  const C_PANEL   = '#161b26';
  const C_TEXT    = '#e8e6df';
  const C_MUTED   = '#8a93a3';
  const C_FOOD    = '#e0a44e';   // residencial/amber → food nodes
  const C_CYAN    = '#2dd4bf';   // transit/cian → trail highlight
  const C_ACCENT  = '#a78bfa';   // violet accent
  const C_WATER   = '#3b82c4';

  // ── Simulation parameters (can be overridden by controls) ─────────────
  let SENSOR_ANGLE_DEG = 45;   // degrees; user-controlled
  let N_AGENTS         = 4000; // user-controlled

  // Fixed physical constants
  const SENSOR_DIST   = 9;     // px in trail-map space
  const STEP_SIZE     = 1.5;   // px per frame
  const DEPOSIT       = 5.0;   // pheromone deposited per step
  const DECAY         = 0.96;  // per-frame multiplier
  const DIFFUSE_W     = 0.065; // weight for 3×3 diffusion (centre gets 1-8w)
  const FOOD_EMIT     = 80;    // constant emission at food nodes
  const FOOD_RADIUS   = 5;     // trail-space radius for food nodes

  // ── Internal state ──────────────────────────────────────────────────────
  let canvas, ctx, dpr;
  let W, H;                       // CSS / logical dimensions
  let TW, TH;                     // trail-map dimensions (downscaled)
  const TRAIL_SCALE = 2;          // each trail cell = TRAIL_SCALE CSS px

  let trail, trailNext;           // Float32Array
  let agents;                     // Float32Array[5*N]: x,y,angle,_,_
  let foodNodes = [];             // [{tx,ty}]  (trail-map coords)

  let running = true;
  let rafId   = null;
  let resizeObs = null;

  // ── Slider references (kept for rebinding after remount) ───────────────
  let sliderAngle, sliderPop;

  // ── Helpers ────────────────────────────────────────────────────────────
  function trailIdx(x, y) {
    const tx = (x + 0.5) | 0;
    const ty = (y + 0.5) | 0;
    if (tx < 0 || tx >= TW || ty < 0 || ty >= TH) return -1;
    return ty * TW + tx;
  }

  function senseAt(cx, cy, angle) {
    const sx = cx + Math.cos(angle) * SENSOR_DIST;
    const sy = cy + Math.sin(angle) * SENSOR_DIST;
    const i  = trailIdx(sx, sy);
    return i < 0 ? 0 : trail[i];
  }

  // ── Initialise / reset simulation data ────────────────────────────────
  function initSim() {
    TW = Math.ceil(W / TRAIL_SCALE);
    TH = Math.ceil(H / TRAIL_SCALE);

    trail     = new Float32Array(TW * TH);
    trailNext = new Float32Array(TW * TH);

    // Place food nodes (urban centres) in a rough ring + centre pattern
    foodNodes = makeFoodNodes();

    // Seed agents randomly in the whole canvas
    const n = N_AGENTS;
    agents = new Float32Array(n * 4); // x, y, angle, _pad
    for (let i = 0; i < n; i++) {
      agents[i * 4 + 0] = Math.random() * TW;
      agents[i * 4 + 1] = Math.random() * TH;
      agents[i * 4 + 2] = Math.random() * Math.PI * 2;
    }
  }

  function makeFoodNodes() {
    // One centre node + ring of 6–8, scaled to trail-map
    const nodes = [];
    const cx = TW * 0.5;
    const cy = TH * 0.5;
    const rx = TW * 0.35;
    const ry = TH * 0.35;
    const count = 8;
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2 - Math.PI * 0.25;
      nodes.push({ tx: cx + Math.cos(a) * rx, ty: cy + Math.sin(a) * ry });
    }
    // Add a few inner nodes for denser topology
    const rxi = TW * 0.18;
    const ryi = TH * 0.18;
    const inner = 4;
    for (let i = 0; i < inner; i++) {
      const a = (i / inner) * Math.PI * 2;
      nodes.push({ tx: cx + Math.cos(a) * rxi, ty: cy + Math.sin(a) * ryi });
    }
    return nodes;
  }

  // ── Simulation step ────────────────────────────────────────────────────
  function stepSim() {
    const SA = SENSOR_ANGLE_DEG * (Math.PI / 180);
    const n  = N_AGENTS;

    // 1. Move & deposit agents
    for (let i = 0; i < n; i++) {
      const base = i * 4;
      let ax    = agents[base];
      let ay    = agents[base + 1];
      let angle = agents[base + 2];

      // Sense left / centre / right
      const fwd   = senseAt(ax, ay, angle);
      const left  = senseAt(ax, ay, angle - SA);
      const right = senseAt(ax, ay, angle + SA);

      // Steer
      if (fwd >= left && fwd >= right) {
        // keep direction
      } else if (left > right) {
        angle -= SA * (0.5 + Math.random() * 0.5);
      } else if (right > left) {
        angle += SA * (0.5 + Math.random() * 0.5);
      } else {
        // tied — random jitter
        angle += (Math.random() - 0.5) * SA;
      }

      // Move
      ax += Math.cos(angle) * STEP_SIZE;
      ay += Math.sin(angle) * STEP_SIZE;

      // Wrap (torus)
      if (ax < 0)   ax += TW;
      if (ax >= TW) ax -= TW;
      if (ay < 0)   ay += TH;
      if (ay >= TH) ay -= TH;

      // Deposit
      const di = trailIdx(ax, ay);
      if (di >= 0) trail[di] += DEPOSIT;

      agents[base]     = ax;
      agents[base + 1] = ay;
      agents[base + 2] = angle;
    }

    // 2. Food nodes emit
    for (const f of foodNodes) {
      const fx = f.tx | 0;
      const fy = f.ty | 0;
      for (let dy = -FOOD_RADIUS; dy <= FOOD_RADIUS; dy++) {
        for (let dx = -FOOD_RADIUS; dx <= FOOD_RADIUS; dx++) {
          if (dx * dx + dy * dy > FOOD_RADIUS * FOOD_RADIUS) continue;
          const nx = (fx + dx + TW) % TW;
          const ny = (fy + dy + TH) % TH;
          trail[ny * TW + nx] = Math.min(trail[ny * TW + nx] + FOOD_EMIT, 255);
        }
      }
    }

    // 3. Diffuse + decay into trailNext
    const w  = DIFFUSE_W;
    const wc = 1 - 8 * w;
    for (let y = 0; y < TH; y++) {
      for (let x = 0; x < TW; x++) {
        let sum = trail[y * TW + x] * wc;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (dx === 0 && dy === 0) continue;
            const nx = (x + dx + TW) % TW;
            const ny = (y + dy + TH) % TH;
            sum += trail[ny * TW + nx] * w;
          }
        }
        trailNext[y * TW + x] = sum * DECAY;
      }
    }

    // Swap buffers
    const tmp = trail; trail = trailNext; trailNext = tmp;
  }

  // ── Render ─────────────────────────────────────────────────────────────
  function render() {
    // Build ImageData from trail
    const cssW = TW * TRAIL_SCALE;
    const cssH = TH * TRAIL_SCALE;

    // Draw trail into offscreen ImageData (upscaled from trail map)
    const imgData = ctx.createImageData(TW, TH);
    const px = imgData.data;

    for (let i = 0; i < TW * TH; i++) {
      const v = trail[i];
      // Normalise to [0,1] — trail maxes ~255
      const t = Math.min(v / 140, 1);

      // Colour gradient: dark → deep teal → cyan
      // t=0 → #0d1117, t=0.5 → #0d4040, t=1 → #2dd4bf
      const r = (t < 0.5)
        ? Math.round(0x0d + (0x0d - 0x0d) * (t * 2))
        : Math.round(0x0d + (0x2d - 0x0d) * ((t - 0.5) * 2));
      const g = (t < 0.5)
        ? Math.round(0x11 + (0x40 - 0x11) * (t * 2))
        : Math.round(0x40 + (0xd4 - 0x40) * ((t - 0.5) * 2));
      const b = (t < 0.5)
        ? Math.round(0x17 + (0x40 - 0x17) * (t * 2))
        : Math.round(0x40 + (0xbf - 0x40) * ((t - 0.5) * 2));

      const p = i * 4;
      px[p]     = r;
      px[p + 1] = g;
      px[p + 2] = b;
      px[p + 3] = 255;
    }

    // Blit trail scaled up to canvas (dpr-adjusted)
    // We use a small offscreen canvas to scale
    if (!render._offscreen || render._offscreen.width !== TW || render._offscreen.height !== TH) {
      render._offscreen = document.createElement('canvas');
    }
    const off = render._offscreen;
    off.width  = TW;
    off.height = TH;
    off.getContext('2d').putImageData(imgData, 0, 0);

    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'low';
    ctx.drawImage(off, 0, 0, W, H);
    ctx.restore();

    // Draw food nodes
    for (const f of foodNodes) {
      const sx = f.tx * TRAIL_SCALE;
      const sy = f.ty * TRAIL_SCALE;
      const r  = 7;

      // Glow
      const grad = ctx.createRadialGradient(sx, sy, 0, sx, sy, r * 2.5);
      grad.addColorStop(0,   C_FOOD + 'cc');
      grad.addColorStop(0.5, C_FOOD + '44');
      grad.addColorStop(1,   'transparent');
      ctx.beginPath();
      ctx.arc(sx, sy, r * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      // Core dot
      ctx.beginPath();
      ctx.arc(sx, sy, r, 0, Math.PI * 2);
      ctx.fillStyle = C_FOOD;
      ctx.fill();
      ctx.strokeStyle = C_TEXT;
      ctx.lineWidth   = 1;
      ctx.stroke();
    }

    // Step counter / readout (top-right)
    ctx.font      = "12px 'Inter', system-ui, sans-serif";
    ctx.fillStyle = C_MUTED;
    ctx.textAlign = 'right';
    ctx.fillText(`${N_AGENTS} agentes · ángulo sensor ${SENSOR_ANGLE_DEG}°`, W - 10, 18);
    ctx.textAlign = 'left';
  }

  // ── Animation loop ──────────────────────────────────────────────────────
  function loop() {
    if (running) {
      stepSim();
    }
    render();
    rafId = requestAnimationFrame(loop);
  }

  // ── Build DOM ───────────────────────────────────────────────────────────
  function buildDOM(container) {
    // Canvas
    canvas = document.createElement('canvas');
    canvas.style.cssText = 'display:block;width:100%;height:100%;';
    container.appendChild(canvas);

    // Controls bar
    const controls = document.createElement('div');
    controls.className = 'sim-controls';
    container.appendChild(controls);

    // Play/Pause button
    const btnPlay = document.createElement('button');
    btnPlay.className   = 'sim-btn';
    btnPlay.textContent = '⏸';
    btnPlay.title       = 'Play / Pausa';
    btnPlay.addEventListener('click', () => {
      running = !running;
      btnPlay.textContent = running ? '⏸' : '▶';
    });
    controls.appendChild(btnPlay);

    // Reset button
    const btnReset = document.createElement('button');
    btnReset.className   = 'sim-btn';
    btnReset.textContent = '↺';
    btnReset.title       = 'Reiniciar';
    btnReset.addEventListener('click', () => {
      initSim();
      running = true;
      btnPlay.textContent = '⏸';
    });
    controls.appendChild(btnReset);

    // Separator label
    const sep = document.createElement('span');
    sep.style.cssText = 'flex:0 0 8px;';
    controls.appendChild(sep);

    // Sensor angle slider
    const lblAngle = document.createElement('label');
    lblAngle.style.cssText  = 'display:flex;align-items:center;gap:6px;font-size:12px;color:#8a93a3;';
    lblAngle.textContent    = 'Ángulo sensor';
    sliderAngle = document.createElement('input');
    sliderAngle.type      = 'range';
    sliderAngle.className = 'sim-range';
    sliderAngle.min       = '10';
    sliderAngle.max       = '90';
    sliderAngle.step      = '5';
    sliderAngle.value     = String(SENSOR_ANGLE_DEG);
    const readoutAngle = document.createElement('span');
    readoutAngle.className   = 'sim-readout';
    readoutAngle.textContent = SENSOR_ANGLE_DEG + '°';
    sliderAngle.addEventListener('input', () => {
      SENSOR_ANGLE_DEG = Number(sliderAngle.value);
      readoutAngle.textContent = SENSOR_ANGLE_DEG + '°';
    });
    lblAngle.appendChild(sliderAngle);
    lblAngle.appendChild(readoutAngle);
    controls.appendChild(lblAngle);

    // Population slider
    const lblPop = document.createElement('label');
    lblPop.style.cssText  = 'display:flex;align-items:center;gap:6px;font-size:12px;color:#8a93a3;';
    lblPop.textContent    = 'Población';
    sliderPop = document.createElement('input');
    sliderPop.type      = 'range';
    sliderPop.className = 'sim-range';
    sliderPop.min       = '500';
    sliderPop.max       = '8000';
    sliderPop.step      = '500';
    sliderPop.value     = String(N_AGENTS);
    const readoutPop = document.createElement('span');
    readoutPop.className   = 'sim-readout';
    readoutPop.textContent = N_AGENTS;
    sliderPop.addEventListener('input', () => {
      N_AGENTS = Number(sliderPop.value);
      readoutPop.textContent = N_AGENTS;
      initSim(); // rebuild agent array to new size
    });
    lblPop.appendChild(sliderPop);
    lblPop.appendChild(readoutPop);
    controls.appendChild(lblPop);

    // Legend
    const legend = document.createElement('div');
    legend.className = 'sim-legend';
    legend.innerHTML =
      '<span style="color:#e0a44e">●</span> nodos = centros urbanos &nbsp;|&nbsp;' +
      '<span style="color:#2dd4bf">━</span> red = infraestructura emergente &nbsp;|&nbsp;' +
      'optimización distribuida sin planificador central';
    container.appendChild(legend);
  }

  // ── Size canvas to container ────────────────────────────────────────────
  function sizeCanvas(container) {
    dpr = window.devicePixelRatio || 1;
    W   = container.clientWidth;
    H   = container.clientHeight;

    // Leave space for controls bar (~46px) and legend (~28px)
    const ctrlH   = 46;
    const legendH = 28;
    H = Math.max(H - ctrlH - legendH, 100);

    canvas.width  = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';

    ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
  }

  // ── SIM object ──────────────────────────────────────────────────────────
  const SIM = {
    title: 'Red Physarum — optimización biológica',

    mount(container) {
      // Reset module-level state for re-entrancy
      running = true;
      rafId   = null;

      buildDOM(container);
      sizeCanvas(container);
      initSim();

      // ResizeObserver
      resizeObs = new ResizeObserver(() => {
        sizeCanvas(container);
        initSim();
      });
      resizeObs.observe(container);

      rafId = requestAnimationFrame(loop);
    },

    unmount() {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      if (resizeObs) {
        resizeObs.disconnect();
        resizeObs = null;
      }
      // Find the container by canvas parent and clear
      if (canvas && canvas.parentElement) {
        canvas.parentElement.innerHTML = '';
      }
      // Nullify references
      canvas = null;
      ctx    = null;
      trail  = null;
      trailNext = null;
      agents = null;
      foodNodes = [];
      // Clear offscreen cache
      if (render._offscreen) render._offscreen = null;
    }
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['physarum'] = SIM;
})();
