"""注入模块 (阶段1 任务2, 真值构造核心).

变量级注入 (对任意可重打分的打分器, 本阶段 cmhmil + iforest):
  - drift:  x_j(t) += beta * sigma_j * (t - s),  beta ∈ {0.01, 0.05, 0.1, 0.2}  (线性漂移)
  - stuck:  x_j(t) = x_j(s)  ∀t∈段                                (卡死在段起点值)
  - var:    x_j(t) = mu_j + alpha*(x_j(t)-mu_j), alpha ∈ {2, 5}    (方差膨胀)
  - joint:  多变量联合漂移 (2~3 个变量, 各自独立 beta)
注入变量集合即真值 (cause_type + cause_vars).

工况级注入 (仅 iforest, 重训留出式):
  - regime holdout: 用 regime 标签从弱训练段剔除工况 k 后重训 iforest,
    测试段中属于工况 k 的正常窗若超阈 → 工况型误报, 真值 = regime(k);
  - gradual: 从留出工况取源段, 与目标位置内容按 α(t) 0→1 渐变混合 (过渡段注入).

所有注入在测试段正常区域 (Y==0 且两侧留 margin) 随机采样段位, 种子固定.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath  # noqa: E402
import scorers_rescore as rs  # noqa: E402

DRIFT_BETAS = (0.01, 0.05, 0.1, 0.2)
VAR_ALPHAS = (2.0, 5.0)
SEG_LEN = 200          # 注入段长 (点)
N_TRIALS = 20          # 每配置试验段数


def sample_normal_segments(Y, b, seg_len=SEG_LEN, n=N_TRIALS, margin=32, seed=0):
    """在测试段 [b,T) 的正常区 (连续 Y==0 且段前后各 margin 点正常) 均匀采样 n 个段起点."""
    rng = np.random.default_rng(seed)
    T = len(Y)
    ok = np.ones(T, bool)
    bad = np.where(Y != 0)[0]
    for i in bad:
        # 段 [s, s+seg_len) 覆盖异常点 i 的起点范围: s ∈ [i-seg_len+1-margin, i+margin]
        ok[max(0, i - seg_len + 1 - margin):min(T, i + margin + 1)] = False
    valid_starts = np.where(ok[b:])[0] + b
    valid_starts = valid_starts[valid_starts + seg_len + margin <= T]
    if len(valid_starts) == 0:
        return np.array([], int)
    picks = rng.choice(valid_starts, size=min(n, len(valid_starts)), replace=False)
    return np.sort(picks)


def active_channels(X, a, b, min_sigma=0.05):
    """校准段 [a,b) 内有实际变化的通道 (SWaT 有 22/51 恒定执行器通道, 注入无意义)."""
    sigma = X[a:b].std(0)
    return np.where(sigma > min_sigma)[0]


def apply_variable_fault(X, s, seg_len, vars_j, kind, strength, mu=None, sigma=None):
    """在 X 副本的 [s, s+seg_len) 上对变量列表 vars_j 施加 kind 型故障. 返回 (X_mod, gt).
    gt: {cause_type, cause_vars, kind, strength}"""
    Xm = X.copy()
    seg = slice(s, s + seg_len)
    t = np.arange(seg_len)
    for j in vars_j:
        if kind == "drift":
            Xm[seg, j] += strength * (sigma[j] if sigma is not None else 1.0) * t
        elif kind == "stuck":
            Xm[seg, j] = X[s, j]
        elif kind == "var":
            m = mu[j] if mu is not None else 0.0
            Xm[seg, j] = m + strength * (Xm[seg, j] - m)
        else:
            raise ValueError(kind)
    gt = {"cause_type": "variable", "cause_vars": [int(v) for v in vars_j],
          "kind": kind, "strength": float(strength), "start": int(s), "seg_len": int(seg_len)}
    return Xm, gt


def eval_injected(scorer, dataset, X, Xm, s, seg_len, tau, window=WINDOW):
    """注入前后对受影响窗口重打分. 返回 dict: 段内窗的 fa 数/比例/分数."""
    ends = np.arange(s + window - 1, s + seg_len)
    if scorer == "cmhmil":
        fn = lambda Xx, ee: rs.aligned_rescore(scorer, dataset, Xx, ee)
    else:
        fn = lambda Xx, ee: rs.rescore_iforest(dataset, Xx, ee)
    s_before = fn(X, ends)
    s_after = fn(Xm, ends)
    return {
        "ends": ends, "scores_before": s_before, "scores_after": s_after,
        "n_windows": len(ends),
        "n_fa_after": int((s_after > tau).sum()),
        "n_fa_before": int((s_before > tau).sum()),
        "fa_rate_after": float((s_after > tau).mean()),
        "score_gain": float(np.mean(s_after - s_before)),
    }
