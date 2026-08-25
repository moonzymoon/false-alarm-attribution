"""E2 (M2): guided 校正 > GT 校正的机制分解.
对每个变量型测试实例记录: guided通道==GT通道? GT校正是否也消除?
分解为: 一致(两者都消/都不消) vs 分歧(仅guided消 / 仅GT消 / 都不消);
并给 分歧率 与 告警边缘 的关系 (弱注入时分歧是否更多)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402


def run():
    rows = []
    for ds in ("SWaT", "SMD", "MetroPT3"):
        units = [u for u in gp._mixed_unit(ds)]
        for u in units:
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            test = ~u.val_mask & (y == 1)
            if test.sum() < 20:
                continue
            attr = rcca_attribute(u, W, bank)
            tmpl, _ = bank.knn_template(W, K=5)
            s0 = attr["s_orig"]
            margin = (s0 - u.tau) / (abs(u.tau) + 1e-12)
            top1 = np.argsort(-attr["phi"], 1)[:, 0]
            n_div, n_agree, g_only, gt_only, none_c, both_c = 0, 0, 0, 0, 0, 0
            weak_div = weak_tot = strong_div = strong_tot = 0
            for i in np.where(test)[0]:
                gt_j = u.gt_vars[i][0]
                gj = top1[i]
                res_g = res_t = None
                w2 = W[i:i + 1].copy(); w2[0, :, gj] = tmpl[i, :, gj]
                res_g = float(u.score(w2)[0] <= u.tau)
                w3 = W[i:i + 1].copy(); w3[0, :, gt_j] = tmpl[i, :, gt_j]
                res_t = float(u.score(w3)[0] <= u.tau)
                wk = margin[i] < 0.2
                if gj == gt_j:
                    n_agree += 1
                    both_c += res_g; none_c += (1 - res_g)
                else:
                    n_div += 1
                    g_only += res_g * (1 - res_t); gt_only += (1 - res_g) * res_t
                    both_c += res_g * res_t; none_c += (1 - res_g) * (1 - res_t)
                    weak_tot += wk; strong_tot += (1 - wk)
                    weak_div += wk; strong_div += (1 - wk)
                weak_tot += wk; strong_tot += (1 - wk)
            n = int(test.sum())
            rows.append({"unit": u.name, "n": n, "agree_rate": n_agree / n,
                         "diverge_rate": n_div / n,
                         "guided_only": g_only / max(n_div, 1), "gt_only": gt_only / max(n_div, 1),
                         "div_weak": weak_div / max(weak_tot, 1),
                         "div_strong": strong_div / max(strong_tot, 1)})
            print(f"{u.name}: 一致率 {n_agree/n:.0%}, 分歧中仅guided消 {g_only/max(n_div,1):.0%}, "
                  f"仅GT消 {gt_only/max(n_div,1):.0%}, 分歧率(弱/强边缘) "
                  f"{weak_div/max(weak_tot,1):.0%}/{strong_div/max(strong_tot,1):.0%}", flush=True)
    if rows:
        agg = {"agree_rate": np.mean([r["agree_rate"] for r in rows]),
               "diverge_rate": np.mean([r["diverge_rate"] for r in rows]),
               "guided_only": np.mean([r["guided_only"] for r in rows]),
               "gt_only": np.mean([r["gt_only"] for r in rows]),
               "div_weak": np.mean([r["div_weak"] for r in rows]),
               "div_strong": np.mean([r["div_strong"] for r in rows])}
        print("均值:", {k: round(float(v), 3) for k, v in agg.items()})
        json.dump({"rows": rows, "mean": agg}, open(cpath("guided_mechanism.json"), "w"),
                  ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    run()
