from __future__ import annotations

from dataclasses import dataclass
import json
import math
import struct
from pathlib import Path

import numpy as np

from .canonical import sha256_bytes
from .errors import ConfigurationError

_MAGIC = b"NSSIMSTATE1\n"


@dataclass(frozen=True)
class State:
    u: np.ndarray
    v: np.ndarray
    p: np.ndarray
    step: int
    time: float


def grid_spacing(experiment: dict) -> tuple[float, float]:
    return (
        experiment["domain"]["x_length"] / experiment["grid"]["nx"],
        experiment["domain"]["y_length"] / experiment["grid"]["ny"],
    )


def initialize_state(experiment: dict) -> State:
    nx = experiment["grid"]["nx"]
    ny = experiment["grid"]["ny"]
    lx = experiment["domain"]["x_length"]
    ly = experiment["domain"]["y_length"]
    dx, dy = grid_spacing(experiment)
    x = (np.arange(nx, dtype=np.float64) + 0.5) * dx
    y = (np.arange(ny, dtype=np.float64) + 0.5) * dy
    xx, yy = np.meshgrid(x, y, indexing="xy")

    initial = experiment["initial_condition"]
    if initial["type"] == "zero":
        u = np.zeros((ny, nx), dtype=np.float64)
        v = np.zeros((ny, nx), dtype=np.float64)
    elif initial["type"] == "taylor_green":
        if not math.isclose(lx, ly, rel_tol=0.0, abs_tol=0.0):
            raise ConfigurationError("taylor_green initialization requires square domain")
        amplitude = np.float64(initial["amplitude"])
        mode = initial["mode"]
        k = np.float64(2.0 * math.pi * mode / lx)
        u = amplitude * np.sin(k * xx) * np.cos(k * yy)
        v = -amplitude * np.cos(k * xx) * np.sin(k * yy)
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
    else:
        raise ConfigurationError(f"unsupported initial condition {initial['type']!r}")
    p = np.zeros((ny, nx), dtype=np.float64)
    return State(u=np.ascontiguousarray(u), v=np.ascontiguousarray(v), p=p, step=0, time=0.0)


def serialize_state(state: State, experiment_hash: str) -> bytes:
    shape = list(state.u.shape)
    if state.v.shape != state.u.shape or state.p.shape != state.u.shape:
        raise ValueError("canonical state fields must have identical shapes")
    header = {
        "format": "ns-sim-state/1",
        "experiment_hash": experiment_hash,
        "step": state.step,
        "time_float64_hex": float(state.time).hex(),
        "shape": shape,
        "fields": ["u", "v", "p"],
        "dtype": "<f8",
        "order": "C",
    }
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload = bytearray(_MAGIC)
    payload.extend(struct.pack(">Q", len(header_bytes)))
    payload.extend(header_bytes)
    for field in (state.u, state.v, state.p):
        payload.extend(np.asarray(field, dtype="<f8", order="C").tobytes(order="C"))
    return bytes(payload)


def deserialize_state(data: bytes) -> tuple[State, dict]:
    if not data.startswith(_MAGIC):
        raise ValueError("invalid NS-SIM state magic")
    offset = len(_MAGIC)
    (header_len,) = struct.unpack(">Q", data[offset : offset + 8])
    offset += 8
    header = json.loads(data[offset : offset + header_len].decode("utf-8"))
    offset += header_len
    ny, nx = header["shape"]
    count = nx * ny
    fields = []
    for _ in range(3):
        byte_count = count * 8
        arr = np.frombuffer(data[offset : offset + byte_count], dtype="<f8").reshape((ny, nx)).copy()
        fields.append(arr)
        offset += byte_count
    if offset != len(data):
        raise ValueError("trailing bytes in NS-SIM state")
    state = State(
        u=fields[0],
        v=fields[1],
        p=fields[2],
        step=int(header["step"]),
        time=float.fromhex(header["time_float64_hex"]),
    )
    return state, header


def state_hash(state: State, experiment_hash: str) -> str:
    return sha256_bytes(serialize_state(state, experiment_hash))


def write_checkpoint(path: str | Path, state: State, experiment_hash: str) -> str:
    data = serialize_state(state, experiment_hash)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha256_bytes(data)
