"""RC-CA 本体 (Regime-Conditioned Counterfactual Attribution, 论文 §4).

流程 (每个误报窗口 w):
  1. 工况识别: GMM (特征=通道均值/斜率/方差, StandardScaler+PCA0.95) 判 w 属 regime k;
  2. 工况条件化反事实: 在 regime k 的正常窗池内取 K 近邻, 邻域均值轨迹为条件期望模板;
     对每变量 j: a_j = s(w) − s(w_{j←模板_j})  (变量级贡献, Eq.3);
  3. Δ_reg = [s−s(w^cf_reg)] − [s−s(w^cf_glob)] (regime 证据差, Eq.4);
  4. 双粒度决策 (Eq.5): Δ_reg>δ 且 max_j a_j 归一 <γ → regime(k);
     否则 argmax_j a_j, 并按通道统计特征细分 drift/stuck/variance;
基线② (regime-aware 全局替换) 同文件实现: 模板=簇均值, φ 仍用全局均值替换.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW  # noqa: E402,F401


class _RegimeBank:
    """正常窗池的工况结构: 特征 GMM + 每簇成员索引 + 全局均值轨迹."""

    def __init__(self, pool_windows, seed=0):
        from sklearn.decomposition import PCA
        from sklearn.mixture import GaussianMixture
        from sklearn.preprocessing import StandardScaler
        self.P = pool_windows.astype(np.float32)          # (N, W, D)
        W = self.P.shape[1]
        t = np.arange(W) - (W - 1) / 2.0
        mean = self.P.mean(1)
        var = self.P.var(1)
        slope = (self.P * t[None, :, None]).sum(1) / ((t ** 2).sum())
        F = np.concatenate([mean, slope, var], 1).astype(np.float64)
        self.scaler = StandardScaler().fit(F)
        Fs = self.scaler.transform(F)
        self.pca = PCA(n_components=0.95, random_state=seed).fit(Fs)
        Fs = self.pca.transform(Fs)
        self.gmm = GaussianMixture(8, covariance_type="diag", random_state=seed,
                                   n_init=2, max_iter=200, reg_covar=1e-3).fit(Fs)
        self.Fs = Fs
        self.labels = self.gmm.predict(Fs)
        self.members = {k: np.where(self.labels == k)[0] for k in range(self.gmm.n_components)}
        self.global_mean_traj = self.P.mean(0)            # (W, D)

    def feats(self, Warr):
        Wn = Warr.shape[1]
        t = np.arange(Wn) - (Wn - 1) / 2.0
        mean = Warr.mean(1)
        var = Warr.var(1)
        slope = (Warr * t[None, :, None]).sum(1) / ((t ** 2).sum())
        F = np.concatenate([mean, slope, var], 1).astype(np.float64)
        return self.pca.transform(self.scaler.transform(F))

    def regime_of(self, Warr):
        return self.gmm.predict(self.feats(Warr))

    def knn_template(self, Warr, K=5):
        """每窗口在其 regime 池内的 K 近邻均值轨迹 (n, W, D)."""
        n = len(Warr)
        labs = self.regime_of(Warr)
        out = np.empty_like(Warr, dtype=np.float32)
        Fs = self.feats(Warr)
        for i in range(n):
            mem = self.members.get(labs[i], np.arange(len(self.P)))
            if len(mem) == 0:
                out[i] = self.global_mean_traj
                continue
            d = np.linalg.norm(self.Fs[mem] - Fs[i], axis=1)
            nb = mem[np.argsort(d)[:K]]
            out[i] = self.P[nb].mean(0)
        return out, labs

    def cluster_template(self, Warr):
        """每窗口所属 regime 簇的均值轨迹 (基线②用)."""
        labs = self.regime_of(Warr)
        out = np.empty_like(Warr, dtype=np.float32)
        for i, k in enumerate(labs):
            mem = self.members.get(k, np.arange(len(self.P)))
            out[i] = self.P[mem].mean(0) if len(mem) else self.global_mean_traj
        return out, labs


def _batch_score(unit, ws_list):
    """打分窗口列表 [(n,W,D)] 拼接一次打分再切回."""
    allw = np.concatenate(ws_list, 0)
    s = unit.score(allw)
    out, off = [], 0
    for w in ws_list:
        out.append(s[off:off + len(w)])
        off += len(w)
    return out


def rcca_attribute(unit, Warr, bank, K=5):
    """RC-CA 归因. 返回 dict: phi(n,D), conf(n), delta(n), regime(n), subtype(list)."""
    n, Wn, D = Warr.shape
    s_orig = unit.score(Warr)
    tmpl, labs = bank.knn_template(Warr, K=K)
    # 每变量替换 + 全量替换 (regime 模板 / 全局均值)
    reps = [np.where(np.arange(D)[None, None, :] == j, tmpl, Warr).astype(np.float32)
            for j in range(D)]
    reps.append(tmpl.astype(np.float32))                                   # w^cf_reg
    reps.append(np.broadcast_to(bank.global_mean_traj, Warr.shape).astype(np.float32))  # w^cf_glob
    scores = _batch_score(unit, reps)
    drops = np.stack([s_orig - scores[j] for j in range(D)], 1)            # (n, D)
    s_reg, s_glob = scores[D], scores[D + 1]
    delta = (s_orig - s_reg) - (s_orig - s_glob)                           # = s_glob - s_reg
    conf = drops.max(1) / (np.abs(s_orig) + 1e-9)
    subtype = [_subtype(Warr[i], drops[i], bank) for i in range(n)]
    return {"phi": drops, "conf": conf, "delta": delta, "regime": labs,
            "s_orig": s_orig, "subtype": subtype}


def regime_aware_global_attribute(unit, Warr, bank):
    """基线② (v2, R6 外部审稿后修正): 模式均值替换 —— GMM 识别工况 + 用该模式簇的
    均值轨迹替换 (v1 用全局均值在 γ-only 决策下退化为 GlobalCF, 被审稿人正确指出).
    现在它真正隔离"模式感知替换(簇均值, 无邻域条件化)"这一成分."""
    n, Wn, D = Warr.shape
    s_orig = unit.score(Warr)
    tmpl, labs = bank.cluster_template(Warr)          # 每窗所属簇的均值轨迹
    reps = []
    for j in range(D):
        reps.append(np.where(np.arange(D)[None, None, :] == j,
                             tmpl, Warr).astype(np.float32))
    scores = _batch_score(unit, reps)                     # list: 每 rep 一个 (n,)
    drops = np.stack([s_orig - scores[j] for j in range(D)], 1)
    conf = drops.max(1) / (np.abs(s_orig) + 1e-9)
    return {"phi": drops, "conf": conf, "delta": None, "regime": labs,
            "s_orig": s_orig, "subtype": [None] * n}

def _subtype(w, phi, bank):
    """top-1 变量的故障细分: 均值偏移z / 方差比 → drift / stuck / variance."""
    j = int(np.argmax(phi))
    P = bank.P[:, :, j]
    mu, sd = P.mean(), P.std() + 1e-9
    z = (w[:, j].mean() - mu) / sd
    vr = (w[:, j].var() + 1e-12) / (P.var() + 1e-12)
    if vr < 0.1:
        return "stuck"
    if abs(z) > 1.0:
        return "drift"
    if vr > 1.5:
        return "variance"
    return "drift" if abs(z) > 0.5 else "variance"
