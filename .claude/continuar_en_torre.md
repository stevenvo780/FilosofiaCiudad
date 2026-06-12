# Continuar este ejercicio en kratos

Misión si esta sesión se retoma en la torre: completar y ampliar el Banco
Epistémico Urbano (tesis cap. 09) usando el cómputo local sin depender del
portátil ni de APIs. Leer primero `CLAUDE.md` (raíz) y
`.claude/contexto_infraestructura.md`.

## Fuentes de verdad (no recalcular a mano, no inventar)

| Archivo | Contenido |
|---|---|
| `03_Trabajos/Ponencia_Yuk_Hui/experimento/resultados.json` | Exp. 1 (6 tareas × 6 sujetos × 2 intentos) con condiciones |
| `experimento/resultados_teorias.json` | Exp. 2 (39 preguntas × 6 sujetos) global/por teoría/cerrada-vs-emergente |
| `experimento/costos.json` | Costos por vía con método (medido/estimado) y supuestos declarados |
| `simulaciones/banco_preguntas.json` | Las 39 preguntas con valor_exacto y tolerancia (¡post-auditoría!) |
| `simulaciones/catalogo.json` | Especificación canónica de las 13 teorías |
| `02_Lecturas_Base/Yuk_Hui/capitulo_limite_ia_extracto.md` | TEXTO PRIMARIO del capítulo — manda sobre ficha, deck y tesis |

Regla: cualquier número nuevo nace de re-ejecutar un script y queda en un JSON
con sus condiciones; el deck/tesis/móvil solo citan JSONs.

## Cómo re-correr los sujetos locales DESDE kratos

Los scripts `experimento/sujetos_kratos.py` y `experimento/sujetos_teorias_kratos.py`
apuntan a `http://100.98.217.229:11434`; corriendo en kratos cambiar a
`http://localhost:11434`. Son reanudables (persisten cada respuesta, saltan las
hechas). Patrón de petición: `/api/chat`, `stream:false`,
`options {temperature:0.2, num_predict:6144}`, `think:false` para qwen3,
extracción de la última línea "Respuesta final:". La calificación la hace
`experimento/calificar_teorias.py` contra el banco.

## Trabajo pendiente, en orden sugerido

1. **Versión offline del deck**: descargar reveal.js 5 (reveal.css, theme/black.css,
   reveal.js, plugin/notes) a `presentacion/lib/` y cambiar las 4 referencias CDN
   del `index.html`. Probar sin red. (Riesgo real para la exposición del 12-jun.)
2. **Ampliar la gradiente de sujetos**: más modelos locales (devstral:24b y
   qwen3-coder:30b ya están descargados) contra el banco de 39 preguntas →
   extender `resultados_teorias.json` y regenerar los 3 PNG de teorías
   (`presentacion/generar_graficos_costos.py` es el patrón: lee JSON, no hardcodea).
3. **Repeticiones para varianza**: Exp. 2 fue 1 intento por sujeto; subir a 3
   intentos daría barras de error honestas. El 32B tarda ~35 min/pasada.
4. **Tesis**: incorporar "noodiversidad" (ya está en deck y libreto, falta en la
   tesis); considerar capítulo de resultados ampliado con la gradiente extendida.
5. **Ficha del autor** (`03_Trabajos/Ponencia_Yuk_Hui/02_ficha_lectura.md`): tiene
   4 imprecisiones REPORTADAS pero no corregidas (es documento personal del autor):
   individuación atribuida a Simondon "según el capítulo" (no está), gobernar/gestionar
   insinuado como de Hui (es del autor), smart cities como eje de Hui (es traslación),
   tríada confuciana/amazónica/maya viene de la contratapa editorial. Corregir solo
   si el autor lo pide.
6. **Demo en vivo**: con ollama local, una slide/página que interrogue a un modelo
   en tiempo real ante la clase (la infraestructura ya está; falta solo la UI).

## Reglas de proceso que demostraron valer

- Capas de verificación: implementar → verificar independiente → auditar contra
  canon → cotejar contra texto primario. Presupuestar la auditoría Opus siempre.
- Jerarquía de modelos (pedida por el usuario): orquestador no ejecuta; Sonnet
  mecánica; Opus diseño/redacción crítica/auditoría.
- QA visual con prueba objetiva (doble captura + diff) y cache-buster.
- Atribución filosófica: "de Hui (cita)" vs "marco del presentador" — nunca mezclar.
- El usuario revisa en vivo: mantener el server 8123 arriba y avisar Ctrl+F5.
