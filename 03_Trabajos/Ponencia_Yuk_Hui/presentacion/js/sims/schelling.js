(function () {
  /* -----------------------------------------------------------------------
   * SCHELLING SEGREGATION MODEL
   * Grid ~60x40, two agent types + empty cells (~10%).
   * An agent is "unhappy" if fraction of same-type neighbours (Moore-8)
   * is below the similarity threshold.  Unhappy agents teleport to a
   * random empty cell each step.
   * Demonstrates: mild local preferences → strong macro-segregation
   * (emergence, not AI).
   * --------------------------------------------------------------------- */

  const COLS = 60;
  const ROWS = 40;
  const EMPTY_FRAC = 0.10;          // fraction of empty cells
  const STEP_INTERVAL_MS = 80;      // ~12 steps/s — readable animation

  // Palette (from SPEC.md)
  const C_BG     = '#0d1117';
  const C_GRID   = '#222b3a';
  const C_PANEL  = '#161b26';
  const C_TEXT   = '#e8e6df';
  const C_MUTED  = '#8a93a3';
  const C_A      = '#2dd4bf';       // transit/cian  → type A
  const C_B      = '#e0a44e';       // residencial/amber → type B
  const C_EMPTY  = '#161b26';       // same as panel — dark empty cell

  // -----------------------------------------------------------------------
  // Grid helpers
  // -----------------------------------------------------------------------
  const TOTAL = COLS * ROWS;

  function idx(c, r) { return r * COLS + c; }

  function buildGrid(threshFrac) {
    const nEmpty = Math.round(TOTAL * EMPTY_FRAC);
    const nA = Math.round((TOTAL - nEmpty) / 2);
    const nB = TOTAL - nEmpty - nA;

    // flat array: 0=empty, 1=typeA, 2=typeB
    const cells = new Uint8Array(TOTAL);
    let pos = 0;
    for (let i = 0; i < nA; i++) cells[pos++] = 1;
    for (let i = 0; i < nB; i++) cells[pos++] = 2;
    // rest is already 0
    // Fisher-Yates shuffle
    for (let i = TOTAL - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      const tmp = cells[i]; cells[i] = cells[j]; cells[j] = tmp;
    }
    return cells;
  }

  // Returns [sameFrac, totalNeighbours] for cell at (c,r)
  function neighbourStats(cells, c, r) {
    const type = cells[idx(c, r)];
    let same = 0, total = 0;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nc = c + dc, nr = r + dr;
        if (nc < 0 || nc >= COLS || nr < 0 || nr >= ROWS) continue;
        const nb = cells[idx(nc, nr)];
        if (nb !== 0) {
          total++;
          if (nb === type) same++;
        }
      }
    }
    return [same, total];
  }

  // One simulation step: move all unhappy agents to random empty cells
  function step(cells, threshFrac) {
    // collect unhappy agents and empty cells
    const unhappy = [];
    const empty = [];
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const i = idx(c, r);
        if (cells[i] === 0) {
          empty.push(i);
        } else {
          const [same, total] = neighbourStats(cells, c, r);
          const frac = total === 0 ? 0 : same / total;
          if (frac < threshFrac) unhappy.push(i);
        }
      }
    }
    // shuffle empty list
    for (let i = empty.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      const tmp = empty[i]; empty[i] = empty[j]; empty[j] = tmp;
    }
    // move each unhappy agent to a random empty slot (if any)
    const moveCount = Math.min(unhappy.length, empty.length);
    for (let k = 0; k < moveCount; k++) {
      const from = unhappy[k];
      const to   = empty[k];
      cells[to] = cells[from];
      cells[from] = 0;
    }
  }

  // Compute % satisfied and mean same-neighbour fraction (segregation index)
  function metrics(cells, threshFrac) {
    let totalAgents = 0, satisfied = 0, sumFrac = 0;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const i = idx(c, r);
        if (cells[i] === 0) continue;
        totalAgents++;
        const [same, total] = neighbourStats(cells, c, r);
        const frac = total === 0 ? 1 : same / total; // isolated → counts as satisfied
        sumFrac += frac;
        if (frac >= threshFrac) satisfied++;
      }
    }
    const pctSat = totalAgents ? (satisfied / totalAgents) * 100 : 0;
    const segIdx = totalAgents ? (sumFrac / totalAgents) * 100 : 0;
    return { pctSat, segIdx };
  }

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  function render(ctx, cells, w, h) {
    ctx.fillStyle = C_BG;
    ctx.fillRect(0, 0, w, h);

    const cellW = w / COLS;
    const cellH = h / ROWS;
    const gap = cellW > 6 ? 1 : 0;   // grid gap only if cells big enough

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const type = cells[idx(c, r)];
        ctx.fillStyle = type === 1 ? C_A : type === 2 ? C_B : C_EMPTY;
        ctx.fillRect(
          c * cellW + gap,
          r * cellH + gap,
          cellW - gap,
          cellH - gap
        );
      }
    }

    // subtle grid lines between empty cells for readability (only if large)
    if (gap) {
      ctx.strokeStyle = C_GRID;
      ctx.lineWidth = 0.5;
      for (let r = 0; r <= ROWS; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * cellH);
        ctx.lineTo(w, r * cellH);
        ctx.stroke();
      }
      for (let c = 0; c <= COLS; c++) {
        ctx.beginPath();
        ctx.moveTo(c * cellW, 0);
        ctx.lineTo(c * cellW, h);
        ctx.stroke();
      }
    }
  }

  // -----------------------------------------------------------------------
  // SIM object
  // -----------------------------------------------------------------------
  const SIM = {
    title: 'Segregación de Schelling',

    // internal state (reset on each mount)
    _cells: null,
    _running: false,
    _rafId: null,
    _timerId: null,
    _observer: null,
    _canvas: null,
    _ctx: null,
    _container: null,
    _threshFrac: 0.30,
    _readoutEl: null,
    _sliderLabel: null,
    _lastStep: 0,

    mount(container) {
      this._container = container;
      this._running = false;
      this._threshFrac = 0.30;
      this._lastStep = 0;

      // ---- Canvas ----
      const canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:100%;';
      container.appendChild(canvas);
      this._canvas = canvas;

      const dpr = window.devicePixelRatio || 1;
      const W = container.clientWidth  || 800;
      const H = container.clientHeight || 533;
      canvas.width  = W * dpr;
      canvas.height = H * dpr;
      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      this._ctx = ctx;

      // ---- Grid ----
      this._cells = buildGrid(this._threshFrac);

      // ---- Controls ----
      const controls = document.createElement('div');
      controls.className = 'sim-controls';

      // Play/Pause
      const btnPlay = document.createElement('button');
      btnPlay.className = 'sim-btn';
      btnPlay.textContent = '▶';
      btnPlay.title = 'Play / Pause';
      btnPlay.addEventListener('click', () => {
        this._running = !this._running;
        btnPlay.textContent = this._running ? '⏸' : '▶';
      });

      // Reset
      const btnReset = document.createElement('button');
      btnReset.className = 'sim-btn';
      btnReset.textContent = '↺';
      btnReset.title = 'Reiniciar';
      btnReset.addEventListener('click', () => {
        this._cells = buildGrid(this._threshFrac);
        this._running = false;
        btnPlay.textContent = '▶';
        this._drawFrame();
      });

      // Threshold slider
      const sliderWrap = document.createElement('span');
      sliderWrap.style.cssText = 'display:inline-flex;align-items:center;gap:6px;';

      const sliderLabel = document.createElement('label');
      sliderLabel.className = 'sim-legend';
      sliderLabel.style.cssText = 'font-size:12px;white-space:nowrap;';
      sliderLabel.textContent = 'Umbral: 30%';
      this._sliderLabel = sliderLabel;

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'sim-range';
      slider.min = '0';
      slider.max = '100';
      slider.step = '5';
      slider.value = '30';
      slider.style.cssText = 'width:110px;';
      slider.addEventListener('input', () => {
        this._threshFrac = parseInt(slider.value, 10) / 100;
        sliderLabel.textContent = 'Umbral: ' + slider.value + '%';
      });

      sliderWrap.appendChild(sliderLabel);
      sliderWrap.appendChild(slider);

      // Readout
      const readout = document.createElement('div');
      readout.className = 'sim-readout';
      readout.style.cssText = 'font-size:12px;min-width:220px;text-align:right;';
      this._readoutEl = readout;

      controls.appendChild(btnPlay);
      controls.appendChild(btnReset);
      controls.appendChild(sliderWrap);
      controls.appendChild(readout);
      container.appendChild(controls);

      // ---- Legend ----
      const legend = document.createElement('div');
      legend.className = 'sim-legend';
      legend.style.cssText = 'display:flex;align-items:center;gap:12px;padding:2px 8px 4px;font-size:11px;';
      legend.innerHTML =
        '<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:' + C_A + ';"></span>' +
        '<span style="color:' + C_TEXT + '">Tipo A</span>' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:' + C_B + ';margin-left:6px;"></span>' +
        '<span style="color:' + C_TEXT + '">Tipo B</span>' +
        '<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:' + C_EMPTY + ';border:1px solid ' + C_GRID + ';margin-left:6px;"></span>' +
        '<span style="color:' + C_MUTED + '">Vacío (~10%)</span>' +
        '<span style="color:' + C_MUTED + ';margin-left:10px;">Preferencia local → segregación macro</span>';
      container.appendChild(legend);

      // ---- ResizeObserver ----
      const ro = new ResizeObserver(() => {
        const dpr2 = window.devicePixelRatio || 1;
        const W2 = container.clientWidth;
        const H2 = container.clientHeight;
        canvas.width  = W2 * dpr2;
        canvas.height = H2 * dpr2;
        ctx.setTransform(dpr2, 0, 0, dpr2, 0, 0);
        this._drawFrame();
      });
      ro.observe(container);
      this._observer = ro;

      // ---- Animation loop ----
      this._drawFrame();
      const loop = (ts) => {
        if (!this._canvas) return; // unmounted
        if (this._running && (ts - this._lastStep) >= STEP_INTERVAL_MS) {
          step(this._cells, this._threshFrac);
          this._lastStep = ts;
          this._drawFrame();
        } else if (!this._running) {
          // still draw (in case of resize)
        }
        this._rafId = requestAnimationFrame(loop);
      };
      this._rafId = requestAnimationFrame(loop);
    },

    _drawFrame() {
      if (!this._canvas || !this._ctx || !this._cells) return;
      const dpr = window.devicePixelRatio || 1;
      const W = this._canvas.width  / dpr;
      const H = this._canvas.height / dpr;
      render(this._ctx, this._cells, W, H);
      // update readout
      if (this._readoutEl) {
        const { pctSat, segIdx } = metrics(this._cells, this._threshFrac);
        this._readoutEl.innerHTML =
          '<span style="color:' + C_MUTED + '">Satisfechos: </span>' +
          '<span style="color:' + C_TEXT  + '">' + pctSat.toFixed(1) + '%</span>' +
          '<span style="color:' + C_MUTED + '"> &nbsp;|&nbsp; Índice segregación: </span>' +
          '<span style="color:' + C_A     + '">' + segIdx.toFixed(1) + '%</span>';
      }
    },

    unmount() {
      // Cancel RAF
      if (this._rafId !== null) {
        cancelAnimationFrame(this._rafId);
        this._rafId = null;
      }
      // Disconnect observer
      if (this._observer) {
        this._observer.disconnect();
        this._observer = null;
      }
      // Clear container
      if (this._container) {
        this._container.innerHTML = '';
        this._container = null;
      }
      // Reset state refs
      this._canvas     = null;
      this._ctx        = null;
      this._cells      = null;
      this._readoutEl  = null;
      this._sliderLabel = null;
      this._running    = false;
    }
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['schelling'] = SIM;
})();
