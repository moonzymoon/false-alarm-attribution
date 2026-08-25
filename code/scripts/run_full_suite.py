"""终版全套补充实验 (审稿 M2/M3 + FAR1% 附录 + 归因-强度敏感性):
  1) FAR5% 主实验 (含 Granger 基线) -> main_results.json (覆盖, 最终版)
  2) FAR1% 鲁棒性附录 -> main_results_far1.json
  3) 归因 top1 随漂移强度 β 曲线 -> attribution_beta_curve.json
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402


def beta_curve():
    """A4: 各方法 top1 随漂移 β 的变化 (iforest×SWaT / iforest×MetroPT3)."""
    from injection.inject import (SEG_LEN, active_channels, apply_variable_fault,
                                  sample_normal_segments)
    res = {}
    for dataset in ("SWaT", "MetroPT3"):
        X, Y = load_raw(dataset)
        a, b = split_of(len(X))
        mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
        active = active_channels(X, a, b)
        tau = float(np.load(cpath(f"fa_iforest_{dataset}_far5.npz"))["tau"])
        pool_ends = np.arange(a + WINDOW - 1, b)
        if len(pool_ends) > 60000:
            pool_ends = pool_ends[np.random.default_rng(0).choice(
                len(pool_ends), 60000, replace=False)]
        bank = _RegimeBank(X[pool_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]],
                           seed=0)

        class _U:
            pass
        u = _U()
        u.scorer, u.dataset, u.iforest_model = "iforest", dataset, None
        u.score = lambda W: tl.rs.score_windows("iforest", dataset, W)
        u.name = f"beta_{dataset}"

        rng = np.random.default_rng(3)
        res[dataset] = {}
        for beta in (0.05, 0.1, 0.2, 0.4):
            Ws, js, s0s, s1s = [], [], [], []
            starts = sample_normal_segments(Y, b, SEG_LEN, 10,
                                            seed=int(beta * 1000) + 7)
            for s in starts:
                j = int(rng.choice(active))
                Xm, _ = apply_variable_fault(X, s, SEG_LEN, [j], "drift", beta, mu, sigma)
                ends = np.arange(s + WINDOW - 1, s + SEG_LEN)
                idx = np.asarray(ends)[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
                W, W0 = Xm[idx], X[idx]
                s1, s0 = u.score(W), u.score(W0)
                m = (s1 > tau) & (s0 <= tau)
                if m.sum():
                    Ws.append(W[m]); js.extend([j] * int(m.sum()))
            if not Ws:
                res[dataset][beta] = {"n": 0}
                continue
            W = np.concatenate(Ws, 0)
            js = np.array(js)
            entry = {"n": len(js)}
            for mname in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger"):
                attr = tl.METHODS[mname](u, W, bank)
                phi = attr["phi"]
                top1 = np.mean([int(np.argsort(-phi[i])[0] == js[i]) for i in range(len(js))])
                entry[mname] = round(float(top1), 3)
            res[dataset][beta] = entry
            print(f"[{dataset}] β={beta}: n={entry['n']} " +
                  " ".join(f"{m}={entry[m]}" for m in
                           ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger")), flush=True)
    import json
    with open(cpath("attribution_beta_curve.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    print("===== 1/3 FAR5% 主实验 (含 Granger) =====", flush=True)
    tl.main(far=0.05, outfile="main_results.json")
    print("\n===== 2/3 FAR1% 鲁棒性附录 =====", flush=True)
    tl.main(far=0.01, outfile="main_results_far1.json")
    print("\n===== 3/3 归因-β 敏感性 =====", flush=True)
    beta_curve()
    print("\n全部完成")
