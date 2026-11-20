"""Pure-Python statistics used by the chart builders (no numpy, so it runs anywhere,
including Termux on Android). Inputs are small (a query result is capped at a few hundred rows)."""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def stdev(xs: Sequence[float]) -> float:
    """Sample standard deviation (0.0 for fewer than two values)."""
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def quantile(sorted_xs: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile of an already sorted sequence (same as NumPy's default)."""
    if not sorted_xs:
        raise ValueError("empty data")
    pos = (len(sorted_xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def normal_ppf(p: float) -> float:
    return statistics.NormalDist().inv_cdf(p)


def silverman_bandwidth(xs: Sequence[float]) -> float:
    s = sorted(xs)
    sd = stdev(s)
    iqr = quantile(s, 0.75) - quantile(s, 0.25)
    sigma = min(sd, iqr / 1.34) if iqr > 0 else sd
    if sigma <= 0:
        sigma = 1.0
    return 0.9 * sigma * len(s) ** -0.2


def gaussian_kde(
    xs: Sequence[float], n_points: int = 200
) -> tuple[list[float], list[float]]:
    """Gaussian kernel density estimate on an evenly spaced grid."""
    xs = list(xs)
    if len(xs) > 2000:  # deterministic thinning keeps this O(grid * 2000)
        step = math.ceil(len(xs) / 2000)
        xs = xs[::step]
    h = silverman_bandwidth(xs)
    lo, hi = min(xs) - 3 * h, max(xs) + 3 * h
    grid = [lo + i * (hi - lo) / (n_points - 1) for i in range(n_points)]
    norm = 1.0 / (len(xs) * h * math.sqrt(2 * math.pi))
    dens = [norm * sum(math.exp(-0.5 * ((g - x) / h) ** 2) for x in xs) for g in grid]
    return grid, dens


def pearson(a: Sequence[float], b: Sequence[float]) -> float | None:
    """Pearson correlation. None when either side has no variance."""
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    sa = sum((x - ma) ** 2 for x in a)
    sb = sum((y - mb) ** 2 for y in b)
    if sa <= 0 or sb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sa * sb)


def ols(x: Sequence[float], y: Sequence[float]) -> tuple[float, float, float] | None:
    """Least-squares line. Returns (slope, intercept, r_squared) or None if x has no variance."""
    n = len(x)
    if n < 2:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx <= 0:
        return None
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    intercept = my - slope * mx
    ss_tot = sum((b - my) ** 2 for b in y)
    ss_res = sum((b - (slope * a + intercept)) ** 2 for a, b in zip(x, y))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2


def correlation_matrix(columns: Sequence[Sequence[float]]) -> list[list[float | None]]:
    p = len(columns)
    out: list[list[float | None]] = [[None] * p for _ in range(p)]
    for i in range(p):
        out[i][i] = 1.0
        for j in range(i + 1, p):
            out[i][j] = out[j][i] = pearson(columns[i], columns[j])
    return out


def jacobi_eigenvalues(
    matrix: Sequence[Sequence[float]], tol: float = 1e-12, max_sweeps: int = 100
) -> list[float]:
    """Eigenvalues of a small symmetric matrix by cyclic Jacobi rotations, sorted descending."""
    n = len(matrix)
    a = [list(map(float, row)) for row in matrix]
    for _ in range(max_sweeps):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(i + 1, n))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (
                    abs(theta) + math.sqrt(theta * theta + 1.0)
                )
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return sorted((a[i][i] for i in range(n)), reverse=True)


def _sorted_by_score(y_true: Sequence[bool], scores: Sequence[float]):
    return sorted(zip(scores, y_true), key=lambda t: -t[0])


def roc_curve(
    y_true: Sequence[bool], scores: Sequence[float]
) -> tuple[list[float], list[float], float]:
    """ROC points (fpr, tpr) and the trapezoidal AUC. Tied scores share one threshold."""
    positives = sum(1 for y in y_true if y)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("need both classes")
    pairs = _sorted_by_score(y_true, scores)
    fpr, tpr = [0.0], [0.0]
    tp = fp = i = 0
    while i < len(pairs):
        j, s = i, pairs[i][0]
        while j < len(pairs) and pairs[j][0] == s:
            tp += 1 if pairs[j][1] else 0
            fp += 0 if pairs[j][1] else 1
            j += 1
        fpr.append(fp / negatives)
        tpr.append(tp / positives)
        i = j
    auc = sum(
        (fpr[k] - fpr[k - 1]) * (tpr[k] + tpr[k - 1]) / 2 for k in range(1, len(fpr))
    )
    return fpr, tpr, auc


def pr_curve(
    y_true: Sequence[bool], scores: Sequence[float]
) -> tuple[list[float], list[float], float]:
    """Precision-recall points and average precision (step-wise, as in scikit-learn)."""
    positives = sum(1 for y in y_true if y)
    if positives == 0 or positives == len(y_true):
        raise ValueError("need both classes")
    pairs = _sorted_by_score(y_true, scores)
    recall, precision = [0.0], [1.0]
    tp = fp = i = 0
    while i < len(pairs):
        j, s = i, pairs[i][0]
        while j < len(pairs) and pairs[j][0] == s:
            tp += 1 if pairs[j][1] else 0
            fp += 0 if pairs[j][1] else 1
            j += 1
        recall.append(tp / positives)
        precision.append(tp / (tp + fp))
        i = j
    ap = sum((recall[k] - recall[k - 1]) * precision[k] for k in range(1, len(recall)))
    return recall, precision, ap
