#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import random
from pathlib import Path


WIDTH = 1200
HEIGHT = 900
CELL = 24
SEED = 23

ROOT = Path("/workspace")
OUT_DIR = ROOT / "Material"
SVG_PATH = OUT_DIR / "distribucion_urbana_physarum.svg"
JSON_PATH = OUT_DIR / "distribucion_urbana_physarum.json"

COLORS = {
    "core": "#cf4d34",
    "mixed": "#f08a4b",
    "residential": "#f6d68a",
    "productive": "#7aa6c2",
    "green": "#bfd8a6",
    "road": "#2f3640",
    "transit": "#0e7490",
    "water": "#9fd3f4",
    "background": "#f8f6ef",
    "label": "#1f2933",
}


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nx = ax + t * dx
    ny = ay + t * dy
    return math.hypot(px - nx, py - ny)


def prim_mst(nodes: list[dict[str, object]]) -> list[tuple[int, int]]:
    if not nodes:
        return []
    connected = {0}
    edges: list[tuple[int, int]] = []
    while len(connected) < len(nodes):
        best = None
        best_pair = None
        for i in connected:
            for j in range(len(nodes)):
                if j in connected:
                    continue
                a = nodes[i]["pos"]
                b = nodes[j]["pos"]
                value = dist(a, b)
                if best is None or value < best:
                    best = value
                    best_pair = (i, j)
        if best_pair is None:
            break
        edges.append(best_pair)
        connected.add(best_pair[1])
    return edges


def svg_line(a: tuple[float, float], b: tuple[float, float], color: str, width: float, opacity: float = 1.0) -> str:
    return (
        f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" '
        f'x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
        f'stroke="{color}" stroke-width="{width:.1f}" '
        f'stroke-linecap="round" opacity="{opacity:.2f}" />'
    )


def svg_circle(center: tuple[float, float], radius: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    extra = ""
    if stroke:
        extra = f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{center[0]:.1f}" cy="{center[1]:.1f}" r="{radius:.1f}" fill="{fill}"{extra} />'


def svg_rect(x: float, y: float, w: float, h: float, fill: str, opacity: float = 1.0) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" opacity="{opacity:.2f}" />'


def svg_text(x: float, y: float, text: str, size: int, weight: int = 400, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
        f'font-family="Georgia, serif" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{COLORS["label"]}">{text}</text>'
    )


def main() -> None:
    random.seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    centers = [
        {"name": "CBD", "pos": (560.0, 450.0), "weight": 1.00},
        {"name": "Nodo Norte", "pos": (560.0, 250.0), "weight": 0.70},
        {"name": "Nodo Este", "pos": (820.0, 420.0), "weight": 0.72},
        {"name": "Nodo Oeste", "pos": (320.0, 500.0), "weight": 0.66},
        {"name": "Nodo Sur", "pos": (610.0, 680.0), "weight": 0.62},
        {"name": "Logistica", "pos": (930.0, 690.0), "weight": 0.52},
    ]

    spine_a = (140.0, 470.0)
    spine_b = (1060.0, 410.0)
    freight_a = (770.0, 780.0)
    freight_b = (1090.0, 640.0)
    river_points = [
        (70.0, 140.0),
        (180.0, 210.0),
        (280.0, 260.0),
        (370.0, 335.0),
        (520.0, 380.0),
        (700.0, 395.0),
        (880.0, 370.0),
        (1070.0, 300.0),
    ]

    grid: list[dict[str, object]] = []
    counts = {"core": 0, "mixed": 0, "residential": 0, "productive": 0, "green": 0}

    for y in range(80, HEIGHT - 80, CELL):
        for x in range(80, WIDTH - 80, CELL):
            cx = x + CELL / 2
            cy = y + CELL / 2

            attraction = 0.0
            nearest_cbd = dist((cx, cy), centers[0]["pos"])
            nearest_any = min(dist((cx, cy), c["pos"]) for c in centers)

            for center in centers:
                d = dist((cx, cy), center["pos"])
                attraction += center["weight"] / ((d / 130.0) ** 2 + 1.0)

            transit_bonus = max(0.0, 1.0 - point_segment_distance(cx, cy, *spine_a, *spine_b) / 190.0) * 0.48
            freight_bonus = max(0.0, 1.0 - point_segment_distance(cx, cy, *freight_a, *freight_b) / 130.0) * 0.38

            water_penalty = 0.0
            for a, b in zip(river_points, river_points[1:]):
                river_d = point_segment_distance(cx, cy, *a, *b)
                water_penalty = max(water_penalty, max(0.0, 1.0 - river_d / 70.0))

            edge_penalty = ((abs(cx - WIDTH / 2) / (WIDTH / 2)) + (abs(cy - HEIGHT / 2) / (HEIGHT / 2))) * 0.12
            noise = random.uniform(-0.04, 0.04)
            score = attraction + transit_bonus + freight_bonus * 0.65 - water_penalty * 0.38 - edge_penalty + noise

            if water_penalty > 0.58 and nearest_cbd > 180:
                zone = "green"
            elif nearest_cbd < 120 and score > 0.80:
                zone = "core"
            elif score > 0.63 or nearest_any < 95:
                zone = "mixed"
            elif freight_bonus > 0.18 and cx > 700:
                zone = "productive"
            elif score > 0.30:
                zone = "residential"
            else:
                zone = "green"

            counts[zone] += 1
            grid.append({"x": x, "y": y, "zone": zone})

    mst_edges = prim_mst(centers)
    ring_edges = [(1, 3), (3, 4), (4, 5), (5, 2), (2, 1)]

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">'
    )
    parts.append(svg_rect(0, 0, WIDTH, HEIGHT, COLORS["background"]))
    parts.append('<defs><filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.18"/></filter></defs>')

    for a, b in zip(river_points, river_points[1:]):
        parts.append(svg_line(a, b, COLORS["water"], 28, 0.9))
        parts.append(svg_line(a, b, "#dff2ff", 14, 0.8))

    for cell in grid:
        parts.append(svg_rect(cell["x"], cell["y"], CELL - 1, CELL - 1, COLORS[cell["zone"]], 0.92))

    parts.append(svg_line(spine_a, spine_b, COLORS["transit"], 16, 0.92))
    parts.append(svg_line(spine_a, spine_b, "#d8f5fb", 6, 0.8))
    parts.append(svg_line(freight_a, freight_b, COLORS["road"], 10, 0.45))

    for i, j in mst_edges:
        a = centers[i]["pos"]
        b = centers[j]["pos"]
        parts.append(svg_line(a, b, COLORS["road"], 9, 0.88))

    for i, j in ring_edges:
        a = centers[i]["pos"]
        b = centers[j]["pos"]
        parts.append(svg_line(a, b, COLORS["road"], 4, 0.44))

    for center in centers:
        pos = center["pos"]
        radius = 17 if center["name"] == "CBD" else 12
        parts.append(svg_circle(pos, radius + 6, "#ffffffcc"))
        parts.append(svg_circle(pos, radius, COLORS["road"], "#ffffff", 2))
        parts.append(svg_text(pos[0], pos[1] - 22, center["name"], 20 if center["name"] == "CBD" else 16, 600, "middle"))

    legend_y = 120
    parts.append('<g filter="url(#shadow)">')
    parts.append('<rect x="865" y="80" width="270" height="285" rx="20" fill="#fffdf8" opacity="0.95" />')
    parts.append('</g>')
    parts.append(svg_text(895, 115, "Distribucion Urbana Bioinspirada", 24, 700))
    parts.append(svg_text(895, 145, "Modelo simple tipo Physarum", 16, 400))

    legend_items = [
        ("core", "Centro de alta densidad"),
        ("mixed", "Uso mixto"),
        ("residential", "Residencial"),
        ("productive", "Productivo / logistico"),
        ("green", "Corredor verde"),
    ]
    yy = legend_y + 60
    for key, label in legend_items:
        parts.append(svg_rect(895, yy - 18, 26, 26, COLORS[key]))
        parts.append(svg_text(935, yy + 2, label, 16, 400))
        yy += 38

    parts.append(svg_line((895, yy + 10), (930, yy + 10), COLORS["road"], 7, 0.9))
    parts.append(svg_text(940, yy + 16, "Red vial minima", 16, 400))
    yy += 38
    parts.append(svg_line((895, yy + 10), (930, yy + 10), COLORS["transit"], 10, 0.9))
    parts.append(svg_text(940, yy + 16, "Eje de transporte", 16, 400))

    parts.append(svg_text(80, 62, "Mapa demo: algoritmo simple para distribucion urbana", 28, 700))
    parts.append(svg_text(80, 90, "Criterios: accesibilidad, red minima, corredor verde y densificacion por nodos", 17, 400))
    parts.append(svg_text(80, 845, "Semilla fija: 23 | Salida reproducible | No usa IA generativa ni optimizacion pesada", 15, 400))

    parts.append('</svg>')
    SVG_PATH.write_text("\n".join(parts), encoding="utf-8")

    metadata = {
        "seed": SEED,
        "canvas": {"width": WIDTH, "height": HEIGHT, "cell": CELL},
        "theory": "Modelo bioinspirado en Physarum polycephalum para conectividad eficiente y zonificacion por campos de atraccion.",
        "centers": centers,
        "network": {
            "mst_edges": mst_edges,
            "ring_edges": ring_edges,
            "transit_spine": [spine_a, spine_b],
            "freight_axis": [freight_a, freight_b],
        },
        "zone_counts": counts,
        "outputs": {"svg": str(SVG_PATH)},
    }
    JSON_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"SVG generado en: {SVG_PATH}")
    print(f"JSON generado en: {JSON_PATH}")


if __name__ == "__main__":
    main()
