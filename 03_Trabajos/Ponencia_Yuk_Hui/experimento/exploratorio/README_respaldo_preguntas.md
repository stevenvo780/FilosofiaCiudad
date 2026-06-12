# Réplica exploratoria con modelos coder — respaldo SOLO para la ronda de preguntas

**Decisión (12-jun): NO se integra al deck/libreto/tesis.** Queda aquí como dato
de respaldo por si en el debate cuestionan que "un modelo más grande ganaría".

## El dato (corrido en kratos, GPU + RAM, vía Ollama)

| Sujeto | Exactitud | Acierta |
|---|---|---|
| devstral 24B (coder) | **20%** (2/10) | solo T3 |
| qwen3-coder 30B (coder) | **20%** (2/10) | solo T3 |
| qwen3-coder-next **80B** (coder, MoE) | **20%** (2/10) | solo T3 |

Los tres, exactamente **20%**. Todos fallan T1 (multiplicación), T2 (ruta), T4
(recursión) y T5 (suma de cuadrados). El único acierto es **T3 = 2.704.156** (el
binomial memorizable). **El 80B no le gana al 24B.**

Frase lista: *"Esta misma madrugada repetí el experimento con modelos especializados
en código, hasta uno de 80 mil millones de parámetros corriendo en mi escritorio:
los tres dieron 20%, y solo aciertan el número que está en todos los libros. Ni el
tamaño ni la especialización compran el cálculo."*

## Asteriscos de honestidad (decirlos si se usa)
- Son modelos **coder** (sesgados *a favor* de lo computacional) y aun así fallan
  → refuerza el punto.
- El 80B **no completó** T5-int2 ni T6: agotó su presupuesto de 120 min (es lento;
  T4 tardó ~29 min en un intento). Su 20% es sobre 10 slots con faltante=fallo.
- **Exploratorio**, condiciones distintas al canon (timeout 120 min vs 25 min).
  No está en `resultados.json`; vive en `resultados_exploratorio.json`.

En T6 (juicio) sí dieron respuestas razonables (niño / acompañante): competencia en
el dominio del significado, donde el cómputo puro ni arranca. Consistente con el canon.
