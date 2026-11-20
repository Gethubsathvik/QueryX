"""A small CART decision tree (classification with Gini, regression with variance).

Pure Python and deterministic. Nodes are plain dicts so the result is easy to test and draw.
"""

from __future__ import annotations

from collections import Counter


def _gini(counts: list[int], n: int) -> float:
    return 1.0 - sum((c / n) ** 2 for c in counts) if n else 0.0


def _variance(total: float, total_sq: float, n: int) -> float:
    return max(0.0, total_sq / n - (total / n) ** 2) if n else 0.0


class DecisionTree:
    def __init__(self, task: str, max_depth: int = 3, min_leaf: int = 5):
        if task not in ("classification", "regression"):
            raise ValueError("task must be 'classification' or 'regression'")
        self.task, self.max_depth, self.min_leaf = task, max_depth, min_leaf
        self.classes: list = []
        self.root: dict | None = None
        self.n_features = 0

    # ---- fitting ---------------------------------------------------------
    def fit(self, X: list[list[float]], y: list) -> DecisionTree:
        if not X or len(X) != len(y):
            raise ValueError("X and y must be non-empty and the same length")
        self.n_features = len(X[0])
        if self.task == "classification":
            self.classes = sorted(set(y), key=str)
            index = {c: i for i, c in enumerate(self.classes)}
            target = [index[v] for v in y]
        else:
            target = [float(v) for v in y]
        self.root = self._grow(X, target, list(range(len(X))), 0)
        return self

    def _node_stats(self, target, idx) -> dict:
        n = len(idx)
        if self.task == "classification":
            counts = [0] * len(self.classes)
            for i in idx:
                counts[target[i]] += 1
            best = max(range(len(counts)), key=lambda k: (counts[k], -k))
            return {
                "n": n,
                "impurity": _gini(counts, n),
                "counts": counts,
                "prediction": best,
            }
        vals = [target[i] for i in idx]
        m = sum(vals) / n
        return {
            "n": n,
            "impurity": _variance(sum(vals), sum(v * v for v in vals), n),
            "mean": m,
            "prediction": m,
        }

    def _grow(self, X, target, idx, depth) -> dict:
        node = self._node_stats(target, idx)
        node["depth"] = depth
        node["feature"] = node["threshold"] = node["left"] = node["right"] = None
        if (
            depth >= self.max_depth
            or node["impurity"] <= 1e-12
            or len(idx) < 2 * self.min_leaf
        ):
            return node
        split = self._best_split(X, target, idx, node["impurity"])
        if split is None:
            return node
        feature, threshold = split
        left = [i for i in idx if X[i][feature] <= threshold]
        right = [i for i in idx if X[i][feature] > threshold]
        node["feature"], node["threshold"] = feature, threshold
        node["left"] = self._grow(X, target, left, depth + 1)
        node["right"] = self._grow(X, target, right, depth + 1)
        return node

    def _best_split(self, X, target, idx, parent_impurity):
        n, best = len(idx), None
        for f in range(self.n_features):
            order = sorted(idx, key=lambda i: X[i][f])
            if self.task == "classification":
                k = len(self.classes)
                left, right = [0] * k, [0] * k
                for i in idx:
                    right[target[i]] += 1
            else:
                left_sum = left_sq = 0.0
                right_sum = sum(target[i] for i in idx)
                right_sq = sum(target[i] ** 2 for i in idx)
            for pos in range(n - 1):
                i = order[pos]
                if self.task == "classification":
                    left[target[i]] += 1
                    right[target[i]] -= 1
                else:
                    v = target[i]
                    left_sum += v
                    left_sq += v * v
                    right_sum -= v
                    right_sq -= v * v
                nl, nr = pos + 1, n - pos - 1
                a, b = X[i][f], X[order[pos + 1]][f]
                if a == b or nl < self.min_leaf or nr < self.min_leaf:
                    continue
                if self.task == "classification":
                    child = (nl * _gini(left, nl) + nr * _gini(right, nr)) / n
                else:
                    child = (
                        nl * _variance(left_sum, left_sq, nl)
                        + nr * _variance(right_sum, right_sq, nr)
                    ) / n
                gain = parent_impurity - child
                if gain > 1e-12 and (best is None or gain > best[0] + 1e-12):
                    best = (gain, f, (a + b) / 2)
        return None if best is None else (best[1], best[2])

    # ---- using the fitted tree ------------------------------------------
    def predict_one(self, row: list[float]):
        node = self.root
        while node["feature"] is not None:
            node = (
                node["left"]
                if row[node["feature"]] <= node["threshold"]
                else node["right"]
            )
        return (
            self.classes[node["prediction"]]
            if self.task == "classification"
            else node["prediction"]
        )

    def score(self, X: list[list[float]], y: list) -> float:
        """Accuracy for classification, R-squared for regression (on the training data)."""
        preds = [self.predict_one(r) for r in X]
        if self.task == "classification":
            return sum(p == t for p, t in zip(preds, y)) / len(y)
        m = sum(y) / len(y)
        ss_tot = sum((t - m) ** 2 for t in y)
        ss_res = sum((t - p) ** 2 for p, t in zip(preds, y))
        return 1 - ss_res / ss_tot if ss_tot > 0 else 1.0

    def nodes(self) -> list[dict]:
        out, stack = [], [self.root]
        while stack:
            node = stack.pop()
            out.append(node)
            if node["feature"] is not None:
                stack.extend([node["right"], node["left"]])
        return out

    def depth(self) -> int:
        return max(n["depth"] for n in self.nodes())

    def leaf_count(self) -> int:
        return sum(1 for n in self.nodes() if n["feature"] is None)

    def importances(self) -> list[float]:
        """Normalised impurity decrease per feature (sums to 1, or all zeros for a single leaf)."""
        imp = [0.0] * self.n_features
        for node in self.nodes():
            if node["feature"] is None:
                continue
            l, r = node["left"], node["right"]
            imp[node["feature"]] += (
                node["n"] * node["impurity"]
                - l["n"] * l["impurity"]
                - r["n"] * r["impurity"]
            )
        total = sum(imp)
        return [v / total for v in imp] if total > 0 else imp

    def majority_label(self, node: dict):
        return (
            self.classes[node["prediction"]]
            if self.task == "classification"
            else node["mean"]
        )


def looks_categorical(values: list) -> bool:
    """Heuristic used by the builder: non-numeric targets, or numbers with few distinct values."""
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in values):
        return True
    return len(Counter(values)) <= 10
