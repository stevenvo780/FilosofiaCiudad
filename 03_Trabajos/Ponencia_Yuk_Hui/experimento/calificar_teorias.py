#!/usr/bin/env python3
"""
calificar_teorias.py
Califica las respuestas de 6 sujetos (4 locales + 2 API) en el banco de preguntas de teorías urbanas.
Genera resultados_teorias.json y tres gráficos PNG en presentacion/assets/.
"""

import json
import re
import unicodedata
import datetime
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── rutas ────────────────────────────────────────────────────────────────────
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad")
BANCO_PATH = BASE / "03_Trabajos/Ponencia_Yuk_Hui/simulaciones/banco_preguntas.json"
KRATOS_PATH = BASE / "03_Trabajos/Ponencia_Yuk_Hui/experimento/respuestas_teorias_kratos.json"
OUT_JSON = BASE / "03_Trabajos/Ponencia_Yuk_Hui/experimento/resultados_teorias.json"
ASSETS_DIR = BASE / "03_Trabajos/Ponencia_Yuk_Hui/presentacion/assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ── respuestas API embebidas ──────────────────────────────────────────────────
API_RESPONSES = [
 {"n":1,"teoria":"alonso_bid_rent","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 13.33","confianza":"alta","uso_herramientas":False},
 {"n":1,"teoria":"alonso_bid_rent","modelo":"claude-opus","respuesta_final":"Respuesta final: 13.33 km","confianza":"alta","uso_herramientas":False},
 {"n":2,"teoria":"alonso_bid_rent","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 200","confianza":"alta","uso_herramientas":False},
 {"n":2,"teoria":"alonso_bid_rent","modelo":"claude-opus","respuesta_final":"Respuesta final: 200","confianza":"alta","uso_herramientas":False},
 {"n":3,"teoria":"alonso_bid_rent","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.4444 (≈4/9; el grupo pobre ocupa [0, 13.33] km de los 30 km totales, ya que R_pobre > R_rico para d < 200/15 ≈ 13.33 km, fracción = 13.33/30 = 4/9 ≈ 0.4444)","confianza":"alta","uso_herramientas":False},
 {"n":3,"teoria":"alonso_bid_rent","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.444","confianza":"alta","uso_herramientas":False},
 {"n":4,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.751","confianza":"alta","uso_herramientas":False},
 {"n":4,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.751","confianza":"alta","uso_herramientas":False},
 {"n":5,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0","confianza":"media","uso_herramientas":False},
 {"n":5,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-opus","respuesta_final":"Respuesta final: 0","confianza":"alta","uso_herramientas":False},
 {"n":6,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 10000","confianza":"baja","uso_herramientas":False},
 {"n":6,"teoria":"automata_celular_crecimiento_urbano","modelo":"claude-opus","respuesta_final":"No determinable sin ejecutar codigo","confianza":"baja","uso_herramientas":False},
 {"n":7,"teoria":"bettencourt_west_escalamiento","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 7943282","confianza":"alta","uso_herramientas":False},
 {"n":7,"teoria":"bettencourt_west_escalamiento","modelo":"claude-opus","respuesta_final":"Respuesta final: 7943282","confianza":"alta","uso_herramientas":False},
 {"n":8,"teoria":"bettencourt_west_escalamiento","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 2^1.15 ≈ 2.219","confianza":"alta","uso_herramientas":False},
 {"n":8,"teoria":"bettencourt_west_escalamiento","modelo":"claude-opus","respuesta_final":"Respuesta final: 2.22","confianza":"alta","uso_herramientas":False},
 {"n":9,"teoria":"bettencourt_west_escalamiento","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1.15","confianza":"alta","uso_herramientas":False},
 {"n":9,"teoria":"bettencourt_west_escalamiento","modelo":"claude-opus","respuesta_final":"Respuesta final: 1.15","confianza":"alta","uso_herramientas":False},
 {"n":10,"teoria":"braess_wardrop_equilibrio","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 65","confianza":"alta","uso_herramientas":False},
 {"n":10,"teoria":"braess_wardrop_equilibrio","modelo":"claude-opus","respuesta_final":"Respuesta final: 65","confianza":"alta","uso_herramientas":False},
 {"n":11,"teoria":"braess_wardrop_equilibrio","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 80","confianza":"alta","uso_herramientas":False},
 {"n":11,"teoria":"braess_wardrop_equilibrio","modelo":"claude-opus","respuesta_final":"Respuesta final: 80","confianza":"alta","uso_herramientas":False},
 {"n":12,"teoria":"braess_wardrop_equilibrio","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 15","confianza":"alta","uso_herramientas":False},
 {"n":12,"teoria":"braess_wardrop_equilibrio","modelo":"claude-opus","respuesta_final":"Respuesta final: 15","confianza":"alta","uso_herramientas":False},
 {"n":13,"teoria":"christaller_lugares_centrales","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 18","confianza":"alta","uso_herramientas":False},
 {"n":13,"teoria":"christaller_lugares_centrales","modelo":"claude-opus","respuesta_final":"Respuesta final: 18","confianza":"alta","uso_herramientas":False},
 {"n":14,"teoria":"christaller_lugares_centrales","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 259.81 km2","confianza":"alta","uso_herramientas":False},
 {"n":14,"teoria":"christaller_lugares_centrales","modelo":"claude-opus","respuesta_final":"Respuesta final: 259.81 km²","confianza":"alta","uso_herramientas":False},
 {"n":15,"teoria":"christaller_lugares_centrales","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 7014.87","confianza":"alta","uso_herramientas":False},
 {"n":15,"teoria":"christaller_lugares_centrales","modelo":"claude-opus","respuesta_final":"Respuesta final: 7014.87","confianza":"alta","uso_herramientas":False},
 {"n":16,"teoria":"dla_batty_longley_fractal","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1.27","confianza":"alta","uso_herramientas":False},
 {"n":16,"teoria":"dla_batty_longley_fractal","modelo":"claude-opus","respuesta_final":"Respuesta final: 1.27","confianza":"alta","uso_herramientas":False},
 {"n":17,"teoria":"dla_batty_longley_fractal","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 650","confianza":"alta","uso_herramientas":False},
 {"n":17,"teoria":"dla_batty_longley_fractal","modelo":"claude-opus","respuesta_final":"Respuesta final: ~650 celdas (200 × 2^1.7 ≈ 649.6)","confianza":"alta","uso_herramientas":False},
 {"n":18,"teoria":"dla_batty_longley_fractal","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1.67","confianza":"media","uso_herramientas":False},
 {"n":18,"teoria":"dla_batty_longley_fractal","modelo":"claude-opus","respuesta_final":"Respuesta final: 1.70","confianza":"baja","uso_herramientas":False},
 {"n":19,"teoria":"duncan_disimilitud","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.4","confianza":"alta","uso_herramientas":False},
 {"n":19,"teoria":"duncan_disimilitud","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.4","confianza":"alta","uso_herramientas":False},
 {"n":20,"teoria":"duncan_disimilitud","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.30","confianza":"alta","uso_herramientas":False},
 {"n":20,"teoria":"duncan_disimilitud","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.3","confianza":"alta","uso_herramientas":False},
 {"n":21,"teoria":"duncan_disimilitud","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.50","confianza":"baja","uso_herramientas":False},
 {"n":21,"teoria":"duncan_disimilitud","modelo":"claude-opus","respuesta_final":"No determinable sin ejecutar la simulacion","confianza":"baja","uso_herramientas":False},
 {"n":22,"teoria":"modelo_gravitacional_flujos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 20000","confianza":"alta","uso_herramientas":False},
 {"n":22,"teoria":"modelo_gravitacional_flujos","modelo":"claude-opus","respuesta_final":"Respuesta final: 20000","confianza":"alta","uso_herramientas":False},
 {"n":23,"teoria":"modelo_gravitacional_flujos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 125000.0","confianza":"alta","uso_herramientas":False},
 {"n":23,"teoria":"modelo_gravitacional_flujos","modelo":"claude-opus","respuesta_final":"Respuesta final: 125000","confianza":"alta","uso_herramientas":False},
 {"n":24,"teoria":"modelo_gravitacional_flujos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 220555.56","confianza":"alta","uso_herramientas":False},
 {"n":24,"teoria":"modelo_gravitacional_flujos","modelo":"claude-opus","respuesta_final":"Respuesta final: 220555.56","confianza":"alta","uso_herramientas":False},
 {"n":25,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 20","confianza":"alta","uso_herramientas":False},
 {"n":25,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-opus","respuesta_final":"Respuesta final: 10","confianza":"alta","uso_herramientas":False},
 {"n":26,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.5","confianza":"alta","uso_herramientas":False},
 {"n":26,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.5","confianza":"alta","uso_herramientas":False},
 {"n":27,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 38/49","confianza":"alta","uso_herramientas":False},
 {"n":27,"teoria":"reilly_huff_gravitacion_comercial","modelo":"claude-opus","respuesta_final":"Respuesta final: 0.7755","confianza":"alta","uso_herramientas":False},
 {"n":28,"teoria":"schelling_segregacion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 5/7","confianza":"alta","uso_herramientas":False},
 {"n":28,"teoria":"schelling_segregacion","modelo":"claude-opus","respuesta_final":"Respuesta final: 5/7","confianza":"alta","uso_herramientas":False},
 {"n":29,"teoria":"schelling_segregacion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 250","confianza":"alta","uso_herramientas":False},
 {"n":29,"teoria":"schelling_segregacion","modelo":"claude-opus","respuesta_final":"Respuesta final: 250","confianza":"alta","uso_herramientas":False},
 {"n":30,"teoria":"schelling_segregacion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 0.75","confianza":"baja","uso_herramientas":False},
 {"n":30,"teoria":"schelling_segregacion","modelo":"claude-opus","respuesta_final":"Respuesta final: ~0.85","confianza":"baja","uso_herramientas":False},
 {"n":31,"teoria":"sintaxis_espacial_integracion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1.5","confianza":"alta","uso_herramientas":False},
 {"n":31,"teoria":"sintaxis_espacial_integracion","modelo":"claude-opus","respuesta_final":"Respuesta final: 1.5","confianza":"alta","uso_herramientas":False},
 {"n":32,"teoria":"sintaxis_espacial_integracion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1.0","confianza":"alta","uso_herramientas":False},
 {"n":32,"teoria":"sintaxis_espacial_integracion","modelo":"claude-opus","respuesta_final":"Respuesta final: 1","confianza":"alta","uso_herramientas":False},
 {"n":33,"teoria":"sintaxis_espacial_integracion","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 23/3 ≈ 7.6667","confianza":"alta","uso_herramientas":False},
 {"n":33,"teoria":"sintaxis_espacial_integracion","modelo":"claude-opus","respuesta_final":"Respuesta final: 7.6667","confianza":"alta","uso_herramientas":False},
 {"n":34,"teoria":"von_thunen_anillos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 24","confianza":"alta","uso_herramientas":False},
 {"n":34,"teoria":"von_thunen_anillos","modelo":"claude-opus","respuesta_final":"Respuesta final: 24","confianza":"alta","uso_herramientas":False},
 {"n":35,"teoria":"von_thunen_anillos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 6.625","confianza":"alta","uso_herramientas":False},
 {"n":35,"teoria":"von_thunen_anillos","modelo":"claude-opus","respuesta_final":"Respuesta final: 16","confianza":"alta","uso_herramientas":False},
 {"n":36,"teoria":"von_thunen_anillos","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 4","confianza":"alta","uso_herramientas":False},
 {"n":36,"teoria":"von_thunen_anillos","modelo":"claude-opus","respuesta_final":"Respuesta final: 4 km","confianza":"alta","uso_herramientas":False},
 {"n":37,"teoria":"zipf_rank_size","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 250,000","confianza":"alta","uso_herramientas":False},
 {"n":37,"teoria":"zipf_rank_size","modelo":"claude-opus","respuesta_final":"Respuesta final: 250000","confianza":"alta","uso_herramientas":False},
 {"n":38,"teoria":"zipf_rank_size","modelo":"claude-sonnet","respuesta_final":"Respuesta final: 1","confianza":"alta","uso_herramientas":False},
 {"n":38,"teoria":"zipf_rank_size","modelo":"claude-opus","respuesta_final":"Respuesta final: 1","confianza":"alta","uso_herramientas":False},
 {"n":39,"teoria":"zipf_rank_size","modelo":"claude-sonnet","respuesta_final":"Respuesta final: -1","confianza":"alta","uso_herramientas":False},
 {"n":39,"teoria":"zipf_rank_size","modelo":"claude-opus","respuesta_final":"Respuesta final: -1","confianza":"alta","uso_herramientas":False},
]

# ── estética ──────────────────────────────────────────────────────────────────
BG      = "#0e1a2b"
FG      = "#e8e6e1"
ACCENT  = "#e0a458"
ACCENT2 = "#5b9bd5"
RED_C   = "#c0392b"
GREEN_C = "#27ae60"

MODELOS_LOCALES = ["qwen2.5:3b", "qwen3:14b", "gpt-oss:20b", "qwen3:32b"]
MODELOS_API     = ["claude-sonnet", "claude-opus"]
TODOS_MODELOS   = MODELOS_LOCALES + MODELOS_API


# ── normalización ─────────────────────────────────────────────────────────────
def normalizar_texto(s: str) -> str:
    """Extrae el primer número de la respuesta (o la cadena normalizada)."""
    # Quitar prefijo "Respuesta final:"
    s = re.sub(r'(?i)respuesta\s+final\s*:', '', s).strip()
    # Quitar unidades (km, km2, km², etc.)
    s = re.sub(r'\s*(km[²2]?|celdas|hab\.?|%)', '', s, flags=re.IGNORECASE)
    # Quitar tildes/unicode especial que no sea número
    s = s.strip()
    return s


def extraer_numero(s: str):
    """
    Intenta parsear el número más relevante del texto normalizado.
    Estrategia:
      1. Si hay '≈' o '~' seguido de número, tomar ese número (ej. "2^1.15 ≈ 2.219" -> 2.219)
      2. Si el primer token es fracción a/b, evaluarla
      3. Si el primer token es miles con coma (250,000), parsearlo
      4. Si el primer token es float directo, tomarlo
      5. Buscar primer número flotante en todo el texto
    Devuelve float o None.
    """
    s = normalizar_texto(s)
    # Eliminar ** trailing (pensamiento qwen3)
    s = re.sub(r'\*+$', '', s).strip()
    # Eliminar ~ inicial
    s_stripped = s.lstrip('~').strip()

    # Primer token (antes del primer espacio o paréntesis)
    s_first = re.split(r'[\s(]', s_stripped)[0] if s_stripped else ''
    s_first = s_first.rstrip('.,;:')

    # Fracción simple a/b como primer token
    frac = re.match(r'^(-?\d+)\s*/\s*(\d+)$', s_first)
    if frac:
        try:
            return float(frac.group(1)) / float(frac.group(2))
        except ZeroDivisionError:
            return None

    # Separador de miles con coma: 250,000 o 1,000,000 como primer token
    miles_coma = re.match(r'^(-?\d{1,3}(?:,\d{3})+)$', s_first)
    if miles_coma:
        return float(s_first.replace(',', ''))

    # Número flotante normal como primer token
    try:
        v = float(s_first)
        return v
    except ValueError:
        pass

    # El primer token no es un número directo (ej. "2^1.15", "23/3").
    # Buscar número precedido por ≈ con punto decimal (ej. "2^1.15 ≈ 2.219")
    m_aprox = re.search(r'[≈]\s*(-?\d+\.\d+)', s)
    if m_aprox:
        try:
            return float(m_aprox.group(1))
        except ValueError:
            pass

    # Buscar fracción a/b precedida por ≈ (ej. "valor ≈ 4/9")
    m_frac_aprox = re.search(r'[≈]\s*(-?\d+)\s*/\s*(\d+)', s)
    if m_frac_aprox:
        try:
            return float(m_frac_aprox.group(1)) / float(m_frac_aprox.group(2))
        except (ValueError, ZeroDivisionError):
            pass

    # Buscar primer número flotante en todo el texto
    m = re.search(r'-?\d+(?:\.\d+)?', s)
    if m:
        try:
            return float(m.group())
        except ValueError:
            pass

    return None


# ── parseo de tolerancia ──────────────────────────────────────────────────────
def parsear_tolerancia(tol_str: str, valor_exacto_str: str):
    """
    Devuelve (tipo, valor_referencia, margen) donde tipo es 'exacta' o 'banda'.
    Para banda porcentual: margen se expresa como fracción (ej. 0.01 para 1%).
    """
    tol = tol_str.lower().strip()

    if 'igualdad exacta' in tol or tol.startswith('valor exacto'):
        ref = extraer_numero(valor_exacto_str)
        return ('exacta', ref, None)

    # Porcentaje: ±1%, ±0.01%
    m_pct = re.search(r'[±+-]?\s*([\d.]+)\s*%', tol)
    if m_pct:
        pct = float(m_pct.group(1)) / 100.0
        ref = extraer_numero(valor_exacto_str)
        return ('banda_pct', ref, pct)

    # Absoluta: ±0.01, ±1, ±5, ±0.05
    m_abs = re.search(r'[±+-]?\s*([\d.]+)', tol)
    if m_abs:
        margen = float(m_abs.group(1))
        # Tomar el valor de referencia del valor_exacto del banco (no del texto de tolerancia)
        ref = extraer_numero(valor_exacto_str)
        return ('banda_abs', ref, margen)

    ref = extraer_numero(valor_exacto_str)
    return ('exacta', ref, None)


# ── calificación ──────────────────────────────────────────────────────────────
TOKENS_NO_RESPUESTA = [
    'sin_respuesta', 'no determinable', 'procedimiento correcto',
    'indice_disimilitud', 'd_estimate', '<valor>', '{final_fraction',
    'infinito',
]
# Tokens que deben coincidir como token completo (no subcadena)
TOKENS_EXACTOS = ['si', 'b']


def es_sin_respuesta(texto: str) -> bool:
    t = texto.lower().strip()
    for tok in TOKENS_NO_RESPUESTA:
        if tok in t:
            return True
    # Tokens exactos: sólo si el texto completo normalizado es esa palabra
    # Normalizar también quitando tildes para comparar "Sí" -> "si"
    t_norm = normalizar_texto(texto).lower().strip()
    t_norm_ascii = unicodedata.normalize('NFD', t_norm)
    t_norm_ascii = ''.join(c for c in t_norm_ascii if unicodedata.category(c) != 'Mn')
    for tok in TOKENS_EXACTOS:
        if t_norm_ascii == tok or t_norm == tok:
            return True
    # Si después de normalizar no hay número
    num = extraer_numero(texto)
    if num is None:
        return True
    return False


def calificar(respuesta_raw: str, banco: dict) -> tuple:
    """
    Devuelve (veredicto: str, nota: str)
    veredicto: 'CORRECTO', 'INCORRECTO', 'SIN_RESPUESTA*'
    nota: descripción breve
    """
    tol_str = banco['tolerancia']
    val_exact = banco['valor_exacto']

    # SIN_RESPUESTA
    if es_sin_respuesta(respuesta_raw):
        return ('SIN_RESPUESTA*', 'no se proporcionó número')

    tipo, ref, margen = parsear_tolerancia(tol_str, val_exact)
    num = extraer_numero(respuesta_raw)

    if num is None:
        return ('SIN_RESPUESTA*', 'no parseable como número')

    if ref is None:
        return ('SIN_RESPUESTA*', 'referencia no parseable')

    if tipo == 'exacta':
        # Comparación estricta numérica (tolerancia mínima de flotante)
        if abs(num - ref) < 1e-6:
            return ('CORRECTO', f'{num} == {ref}')
        else:
            return ('INCORRECTO', f'{num} != {ref}')

    elif tipo == 'banda_abs':
        if abs(num - ref) <= margen + 1e-9:
            return ('CORRECTO', f'|{num} - {ref}| <= {margen}')
        else:
            return ('INCORRECTO', f'|{num} - {ref}| > {margen}')

    elif tipo == 'banda_pct':
        limite = abs(ref) * margen
        if abs(num - ref) <= limite + 1e-9:
            return ('CORRECTO', f'|{num} - {ref}| <= {margen*100:.2f}% de {ref}')
        else:
            return ('INCORRECTO', f'|{num} - {ref}| > {margen*100:.2f}% de {ref}')

    return ('INCORRECTO', 'caso no manejado')


# ── carga de datos ────────────────────────────────────────────────────────────
with open(BANCO_PATH, encoding='utf-8') as f:
    banco_list = json.load(f)
banco_by_n = {q['n']: q for q in banco_list}

with open(KRATOS_PATH, encoding='utf-8') as f:
    kratos_raw = json.load(f)

# Organizar kratos: {modelo: {n: respuesta_final}}
kratos_by_modelo = {}
for key, val in kratos_raw.items():
    m = val['modelo']
    n = val['n']
    if m not in kratos_by_modelo:
        kratos_by_modelo[m] = {}
    kratos_by_modelo[m][n] = val['respuesta_final']

# API: {modelo: {n: respuesta_final}}
api_by_modelo = {}
for entry in API_RESPONSES:
    m = entry['modelo']
    n = entry['n']
    if m not in api_by_modelo:
        api_by_modelo[m] = {}
    api_by_modelo[m][n] = entry['respuesta_final']

# ── calificación por pregunta ─────────────────────────────────────────────────
preguntas_resultado = []

for q in banco_list:
    n = q['n']
    fila = {
        'n': n,
        'teoria': q['teoria'],
        'tipo': q['tipo'],
        'valor_exacto': q['valor_exacto'],
        'tolerancia': q['tolerancia'],
        'sujetos': {}
    }

    for modelo in TODOS_MODELOS:
        if modelo in MODELOS_LOCALES:
            fuente = kratos_by_modelo.get(modelo, {})
        else:
            fuente = api_by_modelo.get(modelo, {})

        resp = fuente.get(n, None)
        if resp is None:
            veredicto = 'SIN_RESPUESTA*'
            nota_v = 'pregunta no encontrada'
            resp_display = 'SIN_RESPUESTA*'
        else:
            veredicto, nota_v = calificar(resp, q)
            resp_display = resp

        fila['sujetos'][modelo] = {
            'respuesta': resp_display,
            'veredicto': veredicto,
            'nota_calificacion': nota_v
        }

    preguntas_resultado.append(fila)

# ── agregados ─────────────────────────────────────────────────────────────────
def calcular_exactitud(preguntas, modelos, filtro_tipo=None):
    """Calcula aciertos/total por modelo, opcionalmente filtrado por tipo."""
    stats = {m: {'aciertos': 0, 'total': 0} for m in modelos}
    for fila in preguntas:
        if filtro_tipo and fila['tipo'] != filtro_tipo:
            continue
        for m in modelos:
            if m in fila['sujetos']:
                stats[m]['total'] += 1
                if fila['sujetos'][m]['veredicto'] == 'CORRECTO':
                    stats[m]['aciertos'] += 1
    return stats

def calcular_exactitud_por_teoria(preguntas, modelos):
    """Devuelve {teoria: {modelo: {aciertos, total}}}"""
    teorias = list(dict.fromkeys(f['teoria'] for f in preguntas))
    result = {}
    for t in teorias:
        preg_t = [f for f in preguntas if f['teoria'] == t]
        result[t] = calcular_exactitud(preg_t, modelos)
    return result

stats_global    = calcular_exactitud(preguntas_resultado, TODOS_MODELOS)
stats_cerrada   = calcular_exactitud(preguntas_resultado, TODOS_MODELOS, 'forma_cerrada')
stats_emergente = calcular_exactitud(preguntas_resultado, TODOS_MODELOS, 'emergente')
stats_teoria    = calcular_exactitud_por_teoria(preguntas_resultado, TODOS_MODELOS)

def ratio(s): return s['aciertos'] / s['total'] if s['total'] > 0 else 0.0

agregados = {
    'global': {m: {'aciertos': stats_global[m]['aciertos'],
                   'total': stats_global[m]['total'],
                   'exactitud': round(ratio(stats_global[m]), 4)}
               for m in TODOS_MODELOS},
    'por_tipo': {
        'forma_cerrada': {m: {'aciertos': stats_cerrada[m]['aciertos'],
                              'total': stats_cerrada[m]['total'],
                              'exactitud': round(ratio(stats_cerrada[m]), 4)}
                          for m in TODOS_MODELOS},
        'emergente': {m: {'aciertos': stats_emergente[m]['aciertos'],
                          'total': stats_emergente[m]['total'],
                          'exactitud': round(ratio(stats_emergente[m]), 4)}
                      for m in TODOS_MODELOS},
    },
    'por_teoria': {
        t: {m: {'aciertos': stats_teoria[t][m]['aciertos'],
                'total': stats_teoria[t][m]['total'],
                'exactitud': round(ratio(stats_teoria[t][m]), 4)}
            for m in TODOS_MODELOS}
        for t in stats_teoria
    }
}

# ── metadata ──────────────────────────────────────────────────────────────────
metadata = {
    'fecha': '2026-06-11',
    'n_sujetos': 6,
    'intentos': 1,
    'temperature_locales': 0.2,
    'uso_herramientas': False,
    'hardware_locales': 'kratos RTX 5070 Ti',
    'modelos_locales': MODELOS_LOCALES,
    'modelos_api': MODELOS_API
}

# ── salida JSON ───────────────────────────────────────────────────────────────
resultado_final = {
    'metadata': metadata,
    'preguntas': preguntas_resultado,
    'agregados': agregados
}

with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(resultado_final, f, ensure_ascii=False, indent=2)
print(f"[OK] {OUT_JSON}")


# ═══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════════

ETIQUETAS = {
    'qwen2.5:3b':  'Qwen2.5\n3B',
    'qwen3:14b':   'Qwen3\n14B',
    'gpt-oss:20b': 'GPT-OSS\n20B',
    'qwen3:32b':   'Qwen3\n32B',
    'claude-sonnet': 'Claude\nSonnet',
    'claude-opus':   'Claude\nOpus',
}

COLORES_MODELO = {
    'qwen2.5:3b':    '#4a90d9',
    'qwen3:14b':     '#7ab8f5',
    'gpt-oss:20b':   '#5dade2',
    'qwen3:32b':     '#85c1e9',
    'claude-sonnet': '#e0a458',
    'claude-opus':   '#f0c070',
}

def set_style(fig, ax):
    fig.patch.set_facecolor(BG)
    if isinstance(ax, np.ndarray):
        for a in ax.flat:
            a.set_facecolor(BG)
            a.tick_params(colors=FG, labelsize=9)
            for spine in a.spines.values():
                spine.set_edgecolor('#2a3a4b')
    else:
        ax.set_facecolor(BG)
        ax.tick_params(colors=FG, labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor('#2a3a4b')


# ── 1. Exactitud global por sujeto (barras + línea referencia) ────────────────
fig1, ax1 = plt.subplots(figsize=(10, 5.5))
set_style(fig1, ax1)

x = np.arange(len(TODOS_MODELOS))
vals = [stats_global[m]['aciertos'] / stats_global[m]['total'] * 100 for m in TODOS_MODELOS]
colores = [COLORES_MODELO[m] for m in TODOS_MODELOS]

bars = ax1.bar(x, vals, color=colores, width=0.55, edgecolor='#0e1a2b', linewidth=0.8, zorder=3)

# Anotar barras
for bar, v in zip(bars, vals):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
             f'{v:.1f}%', ha='center', va='bottom', color=FG, fontsize=9,
             fontweight='bold')

# Línea cómputo puro = 100%
ax1.axhline(100, color=ACCENT, linewidth=1.8, linestyle='--', zorder=4,
            label='Cómputo puro = 100%')

ax1.set_ylim(0, 115)
ax1.set_xticks(x)
ax1.set_xticklabels([ETIQUETAS[m] for m in TODOS_MODELOS], color=FG, fontsize=10)
ax1.set_ylabel('Exactitud (%)', color=FG, fontsize=11)
ax1.set_title('Exactitud global por sujeto — Teorías urbanas (39 preguntas)',
              color=FG, fontsize=13, pad=14)
ax1.yaxis.label.set_color(FG)
ax1.tick_params(axis='y', colors=FG)

# Separador locales / API
ax1.axvline(3.5, color='#2a3a4b', linewidth=1.2, linestyle=':', zorder=2)
ax1.text(1.5, 108, 'Modelos locales (Kratos)', ha='center', color='#8ab4d4', fontsize=9)
ax1.text(4.5, 108, 'Modelos API', ha='center', color=ACCENT, fontsize=9)

legend = ax1.legend(facecolor=BG, edgecolor='#2a3a4b', labelcolor=FG, fontsize=9)

ax1.grid(axis='y', color='#1e2e3e', linewidth=0.5, zorder=1)
fig1.tight_layout()
out1 = ASSETS_DIR / 'teorias_exactitud_global.png'
fig1.savefig(out1, dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig1)
print(f"[OK] {out1}")


# ── 2. Heatmap: 13 teorías × 6 sujetos ───────────────────────────────────────
teorias_ordenadas = list(dict.fromkeys(q['teoria'] for q in banco_list))

# Matriz: filas=teorías, cols=modelos
mat = np.zeros((len(teorias_ordenadas), len(TODOS_MODELOS)))
for i, t in enumerate(teorias_ordenadas):
    for j, m in enumerate(TODOS_MODELOS):
        s = stats_teoria[t][m]
        mat[i, j] = s['aciertos'] / s['total'] if s['total'] > 0 else 0.0

fig2, ax2 = plt.subplots(figsize=(11, 7))
set_style(fig2, ax2)

from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list(
    'custom', ['#1a0a00', '#c0392b', '#e0a458', '#27ae60'], N=256)

im = ax2.imshow(mat, aspect='auto', vmin=0, vmax=1, cmap=cmap, interpolation='nearest')

# Etiquetas teorías (eje y) — nombres más cortos
nombres_cortos = {
    'alonso_bid_rent': 'Alonso bid-rent',
    'automata_celular_crecimiento_urbano': 'Autómata celular',
    'bettencourt_west_escalamiento': 'Bettencourt-West',
    'braess_wardrop_equilibrio': 'Braess-Wardrop',
    'christaller_lugares_centrales': 'Christaller',
    'dla_batty_longley_fractal': 'DLA fractal',
    'duncan_disimilitud': 'Duncan disimilitud',
    'modelo_gravitacional_flujos': 'Modelo gravitacional',
    'reilly_huff_gravitacion_comercial': 'Reilly-Huff',
    'schelling_segregacion': 'Schelling segregación',
    'sintaxis_espacial_integracion': 'Sintaxis espacial',
    'von_thunen_anillos': 'Von Thünen',
    'zipf_rank_size': 'Zipf rank-size',
}

ax2.set_yticks(range(len(teorias_ordenadas)))
ax2.set_yticklabels([nombres_cortos.get(t, t) for t in teorias_ordenadas],
                    color=FG, fontsize=9)

ax2.set_xticks(range(len(TODOS_MODELOS)))
ax2.set_xticklabels([ETIQUETAS[m] for m in TODOS_MODELOS], color=FG, fontsize=10)

# Anotaciones en celdas
for i in range(len(teorias_ordenadas)):
    for j in range(len(TODOS_MODELOS)):
        v = mat[i, j]
        txt = f'{v:.0%}'
        tc = FG if v < 0.8 else '#0e1a2b'
        ax2.text(j, i, txt, ha='center', va='center', color=tc, fontsize=8, fontweight='bold')

cbar = fig2.colorbar(im, ax=ax2, pad=0.02, fraction=0.03)
cbar.ax.yaxis.set_tick_params(color=FG)
cbar.outline.set_edgecolor('#2a3a4b')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=FG, fontsize=8)
cbar.set_label('Proporción de aciertos', color=FG, fontsize=9)

ax2.set_title('Exactitud por teoría y sujeto',
              color=FG, fontsize=13, pad=12)

# Separador locales / API
ax2.axvline(3.5, color=ACCENT, linewidth=1.5, linestyle='--')

fig2.tight_layout()
out2 = ASSETS_DIR / 'teorias_heatmap.png'
fig2.savefig(out2, dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig2)
print(f"[OK] {out2}")


# ── 3. Forma cerrada vs emergente ─────────────────────────────────────────────
fig3, ax3 = plt.subplots(figsize=(11, 5.5))
set_style(fig3, ax3)

x = np.arange(len(TODOS_MODELOS))
w = 0.35

vals_c = [stats_cerrada[m]['aciertos'] / stats_cerrada[m]['total'] * 100
          if stats_cerrada[m]['total'] > 0 else 0 for m in TODOS_MODELOS]
vals_e = [stats_emergente[m]['aciertos'] / stats_emergente[m]['total'] * 100
          if stats_emergente[m]['total'] > 0 else 0 for m in TODOS_MODELOS]

bars_c = ax3.bar(x - w/2, vals_c, width=w, color=ACCENT2, label='Forma cerrada',
                 edgecolor=BG, linewidth=0.8, zorder=3)
bars_e = ax3.bar(x + w/2, vals_e, width=w, color=ACCENT,  label='Emergente',
                 edgecolor=BG, linewidth=0.8, zorder=3)

for bar, v in zip(bars_c, vals_c):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.0,
             f'{v:.0f}%', ha='center', va='bottom', color=FG, fontsize=8)
for bar, v in zip(bars_e, vals_e):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.0,
             f'{v:.0f}%', ha='center', va='bottom', color=FG, fontsize=8)

ax3.axhline(100, color='#7f8c8d', linewidth=1.2, linestyle='--',
            label='Cómputo puro = 100%', zorder=4)
ax3.set_ylim(0, 118)
ax3.set_xticks(x)
ax3.set_xticklabels([ETIQUETAS[m] for m in TODOS_MODELOS], color=FG, fontsize=10)
ax3.set_ylabel('Exactitud (%)', color=FG, fontsize=11)
ax3.set_title('Forma cerrada vs emergente — comparación por sujeto',
              color=FG, fontsize=13, pad=14)
ax3.yaxis.label.set_color(FG)
ax3.tick_params(axis='y', colors=FG)

ax3.axvline(3.5, color='#2a3a4b', linewidth=1.2, linestyle=':', zorder=2)
ax3.text(1.5, 111, 'Modelos locales (Kratos)', ha='center', color='#8ab4d4', fontsize=9)
ax3.text(4.5, 111, 'Modelos API', ha='center', color=ACCENT, fontsize=9)

legend3 = ax3.legend(facecolor=BG, edgecolor='#2a3a4b', labelcolor=FG, fontsize=9)
ax3.grid(axis='y', color='#1e2e3e', linewidth=0.5, zorder=1)
fig3.tight_layout()
out3 = ASSETS_DIR / 'teorias_cerrada_vs_emergente.png'
fig3.savefig(out3, dpi=150, bbox_inches='tight', facecolor=BG)
plt.close(fig3)
print(f"[OK] {out3}")

# ── resumen consola ───────────────────────────────────────────────────────────
print("\n=== EXACTITUD GLOBAL ===")
for m in TODOS_MODELOS:
    s = stats_global[m]
    print(f"  {m:25s}: {s['aciertos']:2d}/{s['total']:2d} = {ratio(s)*100:5.1f}%")
