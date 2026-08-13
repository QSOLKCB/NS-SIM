from __future__ import annotations

import numpy as np


def divergence_backward(u: np.ndarray, v: np.ndarray, dx: float, dy: float) -> np.ndarray:
    return (u - np.roll(u, 1, axis=1)) / dx + (v - np.roll(v, 1, axis=0)) / dy


def gradient_forward(p: np.ndarray, dx: float, dy: float) -> tuple[np.ndarray, np.ndarray]:
    return (np.roll(p, -1, axis=1) - p) / dx, (np.roll(p, -1, axis=0) - p) / dy


def laplacian_periodic(a: np.ndarray, dx: float, dy: float) -> np.ndarray:
    return (
        (np.roll(a, -1, axis=1) - 2.0 * a + np.roll(a, 1, axis=1)) / (dx * dx)
        + (np.roll(a, -1, axis=0) - 2.0 * a + np.roll(a, 1, axis=0)) / (dy * dy)
    )


def derivative_centered_x(a: np.ndarray, dx: float) -> np.ndarray:
    return (np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1)) / (2.0 * dx)


def derivative_centered_y(a: np.ndarray, dy: float) -> np.ndarray:
    return (np.roll(a, -1, axis=0) - np.roll(a, 1, axis=0)) / (2.0 * dy)
