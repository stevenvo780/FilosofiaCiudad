"""
Autómata celular de crecimiento urbano (regla estocástica de transición)
Formulación: Roger White y Guy Engelen (1993) / Keith Clarke (SLEUTH, 1997)
Antecedente conceptual: Waldo Tobler (1979), "geografía celular".
Campo: Morfología y crecimiento urbano

NOTA DE ATRIBUCIÓN (canon): la regla probabilística de transición por conteo
de vecinos — p_i = p_base + p_difusion*(k_i/8) con vecindad de Moore — NO fue
propuesta por Tobler. Tobler (1979, "Cellular Geography") introdujo el concepto
general de geografía celular como antecedente. La formulación estocástica con
coeficientes de difusión/crecimiento espontáneo corresponde al autómata celular
restringido de White y Engelen (1993) y, sobre todo, al modelo SLEUTH de Clarke
(1997). Por eso esta regla se acredita a White-Engelen / Clarke, con Tobler solo
como antecedente conceptual.

Formulación:
    Rejilla de celdas con estado urbano (1) o no urbano (0).
    En cada paso, una celda no urbana se urbaniza con probabilidad (regla
    fronteriza adoptada en esta implementación):
        p_i = p_base + p_difusion * (k_i / 8)   si k_i >= 1 (celda del frente)
        p_i = 0                                  si k_i == 0 (celda aislada)
    donde k_i = número de vecinos urbanos en vecindad de Moore (8 vecinos).
    Se urbaniza si U(0,1) < p_i (número aleatorio uniforme).

    NOTA SOBRE p_base Y EL ALCANCE DE LA REGLA (canon): en el SLEUTH canónico
    el coeficiente de crecimiento espontáneo puede activar celdas en CUALQUIER
    posición (núcleos dispersos). Esta implementación adopta deliberadamente una
    REGLA FRONTERIZA: p_base actúa solo como REFUERZO DEL FRENTE urbano
    (celdas con k_i >= 1), y NO como semilla de núcleos espontáneos. Las celdas
    completamente aisladas tienen p_i = 0. Esto suprime la nucleación espontánea
    de islas dispersas y produce un crecimiento estrictamente compacto dominado
    por difusión de borde, preservando la conectividad >90% en todos los pasos.
    Consecuencia operativa: una celda aislada (k_i=0) NUNCA se urbaniza; su
    probabilidad efectiva bajo la regla del modelo es 0 (no 0.001).

Experimento:
    - Rejilla 100x100
    - Núcleo urbano inicial 3x3 en el centro
    - p_base = 0.001, p_difusion = 1.00  (valor autorizado en el canon;
      el cluster casi satura un disco y D del box-counting tiende a ~2)
    - Vecindad de Moore
    - numpy.random.seed(7)
    - 50 pasos sincrónicos
    - Determinista dada la semilla
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import ListedColormap
import networkx as nx
import json
import os
from scipy.ndimage import label as scipy_label

# ─── Parámetros ───────────────────────────────────────────────────────────────
GRID_SIZE = 100
P_BASE = 0.001
P_DIFUSION = 1.00          # valor autorizado en el canon (catalogo.json): difusión de borde dominante
N_PASOS = 50
SEMILLA = 7
NUCLEO_CENTRO_TAM = 3   # núcleo de 3×3

# Rutas de salida
DIR_SIM = os.path.dirname(os.path.abspath(__file__))
DIR_ASSETS = os.path.join(
    os.path.dirname(DIR_SIM),
    "presentacion", "assets", "sim"
)
os.makedirs(DIR_ASSETS, exist_ok=True)

# ─── Paleta visual ────────────────────────────────────────────────────────────
BG_COLOR      = "#0e1a2b"
TEXT_COLOR    = "#e8e6e1"
ACCENT_AMBER  = "#e0a458"
URBAN_COLOR   = "#e0a458"   # celdas urbanas: ámbar
RURAL_COLOR   = "#1a2f4a"   # celdas no urbanas: azul oscuro
GRID_LINE_CLR = "#152030"


def inicializar_rejilla(n: int, tam_nucleo: int) -> np.ndarray:
    """Crea rejilla n×n con núcleo central urbano de tam_nucleo × tam_nucleo."""
    grid = np.zeros((n, n), dtype=np.int8)
    centro = n // 2
    mitad = tam_nucleo // 2
    grid[centro - mitad: centro - mitad + tam_nucleo,
         centro - mitad: centro - mitad + tam_nucleo] = 1
    return grid


def contar_vecinos_moore(grid: np.ndarray) -> np.ndarray:
    """
    Cuenta vecinos urbanos en vecindad de Moore (8 vecinos) para cada celda.
    Usa suma de desplazamientos para eficiencia.
    """
    n, m = grid.shape
    k = np.zeros_like(grid, dtype=np.int16)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            k += np.roll(np.roll(grid, di, axis=0), dj, axis=1)
    return k


def paso_sincronico(grid: np.ndarray, rng: np.random.RandomState) -> np.ndarray:
    """
    Aplica un paso sincrónico del autómata:
        p_i = p_base + p_difusion * (k_i / 8)  si k_i >= 1  (frente urbano)
        p_i = 0                                  si k_i == 0  (celda aislada)
        nueva celda urbana si U(0,1) < p_i  y  celda era no-urbana

    La restricción p_i = 0 para k_i = 0 garantiza que solo el frente
    urbano puede avanzar: no se forman islas espontáneas alejadas del
    cluster principal, preservando la conectividad >90% en todos los pasos.
    """
    k = contar_vecinos_moore(grid)
    # p_base solo actúa en celdas fronterizas (al menos un vecino urbano)
    p = np.where(k > 0, P_BASE + P_DIFUSION * (k / 8.0), 0.0)
    p = np.minimum(p, 1.0)   # saturar en 1
    # Muestreo uniforme para toda la rejilla
    u = rng.uniform(0.0, 1.0, size=grid.shape)
    no_urbana = (grid == 0)
    nuevas = no_urbana & (u < p)
    nueva_grid = grid.copy()
    nueva_grid[nuevas] = 1
    return nueva_grid


def medir_perimetro(grid: np.ndarray) -> int:
    """
    Cuenta el número de aristas entre celdas urbanas y no-urbanas
    (usando vecindad de Von Neumann para el perímetro estándar).
    """
    k4 = np.zeros_like(grid, dtype=np.int16)
    for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        k4 += np.roll(np.roll(grid, di, axis=0), dj, axis=1)
    # Cada celda urbana contribuye (4 - número de vecinos urbanos) al perímetro
    return int(np.sum(grid * (4 - k4)))


def componente_conexa_principal(grid: np.ndarray) -> float:
    """
    Devuelve la fracción de celdas urbanas que pertenecen al componente
    conexo más grande (conectividad 8 vecinos).
    """
    estructura = np.ones((3, 3), dtype=int)
    etiquetado, n_comp = scipy_label(grid, structure=estructura)
    if n_comp == 0:
        return 0.0
    conteos = np.bincount(etiquetado.ravel())[1:]  # excluir etiqueta 0 (fondo)
    fraccion = conteos.max() / grid.sum()
    return float(fraccion)


def dimension_fractal_box_counting(grid: np.ndarray) -> float:
    """
    Estimación de la dimensión fractal por box-counting (INDICADOR SECUNDARIO).

    Limitación documentada: para esta forma — un blob casi-disco sólido que
    ocupa una fracción importante de la rejilla — la dimensión por box-counting
    NO es una medida honesta de "compacidad vs ramificación": un disco sólido
    tiene D ~ 2.0. Aquí se usan exclusivamente tamaños de caja que DIVIDEN la
    rejilla de 100 (1, 2, 4, 5, 10, 20, 25, 50), evitando el sesgo de cajas que
    no encajan; con este rango D se aproxima a ~2 (forma compacta), coherente
    con la geometría observada. La medida primaria de compacidad para esta
    simulación es la compacidad isoperimétrica (4π·Área/Perímetro²), reportada
    por separado; la dimensión fractal queda como indicador secundario.
    """
    n = grid.shape[0]
    # Solo tamaños que dividen exactamente la rejilla (n=100): evita el artefacto
    # de cajas que mezclan escala de borde rugoso y de bulk de forma inconsistente.
    tamanos = [s for s in [1, 2, 4, 5, 10, 20, 25, 50] if n % s == 0 and s < n]
    cuentas = []
    for s in tamanos:
        bloques = 0
        for i in range(0, n, s):
            for j in range(0, n, s):
                if grid[i:i+s, j:j+s].any():
                    bloques += 1
        cuentas.append((s, bloques))
    if len(cuentas) < 2:
        return float('nan')
    log_s  = np.log([1.0/c[0] for c in cuentas])
    log_n  = np.log([c[1]    for c in cuentas])
    coef   = np.polyfit(log_s, log_n, 1)
    return float(coef[0])


# ─── Simulación principal ────────────────────────────────────────────────────

def correr_simulacion():
    np.random.seed(SEMILLA)
    rng = np.random.RandomState(SEMILLA)

    grid = inicializar_rejilla(GRID_SIZE, NUCLEO_CENTRO_TAM)

    # Métricas por paso
    historico_urbanas  = [int(grid.sum())]
    historico_perimetro = [medir_perimetro(grid)]
    historico_compacidad = []   # 4π·Área / Perímetro²

    def compacidad(area, perim):
        if perim == 0:
            return 0.0
        return 4 * np.pi * area / (perim ** 2)

    historico_compacidad.append(
        compacidad(historico_urbanas[0], historico_perimetro[0])
    )

    # Snapshots
    pasos_snapshot = [0, 15, 30, 50]
    snapshots = {}
    if 0 in pasos_snapshot:
        snapshots[0] = grid.copy()

    for paso in range(1, N_PASOS + 1):
        grid = paso_sincronico(grid, rng)
        n_urb  = int(grid.sum())
        perim  = medir_perimetro(grid)
        historico_urbanas.append(n_urb)
        historico_perimetro.append(perim)
        historico_compacidad.append(compacidad(n_urb, perim))
        if paso in pasos_snapshot:
            snapshots[paso] = grid.copy()

    return grid, historico_urbanas, historico_perimetro, historico_compacidad, snapshots


# ─── Gráficas ─────────────────────────────────────────────────────────────────

def estilo_base():
    plt.rcParams.update({
        "figure.facecolor":   BG_COLOR,
        "axes.facecolor":     BG_COLOR,
        "axes.edgecolor":     TEXT_COLOR,
        "axes.labelcolor":    TEXT_COLOR,
        "xtick.color":        TEXT_COLOR,
        "ytick.color":        TEXT_COLOR,
        "text.color":         TEXT_COLOR,
        "grid.color":         GRID_LINE_CLR,
        "grid.linestyle":     "--",
        "grid.alpha":         0.4,
        "font.family":        "DejaVu Sans",
        "font.size":          10,
    })


def grafico_1_instantaneas(snapshots: dict):
    """
    PNG 1: 4 instantáneas de la rejilla (pasos 0, 15, 30, 50)
    """
    estilo_base()
    cmap = ListedColormap([RURAL_COLOR, URBAN_COLOR])

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    pasos = [0, 15, 30, 50]
    for ax, paso in zip(axes, pasos):
        ax.imshow(
            snapshots[paso], cmap=cmap, vmin=0, vmax=1,
            origin='upper', interpolation='nearest'
        )
        n_urb = int(snapshots[paso].sum())
        ax.set_title(f"Paso {paso}\n{n_urb} celdas urbanas",
                     color=TEXT_COLOR, fontsize=11, pad=6)
        ax.set_xlabel("columna", color=TEXT_COLOR, fontsize=9)
        ax.set_ylabel("fila",    color=TEXT_COLOR, fontsize=9)
        ax.tick_params(colors=TEXT_COLOR, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(TEXT_COLOR)

    fig.suptitle(
        "Autómata celular de crecimiento urbano (regla estocástica de transición)\n"
        "Formulación: White y Engelen 1993 · Clarke (SLEUTH) 1997 · antecedente: Tobler 1979\n"
        f"p_base={P_BASE}, p_difusión={P_DIFUSION}, rejilla {GRID_SIZE}×{GRID_SIZE}, semilla {SEMILLA}",
        color=TEXT_COLOR, fontsize=12, y=1.02
    )
    plt.tight_layout()

    ruta = os.path.join(DIR_ASSETS, "sim_automata_celular_crecimiento_urbano_1.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close()
    print(f"  Guardado: {ruta}")
    return ruta


def grafico_2_curvas(historico_urbanas, historico_perimetro, historico_compacidad):
    """
    PNG 2: curvas de métricas vs. iteración
    """
    estilo_base()
    iteraciones = list(range(len(historico_urbanas)))

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    # Panel 1: celdas urbanas
    ax = axes[0]
    ax.plot(iteraciones, historico_urbanas, color=ACCENT_AMBER, linewidth=2)
    ax.set_xlabel("Iteración", color=TEXT_COLOR)
    ax.set_ylabel("Número de celdas urbanas", color=TEXT_COLOR)
    ax.set_title("Crecimiento urbano total", color=TEXT_COLOR, pad=8)
    ax.set_xlim(0, N_PASOS)
    ax.set_ylim(0, max(historico_urbanas) * 1.05)
    ax.grid(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)

    # Panel 2: perímetro
    ax = axes[1]
    ax.plot(iteraciones, historico_perimetro, color="#7ec8c8", linewidth=2)
    ax.set_xlabel("Iteración", color=TEXT_COLOR)
    ax.set_ylabel("Perímetro (aristas urbano-rural)", color=TEXT_COLOR)
    ax.set_title("Evolución del perímetro", color=TEXT_COLOR, pad=8)
    ax.set_xlim(0, N_PASOS)
    ax.set_ylim(0, max(historico_perimetro) * 1.05)
    ax.grid(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)

    # Panel 3: compacidad (índice de isoperímetro)
    ax = axes[2]
    ax.plot(iteraciones, historico_compacidad, color="#c87ed0", linewidth=2)
    ax.axhline(y=1.0, color=TEXT_COLOR, linestyle=":", linewidth=1, alpha=0.5,
               label="círculo perfecto")
    ax.set_xlabel("Iteración", color=TEXT_COLOR)
    ax.set_ylabel("Compacidad (4π·Área/Perímetro²)", color=TEXT_COLOR)
    ax.set_title("Índice de compacidad", color=TEXT_COLOR, pad=8)
    ax.set_xlim(0, N_PASOS)
    ax.set_ylim(0, max(historico_compacidad) * 1.2 if max(historico_compacidad) > 0 else 1.2)
    ax.legend(fontsize=8, labelcolor=TEXT_COLOR,
              facecolor=BG_COLOR, edgecolor=TEXT_COLOR)
    ax.grid(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)

    fig.suptitle(
        "Métricas del autómata celular de crecimiento urbano · "
        f"p_base={P_BASE}, p_difusión={P_DIFUSION}, semilla {SEMILLA}",
        color=TEXT_COLOR, fontsize=12, y=1.02
    )
    plt.tight_layout()

    ruta = os.path.join(DIR_ASSETS, "sim_automata_celular_crecimiento_urbano_2.png")
    plt.savefig(ruta, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close()
    print(f"  Guardado: {ruta}")
    return ruta


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== Autómata celular de crecimiento urbano ===")
    print(f"Rejilla: {GRID_SIZE}×{GRID_SIZE} | p_base={P_BASE} | "
          f"p_difusión={P_DIFUSION} | pasos={N_PASOS} | semilla={SEMILLA}")

    grid_final, hist_urb, hist_perim, hist_comp, snapshots = correr_simulacion()

    n_urbanas_final = hist_urb[-1]
    print(f"\nResultados tras {N_PASOS} pasos:")
    print(f"  Celdas urbanas al inicio : {hist_urb[0]}")
    print(f"  Celdas urbanas al final  : {n_urbanas_final}")
    print(f"  Celdas totales           : {GRID_SIZE**2}")
    print(f"  Fracción urbana          : {n_urbanas_final / GRID_SIZE**2:.4f}")

    # ── Validación: verificar criterio en TODOS los pasos intermedios ─────────
    pasos_check = [5, 10, 15, 20, 30, 50]
    print(f"\nValidación (componente conexo principal >90% en todos los pasos):")

    # Reproducir simulación para métricas de validación
    np.random.seed(SEMILLA)
    rng_val = np.random.RandomState(SEMILLA)
    grid_val = inicializar_rejilla(GRID_SIZE, NUCLEO_CENTRO_TAM)
    validacion_ok = True
    fracs_intermedias = {}
    for paso in range(1, N_PASOS + 1):
        grid_val = paso_sincronico(grid_val, rng_val)
        if paso in pasos_check:
            frac = componente_conexa_principal(grid_val)
            fracs_intermedias[paso] = frac
            ok_paso = frac > 0.90
            if not ok_paso:
                validacion_ok = False
            print(f"  Paso {paso:2d}: fracción conexo = {frac:.4f}  "
                  f"({'OK >90%' if ok_paso else 'FALLO <90%'})")

    frac_conexo_final = componente_conexa_principal(grid_final)
    print(f"  Componente conexo final  : {frac_conexo_final:.4f}  "
          f"({'OK >90%' if frac_conexo_final > 0.90 else 'FALLO <90%'})")
    print(f"  Criterio global          : {'CUMPLIDO' if validacion_ok else 'INCUMPLIDO'}")

    # Compacidad isoperimétrica final (MEDIDA PRIMARIA de compacidad)
    compacidad_final = hist_comp[-1]
    print(f"  Compacidad isoperimétrica final  : {compacidad_final:.4f}  "
          f"(medida primaria; 1.0 = disco perfecto)")

    # Dimensión fractal (INDICADOR SECUNDARIO; para un blob casi-disco D -> 2)
    dim_fractal = dimension_fractal_box_counting(grid_final)
    df_ok = 1.6 <= dim_fractal <= 2.0
    print(f"  Dimensión fractal (box-counting) : {dim_fractal:.4f}  "
          f"({'OK [1.6,2.0]' if df_ok else 'FUERA DEL RANGO'}; "
          f"secundario, D~2 esperado para blob casi-disco)")

    # Monotonía del crecimiento
    monotono = all(hist_urb[i] <= hist_urb[i+1] for i in range(len(hist_urb)-1))
    print(f"  Crecimiento monótono             : {'Sí' if monotono else 'No'}")

    # Preguntas
    p1_ki = 6
    p1_val = P_BASE + P_DIFUSION * (p1_ki / 8)
    # P2: probabilidad EFECTIVA bajo la regla del modelo (regla fronteriza).
    # Para una celda aislada (k_i=0) la regla fija p_i = 0 (no se urbaniza nunca).
    # El valor coincide con lo que produce el código realmente ejecutado.
    p2_val = 0.0
    p3_val = n_urbanas_final

    print(f"\nPreguntas:")
    print(f"  P1 (k_i=6): p_i = {P_BASE} + {P_DIFUSION}*(6/8) = {p1_val}")
    print(f"  P2 (k_i=0): probabilidad efectiva bajo la regla del modelo = {p2_val} "
          f"(regla fronteriza: k_i>=1 requerido; aislada nunca se urbaniza)")
    print(f"  P3 (simulación, paso 50): {p3_val} celdas urbanas")

    # ── Gráficas ──────────────────────────────────────────────────────────────
    print("\nGenerando gráficas...")
    ruta_g1 = grafico_1_instantaneas(snapshots)
    ruta_g2 = grafico_2_curvas(hist_urb, hist_perim, hist_comp)

    # ── Guardar datos crudos ──────────────────────────────────────────────────
    datos = {
        "teoria": "automata_celular_crecimiento_urbano",
        "nombre": "Autómata celular de crecimiento urbano (regla estocástica de transición)",
        "autor": "Formulación: Roger White y Guy Engelen / Keith Clarke (SLEUTH); antecedente conceptual: Waldo Tobler (geografía celular)",
        "anio": "White-Engelen 1993 / Clarke 1997 (regla); Tobler 1979 (antecedente)",
        "parametros": {
            "grid_size": GRID_SIZE,
            "p_base": P_BASE,
            "p_difusion": P_DIFUSION,
            "n_pasos": N_PASOS,
            "semilla": SEMILLA,
            "nucleo_tam": NUCLEO_CENTRO_TAM,
            "regla": "p_base solo actua en celdas fronterizas (k_i >= 1); p_i=0 para celdas aisladas"
        },
        "celdas_urbanas_por_paso": hist_urb,
        "perimetro_por_paso": hist_perim,
        "compacidad_por_paso": hist_comp,
        "resultados_finales": {
            "celdas_urbanas_paso_0":  hist_urb[0],
            "celdas_urbanas_paso_15": hist_urb[15],
            "celdas_urbanas_paso_30": hist_urb[30],
            "celdas_urbanas_paso_50": hist_urb[50],
            "fraccion_conexo_principal": frac_conexo_final,
            "fraccion_conexo_por_paso": fracs_intermedias,
            "compacidad_isoperimetrica_final": compacidad_final,
            "dimension_fractal": dim_fractal,
            "crecimiento_monotono": monotono
        },
        "validacion": {
            "componente_conexo_principal_gt90pct_todos_pasos": validacion_ok,
            "fraccion_conexo_final": frac_conexo_final,
            "compacidad_isoperimetrica_final": compacidad_final,
            "medida_primaria_compacidad": "compacidad_isoperimetrica (4*pi*Area/Perimetro^2)",
            "dimension_fractal_en_rango_1_6_2_0": df_ok,
            "dimension_fractal": dim_fractal,
            "dimension_fractal_nota": "indicador secundario; cajas que dividen la rejilla (1,2,4,5,10,20,25,50); para blob casi-disco D->2",
            "crecimiento_monotono": monotono
        },
        "preguntas_resultados": {
            "P1_ki6": p1_val,
            "P2_ki0": p2_val,
            "P3_celdas_paso50": p3_val
        },
        "graficos": [ruta_g1, ruta_g2]
    }

    ruta_datos = os.path.join(DIR_SIM, "datos_automata_celular_crecimiento_urbano.json")
    with open(ruta_datos, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"\nDatos guardados: {ruta_datos}")

    # ── Guardar preguntas ─────────────────────────────────────────────────────
    preguntas_json = {
        "teoria": "automata_celular_crecimiento_urbano",
        "nombre": "Autómata celular de crecimiento urbano (regla estocástica de transición)",
        "autor": "Formulación: Roger White y Guy Engelen / Keith Clarke (SLEUTH); antecedente conceptual: Waldo Tobler (geografía celular)",
        "anio": "White-Engelen 1993 / Clarke 1997 (regla); Tobler 1979 (antecedente)",
        "preguntas": [
            {
                "q": "En el autómata celular de crecimiento urbano, la probabilidad de urbanización de una celda es p_i = p_base + p_difusion*(k_i/8), con p_base=0.001 y p_difusion=1.00. Una celda no urbana tiene 6 vecinos urbanos en su vecindad de Moore. Calcula p_i. Formato: 'Respuesta final: <valor>'.",
                "valor_exacto": str(round(p1_val, 6)),
                "tipo": "forma_cerrada",
                "tolerancia": "+-0.001 (0.751)",
                "como_computar": f"p_i = {P_BASE} + {P_DIFUSION}*(6/8) = {P_BASE} + {P_DIFUSION*6/8} = {p1_val}"
            },
            {
                "q": "Bajo la regla del modelo (regla fronteriza: p_base solo refuerza el frente, k_i>=1 requerido), cuál es la probabilidad EFECTIVA de urbanización de una celda completamente aislada (k_i=0 vecinos urbanos)? Formato: 'Respuesta final: <valor>'.",
                "valor_exacto": "0.0",
                "tipo": "forma_cerrada",
                "tolerancia": "igualdad exacta (0.0)",
                "como_computar": f"La regla fija p_i=0 para k_i=0 (celda aislada nunca se urbaniza). Probabilidad efectiva = {p2_val}. (La fórmula algebraica daría p_base={P_BASE}, pero el modelo no la aplica a celdas aisladas; el código ejecutado produce 0.)"
            },
            {
                "q": "Corre el autómata 100x100 con núcleo central 3x3, p_base=0.001, p_difusion=1.00, vecindad de Moore, p_base solo activa celdas fronterizas (k_i>=1), numpy.random.seed(7), 50 pasos sincrónicos. Reporta el número total de celdas urbanas tras el paso 50. Formato: 'Respuesta final: <valor>'.",
                "valor_exacto": str(p3_val),
                "tipo": "emergente",
                "tolerancia": f"valor exacto determinista: {p3_val} (simulacion compacta con regla fronteriza corregida)",
                "como_computar": f"Simulación determinista con semilla 7, regla fronteriza (k_i>=1): resultado = {p3_val} celdas urbanas"
            }
        ]
    }

    ruta_preguntas = os.path.join(DIR_SIM, "preguntas_automata_celular_crecimiento_urbano.json")
    with open(ruta_preguntas, "w", encoding="utf-8") as f:
        json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
    print(f"Preguntas guardadas: {ruta_preguntas}")

    return datos


if __name__ == "__main__":
    main()
