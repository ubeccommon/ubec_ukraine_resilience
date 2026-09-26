"""robust_inference.py — shared inference helpers for 12_moderation.py and 22_trajectories.py.

wild_cluster_p(y, X, js, clusters, w=None, B=9999)
    Restricted wild-cluster bootstrap (WCR-C) for H0: beta_j = 0, one call per model for several j.
    Statistic: t with CR1 cluster-robust SE, factor G/(G-1) * (n-1)/(n-k). Webb six-point weights (suited to
    few clusters; here 24 oblasts), fixed seed. Returns {j: (t_cr1, p)}, p = share of |t*| >= |t|.
wild_cluster_ci(y, X, j, clusters, w=None, B=9999, alpha=0.05)
    Confidence interval by test inversion: the set of b0 for which the restricted wild-cluster test of
    H0: beta_j = b0 has p >= alpha. Bounds found by bracketing and bisection (tolerance 5e-4) with the same
    bootstrap draws for every b0.
conley_t(y, X, js, xy, cutoffs, w=None)
    t-values with Conley spatial-HAC SEs: Bartlett kernel K = max(0, 1 - d / cutoff) on projected
    coordinates in metres (UA_LAEA), factor n / (n - k). Returns {cutoff: {j: t}}; NaN if the variance is not
    positive (the 2-D Bartlett kernel is not guaranteed positive semi-definite).
X must include the constant. With weights w (normalised to mean 1), y and X are scaled by sqrt(w), as in the
weighted OLS of 22_trajectories.py."""
import numpy as np

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
SEED = 20260926


def _prep(y, X, w):
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    if w is not None:
        sw = np.sqrt(np.asarray(w, float) / np.mean(w))
        y, X = y * sw, X * sw[:, None]
    return y, X


class _WCR:
    """Restricted wild-cluster bootstrap for one model; tests H0: beta_j = b0."""

    def __init__(self, y, X, clusters, w=None, B=9999, seed=SEED):
        self.y, self.X = _prep(y, X, w)
        n, k = self.X.shape
        _, self.g = np.unique(np.asarray(clusters).astype(str), return_inverse=True)
        G = self.g.max() + 1
        self.Gm = np.zeros((G, n))
        self.Gm[self.g, np.arange(n)] = 1.0
        self.A = np.linalg.pinv(self.X.T @ self.X)
        self.c = G / (G - 1) * (n - 1) / (n - k)
        self.b = self.A @ (self.X.T @ self.y)
        self.e = self.y - self.X @ self.b
        self.V = WEBB[np.random.default_rng(seed).integers(0, 6, size=(G, B))]
        self.B, self.k = B, k

    def se(self, j):
        h = self.X @ self.A[j]
        return np.sqrt(self.c * np.sum((self.Gm @ (h * self.e)) ** 2)), h

    def t(self, j, b0=0.0):
        s, _ = self.se(j)
        return (self.b[j] - b0) / s

    def p(self, j, b0=0.0, chunk=1000):
        X, y = self.X, self.y
        t0 = self.t(j, b0)
        _, h = self.se(j)
        keep = [i for i in range(self.k) if i != j]
        Xr = X[:, keep]
        yr = y - b0 * X[:, j]
        fr = Xr @ np.linalg.lstsq(Xr, yr, rcond=None)[0] + b0 * X[:, j]
        er = y - fr
        hits = 0
        for s0 in range(0, self.B, chunk):
            Vb = self.V[:, s0:s0 + chunk]
            Ys = fr[:, None] + er[:, None] * Vb[self.g]
            Bs = self.A @ (X.T @ Ys)
            Es = Ys - X @ Bs
            ses = np.sqrt(self.c * np.sum((self.Gm @ (h[:, None] * Es)) ** 2, axis=0))
            hits += int(np.sum(np.abs((Bs[j] - b0) / ses) >= abs(t0)))
        return hits / self.B


def wild_cluster_p(y, X, js, clusters, w=None, B=9999, seed=SEED):
    W = _WCR(y, X, clusters, w, B, seed)
    return {j: (float(W.t(j)), W.p(j)) for j in js}


def wild_cluster_ci(y, X, j, clusters, w=None, B=9999, alpha=0.05, seed=SEED, tol=5e-4):
    W = _WCR(y, X, clusters, w, B, seed)
    b = W.b[j]
    s, _ = W.se(j)

    def bound(direction):
        inside, step = b, 2 * s
        outside = b + direction * step
        for _ in range(12):
            if W.p(j, outside) < alpha:
                break
            inside, step = outside, step * 2
            outside = b + direction * step
        while abs(outside - inside) > tol:
            mid = (inside + outside) / 2
            if W.p(j, mid) >= alpha:
                inside = mid
            else:
                outside = mid
        return (inside + outside) / 2

    return float(bound(-1)), float(bound(+1))


def conley_t(y, X, js, xy, cutoffs, w=None):
    y, X = _prep(y, X, w)
    n, k = X.shape
    xy = np.asarray(xy, float)
    A = np.linalg.pinv(X.T @ X)
    b = A @ (X.T @ y)
    e = y - X @ b
    U = X * e[:, None]
    D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(axis=2))
    out = {}
    for cut in cutoffs:
        K = np.clip(1.0 - D / cut, 0.0, None)
        V = A @ (U.T @ K @ U) @ A * n / (n - k)
        out[cut] = {j: float(b[j] / np.sqrt(V[j, j])) if V[j, j] > 0 else np.nan for j in js}
    return out
