# Ponencia · El límite de la IA y el objeto epistémico del urbanismo computacional

Lectura de **Yuk Hui**, “Sobre el límite de la inteligencia artificial”
(*Fragmentar el futuro*, Caja Negra, 2020, pp. 163-191) — Filosofía de la Ciudad, Unidad Urban AI.
**Steven Vallejo · 12 de junio de 2026 · 20 minutos.**

## Tesis

La IA es asombrosa **como asistente** (aplana curvas de aprendizaje, acelera la creación). Pero
el **objeto epistémico** del urbanismo no es la IA: son los **modelos de cómputo sistémico**
(autómatas celulares, agentes, sintaxis espacial, optimización de redes, modelos gravitacionales).
La IA solo ayuda a *construirlos ágilmente*. Conectado con Hui: por carecer de **mundo** y de
**juicio reflexionante**, la IA no puede ser el objeto del conocimiento urbano —solo su instrumento.
El *límite* es político-cosmológico, y cada modelo es una **cosmotécnica** que instaura un mundo.

## Cómo abrir la presentación (web interactiva)

Necesita servirse por HTTP (los `<script>` y reveal.js no cargan bien con `file://`).

```bash
cd 03_Trabajos/Ponencia_Yuk_Hui/presentacion
npm install                     # SOLO la primera vez (restaura reveal.js; node_modules no está en git)
python3 -m http.server 8000     # o:  npx serve .
# abrir http://localhost:8000
```

Tras ese `npm install` funciona **offline**: reveal.js queda vendorizado en `node_modules/`.
(Las fuentes tipográficas se cargan de Google Fonts; si no hay internet, caen a la tipografía
del sistema sin romper nada.)

### Controles
- **→ / Espacio**: siguiente · **←**: anterior · **Esc**: vista general · **F**: pantalla completa.
- **S**: vista de orador con las notas y el temporizador (¡úsala para exponer!).
- Cada modelo tiene sus propios controles (▶/⏸, ↺ reset, sliders). Son **interactivos en vivo**.

## Las 6 simulaciones (objetos epistémicos, cero IA)

| # | Modelo | Qué demuestra | Disciplina real |
|---|--------|---------------|-----------------|
| 1 | Autómata celular | Morfología urbana emerge de reglas locales | SLEUTH (planeación) |
| 2 | Schelling | Segregación macro desde preferencias micro | Economía (Nobel 1971) |
| 3 | Sintaxis espacial | Centralidad de red predice vitalidad urbana | Hillier & Hanson |
| 4 | Physarum | Red de transporte casi-óptima sin cerebro | Tero et al., *Science* 2010 |
| 5 | Tráfico de agentes | Congestión emergente; evaluar políticas | MATSim / SUMO |
| 6 | Gravitacional | Flujos entre centros ∝ masa / distancia^β | Wilson (geografía cuant.) |

## Estructura (18 diapositivas · ~20 min)

1. Portada · 2. La IA es asombrosa (como asistente) · 3. Pero esto es Filosofía de la Ciudad
· 4. Yuk Hui: el límite · 5. Bergson + cibernética · 6. Kant/Simondon + Dreyfus/Heidegger
· 7. El giro empírico · **8-13. Seis modelos en vivo** · 14. Análisis ontológico · 15. Análisis
técnico · 16. Análisis epistémico (la tesis) · 17. Cosmotécnica / tecnodiversidad · 18. Preguntas y cierre.

**Reparto de tiempo orientativo:** apertura+pivote 3 min · Hui 5 min · modelos 6 min ·
análisis 4 min · cierre+preguntas 2 min.

## Versión PPTX

`build/ponencia-yuk-hui.pptx` — versión estática (mismo contenido, con renders de los modelos)
para entregar o proyectar sin navegador. Regenerar con:

```bash
npm run pptx
```

## Archivos

```
presentacion/
├── index.html              # la ponencia (reveal.js)
├── css/theme.css           # tema visual
├── js/deck.js              # motor: monta/desmonta modelos por diapositiva
├── js/sims/*.js            # los 6 modelos (vanilla JS + Canvas)
├── js/sims/SPEC.md         # contrato de los módulos
├── assets/                 # renders estáticos de los modelos (para el PPTX)
├── scripts/build-pptx.mjs  # generador del PPTX
└── build/                  # PPTX generado
```
