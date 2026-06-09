---
titulo: "Filosofía de la ciudad: ontología, poder y política — Portal del curso"
clase: "Raíz"
temas: [ontologia, ciudad-antigua, tecnica-urbana, poder]
---

# Filosofía de la ciudad: ontología, poder y política

Curso de filosofía urbana organizado en torno a tres ejes: **ontología de la ciudad** (qué es la ciudad, cuál es su telos), **ciudad antigua** (Grecia y Roma: formas, instituciones y espacio), y **técnica, poder y orden urbano** (infraestructura, planificación y estratificación). El repositorio reúne trece unidades temáticas distribuidas en una clase inaugural y un corpus de notas de referencia cruzada.

---

## Estructura de carpetas

```
/
├── clases/                  # Sesiones del curso, ordenadas cronológicamente
│   └── clase-01-fundamentos/
│       ├── README.md        # Índice y presentación de la clase
│       ├── notas/           # Notas de sesión (.md)
│       └── recursos/        # Imágenes y materiales de apoyo
├── temas/                   # Índices temáticos transversales
│   ├── ontologia-de-la-ciudad.md
│   ├── ciudad-antigua-grecia-y-roma.md
│   ├── tecnica-urbana.md
│   └── poder-y-orden-urbano.md
├── glosario.md              # Términos técnicos del curso
├── utils/                   # Scripts Python para generar gráficos
│   ├── generar_grafo.py
│   ├── generar_distribucion_urbana.py
│   ├── generar_diagrama_membrana_urbana.py
│   ├── generar_comparativa_ciudades_amuralladas.py
│   └── generar_mapa_mental_fisico_escalabilidad.py
├── meta/                    # Metadatos del repositorio (configuración, plantillas)
├── requirements.txt         # Dependencias Python
└── .github/                 # Instrucciones para GitHub Copilot
```

---

## Vía 1 — Índice cronológico por clase

| Clase | Título | Enlace |
|-------|--------|--------|
| Clase 1 | Fundamentos: ontología, ciudad antigua y técnica | [clases/clase-01-fundamentos/README.md](clases/clase-01-fundamentos/README.md) |

Las clases siguientes se incorporarán a medida que se dicten. Cada carpeta de clase contiene su propio `README.md` con el orden de lectura recomendado, las notas de sesión en `notas/` y los recursos visuales en `recursos/`.

---

## Vía 2 — Índice temático por eje

Los índices temáticos agrupan notas de distintas clases según el eje conceptual al que pertenecen. Son el punto de entrada recomendado para la lectura no lineal.

| Eje | Descripción | Enlace |
|-----|-------------|--------|
| Ontología de la ciudad | Qué es la ciudad, su telos e intencionalidad; lecturas de Platón, Aristóteles y la distinción polis/urbs | [temas/ontologia-de-la-ciudad.md](temas/ontologia-de-la-ciudad.md) |
| Ciudad antigua: Grecia y Roma | Espacio urbano clásico: acrópolis, ágora, pomerium, vías, murallas, Hipodamo de Mileto, expansión imperial romana | [temas/ciudad-antigua-grecia-y-roma.md](temas/ciudad-antigua-grecia-y-roma.md) |
| Técnica urbana | Infraestructura y pensamiento técnico: Ortega y Gasset, Heidegger, modelo Physarum de distribución urbana | [temas/tecnica-urbana.md](temas/tecnica-urbana.md) |
| Poder y orden urbano | Planificación centralizada, estratificación, orden político y económico de la ciudad | [temas/poder-y-orden-urbano.md](temas/poder-y-orden-urbano.md) |

---

## Glosario

El archivo [glosario.md](glosario.md) recoge los términos técnicos del curso con definición breve y referencia a la nota donde aparecen por primera vez. Incluye: *polis*, *urbs*, *agora*, *acropolis*, *civitas*, *urbanitas*, *cite*, *ville*, *telos*, *pomerium*, entre otros.

---

## Recursos visuales / scripts

La carpeta `utils/` contiene scripts Python que generan los gráficos y diagramas empleados en el curso. Para ejecutarlos:

```bash
# 1. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar los scripts según se necesite
python utils/generar_grafo.py
python utils/generar_distribucion_urbana.py
python utils/generar_diagrama_membrana_urbana.py
python utils/generar_comparativa_ciudades_amuralladas.py
python utils/generar_mapa_mental_fisico_escalabilidad.py
```

Las dependencias principales son `matplotlib`, `networkx`, `numpy` y `Pillow` (versiones especificadas en `requirements.txt`). Las imágenes generadas se depositan en la subcarpeta `recursos/` de la clase correspondiente.
