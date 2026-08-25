"""分布对齐 sanity check (阶段1 任务4): 注入 FA vs 自然 FA.

- 分数分布 KL: 直方图 KL (分位数分箱), 每数据集汇总 (诊断用, 不设硬阈值);
- 窗口特征空间 MMD (RBF, 中值启发式带宽): 3D 手工特征 (均值/斜率/方差).
方案 v3: KL<0.3 降格为 sanity check, 维度扩到 MMD.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, FAR_TARGETS, WINDOW  # noqa: E402
from injection.inject import (SEG_LEN, active_channels,  # noqa: E402
                              apply_variable_fault, eval_injected,
                              sample_normal_segments)
import scorers_rescore as rs  # noqa: E402
from regimes.regimes import features_at  # noqa: E402


def hist_kl(p, q, bins=20):
    """直方图 KL(P||Q) (分位数分箱基于合并样本, 加 eps 平滑)."""
    edges = np.quantile(np.concatenate([p, q]), np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    hp, _ = np.histogram(p, edges)
    hq, _ = np.histogram(q, edges)
    hp = hp / hp.sum() + 1e-6
    hq = hq / hq.sum() + 1e-6
    return float(np.sum(hp * np.log(hp / hq)))


def mmd_rbf(A, B, n=2000, seed=0):
    """RBF-MMD^2 (中值启发式带宽, 子采样 n)."""
    rng = np.random.default_rng(seed)
    A = A[rng.choice(len(A), min(n, len(A)), replace=False)]
    B = B[rng.choice(len(B), min(n, len(B)), replace=False)]
    Z = np.vstack([A, B])
    d2 = ((Z[:, None] - Z[None]) ** 2).sum(-1)
    gamma = 1.0 / np.median(d2[d2 > 0])
    K = np.exp(-gamma * d2)
    na, nb = len(A), len(B)
    kAA = K[:na, :na].sum() - na
    kBB = K[na:, na:].sum() - nb
    kAB = K[:na, na:].sum()
    return float(kAA / (na * (na - 1)) + kBB / (nb * (nb - 1)) - 2 * kAB / (na * nb))


def run(scorer, dataset, n_trials=10, seed=0):
    """对一个组合: 采集注入 FA 的 (分数, 窗口特征) vs 自然 FA, 返回 KL/MMD."""
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
    active = active_channels(X, a, b)
    rng = np.random.default_rng(seed)
    out = {}
    for target in FAR_TARGETS:
        d = np.load(cpath(f"fa_{scorer}_{dataset}_far{int(target*100)}.npz"))
        nat_scores = d["fa_scores"]
        nat_idx = d["fa_idx"]
        tau = float(d["tau"])
        # 注入 FA 采集 (drift@0.2 / stuck / var@5 三配置)
        inj_scores, inj_ends = [], []
        starts = sample_normal_segments(Y, b, SEG_LEN, n_trials, seed=seed + 1)
        for kind, st in (("drift", 0.2), ("stuck", 1.0), ("var", 5.0)):
            for s in starts:
                j = int(rng.choice(active))
                Xm, gt = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
                ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, tau)
                m = ev["scores_after"] > tau
                inj_scores.append(ev["scores_after"][m])
                inj_ends.append(ev["ends"][m])
        inj_scores = np.concatenate(inj_scores) if inj_scores else np.array([])
        inj_ends = np.concatenate(inj_ends) if inj_ends else np.array([], int)
        if len(inj_scores) < 10 or len(nat_scores) < 10:
            out[target] = {"kl": None, "mmd": None,
                           "n_inj": len(inj_scores), "n_nat": len(nat_scores)}
            continue
        # 特征 MMD
        rng2 = np.random.default_rng(seed)
        nat_sample = nat_idx[rng2.choice(len(nat_idx), min(2000, len(nat_idx)), replace=False)]
        F_nat = features_at(X, nat_sample)
        F_inj = features_at(X, inj_ends[:2000])
        out[target] = {"kl": hist_kl(inj_scores, nat_scores),
                       "mmd": mmd_rbf(F_inj, F_nat),
                       "n_inj": len(inj_scores), "n_nat": len(nat_scores)}
    return out


if __name__ == "__main__":
    import json
    res = {}
    for scorer in ("iforest", "cmhmil"):
        for ds in ("SWaT", "SMD", "MetroPT3"):
            if (scorer, ds) == ("cmhmil", "MetroPT3"):
                continue
            print(f"[{scorer},{ds}] 分布对齐 ...", flush=True)
            try:
                r = run(scorer, ds)
                res[f"{scorer}_{ds}"] = r
                for t, v in r.items():
                    print(f"  FAR{t:.0%}: KL={v['kl'] if v['kl'] is None else round(v['kl'],3)} "
                          f"MMD={v['mmd'] if v['mmd'] is None else round(v['mmd'],4)} "
                          f"(n_inj={v['n_inj']}, n_nat={v['n_nat']})")
            except Exception as e:
                import traceback; traceback.print_exc()
                res[f"{scorer}_{ds}"] = {"error": str(e)}
    with open(cpath("alignment_report.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
