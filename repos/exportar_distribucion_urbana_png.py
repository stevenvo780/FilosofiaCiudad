#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import random
import struct
import zlib
from pathlib import Path

WIDTH = 1200
HEIGHT = 900
CELL = 24
SEED = 23

ROOT = Path('/workspace')
OUT_DIR = ROOT / 'Material'
PNG_PATH = OUT_DIR / 'distribucion_urbana_physarum.png'

COLORS = {
    'core': '#cf4d34',
    'mixed': '#f08a4b',
    'residential': '#f6d68a',
    'productive': '#7aa6c2',
    'green': '#bfd8a6',
    'road': '#2f3640',
    'transit': '#0e7490',
    'water': '#9fd3f4',
    'background': '#f8f6ef',
    'label': '#1f2933',
    'white': '#ffffff',
    'light_water': '#dff2ff',
    'light_transit': '#d8f5fb',
    'panel': '#fffdf8',
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


RGB = {k: hex_to_rgb(v) for k, v in COLORS.items()}


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
            for xx in range(x0, x1):
                self.blend_pixel(xx, yy, color, alpha)

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
            return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag + data) & 0xffffffff)

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
        edges.append(best_pair)
        connected.add(best_pair[1])
    return edges


def draw_label_block(canvas: Canvas, x: int, y: int, text: str, color: tuple[int, int, int], scale: int = 2) -> None:
    patterns = {
        'A': ['01110','10001','10001','11111','10001','10001','10001'],
        'B': ['11110','10001','11110','10001','10001','10001','11110'],
        'C': ['01111','10000','10000','10000','10000','10000','01111'],
        'D': ['11110','10001','10001','10001','10001','10001','11110'],
        'E': ['11111','10000','11110','10000','10000','10000','11111'],
        'G': ['01111','10000','10000','10111','10001','10001','01110'],
        'I': ['11111','00100','00100','00100','00100','00100','11111'],
        'L': ['10000','10000','10000','10000','10000','10000','11111'],
        'M': ['10001','11011','10101','10101','10001','10001','10001'],
        'N': ['10001','11001','10101','10011','10001','10001','10001'],
        'O': ['01110','10001','10001','10001','10001','10001','01110'],
        'R': ['11110','10001','10001','11110','10100','10010','10001'],
        'S': ['01111','10000','10000','01110','00001','00001','11110'],
        'T': ['11111','00100','00100','00100','00100','00100','00100'],
        'U': ['10001','10001','10001','10001','10001','10001','01110'],
        'V': ['10001','10001','10001','10001','10001','01010','00100'],
        ' ': ['000','000','000','000','000','000','000'],
    }
    cursor = x
    for ch in text.upper():
        glyph = patterns.get(ch)
        if glyph is None:
            cursor += 4 * scale
            continue
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '1':
                    canvas.rect(cursor + gx * scale, y + gy * scale, scale, scale, color)
        cursor += (len(glyph[0]) + 1) * scale


def main() -> None:
    random.seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(WIDTH, HEIGHT, RGB['background'])

    centers = [
        {'name': 'CBD', 'pos': (560.0, 450.0), 'weight': 1.00},
        {'name': 'Nodo Norte', 'pos': (560.0, 250.0), 'weight': 0.70},
        {'name': 'Nodo Este', 'pos': (820.0, 420.0), 'weight': 0.72},
        {'name': 'Nodo Oeste', 'pos': (320.0, 500.0), 'weight': 0.66},
        {'name': 'Nodo Sur', 'pos': (610.0, 680.0), 'weight': 0.62},
        {'name': 'Logistica', 'pos': (930.0, 690.0), 'weight': 0.52},
    ]
    spine_a = (140.0, 470.0)
    spine_b = (1060.0, 410.0)
    freight_a = (770.0, 780.0)
    freight_b = (1090.0, 640.0)
    river_points = [
        (70.0, 140.0),(180.0, 210.0),(280.0, 260.0),(370.0, 335.0),
        (520.0, 380.0),(700.0, 395.0),(880.0, 370.0),(1070.0, 300.0),
    ]

    for a, b in zip(river_points, river_points[1:]):
        canvas.line(a, b, RGB['water'], 28, 0.9)
        canvas.line(a, b, RGB['light_water'], 14, 0.8)

    for y in range(80, HEIGHT - 80, CELL):
        for x in range(80, WIDTH - 80, CELL):
            cx = x + CELL / 2
            cy = y + CELL / 2
            attraction = 0.0
            nearest_cbd = dist((cx, cy), centers[0]['pos'])
            nearest_any = min(dist((cx, cy), c['pos']) for c in centers)
            for center in centers:
                d = dist((cx, cy), center['pos'])
                attraction += center['weight'] / ((d / 130.0) ** 2 + 1.0)
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
                zone = 'green'
            elif nearest_cbd < 120 and score > 0.80:
                zone = 'core'
            elif score > 0.63 or nearest_any < 95:
                zone = 'mixed'
            elif freight_bonus > 0.18 and cx > 700:
                zone = 'productive'
            elif score > 0.30:
                zone = 'residential'
            else:
                zone = 'green'
            canvas.rect(x, y, CELL - 1, CELL - 1, RGB[zone], 0.92)

    canvas.line(spine_a, spine_b, RGB['transit'], 16, 0.92)
    canvas.line(spine_a, spine_b, RGB['light_transit'], 6, 0.8)
    canvas.line(freight_a, freight_b, RGB['road'], 10, 0.45)

    for i, j in prim_mst(centers):
        canvas.line(centers[i]['pos'], centers[j]['pos'], RGB['road'], 9, 0.88)
    for i, j in [(1,3),(3,4),(4,5),(5,2),(2,1)]:
        canvas.line(centers[i]['pos'], centers[j]['pos'], RGB['road'], 4, 0.44)

    for center in centers:
        radius = 17 if center['name'] == 'CBD' else 12
        canvas.circle(center['pos'], radius + 6, RGB['white'], 0.8)
        canvas.circle(center['pos'], radius, RGB['road'])
        canvas.circle(center['pos'], radius, RGB['road'], 1.0, stroke=RGB['white'], stroke_width=2)

    canvas.rect(865, 80, 270, 285, RGB['panel'], 0.95)
    legend = [('core', 180), ('mixed', 218), ('residential', 256), ('productive', 294), ('green', 332)]
    for key, yy in legend:
        canvas.rect(895, yy - 18, 26, 26, RGB[key])
    canvas.line((895, 380), (930, 380), RGB['road'], 7, 0.9)
    canvas.line((895, 418), (930, 418), RGB['transit'], 10, 0.9)

    draw_label_block(canvas, 80, 40, 'MAPA DEMO', RGB['label'], 3)
    draw_label_block(canvas, 895, 100, 'DISTRIBUCION URBANA', RGB['label'], 2)
    draw_label_block(canvas, 895, 126, 'MODELO SIMPLE', RGB['label'], 2)
    draw_label_block(canvas, 540, 425, 'CBD', RGB['white'], 2)
    draw_label_block(canvas, 510, 220, 'NORTE', RGB['label'], 2)
    draw_label_block(canvas, 790, 390, 'ESTE', RGB['label'], 2)
    draw_label_block(canvas, 270, 470, 'OESTE', RGB['label'], 2)
    draw_label_block(canvas, 590, 650, 'SUR', RGB['label'], 2)
    draw_label_block(canvas, 885, 660, 'LOGISTICA', RGB['label'], 2)

    canvas.save_png(PNG_PATH)
    print(json.dumps({'png': str(PNG_PATH)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
