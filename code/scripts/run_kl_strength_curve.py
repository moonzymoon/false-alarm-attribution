"""KL 随注入强度变化曲线 (v3 必改: 对齐维度敏感性). β 扩展网格 {0.01..0.4},
分数据集报告 注入FA分数分布 vs 自然FA分数分布 的 KL(β)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, WINDOW  # noqa: E402
from injection.inject import (SEG_LEN, active_channels,  # noqa: E402
                              apply_variable_fault, eval_injected,
                              sample_normal_segments)
from evaluation.alignment import hist_kl  # noqa: E402

BETAS = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4)


def run(scorer, dataset):
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
    active = active_channels(X, a, b)
    rng = np.random.default_rng(0)
    d = np.load(cpath(f"fa_{scorer}_{dataset}_far5.npz"))
    nat = d["fa_scores"]
    tau = float(d["tau"])
    out = {}
    starts_all = sample_normal_segments(Y, b, SEG_LEN, 15, seed=99)
    for beta in BETAS:
        inj = []
        for s in starts_all:
            j = int(rng.choice(active))
            Xm, _ = apply_variable_fault(X, s, SEG_LEN, [j], "drift", beta, mu, sigma)
            ev = eval_injected(scorer, dataset, X, Xm, s, SEG_LEN, tau)
            m = ev["scores_after"] > tau
            inj.append(ev["scores_after"][m])
        inj = np.concatenate(inj) if inj else np.array([])
        out[beta] = {"kl": hist_kl(inj, nat) if len(inj) >= 10 else None,
                     "n_inj": len(inj)}
    return out


if __name__ == "__main__":
    import json
    res = {}
    for scorer, ds in (("iforest", "SWaT"), ("iforest", "MetroPT3"), ("cmhmil", "SMD")):
        print(f"[{scorer},{ds}] KL-强度曲线 ...", flush=True)
        try:
            r = run(scorer, ds)
            res[f"{scorer}_{ds}"] = r
            print("  " + "; ".join(f"β={b}: KL={v['kl'] if v['kl'] is None else round(v['kl'],3)}"
                                   f"(n={v['n_inj']})" for b, v in r.items()))
        except Exception as e:
            import traceback; traceback.print_exc()
    with open(cpath("kl_strength_curve.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
