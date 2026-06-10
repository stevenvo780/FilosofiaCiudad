# Contrato de módulos de simulación

Cada simulación es UN archivo autocontenido en `js/sims/<nombre>.js`, sin dependencias
externas (vanilla JS + Canvas 2D). Se registra en un registro global:

```js
(function () {
  const SIM = {
    title: 'Título legible',
    // container: <div> vacío ya dimensionado por CSS (ocupa el área de la diapositiva).
    mount(container) { /* crea canvas + controles, arranca requestAnimationFrame */ },
    unmount() { /* cancela RAF, quita listeners, vacía container.innerHTML */ }
  };
  window.PonenciaSims = window.PonenciaSims || {};
  window.PonenciaSims['<nombre>'] = SIM;
})();
```

## Reglas obligatorias
- NADA de `import`/`export` ni módulos ES. Solo un IIFE que registra en `window.PonenciaSims`.
- Crear `<canvas>` dentro de `container`. Tamaño = `container.clientWidth/clientHeight`.
  Soportar `devicePixelRatio` (canvas.width = clientWidth*dpr; ctx.scale(dpr,dpr)).
- Usar `requestAnimationFrame`. Guardar el id y cancelarlo en `unmount()`.
- Re-dimensionar con `ResizeObserver` sobre `container` (desconectarlo en `unmount`).
- Barra de controles propia: un `<div class="sim-controls">` con botones
  `<button class="sim-btn">`. Mínimo: ▶/⏸ (play/pause) y ↺ (reset). Añadir 1–2 sliders
  `<input type="range" class="sim-range">` con `<label>` si el modelo lo amerita.
- En `unmount()` dejar `container` completamente vacío y sin timers/observers vivos.
- `mount()` debe poder llamarse de nuevo tras `unmount()` (re-entrante, estado limpio).
- Rendimiento: fluido a 60fps en un grid/recuento moderado. Limitar tamaño si hace falta.
- Una leyenda corta (texto pequeño) que explique qué colores/elementos significan,
  dibujada en canvas o en un `<div class="sim-legend">`.

## Paleta compartida (hex exactos — fondo oscuro elegante)
- fondo lienzo:    `#0d1117`
- panel:           `#161b26`
- rejilla/grid:    `#222b3a`
- tinta/texto:     `#e8e6df`
- texto tenue:     `#8a93a3`
- agua:            `#3b82c4`
- parque/verde:    `#5cab73`
- residencial:     `#e0a44e`  (amber)
- CBD/centro:      `#e0524a`  (rojo)
- mixto:           `#d97a3d`
- industrial:      `#7b8fa6`
- transit/cian:    `#2dd4bf`
- acento violeta:  `#a78bfa`
- vía/calle:       `#cdd6e3`

## Tipografía en canvas
`ctx.font = "13px 'Inter', system-ui, sans-serif"`. Títulos cortos en `#e8e6df`,
detalles en `#8a93a3`.

## Estilo de controles (clases ya provistas por el tema; NO redefinir CSS):
`.sim-controls`, `.sim-btn`, `.sim-range`, `.sim-legend`, `.sim-readout`.

## Estética
Sobrio, científico, "data-viz de urbanista". Animación legible a 4–5 metros de
distancia (es para proyectar). Trazos limpios, contraste alto, sin saturar.
