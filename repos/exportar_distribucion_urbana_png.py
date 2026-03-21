#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import struct
import zlib
from collections import Counter
from pathlib import Path

WIDTH = 1600
HEIGHT = 1100
CELL = 8
SEED_NOTE = 23

ROOT = Path('/workspace')
OUT_DIR = ROOT / 'Material'
PNG_PATH = OUT_DIR / 'distribucion_urbana_physarum.png'
JSON_PATH = OUT_DIR / 'distribucion_urbana_physarum.json'

COLORS_HEX = {
    'background': '#f3efe6',
    'water': '#76b7e5',
    'floodplain': '#d9efd7',
    'park': '#9fc98b',
    'cbd': '#af3d2e',
    'mixed': '#d06f3d',
    'res_high': '#efb366',
    'res_low': '#f3ddb0',
    'industrial': '#7b8fa6',
    'arterial': '#373d45',
    'ring': '#5f6770',
    'transit': '#0d7288',
    'rail': '#6b7280',
    'label': '#1f2933',
    'panel': '#fffdf8',
    'white': '#ffffff',
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


RGB = {k: hex_to_rgb(v) for k, v in COLORS_HEX.items()}

FONT = {
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '11110', '10001', '10001', '10001', '11110'],
    'C': ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '11110', '10000', '10000', '10000', '11111'],
    'F': ['11111', '10000', '11110', '10000', '10000', '10000', '10000'],
    'G': ['01111', '10000', '10000', '10111', '10001', '10001', '01110'],
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
    'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
    'K': ['10001', '10010', '11100', '10010', '10001', '10001', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'M': ['10001', '11011', '10101', '10001', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
    'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    ' ': ['000', '000', '000', '000', '000', '000', '000'],
    '-': ['000', '000', '000', '111', '000', '000', '000'],
    '/': ['00001', '00010', '00100', '01000', '10000', '00000', '00000'],
    ':': ['0', '1', '0', '0', '1', '0', '0'],
}

ZONE_COLORS = {
    'cbd': RGB['cbd'],
    'mixed': RGB['mixed'],
    'res_high': RGB['res_high'],
    'res_low': RGB['res_low'],
    'industrial': RGB['industrial'],
    'park': RGB['park'],
    'floodplain': RGB['floodplain'],
    'water': RGB['water'],
}


class Canvas:
    def __init__(self, width: int, height: int, bg: tuple[int, int, int]):
        self.width = width
        self.height = height
        self.pixels = bytearray(bg * (width * height))

    def blend_pixel(self, x: int, y: int, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return
        idx = (y * self.width + x) * 3
        inv = 1.0 - alpha
        self.pixels[idx] = int(self.pixels[idx] * inv + color[0] * alpha)
        self.pixels[idx + 1] = int(self.pixels[idx + 1] * inv + color[1] * alpha)
        self.pixels[idx + 2] = int(self.pixels[idx + 2] * inv + color[2] * alpha)

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int], alpha: float = 1.0) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            row = yy * self.width * 3
            for xx in range(x0, x1):
                idx = row + xx * 3
                inv = 1.0 - alpha
                self.pixels[idx] = int(self.pixels[idx] * inv + color[0] * alpha)
                self.pixels[idx + 1] = int(self.pixels[idx + 1] * inv + color[1] * alpha)
                self.pixels[idx + 2] = int(self.pixels[idx + 2] * inv + color[2] * alpha)

    def line(self, a: tuple[float, float], b: tuple[float, float], color: tuple[int, int, int], width: int, alpha: float = 1.0) -> None:
        ax, ay = a
        bx, by = b
        half = width / 2.0
        min_x = max(0, int(min(ax, bx) - half - 2))
        max_x = min(self.width - 1, int(max(ax, bx) + half + 2))
        min_y = max(0, int(min(ay, by) - half - 2))
        max_y = min(self.height - 1, int(max(ay, by) + half + 2))
        dx = bx - ax
        dy = by - ay
        denom = dx * dx + dy * dy
        if denom == 0:
            self.circle((ax, ay), half, color, alpha)
            return
        for yy in range(min_y, max_y + 1):
            for xx in range(min_x, max_x + 1):
                t = ((xx - ax) * dx + (yy - ay) * dy) / denom
                t = max(0.0, min(1.0, t))
                nx = ax + t * dx
                ny = ay + t * dy
                if math.hypot(xx - nx, yy - ny) <= half:
                    self.blend_pixel(xx, yy, color, alpha)

    def polyline(self, points: list[tuple[float, float]], color: tuple[int, int, int], width: int, alpha: float = 1.0) -> None:
        for a, b in zip(points, points[1:]):
            self.line(a, b, color, width, alpha)

    def circle(self, center: tuple[float, float], radius: float, color: tuple[int, int, int], alpha: float = 1.0, stroke: tuple[int, int, int] | None = None, stroke_width: int = 0) -> None:
        cx, cy = center
        min_x = max(0, int(cx - radius - stroke_width - 2))
        max_x = min(self.width - 1, int(cx + radius + stroke_width + 2))
        min_y = max(0, int(cy - radius - stroke_width - 2))
        max_y = min(self.height - 1, int(cy + radius + stroke_width + 2))
        inner = max(0.0, radius - stroke_width)
        outer = radius
        for yy in range(min_y, max_y + 1):
            for xx in range(min_x, max_x + 1):
                d = math.hypot(xx - cx, yy - cy)
                if stroke is not None and inner <= d <= outer:
                    self.blend_pixel(xx, yy, stroke, alpha)
                elif d <= inner:
                    self.blend_pixel(xx, yy, color, alpha)

    def save_png(self, path: Path) -> None:
        def chunk(tag: bytes, data: bytes) -> bytes:
            crc = zlib.crc32(tag + data) & 0xffffffff
            return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', crc)

        raw = bytearray()
        stride = self.width * 3
        for y in range(self.height):
            raw.append(0)
            start = y * stride
            raw.extend(self.pixels[start:start + stride])

        png = bytearray(b'\x89PNG\r\n\x1a\n')
        png.extend(chunk(b'IHDR', struct.pack('!IIBBBBB', self.width, self.height, 8, 2, 0, 0, 0)))
        png.extend(chunk(b'IDAT', zlib.compress(bytes(raw), 9)))
        png.extend(chunk(b'IEND', b''))
        path.write_bytes(png)


def draw_text(canvas: Canvas, x: int, y: int, text: str, color: tuple[int, int, int], scale: int = 2) -> None:
    cursor = x
    for ch in text.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            cursor += 4 * scale
            continue
        width = len(glyph[0])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '1':
                    canvas.rect(cursor + gx * scale, y + gy * scale, scale, scale, color)
        cursor += (width + 1) * scale


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
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
    connected = {0}
    edges: list[tuple[int, int]] = []
    while len(connected) < len(nodes):
        best = None
        best_pair = None
        for i in connected:
            for j in range(len(nodes)):
                if j in connected:
                    continue
                value = dist(nodes[i]['pos'], nodes[j]['pos'])
                if best is None or value < best:
                    best = value
                    best_pair = (i, j)
        if best_pair is None:
            break
        edges.append(best_pair)
        connected.add(best_pair[1])
    return edges


def terrain_height(x: float, y: float) -> float:
    return (
        0.38 * math.sin(x * 0.0082)
        + 0.19 * math.cos(y * 0.0104)
        + 0.14 * math.sin((x + y) * 0.0048)
        + 0.10 * math.cos((x - 1.8 * y) * 0.0035)
    )


def terrain_slope(x: float, y: float) -> float:
    dx = (
        0.38 * 0.0082 * math.cos(x * 0.0082)
        + 0.14 * 0.0048 * math.cos((x + y) * 0.0048)
        - 0.10 * 0.0035 * math.sin((x - 1.8 * y) * 0.0035)
    )
    dy = (
        -0.19 * 0.0104 * math.sin(y * 0.0104)
        + 0.14 * 0.0048 * math.cos((x + y) * 0.0048)
        + 0.10 * 1.8 * 0.0035 * math.sin((x - 1.8 * y) * 0.0035)
    )
    return math.hypot(dx, dy)


def river_y(x: float) -> float:
    return 245 + 58 * math.sin(x * 0.0068) + 42 * math.sin(x * 0.015)


def build_zone_map() -> tuple[list[list[str]], dict[str, int], list[dict[str, object]], list[tuple[float, float]], list[tuple[int, int]], list[tuple[int, int]]]:
    cols = WIDTH // CELL
    rows = HEIGHT // CELL

    centers = [
        {'name': 'CBD', 'pos': (760.0, 560.0), 'weight': 1.00},
        {'name': 'NORTE', 'pos': (760.0, 330.0), 'weight': 0.70},
        {'name': 'OESTE', 'pos': (500.0, 610.0), 'weight': 0.60},
        {'name': 'ESTE', 'pos': (1080.0, 560.0), 'weight': 0.66},
        {'name': 'SUR', 'pos': (820.0, 820.0), 'weight': 0.58},
        {'name': 'LOGISTICA', 'pos': (1280.0, 835.0), 'weight': 0.54},
    ]

    river_points = [(x, river_y(x)) for x in range(0, WIDTH + 40, 40)]
    transit_spine = [(120.0, 590.0), (1480.0, 520.0)]
    north_south = [(820.0, 220.0), (860.0, 980.0)]
    freight_axis = [(930.0, 980.0), (1490.0, 770.0)]

    zones: list[list[str]] = []
    for gy in range(rows):
        row: list[str] = []
        for gx in range(cols):
            x = gx * CELL + CELL / 2
            y = gy * CELL + CELL / 2

            h = terrain_height(x, y)
            slope = terrain_slope(x, y)
            ry = river_y(x)
            river_dist = abs(y - ry)
            flood_dist = abs(y - (ry + 25))
            flood_risk = max(0.0, 1.0 - flood_dist / 72.0)
            water_band = river_dist < 16

            centrality = 0.0
            for center in centers:
                d = dist((x, y), center['pos'])
                centrality += center['weight'] / ((d / 175.0) ** 2 + 1.0)

            east_west_bonus = max(0.0, 1.0 - point_segment_distance(x, y, *transit_spine[0], *transit_spine[1]) / 165.0) * 0.45
            north_south_bonus = max(0.0, 1.0 - point_segment_distance(x, y, *north_south[0], *north_south[1]) / 150.0) * 0.28
            freight_bonus = max(0.0, 1.0 - point_segment_distance(x, y, *freight_axis[0], *freight_axis[1]) / 125.0) * 0.52
            river_amenity = max(0.0, 1.0 - abs(river_dist - 70.0) / 120.0) * 0.12
            edge_penalty = ((abs(x - WIDTH / 2) / (WIDTH / 2)) + (abs(y - HEIGHT / 2) / (HEIGHT / 2))) * 0.10
            hill_penalty = max(0.0, slope - 0.0048) * 42.0
            south_plateau = max(0.0, (y - 760.0) / 260.0) * 0.08

            urban_score = centrality + east_west_bonus + north_south_bonus + river_amenity - flood_risk * 0.60 - hill_penalty - edge_penalty - south_plateau

            if water_band:
                zone = 'water'
            elif flood_risk > 0.62 or slope > 0.0105:
                zone = 'floodplain' if flood_risk > 0.62 else 'park'
            elif dist((x, y), centers[0]['pos']) < 120 and urban_score > 0.93:
                zone = 'cbd'
            elif freight_bonus > 0.28 and x > 940 and y > 610 and flood_risk < 0.25:
                zone = 'industrial'
            elif urban_score > 0.73 or min(dist((x, y), c['pos']) for c in centers) < 88:
                zone = 'mixed'
            elif urban_score > 0.49:
                zone = 'res_high'
            elif urban_score > 0.25:
                zone = 'res_low'
            else:
                zone = 'park'

            if zone in {'res_high', 'res_low'} and h > 0.45 and y < 260:
                zone = 'park'
            row.append(zone)
        zones.append(row)

    immutable = {'water', 'floodplain'}
    buildable = {'cbd', 'mixed', 'res_high', 'res_low', 'industrial', 'park'}
    for _ in range(3):
        refined = [r[:] for r in zones]
        for y in range(1, rows - 1):
            for x in range(1, cols - 1):
                current = zones[y][x]
                if current in immutable:
                    continue
                neighbors = []
                for yy in range(y - 1, y + 2):
                    for xx in range(x - 1, x + 2):
                        if xx == x and yy == y:
                            continue
                        neighbors.append(zones[yy][xx])
                counts = Counter(n for n in neighbors if n in buildable)
                if not counts:
                    continue
                dominant, amount = counts.most_common(1)[0]
                if amount >= 5 and dominant != current:
                    refined[y][x] = dominant
        zones = refined

    counts: dict[str, int] = Counter()
    for row in zones:
        counts.update(row)

    mst_edges = prim_mst(centers)
    ring_edges = [(1, 2), (2, 4), (4, 5), (5, 3), (3, 1)]
    return zones, dict(counts), centers, river_points, mst_edges, ring_edges


def render() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zones, counts, centers, river_points, mst_edges, ring_edges = build_zone_map()
    canvas = Canvas(WIDTH, HEIGHT, RGB['background'])

    for gy, row in enumerate(zones):
        for gx, zone in enumerate(row):
            canvas.rect(gx * CELL, gy * CELL, CELL, CELL, ZONE_COLORS[zone], 0.96)

    canvas.polyline(river_points, RGB['water'], 24, 0.95)
    canvas.polyline(river_points, RGB['white'], 8, 0.16)

    transit_spine = [(120.0, 590.0), (1480.0, 520.0)]
    north_south = [(820.0, 220.0), (860.0, 980.0)]
    freight_axis = [(930.0, 980.0), (1490.0, 770.0)]
    bridges = [420, 760, 1120]
    for x in bridges:
        y = river_y(x)
        canvas.line((x - 24, y - 42), (x + 24, y + 42), RGB['arterial'], 8, 0.95)

    canvas.line(transit_spine[0], transit_spine[1], RGB['transit'], 18, 0.90)
    canvas.line(north_south[0], north_south[1], RGB['transit'], 14, 0.82)
    canvas.line(freight_axis[0], freight_axis[1], RGB['rail'], 12, 0.74)

    for i, j in mst_edges:
        canvas.line(centers[i]['pos'], centers[j]['pos'], RGB['arterial'], 11, 0.88)
    for i, j in ring_edges:
        canvas.line(centers[i]['pos'], centers[j]['pos'], RGB['ring'], 6, 0.58)

    for center in centers:
        radius = 18 if center['name'] == 'CBD' else 12
        canvas.circle(center['pos'], radius + 7, RGB['white'], 0.72)
        canvas.circle(center['pos'], radius, RGB['arterial'], 1.0, stroke=RGB['white'], stroke_width=2)

    canvas.rect(1110, 90, 400, 250, RGB['panel'], 0.94)
    draw_text(canvas, 1135, 118, 'DISTRIBUCION URBANA', RGB['label'], 3)
    draw_text(canvas, 1135, 155, 'MODELO BIOINSPIRADO', RGB['label'], 2)
    draw_text(canvas, 1135, 188, 'PHYSARUM / CENTRALIDADES', RGB['label'], 2)

    legend_items = [
        ('cbd', 'CBD'),
        ('mixed', 'MIXTO'),
        ('res_high', 'RESID ALTA'),
        ('res_low', 'RESID BAJA'),
        ('industrial', 'INDUSTRIA'),
        ('park', 'PARQUE'),
        ('floodplain', 'BORDE HIDRICO'),
    ]
    yy = 228
    for key, label in legend_items:
        canvas.rect(1138, yy, 22, 22, RGB[key])
        draw_text(canvas, 1175, yy + 4, label, RGB['label'], 2)
        yy += 28

    draw_text(canvas, 80, 74, 'MAPA URBANO MULTICRITERIO', RGB['label'], 3)
    draw_text(canvas, 80, 106, 'SALIDA PNG ACTUALIZADA', RGB['label'], 2)
    draw_text(canvas, 705, 525, 'CBD', RGB['white'], 2)
    draw_text(canvas, 705, 290, 'NORTE', RGB['label'], 2)
    draw_text(canvas, 455, 575, 'OESTE', RGB['label'], 2)
    draw_text(canvas, 1040, 525, 'ESTE', RGB['label'], 2)
    draw_text(canvas, 785, 785, 'SUR', RGB['label'], 2)
    draw_text(canvas, 1195, 800, 'LOGISTICA', RGB['label'], 2)

    canvas.save_png(PNG_PATH)

    metadata = {
        'seed_note': SEED_NOTE,
        'canvas': {'width': WIDTH, 'height': HEIGHT, 'cell': CELL},
        'theory': 'Modelo multicriterio bioinspirado: centralidades, conectividad minima, hidrologia, pendiente y corredor logistico.',
        'zone_counts': counts,
        'output_png': str(PNG_PATH),
    }
    JSON_PATH.write_text(json.dumps(metadata, indent=2), encoding='utf-8')


if __name__ == '__main__':
    render()
