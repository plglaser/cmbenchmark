from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence


def _get(d: Optional[Mapping[str, Any]], *path: str, default: Any = None) -> Any:
    """Safe nested dict getter."""
    cur: Any = d
    for key in path:
        if not isinstance(cur, Mapping):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def create_histogram_data(values: Sequence[Any], bins: int = 20) -> List[Dict[str, Any]]:
    """Create histogram bins like the TS `createHistogramData` helper."""
    nums = [float(v) for v in values if _is_finite_number(v)]
    if not nums:
        return []
    mn = min(nums)
    mx = max(nums)
    if mn == mx:
        return [{"bin": f"{mn:.0f}", "count": len(nums)}]

    if bins <= 0:
        bins = 20
    bin_width = (mx - mn) / bins
    if bin_width <= 0:
        return [{"bin": f"{mn:.0f}", "count": len(nums)}]

    counts = [0] * bins
    for v in nums:
        idx = int((v - mn) / bin_width)
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    out: List[Dict[str, Any]] = []
    for i, c in enumerate(counts):
        a = mn + i * bin_width
        b = mn + (i + 1) * bin_width
        out.append({"bin": f"{a:.0f}-{b:.0f}", "count": c})
    return out


def create_share_histogram_data(values: Sequence[Any], bins: int = 20) -> List[Dict[str, Any]]:
    """Histogram helper specialized for shares in [0, 1] with percent bins."""
    clamped: List[float] = []
    for v in values:
        if not _is_finite_number(v):
            continue
        fv = float(v)
        fv = max(0.0, min(1.0, fv))
        if math.isfinite(fv):
            clamped.append(fv)
    if not clamped:
        return []

    mn = min(clamped)
    mx = max(clamped)
    if mn == mx:
        p = f"{mn * 100:.1f}"
        return [{"bin": f"{p}-{p}%", "count": len(clamped)}]

    if bins <= 0:
        bins = 20
    bin_width = (mx - mn) / bins
    if bin_width <= 0:
        p = f"{mn * 100:.1f}"
        return [{"bin": f"{p}-{p}%", "count": len(clamped)}]

    counts = [0] * bins
    for v in clamped:
        idx = int((v - mn) / bin_width)
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    decimals = 1 if (mx - mn) < 0.2 else 0
    out: List[Dict[str, Any]] = []
    for i, c in enumerate(counts):
        a = mn + i * bin_width
        b = mn + (i + 1) * bin_width
        fa = f"{a * 100:.{decimals}f}"
        fb = f"{b * 100:.{decimals}f}"
        out.append({"bin": f"{fa}-{fb}%", "count": c})
    return out

