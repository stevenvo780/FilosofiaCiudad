# Filosofía de la ciudad

Este repositorio reúne materiales del curso **Filosofía de la ciudad: ontología, poder y política**. El contenido actual está organizado por clase y combina:

- apuntes académicos en `Markdown`;
- prompts reutilizables para asistentes;
- recursos visuales generados con Python.

## Estructura actual

- `Clase 1/`: materiales y notas de la primera clase.
- `prompts/`: prompt base del asistente académico.
- `requirements.txt`: dependencias Python del generador gráfico.
- `AGENTS.md`: contexto de trabajo para Codex en este workspace.

## Material principal de `Clase 1`

- `Clase 1/README.md`: índice interno de la clase.
- `utils/`: scripts generadores de apoyos visuales.
- `Clase 1/apoyosGraficosCreados/`: salidas gráficas de la clase.
- `Clase 1/diferencias_ciudades_griegas_romanas.md`: explicación conceptual y glosario del gráfico.
- `Clase 1/*.md`: resto de notas temáticas de la clase.

## Uso rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python utils/generar_grafo.py
```

## Nota sobre VS Code

Si Pylance marca `matplotlib`, `networkx` o `numpy` como no resueltos, selecciona el intérprete de `.venv` en VS Code.
