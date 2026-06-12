#!/usr/bin/env python3
"""
Corrida EXPLORATORIA del Experimento 1 con sujetos locales nuevos.
NO toca el canon: escribe a experimento/exploratorio/respuestas_exploratorio.json.

Diferencias declaradas respecto a las condiciones canónicas (2026-06-10):
- MODELO_TIMEOUT 120 min (canon: 25 min; el 32B canónico sufrió omisiones por ese tope).
- HTTP_TIMEOUT 900 s por generación (canon: 300 s).
- Sujetos orientados a código (devstral, qwen3-coder*): se declara porque puede
  favorecerlos en tareas aritmético-algorítmicas. qwen3-coder-next ~80B (MoE,
  q4_K_M, 51,7 GB) corre repartido RAM+GPU.
Mismos prompts, temperature 0.2, num_predict 6144, 2 intentos (idéntico al canon).
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sujetos_kratos as sk  # noqa: E402

sk.RESPUESTAS_FILE = HERE / "respuestas_exploratorio.json"
sk.HTTP_TIMEOUT = 900
sk.MODELO_TIMEOUT = 120 * 60

MODELOS = [
    "devstral:24b",
    "qwen3-coder:30b",
    "qwen3-coder-next:q4_K_M",
]

condiciones = {
    "tipo": "EXPLORATORIO - no canónico",
    "fecha": "2026-06-12",
    "plataforma": "kratos",
    "hardware": "RTX 5070 Ti 16 GB + RTX 2060 6 GB + RAM (80B repartido)",
    "modelos": MODELOS,
    "nota_sujetos": "Modelos orientados a código; puede favorecerlos en tareas aritméticas. Declarado.",
    "temperature": 0.2,
    "num_predict": 6144,
    "intentos_por_modelo": 2,
    "timeout_http_s": 900,
    "timeout_modelo_min": 120,
    "diferencia_vs_canon": "Timeouts ampliados (canon: 300 s / 25 min). Prompts y opciones idénticos.",
}
with open(HERE / "condiciones_exploratorio.json", "w", encoding="utf-8") as f:
    json.dump(condiciones, f, ensure_ascii=False, indent=2)

t0 = time.time()
for m in MODELOS:
    print(f"\n######## INICIANDO {m} (t+{(time.time()-t0)/60:.1f} min) ########", flush=True)
    try:
        ok = sk.run_modelo(m)
        print(f"######## {m}: {'COMPLETO' if ok else 'TIMEOUT_MODELO'} ########", flush=True)
    except Exception as e:
        print(f"######## {m}: ERROR {e} ########", flush=True)

print(f"\n[FIN] Corrida exploratoria terminada en {(time.time()-t0)/60:.1f} min", flush=True)
