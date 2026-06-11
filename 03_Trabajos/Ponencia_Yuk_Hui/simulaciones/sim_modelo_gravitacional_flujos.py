"""
Modelo gravitacional de interaccion espacial (flujos de viaje/migracion)
Autor: John Q. Stewart (analogia de cuadrado inverso); raices en Henry Carey
       (1858) y G. K. Zipf (1946); derivacion entropica de Alan Wilson (1967)
Año: 1948/1967

Formulacion:
    T_ij = G * P_i^a * P_j^b / d_ij^c
    Con a=b=1, c=2 (analogia newtoniana exacta de cuadrado inverso):
    T_ij = G * P_i * P_j / d_ij^2
    Esta forma de cuadrado inverso con constante de proporcionalidad es la de
    John Q. Stewart (1948), I_ij = k*P_i*P_j/d_ij^2. NO es la de Zipf, cuya
    hipotesis publicada en 1946 es la forma c=1 (P1*P2/D, distancia lineal).
    Aqui se simula la forma c=2, por tanto la fuente del exponente es Stewart.

Experimento:
    3 zonas: P=[10000, 5000, 20000]
    Posiciones: (0,0), (30,0), (0,40)
    G=1, a=b=1, c=2
    Distancias euclidianas: d_12=30, d_13=40, d_23=50

Verificacion:
    T_12 = 10000*5000/30^2 = 50000000/900 ≈ 55555.56
    T_13 = 10000*20000/40^2 = 200000000/1600 = 125000.00
    T_23 = 5000*20000/50^2 = 100000000/2500 = 40000.00
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import networkx as nx
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui")
SIM_DIR = BASE / "simulaciones"
ASSETS_DIR = BASE / "presentacion" / "assets" / "sim"
SIM_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ── Paleta de colores ──────────────────────────────────────────────────────────
BG_COLOR = "#0e1a2b"
TEXT_COLOR = "#e8e6e1"
ACCENT_AMBER = "#e0a458"
COLOR_NODE1 = "#4e9af1"   # azul claro
COLOR_NODE2 = "#6bcb77"   # verde
COLOR_NODE3 = "#c77dff"   # violeta
EDGE_COLOR = "#e0a458"
GRID_COLOR = "#1e2f45"
CMAP_HEAT = "YlOrBr"

# ── Parametros del modelo ──────────────────────────────────────────────────────
# Determinista: sin semilla necesaria (formula cerrada, sin aleatoriedad)
G = 1.0   # constante gravitacional
a = 1.0   # exponente de masa de origen
b = 1.0   # exponente de masa de destino
c = 2.0   # exponente de friccion de la distancia

# Zonas
nombres_zonas = ["Zona 1\n(0,0)", "Zona 2\n(30,0)", "Zona 3\n(0,40)"]
etiquetas_cortas = ["Z1", "Z2", "Z3"]
poblaciones = np.array([10000.0, 5000.0, 20000.0])
posiciones = np.array([[0.0, 0.0], [30.0, 0.0], [0.0, 40.0]])
n = len(poblaciones)

# ── Calcular distancias euclidianas ───────────────────────────────────────────
def calcular_distancias(pos):
    """Calcula matriz de distancias euclidianas entre zonas."""
    n = len(pos)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                diff = pos[i] - pos[j]
                D[i, j] = np.sqrt(np.dot(diff, diff))
    return D

D = calcular_distancias(posiciones)
# Verificacion de distancias
assert abs(D[0, 1] - 30.0) < 1e-9, f"d_12 deberia ser 30, es {D[0,1]}"
assert abs(D[0, 2] - 40.0) < 1e-9, f"d_13 deberia ser 40, es {D[0,2]}"
assert abs(D[1, 2] - 50.0) < 1e-9, f"d_23 deberia ser 50, es {D[1,2]}"

# ── Calcular matriz de flujos T_ij ─────────────────────────────────────────────
def modelo_gravitacional(G, P, D, a, b, c):
    """
    Calcula T_ij = G * P_i^a * P_j^b / d_ij^c
    La diagonal (i==j) se deja en 0.
    """
    n = len(P)
    T = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                T[i, j] = G * (P[i]**a) * (P[j]**b) / (D[i, j]**c)
    return T

T = modelo_gravitacional(G, poblaciones, D, a, b, c)

# ── Verificacion contra valores teoricos ──────────────────────────────────────
T12_esperado = G * 10000 * 5000 / 30**2    # = 55555.555...
T13_esperado = G * 10000 * 20000 / 40**2   # = 125000.0
T23_esperado = G * 5000 * 20000 / 50**2    # = 40000.0

tol = 0.005  # 0.5%
assert abs(T[0,1] - T12_esperado) / T12_esperado < tol, f"T_12 fallo: {T[0,1]} vs {T12_esperado}"
assert abs(T[0,2] - T13_esperado) / T13_esperado < tol, f"T_13 fallo: {T[0,2]} vs {T13_esperado}"
assert abs(T[1,2] - T23_esperado) / T23_esperado < tol, f"T_23 fallo: {T[1,2]} vs {T23_esperado}"

# Verificar simetria T_ij = T_ji
for i in range(n):
    for j in range(n):
        assert abs(T[i,j] - T[j,i]) < 1e-6, f"Asimetria en T[{i},{j}]={T[i,j]} vs T[{j},{i}]={T[j,i]}"

# Flujos totales por zona
flujos_salientes = T.sum(axis=1)
flujos_entrantes = T.sum(axis=0)
suma_pares = T[0,1] + T[0,2] + T[1,2]

print("=" * 60)
print("MODELO GRAVITACIONAL DE INTERACCION ESPACIAL")
print("J. Q. Stewart (forma c=2) — raices Carey/Zipf, entropia Wilson  —  1948/1967")
print("=" * 60)
print(f"\nParametros: G={G}, a={a}, b={b}, c={c}")
print(f"\nPoblaciones: {poblaciones}")
print(f"\nDistancias:")
print(f"  d_12 = {D[0,1]:.1f}")
print(f"  d_13 = {D[0,2]:.1f}")
print(f"  d_23 = {D[1,2]:.1f}")
print(f"\nMatriz de flujos T_ij:")
for i in range(n):
    row = [f"{T[i,j]:>12.2f}" for j in range(n)]
    print(f"  Zona {i+1}: {' '.join(row)}")
print(f"\nFlujos entre pares:")
print(f"  T_12 = {T[0,1]:.4f}  (esperado: {T12_esperado:.4f})")
print(f"  T_13 = {T[0,2]:.4f}  (esperado: {T13_esperado:.4f})")
print(f"  T_23 = {T[1,2]:.4f}  (esperado: {T23_esperado:.4f})")
print(f"\nSuma de todos los flujos entre pares distintos: {suma_pares:.4f}")
print(f"\nFlujos salientes por zona: {flujos_salientes}")
print(f"Flujos entrantes por zona: {flujos_entrantes}")
print("\nVerificacion de simetria T_ij = T_ji: OK")
print("Verificacion de tolerancia ±0.5%: OK")

# ── Prueba de duplicacion de distancia (criterio_validacion) ──────────────────
# Al duplicar d_12 (30 → 60), con c=2, el flujo debe caer a 1/4
T12_doble_dist = G * 10000 * 5000 / (60.0**2)
ratio = T12_doble_dist / T[0,1]
print(f"\nPrueba duplicacion distancia: d_12*2=60")
print(f"  T_12_original = {T[0,1]:.4f}")
print(f"  T_12_d2x      = {T12_doble_dist:.4f}")
print(f"  ratio         = {ratio:.6f}  (esperado 0.25)")
assert abs(ratio - 0.25) < 1e-9, f"Duplicacion de distancia no da 1/4: {ratio}"

# ── Regresion log-log para recuperar c ───────────────────────────────────────
# log(T_ij) = log(G*P_i*P_j) - c*log(d_ij)
# => controlando masas: residuo vs log(d_ij)
pares = [(0,1), (0,2), (1,2)]
log_T_controlado = []
log_d = []
for (i,j) in pares:
    masa = G * poblaciones[i] * poblaciones[j]
    log_T_controlado.append(np.log(T[i,j]) - np.log(masa))
    log_d.append(np.log(D[i,j]))

log_T_arr = np.array(log_T_controlado)
log_d_arr = np.array(log_d)
# Regresion: log_T_ctrl = alpha - c * log_d
# Usando polyfit
coefs = np.polyfit(log_d_arr, log_T_arr, 1)
c_recuperado = -coefs[0]
print(f"\nRegresion log-log para recuperar c:")
print(f"  c recuperado = {c_recuperado:.6f}  (esperado: {c})")
assert abs(c_recuperado - c) < 0.01, f"c recuperado {c_recuperado} difiere de {c}"

# ── Guardar datos crudos en JSON ──────────────────────────────────────────────
datos = {
    "teoria": "modelo_gravitacional_flujos",
    "nombre": "Modelo gravitacional de interaccion espacial (flujos de viaje/migracion)",
    "autor": "John Q. Stewart (analogia de cuadrado inverso); raices en Henry Carey (1858) y G. K. Zipf (1946); derivacion entropica de Alan Wilson (1967)",
    "anio": "1948/1967",
    "parametros": {
        "G": G, "a": a, "b": b, "c": c
    },
    "zonas": [
        {"id": i+1, "poblacion": float(poblaciones[i]),
         "posicion": list(posiciones[i])} for i in range(n)
    ],
    "distancias": {
        "d_12": float(D[0,1]),
        "d_13": float(D[0,2]),
        "d_23": float(D[1,2])
    },
    "flujos": {
        "T_12": float(T[0,1]),
        "T_13": float(T[0,2]),
        "T_23": float(T[1,2]),
        "T_21": float(T[1,0]),
        "T_31": float(T[2,0]),
        "T_32": float(T[2,1])
    },
    "flujos_esperados": {
        "T_12": float(T12_esperado),
        "T_13": float(T13_esperado),
        "T_23": float(T23_esperado)
    },
    "suma_pares": float(suma_pares),
    "flujos_salientes": [float(x) for x in flujos_salientes],
    "flujos_entrantes": [float(x) for x in flujos_entrantes],
    "validacion": {
        "simetria_ok": True,
        "tolerancia_05pct_ok": True,
        "duplicacion_distancia_ratio": float(ratio),
        "c_recuperado_regresion": float(c_recuperado)
    },
    "matriz_T_completa": T.tolist()
}

json_path = SIM_DIR / "datos_modelo_gravitacional_flujos.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"\nDatos guardados en: {json_path}")

# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 1: Mapa de zonas con flujos proporcionales
# ══════════════════════════════════════════════════════════════════════════════
fig1, ax1 = plt.subplots(figsize=(10, 9), facecolor=BG_COLOR)
ax1.set_facecolor(BG_COLOR)

# Dibujar ejes de referencia
ax1.set_xlim(-8, 42)
ax1.set_ylim(-8, 52)
ax1.set_aspect('equal')

# Grilla suave
ax1.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)
ax1.tick_params(colors=TEXT_COLOR, which='both')
for spine in ax1.spines.values():
    spine.set_edgecolor(GRID_COLOR)
ax1.set_xlabel("Coordenada X (km)", color=TEXT_COLOR, fontsize=11)
ax1.set_ylabel("Coordenada Y (km)", color=TEXT_COLOR, fontsize=11)
ax1.xaxis.label.set_color(TEXT_COLOR)
ax1.yaxis.label.set_color(TEXT_COLOR)
plt.setp(ax1.get_xticklabels(), color=TEXT_COLOR)
plt.setp(ax1.get_yticklabels(), color=TEXT_COLOR)

# Normalizar flujos para grosor de líneas
flujos_pares = [T[0,1], T[0,2], T[1,2]]
flujo_max = max(flujos_pares)
# Grosor entre 1 y 8
def escalar_grosor(flujo, fmax, min_w=1.5, max_w=9.0):
    return min_w + (max_w - min_w) * (flujo / fmax)

colores_nodos = [COLOR_NODE1, COLOR_NODE2, COLOR_NODE3]
pob_max = max(poblaciones)

# Dibujar aristas con grosor proporcional al flujo
pares_idx = [(0, 1), (0, 2), (1, 2)]
pares_labels = ["T₁₂", "T₁₃", "T₂₃"]
for (i, j), lbl in zip(pares_idx, pares_labels):
    flujo = T[i, j]
    grosor = escalar_grosor(flujo, flujo_max)
    xi, yi = posiciones[i]
    xj, yj = posiciones[j]
    ax1.plot([xi, xj], [yi, yj],
             color=EDGE_COLOR, linewidth=grosor, alpha=0.55, zorder=1)
    # Etiqueta en el punto medio
    mx, my = (xi + xj) / 2, (yi + yj) / 2
    # Offset perpendicular para no solapar
    dx, dy = xj - xi, yj - yi
    norm = np.sqrt(dx**2 + dy**2)
    ox, oy = -dy/norm * 2.5, dx/norm * 2.5
    val_fmt = f"{lbl} = {flujo:,.0f}"
    ax1.text(mx + ox, my + oy, val_fmt,
             color=ACCENT_AMBER, fontsize=9, ha='center', va='center',
             fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.25', facecolor=BG_COLOR,
                       edgecolor=EDGE_COLOR, alpha=0.85))

# Dibujar nodos como círculos proporcionales a la población
radio_base = 2.8
for i in range(n):
    radio = radio_base * np.sqrt(poblaciones[i] / pob_max)
    circle = plt.Circle(posiciones[i], radio, color=colores_nodos[i],
                        alpha=0.88, zorder=3)
    ax1.add_patch(circle)
    # Etiqueta con nombre y población
    ax1.text(posiciones[i][0], posiciones[i][1] + radio + 1.5,
             f"Zona {i+1}\nP = {int(poblaciones[i]):,}",
             color=TEXT_COLOR, fontsize=9.5, ha='center', va='bottom',
             fontweight='bold', zorder=5)

# Leyenda de grosor de aristas
leyenda_flujos = [
    Line2D([0], [0], color=EDGE_COLOR, linewidth=escalar_grosor(T[0,2], flujo_max),
           label=f"T₁₃ = {T[0,2]:,.0f} (mayor)"),
    Line2D([0], [0], color=EDGE_COLOR, linewidth=escalar_grosor(T[0,1], flujo_max),
           label=f"T₁₂ = {T[0,1]:,.0f}"),
    Line2D([0], [0], color=EDGE_COLOR, linewidth=escalar_grosor(T[1,2], flujo_max),
           label=f"T₂₃ = {T[1,2]:,.0f} (menor)"),
]
leyenda_nodos = [
    mpatches.Patch(color=colores_nodos[i],
                   label=f"Zona {i+1}: P={int(poblaciones[i]):,}")
    for i in range(n)
]
leg = ax1.legend(handles=leyenda_flujos + leyenda_nodos,
                 loc='upper right', fontsize=8.5,
                 facecolor="#132038", edgecolor=GRID_COLOR,
                 labelcolor=TEXT_COLOR, framealpha=0.9)

ax1.set_title(
    "Modelo Gravitacional de Interacción Espacial\n"
    "Flujos T$_{ij}$ = G·P$_i$·P$_j$ / d$_{ij}^2$  —  "
    "Stewart (c=2, 1948); raíces Carey/Zipf; entropía Wilson (1967)",
    color=TEXT_COLOR, fontsize=12, fontweight='bold', pad=14
)

# Nota sobre la formula
ax1.text(0.01, 0.01,
         "El grosor de cada arista es proporcional al flujo T$_{ij}$.\n"
         "El tamaño de cada nodo es proporcional a √Población.",
         transform=ax1.transAxes, color=TEXT_COLOR, fontsize=7.5, alpha=0.75,
         va='bottom')

plt.tight_layout()
png1 = ASSETS_DIR / "sim_modelo_gravitacional_flujos_1.png"
fig1.savefig(png1, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
plt.close(fig1)
print(f"Grafico 1 guardado en: {png1}")

# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 2: Mapa de calor de la matriz de flujos T_ij
# ══════════════════════════════════════════════════════════════════════════════
fig2, axes = plt.subplots(1, 2, figsize=(13, 5.5), facecolor=BG_COLOR)
fig2.patch.set_facecolor(BG_COLOR)

# --- Subgráfico izquierdo: mapa de calor completo (con ceros en diagonal) ---
ax_heat = axes[0]
ax_heat.set_facecolor(BG_COLOR)

# Crear mascara para la diagonal (ceros)
T_plot = T.copy()
mask = np.eye(n, dtype=bool)
T_masked = np.ma.array(T_plot, mask=mask)

cmap = plt.cm.get_cmap(CMAP_HEAT).copy()
cmap.set_bad(color=BG_COLOR)

im = ax_heat.imshow(T_masked, cmap=cmap, aspect='auto', interpolation='nearest')
cb = fig2.colorbar(im, ax=ax_heat, shrink=0.8)
cb.set_label("Flujo T$_{ij}$ (viajes)", color=TEXT_COLOR, fontsize=10)
cb.ax.yaxis.set_tick_params(color=TEXT_COLOR)
plt.setp(cb.ax.yaxis.get_ticklabels(), color=TEXT_COLOR)

# Anotaciones en celdas
for i in range(n):
    for j in range(n):
        if i != j:
            val = T[i, j]
            ax_heat.text(j, i, f"{val:,.0f}",
                         ha='center', va='center',
                         color='black' if val > T.max()*0.4 else TEXT_COLOR,
                         fontsize=11, fontweight='bold')
        else:
            ax_heat.text(j, i, "—", ha='center', va='center',
                         color=GRID_COLOR, fontsize=13)

etiquetas_ejes = ["Zona 1\n(P=10000)", "Zona 2\n(P=5000)", "Zona 3\n(P=20000)"]
ax_heat.set_xticks(range(n))
ax_heat.set_yticks(range(n))
ax_heat.set_xticklabels(etiquetas_ejes, color=TEXT_COLOR, fontsize=9)
ax_heat.set_yticklabels(etiquetas_ejes, color=TEXT_COLOR, fontsize=9)
for spine in ax_heat.spines.values():
    spine.set_edgecolor(GRID_COLOR)
ax_heat.set_title("Matriz de Flujos T$_{ij}$\n(mapa de calor)", color=TEXT_COLOR,
                  fontsize=11, fontweight='bold')
ax_heat.set_xlabel("Zona de destino j", color=TEXT_COLOR, fontsize=10)
ax_heat.set_ylabel("Zona de origen i", color=TEXT_COLOR, fontsize=10)

# --- Subgráfico derecho: flujos totales salientes/entrantes por zona ---
ax_bar = axes[1]
ax_bar.set_facecolor(BG_COLOR)

x = np.arange(n)
ancho = 0.35
bars1 = ax_bar.bar(x - ancho/2, flujos_salientes, ancho,
                   color=COLOR_NODE1, alpha=0.85, label="Flujos salientes Σ T$_{ij}$")
bars2 = ax_bar.bar(x + ancho/2, flujos_entrantes, ancho,
                   color=COLOR_NODE3, alpha=0.85, label="Flujos entrantes Σ T$_{ji}$")

# Etiquetas de valor sobre las barras
for bar in bars1:
    ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2500,
                f"{bar.get_height():,.0f}", ha='center', va='bottom',
                color=TEXT_COLOR, fontsize=8.5)
for bar in bars2:
    ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2500,
                f"{bar.get_height():,.0f}", ha='center', va='bottom',
                color=TEXT_COLOR, fontsize=8.5)

ax_bar.set_xticks(x)
ax_bar.set_xticklabels(["Zona 1\n(P=10000)", "Zona 2\n(P=5000)", "Zona 3\n(P=20000)"],
                       color=TEXT_COLOR, fontsize=9)
ax_bar.set_ylabel("Flujo total (viajes)", color=TEXT_COLOR, fontsize=10)
ax_bar.tick_params(colors=TEXT_COLOR, which='both')
for spine in ax_bar.spines.values():
    spine.set_edgecolor(GRID_COLOR)
ax_bar.yaxis.set_tick_params(labelcolor=TEXT_COLOR)
ax_bar.grid(axis='y', color=GRID_COLOR, linewidth=0.5, alpha=0.6)
ax_bar.set_facecolor(BG_COLOR)
ax_bar.set_title("Flujos totales por zona\n(salientes = entrantes por simetría)",
                 color=TEXT_COLOR, fontsize=11, fontweight='bold')
leg2 = ax_bar.legend(facecolor="#132038", edgecolor=GRID_COLOR,
                     labelcolor=TEXT_COLOR, fontsize=9)

fig2.suptitle(
    "Modelo Gravitacional de Interacción Espacial — Stewart (c=2, 1948); raíces Carey/Zipf; entropía Wilson (1967)\n"
    "T$_{ij}$ = G · P$_i$ · P$_j$ / d$_{ij}^2$   |   G=1, c=2",
    color=TEXT_COLOR, fontsize=12, fontweight='bold', y=1.01
)

plt.tight_layout()
png2 = ASSETS_DIR / "sim_modelo_gravitacional_flujos_2.png"
fig2.savefig(png2, dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
plt.close(fig2)
print(f"Grafico 2 guardado en: {png2}")

# ── Preguntas y respuestas ─────────────────────────────────────────────────────
preguntas_resp = [
    {
        "q": "Con el modelo gravitacional T_ij = G*P_i*P_j/d_ij^2, G=1, dos zonas con P_i=10000 y P_j=5000 separadas por d_ij=50. Calcula el flujo T_ij. Formato: 'Respuesta final: <valor>'.",
        "valor_exacto": str(int(G * 10000 * 5000 / 50**2)),  # 20000
        "tipo": "forma_cerrada",
        "tolerancia": "igualdad exacta (20000)",
        "como_computar": "T=1*10000*5000/50^2=50,000,000/2500=20,000."
    },
    {
        "q": "Con T_ij = G*P_i*P_j/d_ij^c, G=1, c=2, P_i=10000, P_j=20000. Calcula el flujo a una distancia d_ij=40. Formato: 'Respuesta final: <valor>'.",
        "valor_exacto": str(int(G * 10000 * 20000 / 40**2)),  # 125000
        "tipo": "forma_cerrada",
        "tolerancia": "igualdad exacta (125000)",
        "como_computar": "T=1*10000*20000/40^2=200,000,000/1600=125,000."
    },
    {
        "q": "Calcula la matriz de flujos completa para 3 zonas: P=[10000,5000,20000] en posiciones (0,0),(30,0),(0,40), con G=1, c=2 y distancias euclidianas. Suma todos los flujos entre pares distintos (T_12+T_13+T_23). Reporta el total. Formato: 'Respuesta final: <valor>'.",
        "valor_exacto": f"{suma_pares:.4f}",
        "tipo": "emergente",
        "tolerancia": "±1% en torno a 220555.56",
        "como_computar": f"T_12={T[0,1]:.4f}, T_13={T[0,2]:.4f}, T_23={T[1,2]:.4f}; suma={suma_pares:.4f}"
    }
]

preguntas_json = {
    "teoria": "modelo_gravitacional_flujos",
    "nombre": "Modelo gravitacional de interaccion espacial (flujos de viaje/migracion)",
    "autor": "John Q. Stewart (analogia de cuadrado inverso); raices en Henry Carey (1858) y G. K. Zipf (1946); derivacion entropica de Alan Wilson (1967)",
    "anio": "1948/1967",
    "preguntas": preguntas_resp
}

preguntas_path = SIM_DIR / "preguntas_modelo_gravitacional_flujos.json"
with open(preguntas_path, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
print(f"Preguntas guardadas en: {preguntas_path}")

print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
print(f"T_12 = {T[0,1]:,.4f}")
print(f"T_13 = {T[0,2]:,.4f}")
print(f"T_23 = {T[1,2]:,.4f}")
print(f"Suma pares = {suma_pares:,.4f}")
print(f"c recuperado por regresion = {c_recuperado:.6f}")
print(f"Ratio duplicacion distancia = {ratio:.6f} (debe ser 0.25)")
print("Todas las validaciones: PASADAS")
