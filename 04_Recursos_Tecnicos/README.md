# Recursos tecnicos

## Carpetas

- `scripts/`: generadores de imagenes y datos.
- `prompts/`: instrucciones reutilizables para asistentes.
- `requirements.txt`: dependencias de los generadores visuales.

## Entorno

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r 04_Recursos_Tecnicos/requirements.txt
```

## Generacion

```bash
python 04_Recursos_Tecnicos/scripts/generar_grafo.py
python 04_Recursos_Tecnicos/scripts/generar_diagrama_membrana_urbana.py
python 04_Recursos_Tecnicos/scripts/generar_comparativa_ciudades_amuralladas.py
python 04_Recursos_Tecnicos/scripts/generar_mapa_mental_fisico_escalabilidad.py
python 04_Recursos_Tecnicos/scripts/exportar_distribucion_urbana_png.py
```

Las salidas se escriben en la carpeta correspondiente de `01_Clases/Clase_01/`.
