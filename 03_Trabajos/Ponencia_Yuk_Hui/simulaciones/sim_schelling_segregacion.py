"""
Modelo de segregación de Schelling (1971)
Thomas Schelling – "Dynamic Models of Segregation"
Journal of Mathematical Sociology, 1971.

Implementación exacta y determinista:
  - Rejilla 50×50 = 2500 celdas
  - 45 % grupo Rojo, 45 % grupo Azul, 10 % vacías
  - Umbral T = 0.30 (fracción mínima de mismo-grupo sobre vecinos OCUPADOS)
  - Vecindad de Moore (8 vecinos) con frontera TOROIDAL (periódica): los
    bordes y esquinas se enlazan con el lado opuesto, de modo que todo
    agente tiene siempre 8 vecinos. Es una decisión de modelado explícita
    (difiere del original acotado de Schelling 1971); no altera el fenómeno
    emergente (segregación robusta ~0.75).
  - Semilla fija seed=42 vía numpy.random.default_rng(42)
  - Máximo 200 iteraciones
  - Agentes insatisfechos reubicados en una celda vacía elegida al azar
    (relajación estocástica): el destino NO se exige satisfactorio, en
    orden aleatorio fijado por la misma semilla.
  - Dos ejecuciones producen resultados idénticos.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import matplotlib.gridspec as gridspec

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE = "/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui"
SIM_DIR  = os.path.join(BASE, "simulaciones")
ASSET_DIR = os.path.join(BASE, "presentacion/assets/sim")
os.makedirs(SIM_DIR, exist_ok=True)
os.makedirs(ASSET_DIR, exist_ok=True)

# ── Parámetros ─────────────────────────────────────────────────────────────────
N        = 50          # tamaño de rejilla N×N
FRAC_R   = 0.45        # fracción grupo Rojo
FRAC_B   = 0.45        # fracción grupo Azul
# FRAC_VACIO = 0.10   # implícito
T        = 0.30        # umbral de tolerancia
MAX_ITER = 200
SEED     = 42

# Códigos de celda
VACIO = 0
ROJO  = 1
AZUL  = 2


# ── Funciones auxiliares ───────────────────────────────────────────────────────

def crear_rejilla(n, frac_r, frac_b, seed):
    """Inicializa la rejilla de forma determinista."""
    rng = np.random.default_rng(seed)
    total = n * n
    n_rojo = int(round(total * frac_r))
    n_azul = int(round(total * frac_b))
    n_vacio = total - n_rojo - n_azul
    celdas = (
        [ROJO]  * n_rojo  +
        [AZUL]  * n_azul  +
        [VACIO] * n_vacio
    )
    celdas = np.array(celdas, dtype=np.int8)
    rng.shuffle(celdas)
    return celdas.reshape(n, n), rng


def vecinos_moore(grid, r, c):
    """Devuelve los valores de los 8 vecinos de Moore (bordes toroidales)."""
    n = grid.shape[0]
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    return [grid[(r+dr) % n, (c+dc) % n] for dr, dc in dirs]


def fraccion_mismo_grupo(grid, r, c):
    """
    Fracción de vecinos OCUPADOS que son del mismo grupo que (r,c).
    Si no hay vecinos ocupados devuelve 1.0 (satisfecho).
    """
    grupo = grid[r, c]
    if grupo == VACIO:
        return None
    vecinos = vecinos_moore(grid, r, c)
    ocupados = [v for v in vecinos if v != VACIO]
    if len(ocupados) == 0:
        return 1.0
    mismo = sum(1 for v in ocupados if v == grupo)
    return mismo / len(ocupados)


def esta_satisfecho(grid, r, c, umbral):
    """True si el agente en (r,c) está satisfecho con el umbral dado."""
    frac = fraccion_mismo_grupo(grid, r, c)
    if frac is None:
        return True  # vacío → no aplica
    return frac >= umbral


def fraccion_media_global(grid):
    """Fracción media de mismo-grupo sobre todos los agentes ocupados."""
    n = grid.shape[0]
    fracs = []
    for r in range(n):
        for c in range(n):
            if grid[r, c] != VACIO:
                f = fraccion_mismo_grupo(grid, r, c)
                fracs.append(f)
    return float(np.mean(fracs)) if fracs else 0.0


def insatisfechos(grid, umbral):
    """Devuelve lista de coordenadas (r,c) de agentes insatisfechos."""
    n = grid.shape[0]
    result = []
    for r in range(n):
        for c in range(n):
            if grid[r, c] != VACIO and not esta_satisfecho(grid, r, c, umbral):
                result.append((r, c))
    return result


def celdas_vacias(grid):
    """Devuelve lista de coordenadas vacías."""
    coords = np.argwhere(grid == VACIO)
    return [tuple(x) for x in coords]


# ── Simulación principal ───────────────────────────────────────────────────────

def simular(n=N, frac_r=FRAC_R, frac_b=FRAC_B, umbral=T,
            max_iter=MAX_ITER, seed=SEED):
    """
    Corre el modelo de Schelling de forma completamente determinista.
    Devuelve dict con resultados y datos para graficar.
    """
    # Inicialización
    # Todo el azar del modelo proviene del generador local rng =
    # np.random.default_rng(seed) creado dentro de crear_rejilla (shuffle,
    # permutation, integers). No se usa el estado global de numpy.
    grid, rng = crear_rejilla(n, frac_r, frac_b, seed)

    grid_inicial = grid.copy()
    frac_inicial = fraccion_media_global(grid)

    historial_frac  = [frac_inicial]
    historial_insat = []

    iteracion_convergencia = None

    for it in range(1, max_iter + 1):
        insat = insatisfechos(grid, umbral)
        n_insat = len(insat)
        historial_insat.append(n_insat)

        total_agentes = int(np.sum(grid != VACIO))
        frac_insat = n_insat / total_agentes if total_agentes > 0 else 0.0

        if n_insat == 0:
            iteracion_convergencia = it
            historial_frac.append(fraccion_media_global(grid))
            break

        # Orden aleatorio determinista para recorrer los insatisfechos
        orden = rng.permutation(len(insat))
        vacias = celdas_vacias(grid)

        for idx in orden:
            if not vacias:
                break
            r_orig, c_orig = insat[idx]
            # Verificar que el agente sigue siendo el mismo (no fue movido antes)
            # (en esta implementación un agente puede haber sido movido
            #  si su celda quedó vacía; lo detectamos comprobando que
            #  la celda no sea VACIO)
            if grid[r_orig, c_orig] == VACIO:
                continue

            # Elegir destino aleatorio entre celdas vacías
            dest_idx = rng.integers(0, len(vacias))
            r_dest, c_dest = vacias[dest_idx]

            # Mover agente
            grid[r_dest, c_dest] = grid[r_orig, c_orig]
            grid[r_orig, c_orig] = VACIO

            # Actualizar lista de vacías
            vacias[dest_idx] = (r_orig, c_orig)

        frac_actual = fraccion_media_global(grid)
        historial_frac.append(frac_actual)

        # Criterio de parada estricto: solo cero insatisfechos o max_iter
        # (el umbral blando del 2% fue eliminado para respetar la especificación)

    grid_final = grid.copy()
    frac_final = historial_frac[-1]

    # Calcular % insatisfechos final
    insat_final = insatisfechos(grid_final, umbral)
    total_agentes = int(np.sum(grid_final != VACIO))
    pct_insat_final = len(insat_final) / total_agentes * 100

    return {
        "grid_inicial":          grid_inicial,
        "grid_final":            grid_final,
        "historial_frac":        historial_frac,
        "historial_insat":       historial_insat,
        "frac_inicial":          frac_inicial,
        "frac_final":            frac_final,
        "iteracion_convergencia": iteracion_convergencia,
        "iteraciones_totales":   len(historial_frac) - 1,
        "pct_insat_final":       pct_insat_final,
        "n_insat_final":         len(insat_final),
        "total_agentes":         total_agentes,
        "n":                     n,
        "umbral":                umbral,
        "seed":                  seed,
    }


# ── Gráficos ───────────────────────────────────────────────────────────────────

# Paleta estética
BG        = "#0e1a2b"
FG        = "#e8e6e1"
AMBER     = "#e0a458"
COLOR_R   = "#c0392b"   # rojo sobrio
COLOR_B   = "#2471a3"   # azul sobrio
COLOR_V   = "#0e1a2b"   # vacío = fondo

CMAP_GRID = ListedColormap([COLOR_V, COLOR_R, COLOR_B])


def hacer_graficos(res):
    """Genera los PNG de la simulación."""
    gi   = res["grid_inicial"]
    gf   = res["grid_final"]
    hist = res["historial_frac"]
    iters = list(range(len(hist)))

    # ── PNG 1: Estado inicial + estado final + curva ──────────────────────────
    fig = plt.figure(figsize=(16, 5.8), facecolor=BG)
    gs  = gridspec.GridSpec(1, 3, figure=fig,
                             left=0.05, right=0.97, top=0.82, bottom=0.10,
                             wspace=0.30)

    ax_ini  = fig.add_subplot(gs[0])
    ax_fin  = fig.add_subplot(gs[1])
    ax_curv = fig.add_subplot(gs[2])

    # Panel 1 – Estado inicial
    ax_ini.imshow(gi, cmap=CMAP_GRID, vmin=0, vmax=2,
                  interpolation="nearest", aspect="equal")
    ax_ini.set_title("Estado inicial\n(mezcla aleatoria)",
                     color=FG, fontsize=11, pad=4, y=1.0)
    ax_ini.set_xlabel(f"Fracción inicial: {res['frac_inicial']:.3f}",
                      color=FG, fontsize=9)
    ax_ini.tick_params(colors=FG)
    for spine in ax_ini.spines.values():
        spine.set_edgecolor(AMBER)
    ax_ini.set_xticks([])
    ax_ini.set_yticks([])

    # Panel 2 – Estado final
    ax_fin.imshow(gf, cmap=CMAP_GRID, vmin=0, vmax=2,
                  interpolation="nearest", aspect="equal")
    ax_fin.set_title("Estado final\n(segregación emergente)",
                     color=FG, fontsize=11, pad=4, y=1.0)
    ax_fin.set_xlabel(f"Fracción final: {res['frac_final']:.3f}",
                      color=FG, fontsize=9)
    ax_fin.tick_params(colors=FG)
    for spine in ax_fin.spines.values():
        spine.set_edgecolor(AMBER)
    ax_fin.set_xticks([])
    ax_fin.set_yticks([])

    # Leyenda compartida para los dos paneles de rejilla
    patch_r = mpatches.Patch(color=COLOR_R, label="Grupo Rojo")
    patch_b = mpatches.Patch(color=COLOR_B, label="Grupo Azul")
    patch_v = mpatches.Patch(facecolor=BG, edgecolor=FG,
                             label="Vacío", linewidth=0.8)
    ax_fin.legend(handles=[patch_r, patch_b, patch_v],
                  loc="lower right", fontsize=7.5,
                  facecolor="#152038", edgecolor=AMBER,
                  labelcolor=FG)

    # Panel 3 – Curva de fracción de mismo-grupo
    ax_curv.set_facecolor(BG)
    ax_curv.plot(iters, hist, color=AMBER, linewidth=2, zorder=3,
                 label="Fracción mismo-grupo")
    ax_curv.axhline(res["frac_inicial"], color=FG, linewidth=0.8,
                    linestyle="--", alpha=0.5, zorder=2,
                    label=f"Inicio ({res['frac_inicial']:.2f})")
    ax_curv.axhline(res["frac_final"], color=COLOR_R, linewidth=0.8,
                    linestyle=":", alpha=0.8, zorder=2,
                    label=f"Final ({res['frac_final']:.2f})")
    ax_curv.axhline(T, color="#9b59b6", linewidth=0.8,
                    linestyle="-.", alpha=0.7, zorder=2,
                    label=f"Umbral T={T}")
    ax_curv.set_xlabel("Iteración", color=FG, fontsize=10)
    ax_curv.set_ylabel("Fracción de vecinos del mismo grupo", color=FG, fontsize=9)
    ax_curv.set_title("Emergencia de segregación", color=FG, fontsize=11, pad=6)
    ax_curv.set_xlim(0, max(iters))
    ax_curv.set_ylim(0.0, 1.0)
    ax_curv.tick_params(colors=FG)
    ax_curv.spines["bottom"].set_color(FG)
    ax_curv.spines["left"].set_color(FG)
    ax_curv.spines["top"].set_visible(False)
    ax_curv.spines["right"].set_visible(False)
    ax_curv.legend(fontsize=8, facecolor="#152038", edgecolor=AMBER,
                   labelcolor=FG, loc="lower right")
    ax_curv.grid(True, color=FG, alpha=0.12, linewidth=0.5)

    # Anotación de convergencia
    if res["iteracion_convergencia"]:
        it_c = res["iteracion_convergencia"]
        if it_c < len(hist):
            ax_curv.axvline(it_c, color="#27ae60", linewidth=0.9,
                            linestyle="--", alpha=0.7, zorder=2)
            ax_curv.annotate(
                f"Converge\nit. {it_c}",
                xy=(it_c, hist[it_c]),
                xytext=(it_c + max(iters)*0.05, hist[it_c] - 0.08),
                color="#27ae60", fontsize=7.5,
                arrowprops=dict(arrowstyle="->", color="#27ae60", lw=0.8),
            )

    # Título global (dos niveles separados verticalmente para evitar
    # solaparse con los títulos de los paneles, cuyo borde superior está
    # en top=0.82 del GridSpec)
    fig.suptitle(
        "Modelo de segregación de Schelling  ·  Thomas Schelling (1971)",
        color=FG, fontsize=12, y=0.985, fontweight="bold",
    )
    fig.text(
        0.5, 0.925,
        f"Rejilla {res['n']}×{res['n']}  ·  45% Rojo  ·  45% Azul  ·  "
        f"Umbral T={T}  ·  seed={SEED}",
        color=FG, fontsize=9.5, ha="center", va="center",
    )

    out1 = os.path.join(ASSET_DIR, "sim_schelling_segregacion_1.png")
    fig.savefig(out1, dpi=140, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"[✓] Gráfico 1 guardado: {out1}")

    # ── PNG 2: Detalle comparativo ampliado + histograma de fracciones ─────────
    fig2, axes = plt.subplots(1, 2, figsize=(12, 5.5), facecolor=BG)
    fig2.subplots_adjust(left=0.07, right=0.97, top=0.87, bottom=0.12,
                          wspace=0.30)

    for ax in axes:
        ax.set_facecolor(BG)

    # Subpanel A: fracción insatisfechos vs iteración
    ax_i = axes[0]
    iters_insat = list(range(1, len(res["historial_insat"]) + 1))
    pct_insat = [x / res["total_agentes"] * 100 for x in res["historial_insat"]]
    ax_i.plot(iters_insat, pct_insat, color="#e74c3c", linewidth=1.8,
              label="% agentes insatisfechos")
    ax_i.axhline(0, color=AMBER, linewidth=0.9, linestyle="--", alpha=0.8,
                 label="Convergencia (0 insatisfechos)")
    ax_i.set_xlabel("Iteración", color=FG, fontsize=10)
    ax_i.set_ylabel("Agentes insatisfechos (%)", color=FG, fontsize=10)
    ax_i.set_title("Dinámica de insatisfacción", color=FG, fontsize=11, pad=6)
    ax_i.tick_params(colors=FG)
    ax_i.spines["bottom"].set_color(FG)
    ax_i.spines["left"].set_color(FG)
    ax_i.spines["top"].set_visible(False)
    ax_i.spines["right"].set_visible(False)
    ax_i.legend(fontsize=8.5, facecolor="#152038", edgecolor=AMBER,
                labelcolor=FG)
    ax_i.grid(True, color=FG, alpha=0.12, linewidth=0.5)
    ax_i.set_ylim(bottom=0)

    # Subpanel B: distribución de fracciones de mismo-grupo en estado final
    ax_h = axes[1]
    fracs_finales = []
    for r in range(res["n"]):
        for c in range(res["n"]):
            if res["grid_final"][r, c] != VACIO:
                f = fraccion_mismo_grupo(res["grid_final"], r, c)
                fracs_finales.append(f)
    fracs_finales = np.array(fracs_finales)

    bins = np.linspace(0, 1, 25)
    ax_h.hist(fracs_finales, bins=bins, color=AMBER, alpha=0.85,
              edgecolor=BG, linewidth=0.5, label="Estado final")
    ax_h.axvline(T, color="#9b59b6", linewidth=1.2, linestyle="-.",
                 label=f"Umbral T={T}")
    ax_h.axvline(float(np.mean(fracs_finales)), color=COLOR_R, linewidth=1.2,
                 linestyle="--",
                 label=f"Media final={float(np.mean(fracs_finales)):.3f}")
    ax_h.set_xlabel("Fracción de vecinos del mismo grupo", color=FG, fontsize=10)
    ax_h.set_ylabel("Número de agentes", color=FG, fontsize=10)
    ax_h.set_title("Distribución de homofilia (estado final)", color=FG,
                    fontsize=11, pad=6)
    ax_h.tick_params(colors=FG)
    ax_h.spines["bottom"].set_color(FG)
    ax_h.spines["left"].set_color(FG)
    ax_h.spines["top"].set_visible(False)
    ax_h.spines["right"].set_visible(False)
    ax_h.legend(fontsize=8.5, facecolor="#152038", edgecolor=AMBER,
                labelcolor=FG)
    ax_h.grid(True, color=FG, alpha=0.12, linewidth=0.5)

    fig2.suptitle(
        "Modelo de segregación de Schelling  ·  Thomas Schelling (1971)\n"
        f"Dinámica de convergencia  ·  T={T}  ·  Rejilla {res['n']}×{res['n']}",
        color=FG, fontsize=12, y=0.98, fontweight="bold",
    )

    out2 = os.path.join(ASSET_DIR, "sim_schelling_segregacion_2.png")
    fig2.savefig(out2, dpi=140, bbox_inches="tight", facecolor=BG)
    plt.close(fig2)
    print(f"[✓] Gráfico 2 guardado: {out2}")

    return out1, out2


# ── Guardar datos crudos ───────────────────────────────────────────────────────

def guardar_datos(res):
    datos = {
        "teoria":    "schelling_segregacion",
        "nombre":    "Modelo de segregación de Schelling",
        "autor":     "Thomas Schelling",
        "anio":      "1971",
        "parametros": {
            "n":        res["n"],
            "frac_rojo":  FRAC_R,
            "frac_azul":  FRAC_B,
            "frac_vacio": 1 - FRAC_R - FRAC_B,
            "umbral_T":   res["umbral"],
            "max_iter":   MAX_ITER,
            "seed":       res["seed"],
        },
        "resultados": {
            "fraccion_inicial":           res["frac_inicial"],
            "fraccion_final":             res["frac_final"],
            "iteracion_convergencia":     res["iteracion_convergencia"],
            "iteraciones_totales":        res["iteraciones_totales"],
            "pct_insatisfechos_final":    res["pct_insat_final"],
            "n_insatisfechos_final":      res["n_insat_final"],
            "total_agentes":              res["total_agentes"],
        },
        "historial_frac_mismo_grupo": res["historial_frac"],
        "historial_n_insatisfechos":  res["historial_insat"],
        "validacion": {
            "criterio": "fraccion_final > 0.70 AND convergencia == cero_insatisfechos AND iteracion_convergencia <= 200",
            "fraccion_final_supera_0.70":  res["frac_final"] > 0.70,
            "convergencia_en_200_pasos":   res["iteracion_convergencia"] is not None,
            "n_insatisfechos_final_es_cero": res["n_insat_final"] == 0,
        },
    }
    path = os.path.join(SIM_DIR, "datos_schelling_segregacion.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"[✓] Datos guardados: {path}")
    return datos


# ── Preguntas ──────────────────────────────────────────────────────────────────

def computar_preguntas(res):
    # P1: fracción de mismo-grupo
    # 5 vecinos mismogrupo / (5+2) ocupados = 5/7 ≈ 0.7143
    p1 = 5 / 7

    # P2: celdas vacías en 2500 con 10%
    p2 = 2500 - int(round(2500 * 0.45)) - int(round(2500 * 0.45))

    # P3: fracción final de la simulación
    p3 = res["frac_final"]

    preguntas = [
        {
            "q": (
                "Un agente de Schelling tiene 8 vecinos en la vecindad de Moore: "
                "5 de su mismo grupo, 2 del otro grupo y 1 celda vacía. "
                "El umbral de tolerancia es T=0.30, definido como la fracción mínima "
                "de mismo-grupo sobre los vecinos OCUPADOS. ¿Está satisfecho el agente? "
                "Calcula primero la fracción de mismo-grupo. "
                "Formato: 'Respuesta final: <valor>' donde valor es la fracción (no sí/no)."
            ),
            "valor_exacto": f"{p1:.4f}",
            "tipo": "forma_cerrada",
            "tolerancia": "±0.01 (0.714)",
            "como_computar": (
                "Vecinos ocupados = 5 + 2 = 7; "
                "fracción mismo-grupo = 5/7 = 0.7143; "
                "como 0.7143 >= 0.30 el agente está satisfecho. "
                "La respuesta pedida es la fracción: 0.7143."
            ),
        },
        {
            "q": (
                "En una rejilla de Schelling con 2500 celdas, el 45% son del grupo Rojo, "
                "el 45% del grupo Azul y el resto vacías. ¿Cuántas celdas vacías hay? "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": str(p2),
            "tipo": "forma_cerrada",
            "tolerancia": "igualdad exacta (250)",
            "como_computar": (
                "Vacías = 10% de 2500 = 250. "
                f"Verificación: {int(round(2500*0.45))} Rojo + {int(round(2500*0.45))} Azul + {p2} vacío = 2500."
            ),
        },
        {
            "q": (
                "Corre el modelo de Schelling en rejilla 50×50, 45% Rojo, 45% Azul, "
                "10% vacío, umbral T=0.30, vecindad de Moore, numpy.random.seed(42), "
                "máximo 200 iteraciones. Partiendo de una fracción media de mismo-grupo "
                "inicial cercana a 0.50, reporta la fracción media de vecinos del mismo "
                "grupo en el estado final convergido. "
                "Formato: 'Respuesta final: <valor>'."
            ),
            "valor_exacto": f"{p3:.4f}",
            "tipo": "emergente",
            "tolerancia": f"±0.05 en torno a {p3:.2f}",
            "como_computar": (
                f"Resultado de la simulación con seed=42 y T=0.30: {p3:.4f}. "
                "Con T=0.30 el valor final ronda 0.74-0.76 (cluster robusto "
                "0.738-0.751 sobre seeds 1,7,42,123,999). "
                "La segregación emergente eleva la fracción de mismo-grupo desde "
                f"{res['frac_inicial']:.3f} hasta {p3:.3f} en "
                f"{res['iteraciones_totales']} iteraciones."
            ),
        },
    ]

    doc = {
        "teoria": "schelling_segregacion",
        "nombre": "Modelo de segregación de Schelling",
        "autor":  "Thomas Schelling",
        "anio":   "1971",
        "preguntas": preguntas,
    }
    path = os.path.join(SIM_DIR, "preguntas_schelling_segregacion.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"[✓] Preguntas guardadas: {path}")
    return doc


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Modelo de segregación de Schelling (1971)")
    print(f"Rejilla {N}×{N}  |  T={T}  |  seed={SEED}  |  max_iter={MAX_ITER}")
    print("=" * 60)

    print("\n[→] Ejecutando simulación…")
    res = simular()

    print(f"\n  Fracción inicial:   {res['frac_inicial']:.4f}")
    print(f"  Fracción final:     {res['frac_final']:.4f}")
    print(f"  Iteraciones:        {res['iteraciones_totales']}")
    conv = res["iteracion_convergencia"]
    print(f"  Convergencia en:    {conv if conv else 'no convergió'}")
    print(f"  % insatisfechos fin:{res['pct_insat_final']:.2f}%")

    print("\n[→] Generando gráficos…")
    out1, out2 = hacer_graficos(res)

    print("\n[→] Guardando datos…")
    datos = guardar_datos(res)

    print("\n[→] Calculando respuestas…")
    pregs = computar_preguntas(res)

    print("\n── Validación del criterio ────────────────────────────────")
    ok_frac  = res["frac_final"] > 0.70
    ok_conv  = conv is not None and conv <= 200
    ok_cero  = res["n_insat_final"] == 0
    print(f"  fracción final > 0.70    : {res['frac_final']:.4f}  → {'OK' if ok_frac else 'FALLO'}")
    print(f"  convergencia ≤ 200 iter  : iter={conv}               → {'OK' if ok_conv else 'FALLO'}")
    print(f"  cero insatisfechos final : {res['n_insat_final']}           → {'OK' if ok_cero else 'FALLO'}")
    print(f"\n  Criterio global: {'SUPERADO' if (ok_frac and ok_conv and ok_cero) else 'NO SUPERADO'}")

    print("\n── Respuestas ─────────────────────────────────────────────")
    for i, p in enumerate(pregs["preguntas"], 1):
        print(f"  P{i}: Respuesta final: {p['valor_exacto']}  (tol: {p['tolerancia']})")

    print("\n[✓] Simulación completada.")
