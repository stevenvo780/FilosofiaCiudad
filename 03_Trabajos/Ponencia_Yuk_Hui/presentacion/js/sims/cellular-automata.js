(function () {
  'use strict';

  // ── Paleta ────────────────────────────────────────────────────────────────
  const C = {
    bg:          '#0d1117',
    panel:       '#161b26',
    grid:        '#222b3a',
    ink:         '#e8e6df',
    muted:       '#8a93a3',
    water:       '#3b82c4',
    park:        '#5cab73',
    residential: '#e0a44e',
    cbd:         '#e0524a',
    road:        '#cdd6e3',
    undeveloped: '#161b26',
  };

  // ── Estados de celda ──────────────────────────────────────────────────────
  const ST = {
    EMPTY:   0,   // no desarrollado
    ROAD:    1,   // vía (permanente, acelera urbanización)
    WATER:   2,   // agua (restricción, no se urbaniza)
    PARK:    3,   // parque (restricción)
    GROWING: 4,   // en desarrollo
    URBAN:   5,   // urbanizado
    CBD:     6,   // núcleo central
  };

  const COLS = 120;
  const ROWS = 80;

  // ── Helpers ───────────────────────────────────────────────────────────────
  function mkGrid() {
    return new Uint8Array(COLS * ROWS);
  }

  function idx(c, r) { return r * COLS + c; }

  function initWorld(grid, growthRate) {
    grid.fill(ST.EMPTY);

    // ── Agua: cuatro manchas ──
    const waterPatches = [
      { c: 8,  r: 10, w: 14, h: 10 },
      { c: 95, r: 55, w: 18, h: 12 },
      { c: 5,  r: 60, w: 10, h: 14 },
      { c: 100, r: 5, w: 12, h: 8  },
    ];
    for (const p of waterPatches) {
      for (let r = p.r; r < p.r + p.h; r++) {
        for (let c = p.c; c < p.c + p.w; c++) {
          if (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
            grid[idx(c, r)] = ST.WATER;
          }
        }
      }
    }

    // ── Parques: tres manchas ──
    const parkPatches = [
      { c: 30, r: 5,  w: 12, h: 10 },
      { c: 80, r: 30, w: 10, h: 12 },
      { c: 20, r: 65, w: 14, h: 10 },
    ];
    for (const p of parkPatches) {
      for (let r = p.r; r < p.r + p.h; r++) {
        for (let c = p.c; c < p.c + p.w; c++) {
          if (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
            if (grid[idx(c, r)] === ST.EMPTY) {
              grid[idx(c, r)] = ST.PARK;
            }
          }
        }
      }
    }

    // ── Vías principales (aceleran urbanización adyacente) ──
    // Horizontal
    const roads = [
      { type: 'h', r: 20, c0: 0,  c1: COLS - 1 },
      { type: 'h', r: 40, c0: 0,  c1: COLS - 1 },
      { type: 'h', r: 60, c0: 0,  c1: COLS - 1 },
      { type: 'v', c: 30, r0: 0,  r1: ROWS - 1 },
      { type: 'v', c: 60, r0: 0,  r1: ROWS - 1 },
      { type: 'v', c: 90, r0: 0,  r1: ROWS - 1 },
    ];
    for (const road of roads) {
      if (road.type === 'h') {
        for (let c = road.c0; c <= road.c1; c++) {
          if (grid[idx(c, road.r)] === ST.EMPTY) {
            grid[idx(c, road.r)] = ST.ROAD;
          }
        }
      } else {
        for (let r = road.r0; r <= road.r1; r++) {
          if (grid[idx(road.c, r)] === ST.EMPTY) {
            grid[idx(road.c, r)] = ST.ROAD;
          }
        }
      }
    }

    // ── CBD núcleo central ──
    const cc = Math.floor(COLS / 2);
    const cr = Math.floor(ROWS / 2);
    for (let dr = -3; dr <= 3; dr++) {
      for (let dc = -3; dc <= 3; dc++) {
        const c = cc + dc, r = cr + dr;
        if (c >= 0 && c < COLS && r >= 0 && r < ROWS) {
          grid[idx(c, r)] = ST.CBD;
        }
      }
    }

    // ── Semilla de urbanización inicial alrededor del CBD ──
    for (let dr = -7; dr <= 7; dr++) {
      for (let dc = -7; dc <= 7; dc++) {
        if (Math.abs(dr) <= 3 && Math.abs(dc) <= 3) continue;
        const c = cc + dc, r = cr + dr;
        if (c >= 0 && c < COLS && r >= 0 && r < ROWS) {
          if (grid[idx(c, r)] === ST.EMPTY && Math.random() < 0.6) {
            grid[idx(c, r)] = ST.URBAN;
          }
        }
      }
    }
  }

  function countUrbanNeighbors(grid, c, r) {
    let n = 0;
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nc = c + dc, nr = r + dr;
        if (nc < 0 || nc >= COLS || nr < 0 || nr >= ROWS) continue;
        const s = grid[idx(nc, nr)];
        if (s === ST.URBAN || s === ST.CBD || s === ST.GROWING) n++;
      }
    }
    return n;
  }

  function hasRoadNeighbor(grid, c, r) {
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nc = c + dc, nr = r + dr;
        if (nc < 0 || nc >= COLS || nr < 0 || nr >= ROWS) continue;
        if (grid[idx(nc, nr)] === ST.ROAD) return true;
      }
    }
    return false;
  }

  function stepWorld(grid, next, growthRate) {
    // Copiar estado permanente
    for (let i = 0; i < grid.length; i++) {
      next[i] = grid[i];
    }

    const baseSpont    = 0.0005 * growthRate;   // crecimiento espontáneo
    const diffuseBase  = 0.12   * growthRate;   // difusión desde vecindad urbana
    const roadBoost    = 2.5;                   // multiplicador si hay vía cercana

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const s = grid[idx(c, r)];
        if (s !== ST.EMPTY) continue; // solo celdas vacías cambian

        const urbanN  = countUrbanNeighbors(grid, c, r);
        const hasRoad = hasRoadNeighbor(grid, c, r);
        const roadMul = hasRoad ? roadBoost : 1.0;

        // (1) Crecimiento espontáneo
        if (Math.random() < baseSpont * roadMul) {
          next[idx(c, r)] = ST.GROWING;
          continue;
        }

        // (2) Difusión desde vecinos urbanos (Moore)
        if (urbanN > 0) {
          const p = diffuseBase * (urbanN / 8) * roadMul;
          if (Math.random() < p) {
            next[idx(c, r)] = ST.GROWING;
            continue;
          }
        }

        // (3) Influencia directa de vía (corredores lineales)
        if (hasRoad && Math.random() < 0.04 * growthRate) {
          next[idx(c, r)] = ST.GROWING;
        }
      }
    }

    // GROWING → URBAN al paso siguiente
    for (let i = 0; i < next.length; i++) {
      if (grid[i] === ST.GROWING) next[i] = ST.URBAN;
    }
  }

  function urbanPct(grid) {
    let u = 0, total = 0;
    for (let i = 0; i < grid.length; i++) {
      const s = grid[i];
      if (s === ST.WATER || s === ST.ROAD) continue;
      total++;
      if (s === ST.URBAN || s === ST.CBD || s === ST.GROWING) u++;
    }
    return total > 0 ? (u / total * 100) : 0;
  }

  // ── Color de celda ────────────────────────────────────────────────────────
  function cellColor(state) {
    switch (state) {
      case ST.EMPTY:   return C.undeveloped;
      case ST.ROAD:    return C.road;
      case ST.WATER:   return C.water;
      case ST.PARK:    return C.park;
      case ST.GROWING: return '#c47a28'; // amber oscuro, transición
      case ST.URBAN:   return C.residential;
      case ST.CBD:     return C.cbd;
    }
    return C.undeveloped;
  }

  // ── Módulo principal ──────────────────────────────────────────────────────
  const SIM = {
    title: 'Autómata Celular — Crecimiento Urbano',

    mount(container) {
      // Estado interno limpio
      this._running   = false;
      this._rafId     = null;
      this._gen       = 0;
      this._growthRate = 1.0;
      this._grid      = mkGrid();
      this._next      = mkGrid();
      this._stepEvery = 8;   // pasos de RAF por generación
      this._rafCount  = 0;

      initWorld(this._grid, this._growthRate);

      // ── DOM ───────────────────────────────────────────────────────────────
      container.innerHTML = '';

      // Canvas
      const canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;width:100%;height:calc(100% - 60px);';
      container.appendChild(canvas);

      this._canvas = canvas;
      this._ctx    = canvas.getContext('2d');

      // Controls bar
      const controls = document.createElement('div');
      controls.className = 'sim-controls';

      const btnPlay = document.createElement('button');
      btnPlay.className = 'sim-btn';
      btnPlay.textContent = '▶';
      btnPlay.title = 'Play / Pause';

      const btnReset = document.createElement('button');
      btnReset.className = 'sim-btn';
      btnReset.textContent = '↺';
      btnReset.title = 'Reset';

      const labelRate = document.createElement('label');
      labelRate.style.cssText = 'display:flex;align-items:center;gap:6px;color:#e8e6df;font-size:12px;';
      labelRate.textContent = 'Tasa:';

      const sliderRate = document.createElement('input');
      sliderRate.type      = 'range';
      sliderRate.className = 'sim-range';
      sliderRate.min    = '0.2';
      sliderRate.max    = '3.0';
      sliderRate.step   = '0.1';
      sliderRate.value  = '1.0';
      sliderRate.style.width = '90px';
      labelRate.appendChild(sliderRate);

      const readout = document.createElement('div');
      readout.className = 'sim-readout';
      readout.style.cssText = 'margin-left:auto;font-size:12px;color:#8a93a3;';

      controls.appendChild(btnPlay);
      controls.appendChild(btnReset);
      controls.appendChild(labelRate);
      controls.appendChild(readout);

      container.appendChild(controls);

      // Legend
      const legend = document.createElement('div');
      legend.className = 'sim-legend';
      legend.innerHTML =
        '<span style="color:#e0524a">■</span> CBD &nbsp;' +
        '<span style="color:#e0a44e">■</span> Urbanizado &nbsp;' +
        '<span style="color:#cdd6e3">■</span> Vía &nbsp;' +
        '<span style="color:#3b82c4">■</span> Agua &nbsp;' +
        '<span style="color:#5cab73">■</span> Parque';
      legend.style.cssText = 'font-size:11px;padding:2px 8px;color:#8a93a3;';
      controls.insertBefore(legend, readout);

      this._readout = readout;
      this._btnPlay = btnPlay;

      // ── Eventos ───────────────────────────────────────────────────────────
      const self = this;

      this._onPlay = function () {
        self._running = !self._running;
        btnPlay.textContent = self._running ? '⏸' : '▶';
        if (self._running) self._scheduleRaf();
      };

      this._onReset = function () {
        self._running = false;
        btnPlay.textContent = '▶';
        self._gen = 0;
        self._rafCount = 0;
        initWorld(self._grid, self._growthRate);
        self._drawFrame();
        self._updateReadout();
      };

      this._onRate = function () {
        self._growthRate = parseFloat(sliderRate.value);
      };

      btnPlay.addEventListener('click', this._onPlay);
      btnReset.addEventListener('click', this._onReset);
      sliderRate.addEventListener('input', this._onRate);

      this._btnPlay  = btnPlay;
      this._btnReset = btnReset;
      this._sliderRate = sliderRate;

      // ── ResizeObserver ────────────────────────────────────────────────────
      this._ro = new ResizeObserver(() => { self._resizeCanvas(); self._drawFrame(); });
      this._ro.observe(container);

      this._resizeCanvas();
      this._drawFrame();
      this._updateReadout();
    },

    unmount() {
      this._running = false;
      if (this._rafId !== null) {
        cancelAnimationFrame(this._rafId);
        this._rafId = null;
      }
      if (this._ro) {
        this._ro.disconnect();
        this._ro = null;
      }
      if (this._btnPlay)   this._btnPlay.removeEventListener('click', this._onPlay);
      if (this._btnReset)  this._btnReset.removeEventListener('click', this._onReset);
      if (this._sliderRate) this._sliderRate.removeEventListener('input', this._onRate);

      if (this._canvas && this._canvas.parentNode) {
        this._canvas.parentNode.innerHTML = '';
      }
      this._canvas = null;
      this._ctx    = null;
      this._grid   = null;
      this._next   = null;
    },

    // ── Internos ──────────────────────────────────────────────────────────

    _resizeCanvas() {
      if (!this._canvas) return;
      const c   = this._canvas;
      const dpr = window.devicePixelRatio || 1;
      const w   = c.clientWidth;
      const h   = c.clientHeight;
      c.width   = Math.round(w * dpr);
      c.height  = Math.round(h * dpr);
      this._ctx.scale(dpr, dpr);
      this._w = w;
      this._h = h;
    },

    _scheduleRaf() {
      if (!this._running || this._rafId !== null) return;
      const self = this;
      this._rafId = requestAnimationFrame(function loop() {
        if (!self._running) { self._rafId = null; return; }
        self._rafCount++;
        if (self._rafCount >= self._stepEvery) {
          self._rafCount = 0;
          self._tick();
        }
        self._drawFrame();
        self._updateReadout();
        self._rafId = requestAnimationFrame(loop);
      });
    },

    _tick() {
      stepWorld(this._grid, this._next, this._growthRate);
      // Swap buffers
      const tmp  = this._grid;
      this._grid = this._next;
      this._next = tmp;
      this._gen++;
    },

    _drawFrame() {
      const ctx = this._ctx;
      if (!ctx) return;
      const w = this._w || this._canvas.clientWidth;
      const h = this._h || this._canvas.clientHeight;

      // Fondo
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, w, h);

      const cellW = w / COLS;
      const cellH = h / ROWS;
      const grid  = this._grid;

      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const s = grid[idx(c, r)];
          const color = cellColor(s);
          ctx.fillStyle = color;
          const x = c * cellW;
          const y = r * cellH;
          ctx.fillRect(
            Math.floor(x),
            Math.floor(y),
            Math.ceil(cellW) + 1,
            Math.ceil(cellH) + 1
          );
        }
      }

      // Líneas de cuadrícula (muy tenues, solo cada 10 celdas)
      ctx.strokeStyle = C.grid;
      ctx.lineWidth   = 0.4;
      ctx.globalAlpha = 0.35;
      for (let c = 0; c <= COLS; c += 10) {
        ctx.beginPath();
        ctx.moveTo(c * cellW, 0);
        ctx.lineTo(c * cellW, h);
        ctx.stroke();
      }
      for (let r = 0; r <= ROWS; r += 10) {
        ctx.beginPath();
        ctx.moveTo(0, r * cellH);
        ctx.lineTo(w, r * cellH);
        ctx.stroke();
      }
      ctx.globalAlpha = 1.0;
    },

    _updateReadout() {
      if (!this._readout || !this._grid) return;
      const pct = urbanPct(this._grid).toFixed(1);
      this._readout.textContent = `Gen: ${this._gen}  |  Suelo urbanizado: ${pct}%`;
    },
  };

  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['cellular-automata'] = SIM;
})();
