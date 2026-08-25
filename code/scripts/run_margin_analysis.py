"""边缘分层分析 (R2): AERec 的优势是否由"强注入"驱动?
将变量型测试实例按 FA 边缘 (s(w)−τ)/τ 分层: 低边缘(<20%, 弱注入) vs 高边缘(>=20%),
分方法报告 top-1. 若 AERec 优势集中在高边缘层, 则其收益来自输入偏差幅度而非归因机制.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import scorers_rescore as rs  # noqa: E402


def main():
    import json
    from evaluation.gt_pool import build_all
    units = [u for u in build_all() if "_mix_" in u.name]
    methods = {"RC-CA": tl.METHODS["RC-CA"], "GlobalCF": tl.METHODS["GlobalCF"],
               "CondAttr": tl.METHODS["CondAttr"], "AERec": tl.METHODS["AERec"]}
    res = {}
    for u in units:
        bank = _RegimeBank(u.pool_windows(), seed=0)
        W = u.windows()
        y = (u.gt_type == "variable").astype(int)
        test = ~u.val_mask
        s_orig = u.score(W)
        margin = (s_orig - u.tau) / (abs(u.tau) + 1e-12)
        strat = np.where(margin < 0.2, "low", "high")
        res[u.name] = {}
        for mname, fn in methods.items():
            attr = fn(u, W, bank)
            rec = {}
            for st in ("low", "high"):
                m = test & (y == 1) & (strat == st)
                if m.sum() < 5:
                    continue
                phi = attr["phi"][m]
                hits = [int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                        for i, gi in enumerate(np.where(m)[0])]
                rec[st] = {"n": int(m.sum()), "top1": float(np.mean(hits))}
            res[u.name][mname] = rec
        line = f"{u.name}: "
        for mname in methods:
            lo = res[u.name][mname].get("low", {})
            hi = res[u.name][mname].get("high", {})
            line += (f"{mname} low={lo.get('top1', float('nan')):.2f}(n={lo.get('n',0)}) "
                     f"high={hi.get('top1', float('nan')):.2f} | ")
        print(line, flush=True)
    # 汇总
    print("\n== 跨单元汇总 ==")
    for mname in methods:
        lo = [res[u][mname]["low"]["top1"] for u in res
              if "low" in res[u][mname] and res[u][mname]["low"].get("n", 0) >= 5]
        hi = [res[u][mname]["high"]["top1"] for u in res
              if "high" in res[u][mname] and res[u][mname]["high"].get("n", 0) >= 5]
        print(f"  {mname:10s}: 低边缘 top1={np.mean(lo) if lo else float('nan'):.3f} "
              f"(n单元={len(lo)}), 高边缘 top1={np.mean(hi) if hi else float('nan'):.3f} (n单元={len(hi)})")
    with open(cpath("margin_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
