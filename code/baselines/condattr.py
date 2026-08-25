"""CondAttr (DFKI, ECML-PKDD 2026) 论文忠实复现 — 最强基线端口.

背景: 官方仓库 (dfki-av/...) 截至 2026-08-15 只发布了 README/LICENSE,
无源码 ("Code Coming Soon"). 本模块按论文 v3 (arXiv:2604.17616) 复现其核心机制:
  1. 正常窗学习低维表示 (UMAP: 10 维, n_neighbors=30, min_dist=0.1, metric=欧氏,
     spectral init; 或 VAE: latent 8) — 论文 §4.2;
  2. 上下文检索: 查询窗在表示空间找 K=3 最近正常窗 (论文 §4.3, Eq.7/Eq.10);
  3. 条件化反事实: 对目标传感器 j, 用近邻窗的 x_j 替换查询窗的 j
     (W^(-j) 保留), 构造依赖保持的反事实窗;
  4. 归因分: φ_j = mean_{W'∈N_K} [f(W) − f(W^(-j), W'_j)]  (论文 Eq.5).

与论文的差异 (如实声明): 窗长 16 (对接第6篇打分器口径) 而非 50;
检索距离用全窗 UMAP 嵌入距离 (论文按非目标通道掩码距离, 掩码版留作消融);
检测器用第6篇 iforest-SWaT 而非其自训 TCN/AE.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW  # noqa: E402


class CondAttr:
    """UMAP 变体. f: 打分函数 (N, window*D) -> (N,) 越大越异常."""

    def __init__(self, f_score, K=3, n_neighbors=30, min_dist=0.1, seed=42,
                 n_embed_max=30000):
        self.f_score = f_score
        self.K = K
        self.seed = seed
        self.umap_params = dict(n_neighbors=n_neighbors, min_dist=min_dist)
        self.n_embed_max = n_embed_max
        self.embed_ = None
        self.db_feats_ = None

    def fit(self, normal_windows):
        """normal_windows: (N, window*D) 正常库窗口 (展平)."""
        import umap
        rng = np.random.default_rng(self.seed)
        idx = np.arange(len(normal_windows))
        if len(normal_windows) > self.n_embed_max:
            idx = rng.choice(len(normal_windows), self.n_embed_max, replace=False)
        sub = normal_windows[idx].astype(np.float32)
        self._reducer = umap.UMAP(n_components=10,
                                  n_neighbors=self.umap_params["n_neighbors"],
                                  min_dist=self.umap_params["min_dist"], metric="euclidean",
                                  init="spectral", random_state=self.seed)
        self.embed_ = self._reducer.fit_transform(sub)
        self.db_feats_ = sub
        self.db_idx_ = idx
        return self

    def _neighbors(self, q_flat):
        """查询窗在嵌入空间的 K 近邻 (用已学 UMAP 的 transform; 查询极少, 开销可接受)."""
        q = np.atleast_2d(q_flat.astype(np.float32))
        qe = self._reducer.transform(q)[0]
        d = np.linalg.norm(self.embed_ - qe, axis=1)
        return np.argsort(d)[:self.K]

    def attribute(self, W):
        """W: (window, D) 单个窗口 -> φ: (D,) 每传感器归因分 (越大越像根因)."""
        w, D = W.shape
        flat = W.reshape(1, -1)
        s_orig = float(self.f_score(flat)[0])
        nb = self._neighbors(flat)
        phi = np.zeros(D)
        for j in range(D):
            drops = []
            for i in nb:
                Wcf = W.copy()
                Wcf[:, j] = self.db_feats_[i].reshape(w, D)[:, j]
                s_cf = float(self.f_score(Wcf.reshape(1, -1))[0])
                drops.append(s_orig - s_cf)
            phi[j] = np.mean(drops)
        return phi, {"s_orig": s_orig, "n_neighbors": len(nb)}
