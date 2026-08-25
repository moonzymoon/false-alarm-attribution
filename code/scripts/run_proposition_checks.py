"""Proposition 1 假设的经验验证 (v3 必改1).

A1 (联合分布敏感性): 同边缘、不同联合的窗口应改变打分器输出 —— 对正常池窗逐通道
    独立时间置换 (边缘保持、联合结构破坏), 度量分数变化与超阈比例;
A4 (OOD 不减分): 对单通道施加递增偏移, 分数应单调不减 —— 报告单调比例
    (cmhmil 在 SWaT 已知反向, 如实报告即假设失效的数据证据);
边界 (KL 小 ⇒ 不可消除性弱化): 各 regime 的 特征空间(regime vs 全局) KL 与
    该 regime 型 FA 的 Δ_reg 均值的相关性.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, WINDOW  # noqa: E402
import scorers_rescore as rs  # noqa: E402
from regimes.regimes import RegimeModel, features_at  # noqa: E402
from evaluation.alignment import hist_kl  # noqa: E402


def check_A1(scorer, dataset, n=300):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    ends = np.random.default_rng(0).choice(np.arange(a + WINDOW - 1, b), n, replace=False)
    W = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
    rng = np.random.default_rng(1)
    Wsh = np.stack([np.stack([w[rng.permutation(WINDOW), j] for j in range(W.shape[2])], 1)
                    for w in W])
    s0 = rs.score_windows(scorer, dataset, W)
    s1 = rs.score_windows(scorer, dataset, Wsh)
    tau = float(np.load(cpath(f"fa_{scorer}_{dataset}_far5.npz"))["tau"])
    return {"score_shift_median": float(np.median(s1 - s0)),
            "abs_shift_over_std": float(np.median(np.abs(s1 - s0)) / (s0.std() + 1e-12)),
            "frac_newly_above_tau": float(((s0 <= tau) & (s1 > tau)).mean())}


def check_A4(scorer, dataset, n=150):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    ends = np.random.default_rng(0).choice(np.arange(a + WINDOW - 1, b), n, replace=False)
    W = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].copy()
    D = W.shape[2]
    rng = np.random.default_rng(2)
    j = int(rng.choice(np.where(X[a:b].std(0) > 0.05)[0]))
    offs = np.linspace(0, 20, 9)
    curves = []
    for off in offs:
        W2 = W.copy(); W2[:, :, j] += off
        curves.append(rs.score_windows(scorer, dataset, W2))
    curves = np.stack(curves)                     # (n_off, n)
    mono_frac = float((np.diff(curves, axis=0) >= -1e-12).mean())
    return {"channel": j, "monotone_frac": mono_frac,
            "mean_score_curve": curves.mean(1).round(4).tolist()}


def check_boundary(dataset):
    """各 regime 的 KL(regime vs 其余) 与 regime 型 FA 的 Δ_reg 相关 (混合单元逐 k)."""
    from sklearn.ensemble import IsolationForest
    from rcca.rcca import _RegimeBank
    from evaluation.gt_pool import _mixed_unit
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    rows = []
    units = _mixed_unit(dataset)
    for u in units:
        k = u.gt_regime[0] if u.gt_regime is not None else None
        pool = u.pool_windows()
        # regime k 的特征分布: 从全正常池 (未剔除) 重新聚类拿 k 的窗
        rm = RegimeModel().fit(X, seed=0)
        tr_ends = np.arange(a + WINDOW - 1, b)
        labs = rm.transform(features_at(X, tr_ends))
        Wk = X[tr_ends[labs == k][:5000][:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
        Wo = X[tr_ends[labs != k][:5000][:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
        Fk = features_at_pool(Wk); Fo = features_at_pool(Wo)
        kl = np.mean([hist_kl(Fk[:, d], Fo[:, d], bins=20) for d in range(Fk.shape[1])])
        # Δ_reg on regime 型实例
        bank = _RegimeBank(pool, seed=0)
        rm_mask = u.gt_type == "regime"
        W = u.windows(np.where(rm_mask)[0])
        from rcca.rcca import rcca_attribute
        attr = rcca_attribute(u, W, bank)
        rows.append({"regime": int(k), "kl_mean_ch": float(kl),
                     "delta_reg_mean": float(np.mean(attr["delta"])),
                     "delta_reg_pos_frac": float((attr["delta"] > 0).mean()),
                     "n": int(rm_mask.sum())})
    return rows


def features_at_pool(P):
    Wn = P.shape[1]
    t = np.arange(Wn) - (Wn - 1) / 2.0
    return np.concatenate([P.mean(1), (P * t[None, :, None]).sum(1) / ((t ** 2).sum()),
                           P.var(1)], 1).astype(np.float64)


if __name__ == "__main__":
    import json
    out = {"A1": {}, "A4": {}, "boundary": {}}
    for scorer in ("iforest", "cmhmil"):
        for ds in ("SWaT", "SMD"):
            if (scorer, ds) == ("cmhmil", "SWaT") or True:
                try:
                    out["A1"][f"{scorer}_{ds}"] = check_A1(scorer, ds)
                    out["A4"][f"{scorer}_{ds}"] = check_A4(scorer, ds)
                    print(f"[{scorer},{ds}] A1={out['A1'][f'{scorer}_{ds}']}")
                    print(f"[{scorer},{ds}] A4={out['A4'][f'{scorer}_{ds}']}")
                except Exception as e:
                    print(f"[{scorer},{ds}] A1/A4 失败: {e}")
    for ds in ("SWaT", "SMD", "MetroPT3"):
        try:
            out["boundary"][ds] = check_boundary(ds)
            for r in out["boundary"][ds]:
                print(f"[{ds}] regime{r['regime']}: KL={r['kl_mean_ch']:.3f} "
                      f"Δ_reg_mean={r['delta_reg_mean']:.4f} pos={r['delta_reg_pos_frac']:.0%}")
        except Exception as e:
            import traceback; traceback.print_exc()
    with open(cpath("proposition_checks.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print("已写入 proposition_checks.json")
