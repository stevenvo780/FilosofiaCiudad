#!/usr/bin/env python3
"""
Inferencia local en Ollama (kratos) para las 39 preguntas del banco de teorias urbanas.
Uso: python sujetos_teorias_kratos.py --modelo <nombre>
       python sujetos_teorias_kratos.py  (corre todos los modelos en orden)
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error

# ── Configuracion ──────────────────────────────────────────────────────────────
OLLAMA_URL       = "http://100.98.217.229:11434/api/chat"
BANCO_FILE       = Path(__file__).parent.parent / "simulaciones" / "banco_preguntas.json"
RESPUESTAS_FILE  = Path(__file__).parent / "respuestas_teorias_kratos.json"
HTTP_TIMEOUT     = 300        # segundos por peticion HTTP
MAX_REINTENTOS   = 1          # 1 reintento HTTP por pregunta
MODELO_TIMEOUT   = 40 * 60   # 40 minutos por modelo

MODELOS = ["qwen2.5:3b", "qwen3:14b", "gpt-oss:20b", "qwen3:32b"]

SYSTEM_PROMPT = (
    "Resuelve la tarea razonando por escrito si lo necesitas. "
    "Tu ultima linea debe ser exactamente: Respuesta final: <valor>"
)

# ── Carga banco de preguntas ───────────────────────────────────────────────────

def load_banco() -> list[dict]:
    with open(BANCO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Solo devuelve n y q; NUNCA incluye valor_exacto, tolerancia, como_computar
    return [{"n": item["n"], "q": item["q"]} for item in data]

# ── Persistencia ───────────────────────────────────────────────────────────────

def load_respuestas() -> dict:
    if RESPUESTAS_FILE.exists():
        try:
            with open(RESPUESTAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_respuesta(data: dict, key: str, entry: dict):
    data[key] = entry
    with open(RESPUESTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── Extraccion robusta ─────────────────────────────────────────────────────────

def strip_think_blocks(text: str) -> str:
    text = re.sub(r"<think>.*?</think>",       "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_respuesta_final(text: str) -> tuple[str, str]:
    """Returns (respuesta_final, nota)."""
    clean = strip_think_blocks(text)
    pattern = re.compile(r"Respuesta\s+final\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE)
    matches = list(pattern.finditer(clean))
    if matches:
        value = matches[-1].group(1).strip()
        return value, ""
    else:
        cola = clean.strip()[-300:]
        return "SIN_RESPUESTA", cola

# ── HTTP ───────────────────────────────────────────────────────────────────────

def make_key(modelo: str, n: int) -> str:
    return f"{modelo}|{n}"


def post_chat(modelo: str, pregunta_q: str, use_think: bool = False) -> str:
    """POST to Ollama /api/chat; returns message content string."""
    payload: dict = {
        "model":  modelo,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 6144,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": pregunta_q},
        ],
    }
    if use_think:
        payload["think"] = False

    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    result = json.loads(raw)
    return result["message"]["content"]

# ── Runner por modelo ──────────────────────────────────────────────────────────

def run_modelo(modelo: str, banco: list[dict]) -> dict:
    """
    Ejecuta las 39 preguntas para un modelo.
    Devuelve {"respondidas": int, "omitidas": int, "razon_omision": str}.
    """
    print(f"\n{'='*65}", flush=True)
    print(f"MODELO: {modelo}", flush=True)
    print(f"{'='*65}", flush=True)

    data         = load_respuestas()
    modelo_start = time.time()
    is_qwen3     = "qwen3" in modelo.lower()

    respondidas = 0
    omitidas    = 0

    for pregunta in banco:
        n = pregunta["n"]
        q = pregunta["q"]
        key = make_key(modelo, n)

        # Reanudable: salta si ya existe
        if key in data:
            print(f"  [SKIP] n={n} (ya guardado)", flush=True)
            respondidas += 1
            continue

        # Timeout del modelo
        elapsed_modelo = time.time() - modelo_start
        if elapsed_modelo > MODELO_TIMEOUT:
            omitidas = len(banco) - respondidas
            print(
                f"  [TIMEOUT_MODELO] {modelo} supero 40 min; "
                f"respondidas={respondidas}, omitidas restantes={omitidas}",
                flush=True,
            )
            # Registrar omision para las preguntas no hechas
            for preg_restante in banco:
                k2 = make_key(modelo, preg_restante["n"])
                if k2 not in data:
                    entry_omitida = {
                        "modelo": modelo,
                        "n":      preg_restante["n"],
                        "respuesta_final": "OMITIDA_TIMEOUT",
                        "nota":   f"Modelo abandono tras >40 min; respondidas hasta ese punto: {respondidas}",
                        "raw":    "",
                        "elapsed_s": None,
                    }
                    save_respuesta(data, k2, entry_omitida)
            return {"respondidas": respondidas, "omitidas": omitidas, "razon_omision": "timeout_modelo"}

        print(f"  [n={n}] ...", end=" ", flush=True)
        t0 = time.time()

        raw_text  = None
        error_msg = None
        use_think = is_qwen3

        # 1 intento + 1 reintento
        for intento_http in range(MAX_REINTENTOS + 1):
            try:
                raw_text = post_chat(modelo, q, use_think=use_think)
                break
            except urllib.error.HTTPError as e:
                body_err = e.read().decode("utf-8", errors="replace")
                # Si el servidor rechaza el campo "think", reintentar sin el
                if use_think and ("think" in body_err.lower() or e.code in (400, 422)):
                    print(f"[retry sin think] ", end="", flush=True)
                    use_think = False
                    continue
                error_msg = f"HTTPError {e.code}: {body_err[:300]}"
                break
            except Exception as exc:
                if intento_http == 0:
                    print(f"[retry] ", end="", flush=True)
                    time.sleep(3)
                    continue
                error_msg = str(exc)[:300]
                break

        elapsed_req = time.time() - t0
        print(f"({elapsed_req:.1f}s)", flush=True)

        if raw_text is None:
            respuesta_final = "ERROR"
            nota            = error_msg or "Sin respuesta del servidor"
            raw_truncated   = ""
        else:
            respuesta_final, nota = extract_respuesta_final(raw_text)
            raw_truncated         = raw_text[:1500]

        entry = {
            "modelo":          modelo,
            "n":               n,
            "respuesta_final": respuesta_final,
            "nota":            nota,
            "raw":             raw_truncated,
            "elapsed_s":       round(elapsed_req, 1),
        }
        save_respuesta(data, key, entry)
        respondidas += 1
        print(f"    => Respuesta final: {respuesta_final[:120]}", flush=True)

    print(f"\n[DONE] {modelo}: respondidas={respondidas}", flush=True)
    return {"respondidas": respondidas, "omitidas": 0, "razon_omision": ""}

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Inferencia local Ollama kratos — banco de teorias urbanas"
    )
    parser.add_argument(
        "--modelo",
        default=None,
        help="Nombre del modelo Ollama (omitir = todos en orden)",
    )
    args = parser.parse_args()

    banco = load_banco()
    print(f"Banco cargado: {len(banco)} preguntas", flush=True)

    modelos_a_correr = [args.modelo] if args.modelo else MODELOS

    resumen = {}
    for modelo in modelos_a_correr:
        resultado = run_modelo(modelo, banco)
        resumen[modelo] = resultado

    print("\n" + "="*65, flush=True)
    print("RESUMEN FINAL", flush=True)
    print("="*65, flush=True)
    for m, r in resumen.items():
        print(
            f"  {m}: respondidas={r['respondidas']}, omitidas={r['omitidas']}"
            + (f" [{r['razon_omision']}]" if r["razon_omision"] else ""),
            flush=True,
        )


if __name__ == "__main__":
    main()
