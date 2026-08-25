"""工况识别与验证模块 (阶段1 任务3).

- 特征: 手工统计特征 (方案允许的 tsfresh 替代): 每通道 {均值, 线性斜率, 方差} → 3D 维;
- 聚类: GMM (K=2..8, BIC 选择) 拟合于弱训练段正常窗;
- 验证: SWaT 阶段标签 (从原始 normal.csv 执行器列推导, 见 swat_stage_labels) / MetroPT3
  运行段 (Motor_current 占空比) → ARI/NMI;
- ARI < 0.5 如实报告 (预案: 改称"模式条件化").

SWaT 阶段推导规则 (P1-P6 工艺的粗粒度占空比主循环, 规则写入实验记录):
  stage=1 进水期  (P101==1, P1 进水泵运行, T101/T301 补水)
  stage=2 反洗期  (P101!=1 且 MV303 开启, UF 反洗)
  stage=3 待机期  (其余: 无进水无反洗, 液位消耗段)
标签在原始 csv 上推导后按 downsample=5 对齐到加载流 (与 load_swat 一致).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import DATA_ROOT, WINDOW, cpath, split_of  # noqa: E402


# ---------------- 窗口特征 ----------------
def window_features(X, window=WINDOW, stride=1):
    """(T,D) -> (N, 3D): 每通道 [mean, slope, var]. 窗尾索引 = window-1 + i*stride."""
    N = (len(X) - window) // stride + 1
    idx = np.arange(window)[None, :] + (np.arange(N)[:, None] * stride)
    W = X[idx]                                    # (N, window, D)
    mean = W.mean(1)
    var = W.var(1)
    t = np.arange(window) - (window - 1) / 2.0
    slope = (W * t[None, :, None]).sum(1) / ((t ** 2).sum())
    return np.concatenate([mean, slope, var], axis=1).astype(np.float32)


class RegimeModel:
    """GMM 工况模型: fit(弱训练段正常窗特征), predict(任意窗特征).
    数值稳定: 特征 float64 + PCA(0.95) 白化 + reg_covar (SWaT/MetroPT3 有大量
    恒定通道 -> 零方差特征, 直接 GMM 会产生退化协方差)."""

    def __init__(self, K=None, seed=0):
        self.K = K
        self.seed = seed
        self.gmm = None
        self.scaler = None
        self.pca = None
        self.bic_ = {}

    def fit(self, X, window=WINDOW, stride=8, max_windows=60000, seed=0):
        from sklearn.decomposition import PCA
        from sklearn.mixture import GaussianMixture
        from sklearn.preprocessing import StandardScaler
        a, _ = split_of(len(X))
        F = window_features(X[:a], window, stride)
        if len(F) > max_windows:
            rng = np.random.default_rng(seed)
            F = F[rng.choice(len(F), max_windows, replace=False)]
        self.scaler = StandardScaler().fit(F)
        Fs = self.scaler.transform(F).astype(np.float64)
        self.pca = PCA(n_components=0.95, random_state=self.seed).fit(Fs)
        Fs = self.pca.transform(Fs)
        if self.K is None:
            best, best_bic = None, np.inf
            for k in range(2, 9):
                try:
                    g = GaussianMixture(k, covariance_type="diag", random_state=self.seed,
                                        n_init=2, max_iter=200, reg_covar=1e-3).fit(Fs)
                except ValueError:
                    continue
                self.bic_[k] = float(g.bic(Fs))
                if self.bic_[k] < best_bic:
                    best, best_bic = k, self.bic_[k]
            self.K = best if best is not None else 2
        self.gmm = GaussianMixture(self.K, covariance_type="diag", random_state=self.seed,
                                   n_init=2, max_iter=200, reg_covar=1e-3).fit(Fs)
        return self

    def transform(self, F):
        """特征 (N,3D) -> regime 标签."""
        return self.gmm.predict(self.pca.transform(self.scaler.transform(F.astype(np.float64))))

    def predict_windows(self, X, window=WINDOW, stride=1):
        """对全流滑窗 (stride=1) 预测 regime. 返回 (labels, 窗尾索引)."""
        F = window_features(X, window, stride)
        return self.gmm.predict(self.scaler.transform(F)), \
            np.arange(window - 1, window - 1 + (len(F) - 1) * stride + 1, stride)

    def profile(self, X, window=WINDOW):
        """每 regime 的通道画像: 均值/方差表 (D×K). 返回 dict."""
        labels, _ = self.predict_windows(X, window)
        F = window_features(X, window, 1)
        D = X.shape[1]
        prof = {}
        for k in range(self.K):
            m = labels == k
            prof[k] = {"n_windows": int(m.sum()),
                       "ch_mean": F[m][:, :D].mean(0), "ch_var": F[m][:, 2 * D:3 * D].mean(0)}
        return prof


# ---------------- SWaT 阶段标签 ----------------
def swat_stage_labels(downsample=5):
    """原始 normal.csv 执行器列 → 阶段标签, 对齐 load_swat 降采样. 返回 (T_n,) int8."""
    import pandas as pd
    path = os.path.join(DATA_ROOT, "SWaT", "normal.csv")
    df = pd.read_csv(path, usecols=lambda c: c.strip() in ("P101", "MV303"))
    p101 = df[" P101"].values if " P101" in df else df["P101"].values
    mv303 = df.columns.str.strip().tolist()
    mv303_col = [c for c in df.columns if c.strip() == "MV303"][0]
    mv303 = df[mv303_col].values
    on_p101 = p101 < 1.5      # 1=on, 2=off, 过渡小数
    on_mv303 = mv303 < 1.5
    stage = np.where(on_p101, 1, np.where(on_mv303, 2, 3)).astype(np.int8)
    return stage[::downsample]


# ---------------- MetroPT3 运行段标签 ----------------
def metropt3_cycle_labels(X, motor_col=6, smooth=2000):
    """Motor_current 滑动中值二值化 → 负载(1)/卸载(0) 运行段. X 已 z-score.
    motor_col=6: 列序 TP2,TP3,H1,DV_pressure,Reservoirs,Oil_temperature,Motor_current."""
    import scipy.ndimage as ndi
    mc = ndi.median_filter(X[:, motor_col], size=smooth)
    thr = (np.quantile(mc, 0.1) + np.quantile(mc, 0.9)) / 2
    return (mc > thr).astype(np.int8)


def alignment_report(labels_pred, labels_true):
    """ARI/NMI. 返回 dict."""
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
    return {"ari": float(adjusted_rand_score(labels_true, labels_pred)),
            "nmi": float(normalized_mutual_info_score(labels_true, labels_pred))}


def features_at(X, ends, window=WINDOW):
    """任意窗尾索引数组 ends 的特征 (N, 3D), 与 window_features 同口径."""
    idx = np.arange(window)[None, :] + (np.asarray(ends)[:, None] - (window - 1))
    W = X[idx]
    mean = W.mean(1)
    var = W.var(1)
    t = np.arange(window) - (window - 1) / 2.0
    slope = (W * t[None, :, None]).sum(1) / ((t ** 2).sum())
    return np.concatenate([mean, slope, var], axis=1).astype(np.float32)


def window_majority(point_labels, window=WINDOW, stride=1):
    """点级标签 → 窗级多数标签 (与 window_features 同窗位)."""
    N = (len(point_labels) - window) // stride + 1
    idx = np.arange(window)[None, :] + (np.arange(N)[:, None] * stride)
    W = point_labels[idx]
    vals = np.unique(W)
    counts = np.stack([(W == v).sum(1) for v in vals], 0)   # (n_vals, N)
    return vals[counts.argmax(0)]
