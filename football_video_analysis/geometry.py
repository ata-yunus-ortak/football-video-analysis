"""Small pure-Python homography for explicitly supplied pitch calibration."""

from math import hypot
from .tracks import finite_vector


def center(bbox):
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def foot(bbox):
    return ((bbox[0] + bbox[2]) / 2, bbox[3])


def distance(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])


def _solve(matrix, target):
    rows = [list(row) + [value] for row, value in zip(matrix, target)]
    n = len(rows)
    for col in range(n):
        pivot = max(range(col, n), key=lambda i: abs(rows[i][col]))
        if abs(rows[pivot][col]) < 1e-10:
            raise ValueError("Calibration points are degenerate")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        scale = rows[col][col]
        rows[col] = [value / scale for value in rows[col]]
        for index in range(n):
            if index != col:
                scale = rows[index][col]
                rows[index] = [value - scale * other for value, other in zip(rows[index], rows[col])]
    return [row[-1] for row in rows]


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])


def _convex(vertices):
    turns = [_cross(vertices[i], vertices[(i + 1) % 4], vertices[(i + 2) % 4]) for i in range(4)]
    return all(value > 1e-8 for value in turns) or all(value < -1e-8 for value in turns)


class PitchTransform:
    def __init__(self, calibration):
        try:
            self.pixels = calibration["pixel_points"]
            target = calibration["pitch_points_m"]
        except (KeyError, TypeError) as error:
            raise ValueError("Calibration needs pixel_points and pitch_points_m") from error
        if len(self.pixels) != 4 or len(target) != 4:
            raise ValueError("Calibration requires four point correspondences in perimeter order")
        for point in self.pixels + target:
            finite_vector(point, 2, "calibration point")
        if not _convex(self.pixels) or not _convex(target):
            raise ValueError("Calibration points must form convex quadrilaterals in perimeter order")
        matrix, values = [], []
        for (x, y), (u, v) in zip(self.pixels, target):
            matrix.extend([[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]])
            values.extend([u, v])
        self.h = _solve(matrix, values)

    def point(self, point):
        x, y = point
        signs = [_cross(self.pixels[i], self.pixels[(i + 1) % 4], point) for i in range(4)]
        if not (all(value >= -1e-8 for value in signs) or all(value <= 1e-8 for value in signs)):
            return None
        a, b, c, d, e, f, g, h = self.h
        denominator = g * x + h * y + 1
        if abs(denominator) < 1e-10:
            return None
        return [(a * x + b * y + c) / denominator, (d * x + e * y + f) / denominator]
