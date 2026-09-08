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


def create_histogram_data(values: Sequence[Any], bins: Optional[int] = None) -> List[Dict[str, Any]]:
    """Bin finite values adaptively, honoring an explicit positive bin count."""
    nums = [float(v) for v in values if _is_finite_number(v)]
    if not nums:
        return []
    mn = min(nums)
    mx = max(nums)
    if mn == mx:
        return [{"bin": str(int(mn)) if mn.is_integer() else str(mn), "count": len(nums)}]

    if bins is None or bins <= 0:
        bins = min(20, math.ceil(math.sqrt(len(nums))))
    bin_width = (mx - mn) / bins
    if bin_width <= 0:
        return [{"bin": str(int(mn)) if mn.is_integer() else str(mn), "count": len(nums)}]

    counts = [0] * bins
    for v in nums:
        idx = int((v - mn) / bin_width)
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    # Keep one more decimal place than the bin width's order of magnitude.
    decimals = max(0, 1 - math.floor(math.log10(bin_width)))
    out: List[Dict[str, Any]] = []
    for i, c in enumerate(counts):
        a = mn + i * bin_width
        b = mx if i == bins - 1 else mn + (i + 1) * bin_width
        out.append({"bin": f"{a:.{decimals}f}-{b:.{decimals}f}", "count": c})
    return out


def create_share_histogram_data(values: Sequence[Any], bins: Optional[int] = None) -> List[Dict[str, Any]]:
    """Histogram helper specialized for shares in [0, 1] with percent bins."""
    clamped: List[float] = []
    for v in values:
        if not _is_finite_number(v):
            continue
        fv = float(v)
        fv = max(0.0, min(1.0, fv))
        if math.isfinite(fv):
            clamped.append(fv)
    # Format in percentage units so precision follows the displayed bin width.
    histogram = create_histogram_data([v * 100 for v in clamped], bins=bins)
    return [{"bin": f"{row['bin']}%", "count": row["count"]} for row in histogram]
