"""自然误报案例研究 (R2, v3 要求的 10-20 窗定性案例, 机器辅助).
对 iforest×SWaT FAR5% 的自然误报事件取 top 20 (按事件分数峰值排序, 事件间隔去重),
跑 RC-CA 归因, 报告: 判定类型 / top-3 变量 / Δ_reg / regime / 细分类型 + 事件上下文.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, WINDOW  # noqa: E402
import scorers_rescore as rs  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402


def main(scorer="iforest", dataset="SWaT", n_events=20, outfile="natural_cases.json"):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    d = np.load(cpath(f"fa_{scorer}_{dataset}_far5.npz"))
    idx, scores, tau = d["fa_idx"], d["fa_scores"], float(d["tau"])
    # 事件分组 (gap>5), 每事件取峰值窗
    brk = np.where(np.diff(idx) > 5)[0] + 1
    segs = np.split(np.arange(len(idx)), brk)
    events = sorted(segs, key=lambda s: -scores[s].max())[:n_events]
    peak_idx = np.array([idx[s[np.argmax(scores[s])]] for s in events])
    peak_sc = np.array([scores[s].max() for s in events])

    pool_ends = np.arange(a + WINDOW - 1, b)
    if len(pool_ends) > 60000:
        pool_ends = pool_ends[np.random.default_rng(0).choice(len(pool_ends), 60000, replace=False)]
    bank = _RegimeBank(X[pool_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]], seed=0)

    class _U:  # 轻量 unit 适配 rcca_attribute
        pass
    u = _U()
    u.scorer, u.dataset, u.iforest_model = scorer, dataset, None
    u.score = lambda W: rs.score_windows(scorer, dataset, W)

    W = X[peak_idx[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
    attr = rcca_attribute(u, W, bank)
    # 决策阈值示意: 用 conf/delta 分布中位数作非标定参考 (自然 FA 无真值, 只作定性)
    conf, delta = attr["conf"], attr["delta"]
    rows = []
    for i in range(len(peak_idx)):
        top3 = np.argsort(-attr["phi"][i])[:3]
        regime_like = (delta[i] > np.median(delta)) and (conf[i] < np.median(conf))
        rows.append({"event": i, "peak_end": int(peak_idx[i]), "score": float(peak_sc[i]),
                     "top3_vars": top3.tolist(), "delta_reg": float(delta[i]),
                     "conf": float(conf[i]), "regime": int(attr["regime"][i]),
                     "subtype": attr["subtype"][i] if not regime_like else None,
                     "verdict": "regime-like" if regime_like else "variable-like"})
    import json
    with open(cpath(outfile), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1, default=float)
    n_regime = sum(r["verdict"] == "regime-like" for r in rows)
    print(f"自然误报 top{n_events} 事件: regime-like {n_regime} / variable-like {len(rows)-n_regime}")
    for r in rows[:10]:
        print(f"  E{r['event']:02d} score={r['score']:.3f} {r['verdict']:12s} "
              f"top3={r['top3_vars']} Δ={r['delta_reg']:.4f} sub={r['subtype']}")
    return rows


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2], outfile=f"natural_cases_{sys.argv[1]}_{sys.argv[2]}.json")
    else:
        main()
