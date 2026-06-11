# 05. Resultados: cómputo puro frente a IA estadística

Este capítulo presenta los resultados del experimento propio descrito en el capítulo 04 (Metodología experimental), sin todavía interpretarlos a la luz de la triple crítica que despliegan los capítulos 06, 07 y 08. Su función es estrictamente descriptiva: exponer las cifras tal como salieron, ordenadas de modo que el lector pueda contrastarlas con la verdad de referencia y juzgar por sí mismo. Por eso adoptamos una regla de escritura que mantenemos a lo largo del capítulo: ninguna cifra que aparezca aquí ha sido producida en esta redacción; toda magnitud procede de los dos registros del experimento —`experimento/resultados.json`, que recoge el bloque T1–T6 sobre cómputo puro, y `experimento/resultados_teorias.json`, que recoge las 39 preguntas derivadas de trece modelos urbanos clásicos—. Donde un valor no consta en esos archivos, no se enuncia. Las lecturas, las consecuencias y las analogías filosóficas quedan diferidas; aquí solo se reporta.

El capítulo procede en seis pasos. Primero fija las condiciones de ejecución y la nómina de sujetos. Después presenta la exactitud agregada por sujeto en cada uno de los dos bloques. Luego desciende al detalle del bloque T1–T6, tarea por tarea e intento por intento, donde la verdad de referencia aritmética permite un veredicto binario. A continuación expone el bloque de las trece teorías desagregado por el tipo de pregunta —forma cerrada frente a emergente—, que es donde aparece el contraste más nítido. Sigue un inventario de los patrones de error con sus casos testigo. Y cierra con el estatuto particular de T6, la tarea inversa, marcada como no computable.

## 5.1. Condiciones de ejecución y sujetos

Las dos series del experimento se ejecutaron sin herramientas externas: los sujetos respondieron solo con su razonamiento interno, sin acceso a intérprete, calculadora ni recuperación de datos. Esta condición es constitutiva y no accidental, porque el experimento no pregunta si un sistema puede calcular cuando se le concede una calculadora —puede, trivialmente—, sino qué hace cuando debe producir el resultado del cálculo sin ejecutarlo. El bloque T1–T6 se corrió con dos intentos por sujeto; el bloque de las trece teorías, con un intento por sujeto sobre 39 preguntas.

Los seis sujetos son los mismos en ambas series. Dos son modelos accesibles por interfaz de programación: **Claude Sonnet**, de menor escala nominal, y **Claude Opus**, de mayor escala nominal. Los otros cuatro son modelos locales ejecutados bajo Ollama 0.24 sobre una plataforma denominada «kratos», equipada con una RTX 5070 Ti de 16 GB, a temperatura 0.2: **qwen2.5:3b**, **qwen3:14b**, **gpt-oss:20b** y **qwen3:32b**. Conviene retener que estos cuatro modelos cubren un rango de escala nominal de más de un orden de magnitud en número de parámetros, lo que vuelve la serie útil para observar si la exactitud crece con el tamaño.

El registro documenta además omisiones. El modelo qwen3:32b no produjo respuesta utilizable en varias celdas del bloque T1–T6: agotó el tiempo en t2 (intento 1) y en t4 (intento 1), ambos por encima de los 604 segundos, y faltan datos para t4 (intento 2), t5 (intentos 1 y 2) y t6 (intentos 1 y 2). En el bloque de teorías, ese mismo modelo registró tiempos de 605.2 y 604.5 segundos en sendas preguntas. Estas ausencias se contabilizan como no acierto, según la regla del experimento, y se señalan aquí para que las cifras agregadas de qwen3:32b se lean con esa salvedad.

## 5.2. Exactitud agregada por sujeto

Comenzamos por las cifras de cierre de cada bloque, que el lector puede contrastar después con el detalle. En el bloque T1–T6, donde cada sujeto enfrenta diez celdas evaluables (cinco tareas con verdad de referencia por dos intentos), la exactitud agregada fue la siguiente.

| Sujeto | Aciertos | Total | Exactitud |
|---|---|---|---|
| Claude Sonnet | 9 | 10 | 90.0 % |
| Claude Opus | 7 | 10 | 70.0 % |
| gpt-oss:20b | 4 | 10 | 40.0 % |
| qwen2.5:3b | 2 | 10 | 20.0 % |
| qwen3:14b | 2 | 10 | 20.0 % |
| qwen3:32b | 2 | 10 | 20.0 % |

La primera observación que el agregado permite enunciar sin interpretar es que el sujeto de mayor escala nominal entre los dos modelos de interfaz, Opus, obtuvo menos aciertos que Sonnet —70.0 % frente a 90.0 %—. La diferencia no es un artefacto de redondeo: son siete celdas correctas frente a nueve sobre las mismas diez. Entre los modelos locales, gpt-oss:20b encabeza con 40.0 %, y los tres restantes empatan en 20.0 %, incluido el de mayor tamaño nominal del grupo, qwen3:32b.

En el bloque de las trece teorías, con 39 preguntas por sujeto, los agregados globales son los siguientes.

| Sujeto | Aciertos | Total | Exactitud |
|---|---|---|---|
| Claude Opus | 36 | 39 | 92.31 % |
| Claude Sonnet | 35 | 39 | 89.74 % |
| gpt-oss:20b | 31 | 39 | 79.49 % |
| qwen3:14b | 30 | 39 | 76.92 % |
| qwen3:32b | 30 | 39 | 76.92 % |
| qwen2.5:3b | 15 | 39 | 38.46 % |

Aquí el orden entre Opus y Sonnet se invierte respecto del bloque anterior: Opus aventaja a Sonnet por una pregunta (36 frente a 35). Que el orden relativo de los dos modelos cambie de un bloque al otro es, en sí mismo, un dato que registramos sin explicar todavía. Entre los modelos locales reaparece una jerarquía aproximada por escala —gpt-oss:20b por delante, qwen2.5:3b muy por detrás— pero con dos modelos de tamaño dispar, qwen3:14b y qwen3:32b, empatados en 30 aciertos. La serie completa de seis sujetos, por tanto, no traza una curva creciente y limpia entre tamaño nominal y exactitud: es una relación no monótona, con cruces en ambos extremos del rango.

## 5.3. El bloque T1–T6 en detalle: el cómputo puro y su imitación

Descendemos ahora al detalle del primer bloque, tarea por tarea. Cada una de las cinco tareas computables (T1–T5) tiene un valor exacto único, y cada celda recibe un veredicto binario por comparación literal con ese valor. La tabla siguiente registra la respuesta de cada intento de Sonnet y Opus, que son los dos sujetos sobre los que ancla la discusión cuantitativa principal.

| Tarea | Valor exacto | Sonnet i1 | Sonnet i2 | Opus i1 | Opus i2 |
|---|---|---|---|---|---|
| T1 multiplicación | 349625969488102520908371 | correcto | correcto | correcto | **349634804376851666458571** (incorrecto) |
| T2 camino más corto | (ruta de 10 barrios) | correcto | **ruta de 11 barrios** (incorrecto) | correcto | correcto |
| T3 conteo retícula | 2704156 | correcto | correcto | correcto | correcto |
| T4 recursión afín | 23842 | correcto | correcto | correcto | correcto |
| T5 suma de cuadrados | 651396404 | correcto | correcto | **651397404** (incorrecto) | **651400404** (incorrecto) |

El bloque muestra un patrón que conviene describir con precisión. Sonnet acierta en nueve de sus diez celdas; su único fallo está en T2, donde en el segundo intento entregó una ruta de once barrios —«Altavista, Bellavista, Cumbres, Farallon, Girasol, Horizonte, Jacaranda, Lagos, Tejar, Yarumal, Zafiro»— en lugar de la ruta mínima de diez. Opus acierta en siete de diez: falla en T1 (segundo intento) y en las dos celdas de T5. En T1, su respuesta errónea —349634804376851666458571— coincide con la correcta en los primeros cinco dígitos y diverge a partir de ahí; en T5, sus dos respuestas erróneas —651397404 y 651400404— difieren del valor exacto, 651396404, en mil y en cuatro mil unidades respectivamente, sobre una magnitud del orden de seiscientos cincuenta millones.

Tres rasgos del bloque merecen quedar consignados como descripción. Primero, la inestabilidad entre intentos del mismo sujeto: tanto Sonnet en T2 como Opus en T1 aciertan en un intento y fallan en el otro de la misma tarea, de modo que el acierto no es estable bajo repetición. Segundo, T3 y T4 son las dos únicas tareas en las que ambos modelos de interfaz aciertan en sus cuatro celdas; T3 corresponde al conteo combinatorio cuyo valor, 2704156, fue además producido correctamente por cuatro de los seis sujetos en ambos intentos. Tercero, el error, cuando ocurre, es un error de magnitud cercana: las respuestas falladas no son disparates sino números del orden correcto que yerran en dígitos internos.

El comportamiento de los cuatro modelos locales en este bloque es más disperso. En T1, ninguno de los cuatro acertó la multiplicación; sus respuestas son enteros del orden de magnitud correcto pero distintos del valor exacto en casi todos los dígitos (por ejemplo, qwen3:14b devolvió 34962209758543162489373 en su primer intento, que comparte el prefijo «3496» con el valor verdadero). En T3, en cambio, los cuatro modelos locales acertaron el conteo combinatorio en al menos un intento, y qwen2.5:3b, qwen3:14b, gpt-oss:20b y qwen3:32b lo acertaron en ambos. La tarea recursiva T4 fue la más destructiva para los modelos locales: qwen2.5:3b devolvió «SIN_RESPUESTA» en sus dos intentos, gpt-oss:20b también, qwen3:14b falló con 37521 y luego «SIN_RESPUESTA», y qwen3:32b agotó el tiempo o quedó sin datos. En T5, solo gpt-oss:20b acertó la suma de cuadrados, y solo en uno de sus dos intentos.

## 5.4. El bloque de teorías: forma cerrada frente a emergente

El segundo bloque permite una desagregación que el primero no ofrece: cada una de las 39 preguntas está clasificada como de **forma cerrada** —cuyo valor se obtiene sustituyendo en una fórmula explícita del modelo— o **emergente** —cuyo valor requiere desplegar una iteración o una simulación cuyo resultado no se lee de una fórmula—. Hay 27 preguntas de forma cerrada y 12 emergentes. La distinción organiza el resultado más marcado del bloque, que la tabla siguiente recoge con las exactitudes que constan en el registro.

| Sujeto | Forma cerrada (27) | Emergente (12) |
|---|---|---|
| Claude Opus | 100.0 % (27/27) | 75.0 % (9/12) |
| Claude Sonnet | 92.59 % (25/27) | 83.33 % (10/12) |
| gpt-oss:20b | 92.59 % (25/27) | 50.0 % (6/12) |
| qwen3:32b | 88.89 % (24/27) | 50.0 % (6/12) |
| qwen3:14b | 92.59 % (25/27) | 41.67 % (5/12) |
| qwen2.5:3b | 55.56 % (15/27) | 0.0 % (0/12) |

La separación entre las dos columnas es la regularidad central del bloque. Para los seis sujetos, la exactitud en forma cerrada es mayor o igual que en emergente, y en la mayoría la brecha es amplia: Opus pasa del 100.0 % al 75.0 %, gpt-oss:20b del 92.59 % al 50.0 %, qwen3:32b del 88.89 % al 50.0 %, qwen3:14b del 92.59 % al 41.67 %, y qwen2.5:3b del 55.56 % al 0.0 %, esto es, no acertó ninguna de las doce preguntas emergentes. El caso de Sonnet es el de menor brecha: su forma cerrada es 92.59 % y su emergente 83.33 %. Conviene además consignar un cruce: la cifra emergente de Sonnet (83.33 %, diez de doce) es la más alta de los seis sujetos y queda por encima de la de Opus (75.0 %, nueve de doce), pese a que Opus es perfecto en forma cerrada.

Dicho de otro modo, el sujeto de mayor escala nominal alcanza el techo en las preguntas con fórmula explícita y, sin embargo, cede el primer puesto en las que exigen desplegar una dinámica. En el extremo inferior, qwen2.5:3b ilustra la regularidad en su forma más nítida: aprueba la mitad larga de las preguntas de forma cerrada y ninguna de las emergentes.

Las cifras por teoría completan el cuadro. Hay una teoría en la que los seis sujetos coinciden en la misma exactitud: en `automata_celular_crecimiento_urbano`, los seis obtienen 2 de 3 (66.67 %), porque todos aciertan las dos preguntas de forma cerrada y fallan o no responden la emergente. En `duncan_disimilitud` cinco de los seis sujetos obtienen también 2 de 3, pero qwen2.5:3b se queda en 1 de 3: falló una de las dos preguntas de forma cerrada, la pregunta 19, al devolver 40 frente al valor exacto 0.4. Hay teorías de techo: en `alonso_bid_rent`, `christaller_lugares_centrales`, `dla_batty_longley_fractal`, `sintaxis_espacial_integracion` y `zipf_rank_size`, varios sujetos alcanzan el 100.0 %. Y hay una teoría que resultó dura para casi todos, `von_thunen_anillos`, donde qwen2.5:3b, qwen3:14b y gpt-oss:20b obtienen 1 de 3 (33.33 %) y solo Opus alcanza el pleno; el escollo está en la pregunta 35, de valor exacto 16.0, que únicamente Opus respondió correctamente —Sonnet devolvió 6.625; qwen3:14b, 4; gpt-oss:20b, 0.48; qwen3:32b, 1.29; qwen2.5:3b, «Infinito»—.

## 5.5. Patrones de error con casos testigo

Reunimos ahora los patrones de error que recorren los dos bloques, cada uno anclado en un caso testigo cuya cifra consta en el registro. No los explicamos; los clasificamos.

**Inestabilidad entre intentos.** El mismo sujeto, sobre la misma tarea, produce un acierto y un fallo. Caso testigo: Opus en T1, correcto en el primer intento y erróneo en el segundo (349634804376851666458571); Sonnet en T2, correcto en el primero y con ruta de once barrios en el segundo.

**Error de dígito interno.** La respuesta tiene el orden de magnitud y a menudo el prefijo correcto, pero yerra en dígitos centrales. Casos testigo: Opus en T5 devuelve 651397404 y 651400404 frente a 651396404; en la pregunta 7, qwen2.5:3b devuelve 1762894 frente al valor 7943282, errando ya en el primer dígito, mientras qwen3:14b devuelve 7943000, dentro de la tolerancia del 1 %.

**Error de orden de magnitud.** La respuesta yerra por un factor de diez o más. Casos testigo: en la pregunta 24, de valor 220555.5556, qwen2.5:3b devuelve 8666666.67 y qwen3:14b 4333333.33, ambos órdenes de magnitud por encima, mientras gpt-oss:20b acierta con 220556; en la pregunta 23, qwen2.5:3b devuelve 15625 frente a 125000.

**Confusión de unidad o de escala.** La respuesta es el número correcto en otra escala. Caso testigo: en la pregunta 19, de valor 0.4, qwen2.5:3b devuelve 40 —el índice expresado como porcentaje sin normalizar—.

**Respuesta no numérica o de plantilla.** El sujeto devuelve un marcador, una variable simbólica o una fórmula sin evaluar en lugar de un número. Casos testigo: qwen2.5:3b responde «{final_fraction:.4f}» en la pregunta 30, «indice_disimilitud» en la 21, «D_estimate» en la 18 y «b» en la 39; todas se contabilizan como sin respuesta.

**Ausencia por límite de cómputo.** El sujeto no entrega respuesta porque agota el tiempo o no se recogen sus datos. Caso testigo: qwen3:32b agota el tiempo en T2 (605.2 s) y T4 (604.5 s) del primer bloque, y registra 605.2 y 604.5 segundos en el segundo; gpt-oss:20b devuelve «SIN_RESPUESTA» en ambos intentos de T1 y T4, con tiempos de hasta 108.5 segundos.

**Fallo selectivo del modelo mayor.** En tareas concretas, el sujeto de mayor escala nominal falla donde uno menor acierta. Casos testigo: en T1 y T5, Sonnet acierta donde Opus falla; en la pregunta 25, de valor 10.0, Opus acierta (10) y Sonnet falla (20); en la pregunta 30, Sonnet acierta (0.75, dentro de ±0.05 de 0.7507) y Opus falla (≈0.85). El patrón no tiene una dirección única: ni el modelo mayor falla siempre ni el menor acierta siempre.

**Alucinación de entidad.** En la tarea de relevancia, un sujeto introduce un elemento ausente de la escena. Caso testigo: qwen3:14b, en T6 (intento 1), dirige la alerta «a la mujer mayor», entidad que no figura en el enunciado, donde solo hay un niño, un acompañante y un repartidor.

## 5.6. T6, la tarea inversa: no computable

Cerramos con T6, que el experimento marca de modo distinto a las demás. Su valor exacto consta en el registro como «NO_COMPUTABLE» y el campo de corrección de cada respuesta como «NO_APLICA». La razón, según la nota del propio registro, es que la escena se entrega en lenguaje natural —un niño que pisa la calzada, un repartidor en moto que acelera, un acompañante, un semáforo en rojo, pavimento mojado— sin estructura de datos, sin métrica de peligro y sin función objetivo; no hay, por tanto, una salida única contra la cual medir acierto o error. En consecuencia, T6 no entra en ninguna de las exactitudes agregadas reportadas arriba: las diez celdas evaluables por sujeto del primer bloque corresponden a T1–T5.

Lo que el registro sí documenta son las respuestas, y conviene exhibirlas porque su variedad es el dato. Sonnet, en su primer intento, dirigió la alerta al repartidor en moto «porque es el único agente con capacidad de causar un impacto letal»; en su segundo intento, al niño «para detenerlo de inmediato». Opus, en su primer intento, al acompañante del niño «para que lo sujete»; en su segundo, al niño y secundariamente al acompañante. Entre los modelos locales, gpt-oss:20b dirigió la alerta al niño en sus dos intentos con respuesta idéntica; qwen3:14b al repartidor en un intento y, en el otro, a la inexistente «mujer mayor»; qwen2.5:3b dio una alerta genérica «a las personas en el cruce» y luego «al niño» con marcadores no solicitados.

El rasgo que el registro destaca es que estas respuestas son plausibles y coherentes pese a no ser comparables con una verdad de referencia: cada sujeto fija un foco de la alerta distinto —el agente activo del peligro, la víctima directa, el tercero capaz de intervenir— y argumenta a su favor. A diferencia de T1–T5, donde el fallo es un dígito errado, en T6 no hay dígito que errar. El registro consigna que los modelos «produjeron respuestas plausibles y coherentes» en «el dominio del significado contextual donde el cómputo puro no puede arrancar». Con ese dato cierra el cuadro experimental: cinco tareas con verdad de referencia donde el escalamiento no produjo una mejora monótona ni un acierto garantizado, y una tarea sin verdad de referencia donde la cuestión no es acertar sino fijar qué cuenta como relevante.

Hasta aquí la descripción. Las consecuencias —que el escalamiento mejora la imitación sin cruzar ningún umbral categorial, que el error de la IA estadística es el del token plausible y no el de la ejecución del algoritmo, y que T6 marca la frontera entre juicio determinante y reflexionante— se argumentan en el capítulo 06 (Crítica técnica) y se reinterpretan ontológicamente en el 07. Este capítulo deja sobre la mesa, sin glosa, las cifras que esos capítulos habrán de explicar.

## Referencias

- Dreyfus, H. L. (1992). *What Computers Still Can't Do: A Critique of Artificial Reason*. Cambridge, MA: MIT Press.
- Heidegger, M. (1927). *Sein und Zeit*. Halle: Max Niemeyer.
- Hui, Y. (2020). *Fragmentar el futuro. Ensayos sobre tecnodiversidad*. Buenos Aires: Caja Negra.
- Kant, I. (1790). *Kritik der Urteilskraft*. Berlin und Libau: Lagarde und Friederich.
- Wiener, N. (1948). *Cybernetics: or Control and Communication in the Animal and the Machine*. Cambridge, MA: MIT Press.
