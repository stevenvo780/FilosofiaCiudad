# Algoritmo simple para distribucion urbana

## Idea central

Este material muestra una tesis concreta y defendible: para una tarea acotada de planificacion urbana, un algoritmo simple, explicable y reproducible puede rendir mejor que una IA generalista.

Aqui "mejor" no significa que siempre produzca la ciudad perfecta. Significa algo mas preciso para ingenieria y planificacion:

- usa reglas claras
- produce siempre una salida verificable
- permite auditar cada decision
- cuesta muy poco computacionalmente
- se puede ajustar con criterios urbanos concretos

## Teoria elegida

La base del ejemplo es un modelo bioinspirado en `Physarum polycephalum`. No es un hongo estricto, sino un moho mucilaginoso, pero se estudia mucho junto a modelos biologicos de crecimiento eficiente.

La idea es util porque este organismo tiende a formar redes de conexion muy eficientes entre puntos de alimento. En investigacion se ha usado como inspiracion para:

- redes de transporte
- conexiones optimizadas
- reduccion de costo de infraestructura
- equilibrio entre cobertura y longitud total de red

En urbanismo, esta idea se puede traducir asi:

- los centros urbanos atraen densidad
- las conexiones entre nodos deben ser cortas y robustas
- un corredor fuerte de transporte ordena el crecimiento
- el borde ecologico limita la expansion ciega

## Que hace el algoritmo

El script `repos/generar_distribucion_urbana.py` construye una imagen urbana con reglas simples:

1. Define un centro principal y varios subcentros.
2. Calcula la atraccion espacial de cada punto del mapa hacia esos nodos.
3. Agrega un eje fuerte de transporte y un eje logistico.
4. Introduce un corredor de agua y areas verdes como restriccion ecologica.
5. Clasifica cada celda del territorio en:
   `core`, `mixed`, `residential`, `productive` o `green`.
6. Conecta los nodos con una red minima usando un arbol de expansion minima.
7. Agrega enlaces secundarios para robustez territorial.

## Por que esto puede superar a una IA generalista

En una tarea como "distribuir nodos urbanos y conectarlos con baja longitud total y buena cobertura", una IA generalista suele tener tres problemas:

- no garantiza consistencia entre ejecuciones
- puede producir propuestas bonitas pero poco auditables
- mezcla intuicion textual con criterios tecnicos no explicitados

En cambio, un algoritmo simple como este tiene ventajas directas:

- cada parametro tiene significado urbano
- cada cambio puede medirse
- la solucion es replicable
- el costo computacional es bajo
- se integra facilmente con datos reales

La afirmacion fuerte y razonable no es "los algoritmos simples vencen siempre a la mejor IA". La formulacion correcta es esta:

> En tareas urbanas bien definidas, con objetivos geometricos y restricciones explicitas, un algoritmo simple puede superar a una IA generalista en transparencia, estabilidad, trazabilidad y control operativo.

## Que se uso exactamente

- lenguaje: `Python 3`
- librerias externas: ninguna
- salida principal: `Material/distribucion_urbana_physarum.svg`
- salida auxiliar: `Material/distribucion_urbana_physarum.json`
- semilla fija: `23`

## Variables urbanas usadas

- atraccion por centro principal
- atraccion por subcentros
- proximidad al eje de transporte
- proximidad al eje logistico
- penalizacion por cercania al corredor de agua
- penalizacion ligera por borde
- ruido pequeno para evitar rigidez total

## Lectura de la imagen

- rojo: centro de alta densidad
- naranja: uso mixto
- amarillo: residencial
- azul gris: productivo y logistico
- verde: corredor ecologico o baja ocupacion
- linea oscura: red vial minima
- linea azul: eje principal de transporte

## Valor filosofico y metodologico

Este ejemplo tambien sirve para una discusion filosofica sobre tecnica y ciudad:

- la tecnica no necesita ser opaca para ser poderosa
- un sistema simple puede contener mas racionalidad practica que una caja negra
- en planificacion, explicar por que se decide algo puede ser mas importante que impresionar visualmente

## Limites honestos del modelo

Este algoritmo es una demostracion, no un plan regulador real. No incorpora:

- topografia real
- costo del suelo
- datos demograficos observados
- riesgo hidrologico detallado
- normativa urbana
- tiempos reales de viaje

## Conclusion

La mejor leccion de este ejercicio es metodologica: cuando el problema esta bien definido, un algoritmo pequeno y claro puede ser mas util que una IA poderosa pero generica.

No reemplaza toda la planificacion urbana. Pero para estructurar redes, ordenar centralidades y producir una primera distribucion territorial coherente, este tipo de algoritmo es extremadamente eficiente.
