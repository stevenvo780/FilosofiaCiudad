"""
Simulacion: Sintaxis Espacial - Integracion de Grafos Viarios
Teoria: Hillier & Hanson (1984), "The Social Logic of Space"

Formulacion:
  - Grafo donde nodos = lineas axiales (calles) y aristas = intersecciones
  - Profundidad media: MD = (suma de distancias topologicas a todos los demas) / (n-1)
  - Asimetria relativa: RA = 2 * (MD - 1) / (n - 2)   en [0, 1]
  - Integracion: Integration = 1 / RA  (valores altos => nodo topologicamente central)

Experimento determinista (sin semilla aleatoria):
  Camino lineal 5 nodos: A-B-C-D-E
  Verificacion:
    C: profundidades {A:2,B:1,D:1,E:2}, suma=6, MD=1.5, RA=0.333, Integration=3.0
    A: profundidades {B:1,C:2,D:3,E:4}, suma=10, MD=2.5, RA=1.0, Integration=1.0
"""

import json
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# ─────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────
BASE = Path("/home/stev/Documentos/repos/FilosofiaNeurociencias/FilosofiaCiudad/03_Trabajos/Ponencia_Yuk_Hui")
SIM_DIR  = BASE / "simulaciones"
ASSET_DIR = BASE / "presentacion" / "assets" / "sim"
SIM_DIR.mkdir(parents=True, exist_ok=True)
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Funciones de calculo de sintaxis espacial
# ─────────────────────────────────────────────

def mean_depth(G: nx.Graph, node) -> float:
    """Profundidad media: promedio de distancias topologicas a todos los demas nodos."""
    lengths = nx.single_source_shortest_path_length(G, node)
    n = G.number_of_nodes()
    total = sum(d for v, d in lengths.items() if v != node)
    return total / (n - 1)


def relative_asymmetry(md: float, n: int) -> float:
    """Asimetria relativa RA = 2*(MD-1)/(n-2). Resultado en [0,1] para grafos conexos."""
    return 2.0 * (md - 1.0) / (n - 2)


def integration(ra: float) -> float:
    """Integracion = 1 / RA."""
    if ra == 0.0:
        return float("inf")
    return 1.0 / ra


def compute_integration_map(G: nx.Graph) -> dict:
    """Calcula MD, RA e integracion para todos los nodos del grafo."""
    n = G.number_of_nodes()
    result = {}
    for node in G.nodes():
        md = mean_depth(G, node)
        ra = relative_asymmetry(md, n)
        intg = integration(ra)
        result[node] = {"MD": round(md, 6), "RA": round(ra, 6), "Integration": round(intg, 6)}
    return result


# ─────────────────────────────────────────────
# EXPERIMENTO 1: Camino lineal de 5 nodos
# ─────────────────────────────────────────────

labels_5 = ["A", "B", "C", "D", "E"]
G5 = nx.path_graph(5)
G5 = nx.relabel_nodes(G5, {i: labels_5[i] for i in range(5)})

map5 = compute_integration_map(G5)

# Verificacion manual
print("=== Camino lineal A-B-C-D-E (5 nodos) ===")
for nodo in labels_5:
    d = map5[nodo]
    print(f"  {nodo}: MD={d['MD']:.4f}, RA={d['RA']:.4f}, Integration={d['Integration']:.4f}")

# Valores esperados
assert abs(map5["C"]["MD"] - 1.5)  < 0.01, f"MD_C esperado 1.5, obtenido {map5['C']['MD']}"
assert abs(map5["C"]["RA"] - 1/3)  < 0.01, f"RA_C esperado 0.333, obtenido {map5['C']['RA']}"
assert abs(map5["C"]["Integration"] - 3.0) < 0.01, f"Integracion_C esperado 3.0, obtenido {map5['C']['Integration']}"
assert abs(map5["A"]["MD"] - 2.5)  < 0.01, f"MD_A esperado 2.5, obtenido {map5['A']['MD']}"
assert abs(map5["A"]["RA"] - 1.0)  < 0.01, f"RA_A esperado 1.0, obtenido {map5['A']['RA']}"
assert abs(map5["A"]["Integration"] - 1.0) < 0.01, f"Integracion_A esperado 1.0, obtenido {map5['A']['Integration']}"
print("  [OK] Verificacion numerica superada.")

# ─────────────────────────────────────────────
# EXPERIMENTO 2: Rejilla viaria 5x5
# ─────────────────────────────────────────────

G_grid = nx.grid_2d_graph(5, 5)   # nodos = tuplas (fila, columna) 0-indexed
map_grid = compute_integration_map(G_grid)

print("\n=== Rejilla viaria 5x5 ===")
central = (2, 2)
corner  = (0, 0)
print(f"  Nodo central {central}: MD={map_grid[central]['MD']:.4f}, "
      f"RA={map_grid[central]['RA']:.6f}, "
      f"Integration={map_grid[central]['Integration']:.4f}")
print(f"  Nodo esquina {corner}:   MD={map_grid[corner]['MD']:.4f}, "
      f"RA={map_grid[corner]['RA']:.6f}, "
      f"Integration={map_grid[corner]['Integration']:.4f}")

# ─────────────────────────────────────────────
# FIGURA 1: Camino de 5 nodos coloreado por integracion
# ─────────────────────────────────────────────

intg_values_5 = [map5[n]["Integration"] for n in labels_5]

fig1, ax1 = plt.subplots(figsize=(10, 4))
fig1.patch.set_facecolor("#0e1a2b")
ax1.set_facecolor("#0e1a2b")

# Layout: nodos en linea horizontal
pos5 = {n: (i, 0) for i, n in enumerate(labels_5)}

# Colormap tipo mapa de calor: azul (baja) -> rojo (alta integracion)
cmap = plt.cm.RdYlBu_r
norm = mcolors.Normalize(vmin=min(intg_values_5), vmax=max(intg_values_5))
node_colors = [cmap(norm(v)) for v in intg_values_5]

# Aristas
nx.draw_networkx_edges(G5, pos5, ax=ax1,
                       edge_color="#e0a458", width=2.5, alpha=0.8)

# Nodos
nx.draw_networkx_nodes(G5, pos5, ax=ax1,
                       node_color=node_colors, node_size=1200,
                       edgecolors="#e8e6e1", linewidths=1.5)

# Etiquetas: nombre del nodo
nx.draw_networkx_labels(G5, pos5, ax=ax1,
                        labels={n: n for n in labels_5},
                        font_size=14, font_color="#0e1a2b", font_weight="bold")

# Etiquetas: valor de integracion debajo de cada nodo
for nodo, (x, y) in pos5.items():
    val = map5[nodo]["Integration"]
    ax1.text(x, y - 0.18, f"Integ={val:.2f}",
             ha="center", va="top", fontsize=10,
             color="#e8e6e1", fontstyle="italic")

# Barra de color
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig1.colorbar(sm, ax=ax1, orientation="vertical", fraction=0.04, pad=0.04)
cbar.set_label("Integración (1/RA)", color="#e8e6e1", fontsize=11)
cbar.ax.yaxis.set_tick_params(color="#e8e6e1")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#e8e6e1")

ax1.set_title(
    "Sintaxis Espacial – Integración en Camino Lineal (5 nodos)\n"
    "Hillier & Hanson (1984) · Rojo = alta integración, Azul = baja",
    color="#e8e6e1", fontsize=13, pad=14
)
# Ampliar el rango vertical para incluir las etiquetas 'Integ=' situadas en y-0.18,
# evitando el UserWarning de tight_layout (margenes insuficientes).
ax1.set_ylim(-0.45, 0.45)
ax1.axis("off")

# Margenes explicitos en vez de tight_layout() para no emitir el UserWarning
# 'Tight layout not applied' provocado por las etiquetas fuera del eje.
fig1.subplots_adjust(left=0.04, right=0.96, top=0.82, bottom=0.08)
out1 = ASSET_DIR / "sim_sintaxis_espacial_integracion_1.png"
fig1.savefig(out1, dpi=150, bbox_inches="tight", facecolor=fig1.get_facecolor())
plt.close(fig1)
print(f"\n[PNG 1 guardado] {out1}")

# ─────────────────────────────────────────────
# FIGURA 2: Rejilla 5x5 - Mapa axial de integracion
# ─────────────────────────────────────────────

intg_grid = {node: map_grid[node]["Integration"] for node in G_grid.nodes()}
intg_array = np.array([intg_grid[n] for n in G_grid.nodes()])

fig2, ax2 = plt.subplots(figsize=(8, 8))
fig2.patch.set_facecolor("#0e1a2b")
ax2.set_facecolor("#0e1a2b")

# Layout de la rejilla
pos_grid = {(r, c): (c, -r) for r, c in G_grid.nodes()}   # x=col, y=-fila (origen arriba-izquierda)
node_intg_list = [intg_grid[n] for n in G_grid.nodes()]

cmap2 = plt.cm.RdYlBu_r
norm2 = mcolors.Normalize(vmin=min(node_intg_list), vmax=max(node_intg_list))
node_colors2 = [cmap2(norm2(v)) for v in node_intg_list]

# Aristas
nx.draw_networkx_edges(G_grid, pos_grid, ax=ax2,
                       edge_color="#4a6080", width=1.8, alpha=0.6)

# Nodos
nx.draw_networkx_nodes(G_grid, pos_grid, ax=ax2,
                       node_color=node_colors2, node_size=900,
                       edgecolors="#e8e6e1", linewidths=1.0)

# Etiquetas con valor de integracion
labels_grid = {n: f"{intg_grid[n]:.1f}" for n in G_grid.nodes()}
nx.draw_networkx_labels(G_grid, pos_grid, ax=ax2,
                        labels=labels_grid,
                        font_size=8, font_color="#0e1a2b", font_weight="bold")

# Barra de color
sm2 = plt.cm.ScalarMappable(cmap=cmap2, norm=norm2)
sm2.set_array([])
cbar2 = fig2.colorbar(sm2, ax=ax2, orientation="vertical", fraction=0.04, pad=0.04)
cbar2.set_label("Integración (1/RA)", color="#e8e6e1", fontsize=11)
cbar2.ax.yaxis.set_tick_params(color="#e8e6e1")
plt.setp(cbar2.ax.yaxis.get_ticklabels(), color="#e8e6e1")

ax2.set_title(
    "Sintaxis Espacial – Mapa de Integración en Rejilla Viaria 5×5\n"
    "Hillier & Hanson (1984) · Rojo = alta integración (centro), Azul = baja (esquinas)",
    color="#e8e6e1", fontsize=12, pad=14
)
ax2.axis("off")

plt.tight_layout()
out2 = ASSET_DIR / "sim_sintaxis_espacial_integracion_2.png"
fig2.savefig(out2, dpi=150, bbox_inches="tight", facecolor=fig2.get_facecolor())
plt.close(fig2)
print(f"[PNG 2 guardado] {out2}")

# ─────────────────────────────────────────────
# Guardar datos crudos en JSON
# ─────────────────────────────────────────────

datos = {
    "teoria": "sintaxis_espacial_integracion",
    "autor": "Bill Hillier y Julienne Hanson",
    "anio": "1984",
    "experimento_1_camino_5_nodos": {
        "descripcion": "Camino lineal A-B-C-D-E, 5 nodos",
        "nodos": map5
    },
    "experimento_2_rejilla_5x5": {
        "descripcion": "Rejilla viaria 5x5, 25 nodos, conexiones ortogonales",
        "nodos": {str(k): v for k, v in map_grid.items()}
    },
    "validacion": {
        "Integration_C_esperado": 3.0,
        "Integration_C_obtenido": map5["C"]["Integration"],
        "Integration_A_esperado": 1.0,
        "Integration_A_obtenido": map5["A"]["Integration"],
        "RA_en_rango_0_1": all(0.0 <= map5[n]["RA"] <= 1.0 for n in labels_5),
        "MD_coincide_formula": True
    }
}

datos_path = SIM_DIR / "datos_sintaxis_espacial_integracion.json"
with open(datos_path, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)
print(f"[JSON guardado] {datos_path}")

# ─────────────────────────────────────────────
# Preguntas con valores exactos
# ─────────────────────────────────────────────

int_central_grid = map_grid[(2, 2)]["Integration"]

preguntas_json = {
    "teoria": "sintaxis_espacial_integracion",
    "nombre": "Sintaxis espacial: integracion de grafos viarios (Hillier-Hanson)",
    "autor": "Bill Hillier y Julienne Hanson",
    "anio": "1984",
    "preguntas": [
        {
            "q": "En un grafo viario en linea de 5 nodos A-B-C-D-E (camino simple), las profundidades topologicas del nodo central C a los demas son: A=2, B=1, D=1, E=2. Calcula la profundidad media MD = (suma de profundidades)/(n-1) para C, con n=5. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(map5["C"]["MD"]),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.01 (1.5)",
            "como_computar": "MD=(2+1+1+2)/(5-1)=6/4=1.5."
        },
        {
            "q": "Para el nodo extremo A del camino de 5 nodos (profundidades 1,2,3,4, MD=2.5), calcula la asimetria relativa RA = 2*(MD-1)/(n-2) con n=5, y luego la integracion = 1/RA. Reporta la integracion. Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(map5["A"]["Integration"]),
            "tipo": "forma_cerrada",
            "tolerancia": "±0.01 (1.0)",
            "como_computar": "RA=2*(2.5-1)/(5-2)=2*1.5/3=1.0; Integracion=1/1.0=1.0."
        },
        {
            "q": "Construye el grafo de una rejilla viaria 5x5 (25 nodos, conexiones a vecinos ortogonales), calcula la profundidad media de cada nodo via caminos minimos (BFS) y la integracion=1/RA con RA=2*(MD-1)/(n-2), n=25. Reporta la integracion del nodo central (fila 2, columna 2, indexado desde 0). Formato: 'Respuesta final: <valor>'.",
            "valor_exacto": str(round(int_central_grid, 4)),
            "tipo": "emergente",
            "tolerancia": f"±1.0 en torno a {round(int_central_grid, 2)}",
            "como_computar": f"BFS desde (2,2) en rejilla 5x5: MD={map_grid[(2,2)]['MD']}, RA={map_grid[(2,2)]['RA']}, Integration={int_central_grid}."
        }
    ]
}

preguntas_path = SIM_DIR / "preguntas_sintaxis_espacial_integracion.json"
with open(preguntas_path, "w", encoding="utf-8") as f:
    json.dump(preguntas_json, f, ensure_ascii=False, indent=2)
print(f"[Preguntas JSON guardado] {preguntas_path}")

# ─────────────────────────────────────────────
# Resumen final
# ─────────────────────────────────────────────
print("\n=== RESUMEN FINAL ===")
print(f"  Integration(C) = {map5['C']['Integration']:.4f}  [esperado 3.0]")
print(f"  Integration(A) = {map5['A']['Integration']:.4f}  [esperado 1.0]")
print(f"  Integration(rejilla central (2,2)) = {int_central_grid:.4f}  [esperado ~7.67]")
print(f"  RA en [0,1] para todos los nodos del camino: {all(0<=map5[n]['RA']<=1 for n in labels_5)}")
print("=== FIN ===")
