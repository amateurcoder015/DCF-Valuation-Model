"""Internal validation utilities for DCF Valuation Model modules."""

import math


def validate_number(
    val: float,
    name: str,
    allow_negative: bool = True,
    min_val: float | None = None,
    max_val: float | None = None,
) -> float:
    """Validates that val is a valid numeric float/int, not bool, not NaN/Inf, and meets range constraints."""
    if isinstance(val, bool):
        raise TypeError(f"Argument '{name}' cannot be a boolean.")
    if not isinstance(val, (int, float)):
        raise TypeError(f"Argument '{name}' must be a number, got {type(val).__name__}.")
    val_float = float(val)
    if math.isnan(val_float) or math.isinf(val_float):
        raise ValueError(f"Argument '{name}' cannot be NaN or Infinity.")
    if not allow_negative and val_float < 0:
        raise ValueError(f"Argument '{name}' cannot be negative. Got {val_float}.")
    if min_val is not None and val_float < min_val:
        raise ValueError(f"Argument '{name}' must be >= {min_val}. Got {val_float}.")
    if max_val is not None and val_float > max_val:
        raise ValueError(f"Argument '{name}' must be <= {max_val}. Got {val_float}.")
    return val_float


def validate_positive_int(val: int, name: str) -> int:
    """Validates that val is a positive integer (> 0), not bool, not float."""
    if isinstance(val, bool):
        raise TypeError(f"Argument '{name}' cannot be a boolean.")
    if type(val) is not int:
        raise TypeError(f"Argument '{name}' must be an integer, got {type(val).__name__}.")
    if val <= 0:
        raise ValueError(f"Argument '{name}' must be a positive integer (> 0). Got {val}.")
    return val
