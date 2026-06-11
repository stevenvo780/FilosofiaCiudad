#!/usr/bin/env python3
"""
Inferencia local en Ollama (kratos) para las tareas del experimento.
Uso: python sujetos_kratos.py --modelo <nombre>
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
OLLAMA_URL = "http://100.98.217.229:11434/api/chat"
RESPUESTAS_FILE = Path(__file__).parent / "respuestas_kratos.json"
HTTP_TIMEOUT = 300  # segundos por generacion
MAX_INTENTOS = 2
MODELO_TIMEOUT = 25 * 60  # 25 minutos por modelo

SYSTEM_PROMPT = (
    "Resuelve la tarea razonando por escrito si lo necesitas. "
    "Tu ultima linea debe ser exactamente: Respuesta final: <valor>"
)

TAREAS = [
    {
        "id": "t1_multiplicacion",
        "prompt_llm": "Eres una calculadora. NO uses herramientas, codigo ni calculadora externa; responde solo con tu razonamiento interno. Multiplica estos dos enteros exactos y da el producto completo, sin notacion cientifica, sin redondear, con todos sus digitos: 387465129847 x 902341765893. No expliques pasos largos; basta el resultado. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <un solo numero entero, sin comas, sin puntos, sin espacios>",
    },
    {
        "id": "t2_camino_corto",
        "prompt_llm": "Tienes una red vial entre barrios. Es un grafo NO dirigido; cada linea es una calle entre dos barrios con su distancia en minutos. NO uses herramientas ni codigo; razona internamente. Aristas (barrio_A - barrio_B = peso):\nAltavista-Bellavista=4; Altavista-Cumbres=7; Bellavista-Cumbres=2; Bellavista-Dorado=9; Cumbres-Esmeralda=3; Dorado-Esmeralda=6; Dorado-Farallon=5; Esmeralda-Girasol=8; Farallon-Girasol=1; Farallon-Horizonte=4; Girasol-Horizonte=2; Girasol-Iguazu=7; Horizonte-Jacaranda=3; Iguazu-Jacaranda=2; Iguazu-Kennedy=6; Jacaranda-Lagos=5; Kennedy-Lagos=4; Kennedy-Miramar=8; Lagos-Nogal=3; Miramar-Nogal=2; Miramar-Olivos=5; Nogal-Palermo=6; Olivos-Palermo=1; Palermo-Quinta=4; Quinta-Roble=3; Roble-Sauce=2; Sauce-Tejar=5; Tejar-Urapan=4; Urapan-Veranda=2; Veranda-Ximena=6; Ximena-Yarumal=3; Yarumal-Zafiro=2; Olivos-Roble=9; Nogal-Sauce=7; Lagos-Tejar=10; Quinta-Urapan=8; Roble-Veranda=6; Sauce-Ximena=9; Tejar-Yarumal=7; Urapan-Zafiro=11; Altavista-Dorado=12; Cumbres-Farallon=10; Esmeralda-Horizonte=9.\nEncuentra el camino de MENOR distancia total desde Altavista hasta Zafiro. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <secuencia de barrios desde Altavista hasta Zafiro separados por coma y un espacio, p.ej. Altavista, Bellavista, ...>",
    },
    {
        "id": "t3_conteo_reticula",
        "prompt_llm": "Imagina una cuadricula de calles de una ciudad: 12 cuadras de ancho por 12 cuadras de alto, formando una retícula. Un repartidor parte de la esquina inferior izquierda y debe llegar a la esquina superior derecha moviendose SOLO hacia el este (derecha) o hacia el norte (arriba), nunca al oeste ni al sur. NO uses herramientas ni codigo; razona internamente. Calcula cuantas rutas distintas existen. Da el numero entero exacto. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <un solo numero entero, sin comas, sin puntos, sin espacios>",
    },
    {
        "id": "t4_recursion_afin",
        "prompt_llm": "Tienes una funcion de retroalimentacion: f(x) = (137 * x + 991) mod 100000. El resultado de cada paso se vuelve la entrada del paso siguiente (retroalimentacion). NO uses herramientas ni codigo; razona internamente. Empieza con la semilla x = 42 y aplica f exactamente 40 veces (es decir, calcula x_1 = f(x_0), x_2 = f(x_1), ..., hasta x_40, con x_0 = 42). Da el valor entero de x_40. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <un solo numero entero entre 0 y 99999, sin comas, sin puntos, sin espacios>",
    },
    {
        "id": "t5_calculo_exteriorizado",
        "prompt_llm": "Tienes 30 lecturas de consumo energetico (en vatios-hora) de sensores de alumbrado de una ciudad. NO uses herramientas ni codigo; razona internamente. Lecturas: 4821, 3990, 5172, 4408, 3765, 6011, 2987, 5540, 4123, 3876, 5298, 4710, 3654, 6102, 2890, 5471, 4019, 3788, 5630, 4255, 3912, 6044, 2976, 5388, 4187, 3801, 5519, 4630, 3745, 6088. Calcula la SUMA DE LOS CUADRADOS de las 30 lecturas (eleva cada lectura al cuadrado y suma todos los cuadrados). Da el numero entero exacto. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <un solo numero entero, sin comas, sin puntos, sin espacios>",
    },
    {
        "id": "t6_relevancia_escena",
        "prompt_llm": "Lee esta escena urbana y responde. NO uses herramientas ni codigo; razona como un observador humano. Escena: 'Son las 7:40 de la manana en una esquina del centro. Un hombre con traje corre hacia la parada del bus mientras revisa su reloj; una mujer mayor con bolsas de mercado esta detenida en mitad del cruce mirando hacia ambos lados sin avanzar; un nino suelta la mano de su acompanante y da un paso hacia la calzada; el semaforo peatonal acaba de ponerse en rojo; un repartidor en moto acelera al ver el cambio de luz; cae una llovizna fina y el pavimento empieza a brillar.' Pregunta: si tu fueras un sistema de asistencia urbana que solo puede emitir UNA alerta para evitar el peor desenlace, a quien o a que situacion debe dirigirse esa alerta y por que es la mas relevante de la escena. Termina tu respuesta EXACTAMENTE con la linea: Respuesta final: <una sola frase indicando a quien o a que se dirige la alerta>",
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────

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


def strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks and similar reasoning channels."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_respuesta_final(text: str) -> tuple[str, str]:
    """
    Returns (respuesta_final, nota).
    respuesta_final is the value after the last 'Respuesta final:' occurrence.
    If not found, returns ('SIN_RESPUESTA', last 200 chars).
    """
    clean = strip_think_blocks(text)
    # Find all occurrences (case-insensitive)
    pattern = re.compile(r"Respuesta\s+final\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE)
    matches = list(pattern.finditer(clean))
    if matches:
        last = matches[-1]
        value = last.group(1).strip()
        return value, ""
    else:
        last_200 = clean.strip()[-200:]
        return "SIN_RESPUESTA", last_200


def make_key(modelo: str, tarea_id: str, intento: int) -> str:
    return f"{modelo}|{tarea_id}|{intento}"


def post_chat(modelo: str, tarea_prompt: str, use_think: bool = False) -> str:
    """POST to Ollama chat endpoint, return message content string."""
    payload: dict = {
        "model": modelo,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 6144,
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": tarea_prompt},
        ],
    }
    if use_think:
        payload["think"] = False

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    result = json.loads(raw)
    # Ollama /api/chat non-stream response: result["message"]["content"]
    return result["message"]["content"]


def run_modelo(modelo: str):
    print(f"\n{'='*60}", flush=True)
    print(f"MODELO: {modelo}", flush=True)
    print(f"{'='*60}", flush=True)

    data = load_respuestas()
    modelo_start = time.time()

    # Determine if this is a qwen3 model (supports think field)
    is_qwen3 = "qwen3" in modelo.lower()

    for tarea in TAREAS:
        tarea_id = tarea["id"]
        prompt = tarea["prompt_llm"]

        for intento in range(1, MAX_INTENTOS + 1):
            key = make_key(modelo, tarea_id, intento)

            # Skip if already done
            if key in data:
                print(f"  [SKIP] {tarea_id} intento={intento} (ya guardado)", flush=True)
                continue

            # Check model timeout
            elapsed = time.time() - modelo_start
            if elapsed > MODELO_TIMEOUT:
                print(f"  [TIMEOUT_MODELO] {modelo} supero 25 min; abandonando.", flush=True)
                return False  # signal timeout

            print(f"  [{tarea_id}] intento={intento} ...", end=" ", flush=True)
            t0 = time.time()

            raw_text = None
            error_msg = None
            use_think = is_qwen3

            # First attempt with think=False if qwen3
            for retry in range(2):
                try:
                    raw_text = post_chat(modelo, prompt, use_think=use_think)
                    break
                except urllib.error.HTTPError as e:
                    body_err = e.read().decode("utf-8", errors="replace")
                    if use_think and ("think" in body_err.lower() or e.code in (400, 422)):
                        print(f"[retry sin think] ", end="", flush=True)
                        use_think = False
                        continue
                    error_msg = f"HTTPError {e.code}: {body_err[:300]}"
                    break
                except Exception as exc:
                    if retry == 0:
                        print(f"[retry] ", end="", flush=True)
                        time.sleep(2)
                        continue
                    error_msg = str(exc)[:300]
                    break

            elapsed_req = time.time() - t0
            print(f"({elapsed_req:.1f}s)", flush=True)

            if raw_text is None:
                respuesta_final = "ERROR"
                nota = error_msg or "Sin respuesta del servidor"
                raw_truncated = ""
            else:
                respuesta_final, nota = extract_respuesta_final(raw_text)
                raw_truncated = raw_text[:2000]

            entry = {
                "modelo": modelo,
                "tarea_id": tarea_id,
                "intento": intento,
                "respuesta_final": respuesta_final,
                "nota": nota,
                "raw": raw_truncated,
                "elapsed_s": round(elapsed_req, 1),
            }
            save_respuesta(data, key, entry)
            print(f"    => Respuesta final: {respuesta_final[:120]}", flush=True)

    print(f"\n[DONE] {modelo} completado.", flush=True)
    return True


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inferencia local Ollama kratos")
    parser.add_argument("--modelo", required=True, help="Nombre del modelo Ollama")
    args = parser.parse_args()

    success = run_modelo(args.modelo)
    sys.exit(0 if success else 2)


if __name__ == "__main__":
    main()
