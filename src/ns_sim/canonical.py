from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .errors import ConfigurationError


def _identity_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ConfigurationError("non-finite numbers are forbidden in canonical identity documents")
        return {"$float64": value.hex()}
    if isinstance(value, list):
        return [_identity_value(item) for item in value]
    if isinstance(value, tuple):
        return [_identity_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _identity_value(value[key]) for key in sorted(value)}
    raise ConfigurationError(f"unsupported canonical identity value type: {type(value).__name__}")


def canonical_identity_document(value: Any) -> Any:
    """Return the schema-v1 identity representation.

    Every binary64 semantic float is encoded using Python's exact IEEE-754
    hexadecimal form. This avoids ambiguity from decimal pretty-printing.
    """

    return _identity_value(value)


def canonical_json_bytes(value: Any) -> bytes:
    doc = canonical_identity_document(value)
    return json.dumps(
        doc,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity_hash(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
