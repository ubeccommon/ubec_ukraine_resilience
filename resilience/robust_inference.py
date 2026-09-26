"""robust_inference.py — shared inference helpers for 12_moderation.py and 22_trajectories.py.

wild_cluster_p(y, X, js, clusters, w=None, B=9999)
    Restricted wild-cluster bootstrap (WCR-C) for H0: beta_j = 0, one call per model for several j.
    Statistic: t with CR1 cluster-robust SE, factor G/(G-1) * (n-1)/(n-k). Webb six-point weights (suited to
    few clusters; here 24 oblasts), fixed seed. Returns {j: (t_cr1, p)}, p = share of |t*| >= |t|.
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


def wild_cluster_p(y, X, js, clusters, w=None, B=9999, seed=SEED, chunk=1000):
    y, X = _prep(y, X, w)
    n, k = X.shape
    _, g_idx = np.unique(np.asarray(clusters).astype(str), return_inverse=True)
    G = g_idx.max() + 1
    Gm = np.zeros((G, n))
    Gm[g_idx, np.arange(n)] = 1.0
    A = np.linalg.pinv(X.T @ X)
    c = G / (G - 1) * (n - 1) / (n - k)
    b = A @ (X.T @ y)
    e = y - X @ b
    V = WEBB[np.random.default_rng(seed).integers(0, 6, size=(G, B))]
    out = {}
    for j in js:
        h = X @ A[j]
        t0 = b[j] / np.sqrt(c * np.sum((Gm @ (h * e)) ** 2))
        keep = [i for i in range(k) if i != j]
        Xr = X[:, keep]
        fr = Xr @ np.linalg.lstsq(Xr, y, rcond=None)[0]
        er = y - fr
        hits = 0
        for s0 in range(0, B, chunk):
            Vb = V[:, s0:s0 + chunk]
            Ys = fr[:, None] + er[:, None] * Vb[g_idx]
            Bs = A @ (X.T @ Ys)
            Es = Ys - X @ Bs
            ses = np.sqrt(c * np.sum((Gm @ (h[:, None] * Es)) ** 2, axis=0))
            hits += int(np.sum(np.abs(Bs[j] / ses) >= abs(t0)))
        out[j] = (float(t0), hits / B)
    return out


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
