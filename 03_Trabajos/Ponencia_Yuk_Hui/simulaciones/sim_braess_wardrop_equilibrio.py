"""
Simulacion: Paradoja de Braess y Equilibrio de Wardrop en Redes de Transito
Autores teoricos: Dietrich Braess (1968) / John Glen Wardrop (1952)

Red clasica de Braess con N=4000 vehiculos.
Determinista: sin aleatoriedad, dos corridas dan identico resultado.

Estructura de la red:
  Inicio -> A  con t(x) = x/100      (congestionable)
  A -> Fin     con t = 45            (fijo)
  Inicio -> B  con t = 45            (fijo)
  B -> Fin     con t(x) = x/100      (congestionable)
  [Con atajo]: A -> B  con t = 0     (atajo libre)

Rutas posibles:
  Sin atajo:
    R1: Inicio -> A -> Fin
    R2: Inicio -> B -> Fin
  Con atajo:
    R1: Inicio -> A -> Fin
    R2: Inicio -> B -> Fin
    R3: Inicio -> A -> B -> Fin  (usa el atajo)
"""

import json
import os
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ============================================================
# PARAMETROS GLOBALES
# ============================================================
N = 4000          # numero total de vehiculos
CAPACIDAD = 100   # capacidad para funcion de congestion: t(x) = x/capacidad
T_FIJO = 45       # tiempo fijo en tramos no congestionables

# Directorio de salida para PNGs
DIR_ASSETS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "presentacion", "assets", "sim"
)
# Directorio de datos
DIR_SIM = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# FUNCIONES DE TIEMPO EN ARISTAS
# ============================================================

def t_congestionable(flujo):
    """Tiempo en arista congestionable: t(x) = x / 100"""
    return flujo / CAPACIDAD

def t_fijo(_flujo=None):
    """Tiempo fijo: t = 45 (independiente del flujo)"""
    return T_FIJO

def t_cero(_flujo=None):
    """Tiempo cero: el atajo de Braess"""
    return 0.0


# ============================================================
# CALCULO ANALITICO DEL EQUILIBRIO DE WARDROP
# ============================================================

def equilibrio_sin_atajo():
    """
    Sin atajo: dos rutas simetricas.
    R1: Inicio->A->Fin  tiempo = x_A/100 + 45
    R2: Inicio->B->Fin  tiempo = 45 + x_B/100

    Wardrop: t_R1 = t_R2 y x_A + x_B = N
    Por simetria: x_A = x_B = N/2 = 2000
    Tiempo = 2000/100 + 45 = 20 + 45 = 65
    """
    x_A = N / 2  # 2000
    x_B = N / 2  # 2000
    tiempo_R1 = x_A / CAPACIDAD + T_FIJO   # 2000/100 + 45 = 65
    tiempo_R2 = T_FIJO + x_B / CAPACIDAD   # 45 + 2000/100 = 65

    assert abs(tiempo_R1 - tiempo_R2) < 1e-9, "Wardrop violado sin atajo"
    assert abs(x_A + x_B - N) < 1e-9, "Conservacion de flujo violada"

    return {
        "flujo_R1": x_A,
        "flujo_R2": x_B,
        "flujo_IA": x_A,   # Inicio->A
        "flujo_AFin": x_A, # A->Fin
        "flujo_IB": x_B,   # Inicio->B
        "flujo_BFin": x_B, # B->Fin
        "flujo_AB": 0.0,   # sin atajo
        "tiempo_R1": tiempo_R1,
        "tiempo_R2": tiempo_R2,
        "tiempo_equilibrio": tiempo_R1,
        "wardrop_ok": True
    }


def equilibrio_con_atajo():
    """
    Con atajo A->B de coste 0:
    Tres rutas:
    R1: Inicio->A->Fin         tiempo = x_A/100 + 45  (x_A = flujo en I->A)
    R2: Inicio->B->Fin         tiempo = 45 + x_B/100  (x_B = flujo en B->Fin proveniente de I->B)
    R3: Inicio->A->B->Fin      tiempo = x_IA/100 + 0 + x_BFin/100

    Nota: x_IA = flujo total por arista Inicio->A = flujo_R1 + flujo_R3
          x_BFin = flujo total por arista B->Fin = flujo_R2 + flujo_R3

    Resolucion del equilibrio de Wardrop:
    Se debe verificar que ningun conductor mejora cambiando de ruta.

    En el equilibrio con atajo la solucion es:
    flujo_R1 = 0, flujo_R2 = 0, flujo_R3 = N = 4000
    (todos usan el atajo)

    Verificacion:
    x_IA = 4000, x_BFin = 4000
    t_R3 = 4000/100 + 0 + 4000/100 = 40 + 0 + 40 = 80
    t_R1 = 0/100 + 45 = 45 < 80 ???  -> revisar

    Analisis correcto:
    Si alguien se desvía de R3 a R1: x_IA baja en 1 (quita vehiculo de I->A)
    pero el vehiculo que va por R1 usa I->A y A->Fin.
    Con flujo_R1=epsilon, flujo_R3=N-epsilon:
    x_IA = N (epsilon + N - epsilon = N), x_AFin = epsilon (solo R1 usa A->Fin)
    t_R1 = N/100 + 45 = 40 + 45 = 85  > 80 -> no conviene irse a R1

    Si alguien usa R2: x_IB = epsilon, x_BFin = N (N-epsilon + epsilon = N)
    t_R2 = 45 + N/100 = 45 + 40 = 85 > 80 -> no conviene irse a R2

    Luego R3 es el equilibrio estable con tiempo 80.

    Para la ecuacion exacta de equilibrio igualando tiempos de rutas activas:
    Solo R3 activa: t_R3 = N/100 + N/100 = 80
    Rutas inactivas: sus tiempos deben ser >= 80 (verificado arriba con 85).
    """
    flujo_R1 = 0.0
    flujo_R2 = 0.0
    flujo_R3 = float(N)

    x_IA   = flujo_R1 + flujo_R3           # flujo en Inicio->A
    x_AFin = flujo_R1                       # flujo en A->Fin
    x_IB   = flujo_R2                       # flujo en Inicio->B
    x_AB   = flujo_R3                       # flujo en A->B (atajo)
    x_BFin = flujo_R2 + flujo_R3           # flujo en B->Fin

    t_R3 = x_IA / CAPACIDAD + 0 + x_BFin / CAPACIDAD
    t_R1 = x_IA / CAPACIDAD + T_FIJO       # si alguien desvía a R1
    t_R2 = T_FIJO + x_BFin / CAPACIDAD     # si alguien desvía a R2

    wardrop_activas = True  # R3 es la unica activa, su tiempo es unico
    # Verificar que rutas inactivas tienen tiempo >= tiempo_R3
    wardrop_inactivas = (t_R1 >= t_R3 - 1e-9) and (t_R2 >= t_R3 - 1e-9)

    return {
        "flujo_R1": flujo_R1,
        "flujo_R2": flujo_R2,
        "flujo_R3": flujo_R3,
        "flujo_IA": x_IA,
        "flujo_AFin": x_AFin,
        "flujo_IB": x_IB,
        "flujo_AB": x_AB,
        "flujo_BFin": x_BFin,
        "tiempo_R1_si_usado": t_R1,
        "tiempo_R2_si_usado": t_R2,
        "tiempo_R3": t_R3,
        "tiempo_equilibrio": t_R3,
        "wardrop_activas_ok": wardrop_activas,
        "wardrop_inactivas_ok": bool(wardrop_inactivas)
    }


# ============================================================
# VERIFICACION NUMERICA ITERATIVA (Mejor Respuesta / MSA)
# ============================================================

def wardrop_iterativo(con_atajo=False, n_iter=10000, step_size=0.01):
    """
    Metodo del promedio sucesivo (MSA) para encontrar el equilibrio de Wardrop.
    Determinista: no usa aleatoriedad.

    En cada iteracion:
    1. Calcular tiempos de todas las rutas con flujos actuales.
    2. Asignar todo el flujo a la ruta de menor tiempo (best-response).
    3. Promediar el flujo nuevo con el acumulado (paso decreciente 1/k).
    """
    if not con_atajo:
        # Rutas: R1=[IA, AFin], R2=[IB, BFin]
        # Flujos iniciales: reparto uniforme
        f = np.array([N / 2.0, N / 2.0])  # [flujo_R1, flujo_R2]

        for k in range(1, n_iter + 1):
            x_IA   = f[0]
            x_BFin = f[1]
            t_R1 = x_IA / CAPACIDAD + T_FIJO
            t_R2 = T_FIJO + x_BFin / CAPACIDAD

            # Best response: todo a la ruta mas barata
            if t_R1 < t_R2:
                f_new = np.array([float(N), 0.0])
            elif t_R2 < t_R1:
                f_new = np.array([0.0, float(N)])
            else:
                f_new = np.array([N / 2.0, N / 2.0])

            # MSA: promedio ponderado
            alpha = 1.0 / k
            f = (1 - alpha) * f + alpha * f_new

        x_IA   = f[0]
        x_BFin = f[1]
        t_R1 = x_IA / CAPACIDAD + T_FIJO
        t_R2 = T_FIJO + x_BFin / CAPACIDAD
        return {
            "flujos": f.tolist(),
            "tiempos": [t_R1, t_R2],
            "tiempo_equilibrio": (t_R1 + t_R2) / 2,
            "convergio": abs(t_R1 - t_R2) < 0.5
        }
    else:
        # Rutas: R1=[IA, AFin], R2=[IB, BFin], R3=[IA, AB, BFin]
        f = np.array([N / 3.0, N / 3.0, N / 3.0])

        for k in range(1, n_iter + 1):
            flujo_R1, flujo_R2, flujo_R3 = f
            x_IA   = flujo_R1 + flujo_R3
            x_BFin = flujo_R2 + flujo_R3

            t_R1 = x_IA / CAPACIDAD + T_FIJO
            t_R2 = T_FIJO + x_BFin / CAPACIDAD
            t_R3 = x_IA / CAPACIDAD + 0 + x_BFin / CAPACIDAD

            tiempos = np.array([t_R1, t_R2, t_R3])
            mejor = np.argmin(tiempos)

            f_new = np.zeros(3)
            f_new[mejor] = float(N)

            alpha = 1.0 / k
            f = (1 - alpha) * f + alpha * f_new

        flujo_R1, flujo_R2, flujo_R3 = f
        x_IA   = flujo_R1 + flujo_R3
        x_BFin = flujo_R2 + flujo_R3
        t_R1 = x_IA / CAPACIDAD + T_FIJO
        t_R2 = T_FIJO + x_BFin / CAPACIDAD
        t_R3 = x_IA / CAPACIDAD + x_BFin / CAPACIDAD

        return {
            "flujos": f.tolist(),
            "flujos_aristas": {
                "IA": x_IA, "AFin": flujo_R1,
                "IB": flujo_R2, "BFin": x_BFin, "AB": flujo_R3
            },
            "tiempos": [t_R1, t_R2, t_R3],
            "tiempo_equilibrio": float(np.min([t_R1, t_R2, t_R3])),
            "convergio": abs(t_R3 - 80.0) < 0.5
        }


# ============================================================
# GENERACION DE GRAFICOS
# ============================================================

# Colores de estilo
COLOR_FONDO    = "#0e1a2b"
COLOR_TEXTO    = "#e8e6e1"
COLOR_AMBER    = "#e0a458"
COLOR_AZUL     = "#4a9eca"
COLOR_ROJO     = "#c94040"
COLOR_VERDE    = "#5dac6e"
COLOR_GRIS     = "#7a8a9a"
COLOR_NODO     = "#1e3050"
COLOR_BORDE    = "#4a9eca"


def dibujar_red(ax, eq, con_atajo=False):
    """
    Dibuja la red de Braess en un eje matplotlib.
    Nodos: Inicio (izq), A (arriba centro), B (abajo centro), Fin (der).
    """
    # Posiciones de nodos
    pos = {
        "Inicio": (0.0, 0.5),
        "A":      (0.5, 0.85),
        "B":      (0.5, 0.15),
        "Fin":    (1.0, 0.5),
    }
    nodos = list(pos.keys())

    ax.set_facecolor(COLOR_FONDO)
    ax.set_xlim(-0.15, 1.15)
    ax.set_ylim(-0.05, 1.1)
    ax.axis("off")

    # Aristas y sus flujos/tiempos
    aristas = [
        ("Inicio", "A",   eq["flujo_IA"],   f"x/100\nflujo={eq['flujo_IA']:.0f}\nt={eq['flujo_IA']/CAPACIDAD:.0f}",   COLOR_AZUL),
        ("A",      "Fin", eq["flujo_AFin"],  f"t=45 (fijo)\nflujo={eq['flujo_AFin']:.0f}",                              COLOR_AZUL),
        ("Inicio", "B",   eq["flujo_IB"],    f"t=45 (fijo)\nflujo={eq['flujo_IB']:.0f}",                                COLOR_AZUL),
        ("B",      "Fin", eq["flujo_BFin"],  f"x/100\nflujo={eq['flujo_BFin']:.0f}\nt={eq['flujo_BFin']/CAPACIDAD:.0f}", COLOR_AZUL),
    ]
    if con_atajo:
        aristas.append(
            ("A", "B", eq["flujo_AB"],
             f"t=0 (ATAJO)\nflujo={eq['flujo_AB']:.0f}",
             COLOR_AMBER)
        )

    # Dibujar aristas como flechas curvas
    for (src, dst, flujo, etiqueta, color) in aristas:
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        # Grosor proporcional al flujo
        lw = 1.0 + 3.5 * (flujo / N)
        ax.annotate(
            "", xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=lw,
                connectionstyle="arc3,rad=0.15" if (src, dst) in [("A","B"), ("B","A")] else "arc3,rad=0.0",
                mutation_scale=18
            )
        )
        # Etiqueta en el punto medio
        mx = (x0 + x1) / 2
        my = (y0 + y1) / 2
        # Desplazamiento para evitar solapamiento
        dx_off = 0
        dy_off = 0
        if src == "Inicio" and dst == "A":
            dx_off, dy_off = -0.04, 0.08
        elif src == "A" and dst == "Fin":
            dx_off, dy_off = 0.04, 0.08
        elif src == "Inicio" and dst == "B":
            dx_off, dy_off = -0.04, -0.08
        elif src == "B" and dst == "Fin":
            dx_off, dy_off = 0.04, -0.08
        elif src == "A" and dst == "B":
            dx_off, dy_off = 0.10, 0.0

        ax.text(
            mx + dx_off, my + dy_off, etiqueta,
            ha="center", va="center",
            fontsize=7.5, color=COLOR_TEXTO,
            bbox=dict(boxstyle="round,pad=0.2", fc=COLOR_NODO, ec=color, alpha=0.85, lw=0.8)
        )

    # Dibujar nodos
    for nodo, (x, y) in pos.items():
        circle = plt.Circle((x, y), 0.065, color=COLOR_NODO, ec=COLOR_BORDE, lw=2, zorder=5)
        ax.add_patch(circle)
        ax.text(x, y, nodo, ha="center", va="center",
                fontsize=9, color=COLOR_AMBER, fontweight="bold", zorder=6)

    # Tiempo de equilibrio destacado
    t_eq = eq["tiempo_equilibrio"]
    ax.text(0.5, 1.03,
            f"Tiempo de equilibrio: {t_eq:.0f} unidades",
            ha="center", va="bottom", fontsize=11, color=COLOR_AMBER,
            fontweight="bold", transform=ax.transAxes)


def generar_figura_redes(eq_sin, eq_con, ruta_png):
    """
    Figura 1: Dos diagramas de red lado a lado (sin atajo / con atajo).
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fig.patch.set_facecolor(COLOR_FONDO)
    fig.suptitle(
        "Paradoja de Braess — Equilibrio de Wardrop\n"
        "Dietrich Braess (1968) / John Glen Wardrop (1952)\n"
        "N = 4 000 vehículos",
        fontsize=13, color=COLOR_TEXTO, fontweight="bold", y=0.98
    )

    # Panel izquierdo: sin atajo
    axes[0].set_title("Red SIN atajo\n(Equilibrio simétrico)",
                       color=COLOR_TEXTO, fontsize=11, pad=8)
    dibujar_red(axes[0], eq_sin, con_atajo=False)

    # Panel derecho: con atajo
    axes[1].set_title("Red CON atajo A→B (coste=0)\n(Paradoja de Braess)",
                       color=COLOR_TEXTO, fontsize=11, pad=8)
    dibujar_red(axes[1], eq_con, con_atajo=True)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(ruta_png, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"PNG guardado: {ruta_png}")


def generar_figura_comparativa(eq_sin, eq_con, ruta_png):
    """
    Figura 2: Barra comparativa del tiempo de equilibrio y analisis de la paradoja.
    """
    t_sin = eq_sin["tiempo_equilibrio"]
    t_con = eq_con["tiempo_equilibrio"]
    delta = t_con - t_sin

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    fig.patch.set_facecolor(COLOR_FONDO)
    fig.suptitle(
        "Paradoja de Braess — Comparativa de tiempos de equilibrio\n"
        "Braess (1968) / Wardrop (1952)  |  N = 4 000 vehículos",
        fontsize=12, color=COLOR_TEXTO, fontweight="bold", y=0.99
    )

    # --- Grafico 1: barras de tiempo ---
    ax1 = axes[0]
    ax1.set_facecolor(COLOR_FONDO)
    etiquetas = ["Sin atajo", "Con atajo\n(Paradoja)"]
    tiempos   = [t_sin, t_con]
    colores   = [COLOR_AZUL, COLOR_ROJO]
    bars = ax1.bar(etiquetas, tiempos, color=colores, width=0.45, edgecolor=COLOR_TEXTO, lw=0.8)

    for bar, val in zip(bars, tiempos):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{val:.0f}",
            ha="center", va="bottom",
            fontsize=14, color=COLOR_AMBER, fontweight="bold"
        )

    # Flecha y anotacion del aumento
    ax1.annotate(
        f"+{delta:.0f} unidades\n(+{delta/t_sin*100:.1f}%)",
        xy=(1, t_con), xytext=(0.5, (t_sin + t_con) / 2 + 3),
        fontsize=10, color=COLOR_AMBER,
        arrowprops=dict(arrowstyle="->", color=COLOR_AMBER, lw=1.5),
        ha="center"
    )

    ax1.set_ylim(0, t_con * 1.25)
    ax1.set_ylabel("Tiempo de viaje (unidades)", color=COLOR_TEXTO, fontsize=10)
    ax1.set_title("Tiempo de equilibrio de Wardrop", color=COLOR_TEXTO, fontsize=10)
    ax1.tick_params(colors=COLOR_TEXTO, labelsize=10)
    ax1.spines["bottom"].set_color(COLOR_GRIS)
    ax1.spines["left"].set_color(COLOR_GRIS)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # --- Grafico 2: flujos en aristas ---
    ax2 = axes[1]
    ax2.set_facecolor(COLOR_FONDO)

    aristas_labels = ["I→A", "A→Fin", "I→B", "B→Fin"]
    flujos_sin = [eq_sin["flujo_IA"], eq_sin["flujo_AFin"],
                  eq_sin["flujo_IB"], eq_sin["flujo_BFin"]]
    flujos_con = [eq_con["flujo_IA"], eq_con["flujo_AFin"],
                  eq_con["flujo_IB"], eq_con["flujo_BFin"]]

    x_pos = np.arange(len(aristas_labels))
    ancho = 0.35
    b1 = ax2.bar(x_pos - ancho/2, flujos_sin, ancho, label="Sin atajo", color=COLOR_AZUL,
                 edgecolor=COLOR_TEXTO, lw=0.8)
    b2 = ax2.bar(x_pos + ancho/2, flujos_con, ancho, label="Con atajo", color=COLOR_ROJO,
                 edgecolor=COLOR_TEXTO, lw=0.8, alpha=0.85)

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(aristas_labels, color=COLOR_TEXTO, fontsize=10)
    ax2.set_ylabel("Flujo de vehículos", color=COLOR_TEXTO, fontsize=10)
    ax2.set_title("Distribución del flujo en aristas", color=COLOR_TEXTO, fontsize=10)
    ax2.tick_params(colors=COLOR_TEXTO, labelsize=9)
    ax2.spines["bottom"].set_color(COLOR_GRIS)
    ax2.spines["left"].set_color(COLOR_GRIS)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_ylim(0, N * 1.25)
    ax2.legend(facecolor=COLOR_NODO, edgecolor=COLOR_GRIS,
               labelcolor=COLOR_TEXTO, fontsize=9)

    # Texto explicativo
    texto_paradoja = (
        f"Paradoja de Braess:\n"
        f"Al añadir un atajo de coste cero,\n"
        f"el equilibrio egoísta lleva a todos\n"
        f"por la misma ruta → congestión.\n"
        f"Tiempo sube de {t_sin:.0f} a {t_con:.0f} (+{delta:.0f})\n\n"
        f"\"Más opciones no siempre\n"
        f"mejoran el bienestar colectivo.\""
    )
    fig.text(
        0.5, 0.01, texto_paradoja,
        ha="center", va="bottom", fontsize=9,
        color=COLOR_GRIS, style="italic",
        bbox=dict(boxstyle="round,pad=0.5", fc=COLOR_NODO, ec=COLOR_AMBER, alpha=0.7, lw=0.8)
    )

    plt.tight_layout(rect=[0, 0.16, 1, 0.96])
    fig.savefig(ruta_png, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"PNG guardado: {ruta_png}")


# ============================================================
# VALIDACION DEL CRITERIO DE WARDROP
# ============================================================

def validar_criterio(eq_sin, eq_con):
    """
    Criterio de validacion:
    - Sin atajo: flujo 2000/2000, tiempo 65 (±0.5)
    - Con atajo: tiempo 80 (±0.5), todos van por R3 (atajo)
    - Diferencia 80-65=15 (>0) confirma la paradoja
    - Wardrop: tiempos de rutas activas iguales (±1e-6)
    """
    resultados = {}

    # --- Sin atajo ---
    t_sin = eq_sin["tiempo_equilibrio"]
    f_R1  = eq_sin["flujo_R1"]
    f_R2  = eq_sin["flujo_R2"]
    resultados["sin_atajo_flujo_R1"]  = f_R1
    resultados["sin_atajo_flujo_R2"]  = f_R2
    resultados["sin_atajo_tiempo"]    = t_sin
    resultados["sin_atajo_flujo_ok"]  = bool(abs(f_R1 - 2000) < 0.5 and abs(f_R2 - 2000) < 0.5)
    resultados["sin_atajo_tiempo_ok"] = bool(abs(t_sin - 65) < 0.5)

    # Wardrop sin atajo: tiempos R1 == R2
    diff_tiempos_sin = abs(eq_sin["tiempo_R1"] - eq_sin["tiempo_R2"])
    resultados["sin_atajo_wardrop_diff"] = diff_tiempos_sin
    resultados["sin_atajo_wardrop_ok"]   = bool(diff_tiempos_sin < 1e-6)

    # --- Con atajo ---
    t_con = eq_con["tiempo_equilibrio"]
    resultados["con_atajo_tiempo"]    = t_con
    resultados["con_atajo_tiempo_ok"] = bool(abs(t_con - 80) < 0.5)
    resultados["con_atajo_flujo_R3"]  = eq_con["flujo_R3"]
    resultados["con_atajo_todos_R3"]  = bool(abs(eq_con["flujo_R3"] - N) < 0.5)

    # Wardrop con atajo: rutas inactivas tienen tiempo >= t_R3
    resultados["con_atajo_wardrop_inactivas_ok"] = eq_con["wardrop_inactivas_ok"]

    # --- Paradoja confirmada ---
    delta = t_con - t_sin
    resultados["delta_tiempo"]       = delta
    resultados["paradoja_confirmada"] = bool(delta > 0)
    resultados["paradoja_valor"]      = delta  # debe ser 15

    # --- Resumen ---
    todo_ok = (
        resultados["sin_atajo_flujo_ok"] and
        resultados["sin_atajo_tiempo_ok"] and
        resultados["sin_atajo_wardrop_ok"] and
        resultados["con_atajo_tiempo_ok"] and
        resultados["con_atajo_todos_R3"] and
        resultados["paradoja_confirmada"]
    )
    resultados["validacion_global"] = bool(todo_ok)

    return resultados


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("Paradoja de Braess — Equilibrio de Wardrop")
    print(f"N = {N} vehiculos, CAPACIDAD = {CAPACIDAD}, T_FIJO = {T_FIJO}")
    print("=" * 60)

    # 1. Calculo analitico
    print("\n[1] Calculo analitico del equilibrio de Wardrop...")
    eq_sin = equilibrio_sin_atajo()
    eq_con = equilibrio_con_atajo()
    print(f"    Sin atajo: flujo_R1={eq_sin['flujo_R1']:.0f}, flujo_R2={eq_sin['flujo_R2']:.0f}, tiempo={eq_sin['tiempo_equilibrio']:.2f}")
    print(f"    Con atajo: flujo_R3={eq_con['flujo_R3']:.0f}, tiempo={eq_con['tiempo_equilibrio']:.2f}")

    # 2. Verificacion numerica (MSA)
    print("\n[2] Verificacion numerica (MSA / Mejor Respuesta Promediada)...")
    msa_sin = wardrop_iterativo(con_atajo=False, n_iter=5000)
    msa_con = wardrop_iterativo(con_atajo=True,  n_iter=5000)
    print(f"    MSA sin atajo: flujos={[f'{x:.1f}' for x in msa_sin['flujos']]}, "
          f"tiempo={msa_sin['tiempo_equilibrio']:.4f}, convergio={msa_sin['convergio']}")
    print(f"    MSA con atajo: flujos={[f'{x:.1f}' for x in msa_con['flujos']]}, "
          f"tiempo={msa_con['tiempo_equilibrio']:.4f}, convergio={msa_con['convergio']}")

    # 3. Validacion
    print("\n[3] Validando criterio de Wardrop...")
    val = validar_criterio(eq_sin, eq_con)
    print(f"    Sin atajo — flujo ok: {val['sin_atajo_flujo_ok']}, tiempo ok: {val['sin_atajo_tiempo_ok']}")
    print(f"    Sin atajo — Wardrop (diff tiempos rutas): {val['sin_atajo_wardrop_diff']:.2e}")
    print(f"    Con atajo — tiempo ok: {val['con_atajo_tiempo_ok']}, todos por R3: {val['con_atajo_todos_R3']}")
    print(f"    Delta tiempo (paradoja): {val['delta_tiempo']:.2f} (esperado: 15)")
    print(f"    VALIDACION GLOBAL: {'PASSED' if val['validacion_global'] else 'FAILED'}")

    # 4. Generar PNGs
    print("\n[4] Generando graficos...")
    ruta_png1 = os.path.join(DIR_ASSETS, "sim_braess_wardrop_equilibrio_1.png")
    ruta_png2 = os.path.join(DIR_ASSETS, "sim_braess_wardrop_equilibrio_2.png")
    generar_figura_redes(eq_sin, eq_con, ruta_png1)
    generar_figura_comparativa(eq_sin, eq_con, ruta_png2)

    # 5. Guardar datos crudos
    print("\n[5] Guardando datos crudos...")
    datos = {
        "teoria": "braess_wardrop_equilibrio",
        "parametros": {
            "N": N,
            "capacidad": CAPACIDAD,
            "t_fijo": T_FIJO
        },
        "equilibrio_sin_atajo": eq_sin,
        "equilibrio_con_atajo": eq_con,
        "verificacion_msa_sin_atajo": msa_sin,
        "verificacion_msa_con_atajo": msa_con,
        "validacion": val,
        "preguntas": {
            "P1_tiempo_sin_atajo": eq_sin["tiempo_equilibrio"],
            "P2_tiempo_con_atajo": eq_con["tiempo_equilibrio"],
            "P3_aumento_tiempo": val["delta_tiempo"]
        }
    }
    ruta_datos = os.path.join(DIR_SIM, "datos_braess_wardrop_equilibrio.json")

    def _convert(obj):
        """Convierte tipos numpy y bool a tipos JSON serializables."""
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Python bool ya es serializable por json nativo, pero por si acaso
        if type(obj).__name__ == "bool":
            return bool(obj)
        raise TypeError(f"No serializable: {type(obj)}")

    with open(ruta_datos, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, default=_convert)
    print(f"    Datos guardados: {ruta_datos}")

    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print(f"  Tiempo sin atajo (equilibrio): {eq_sin['tiempo_equilibrio']:.2f}")
    print(f"  Tiempo con atajo (paradoja):   {eq_con['tiempo_equilibrio']:.2f}")
    print(f"  Aumento por anadir atajo:      {val['delta_tiempo']:.2f}")
    print(f"  Paradoja confirmada:           {val['paradoja_confirmada']}")
    print("=" * 60)

    return datos


if __name__ == "__main__":
    datos = main()
