"""牌2 DAAS-v2: 代价感知选择(LOO按检测器, λ扫描Pareto) + LOO保形覆盖(regret上界).

数据: pairs_table_19.json (19对×9方法 mean top1) + runtime_timing.json (ms/窗口).
输出: _cache/daas_v2.json + paper/fig_daas_pareto.pdf
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

PT = json.load(open(cpath("pairs_table_19.json"), encoding="utf-8"))
RT = json.load(open(cpath("runtime_timing.json"), encoding="utf-8"))
# 补全 cmhmil/PSM 与 cmhmil/SMAP (pairs_table_19 只有 SHAP 列; 其余方法来自 cmhmil_ext)
CE = json.load(open(cpath("cmhmil_ext.json"), encoding="utf-8"))
for ds in ("PSM", "SMAP"):
    for m, v in CE[ds].items():
        PT[f"cmhmil/{ds}"][m] = v["top1"]
METHODS = ["RC-CA", "GlobalCF", "RegimeGlobal", "CondAttr", "AERec", "Granger", "zDev", "SHAP"]

cost = {m: [] for m in METHODS}
for ds, rec in RT.items():
    for m in METHODS:
        if m in rec:
            cost[m].append(rec[m]["ms_per_window"])
COST = {m: (float(np.mean(v)) if v else 3.0 * RT["SWaT"]["CondAttr"]["ms_per_window"])
        for m, v in cost.items()}
print("cost ms/window:", {m: round(c, 2) for m, c in COST.items()})

pairs = list(PT.keys())
det_of = lambda p: p.split("/")[0]


def loo_pick(lam):
    """对每对留出: 同检测器其余对(缺该对不含的方法), 选 mean(top1 - lam*cost) 最大者."""
    sel = {}
    for p in pairs:
        tr = [q for q in pairs if q != p and det_of(q) == det_of(p)]
        if not tr:
            tr = [q for q in pairs if q != p]
        cands = [m for m in METHODS if m in PT[p]]
        scores = {}
        for m in cands:
            vals = [PT[q][m] - lam * COST[m] for q in tr if m in PT[q]]
            scores[m] = np.mean(vals) if vals else -1e9
        sel[p] = max(scores, key=scores.get)
    return sel

lams = np.concatenate([[0.0], np.geomspace(1e-4, 10.0, 25)])
curve = []
for lam in lams:
    sel = loo_pick(float(lam))
    acc = float(np.mean([PT[p][sel[p]] for p in pairs]))
    c = float(np.mean([COST[sel[p]] for p in pairs]))
    curve.append({"lam": float(lam), "top1": acc, "cost_ms": c, "sel": sel})
print("λ=0 (纯精度=DAAS方法级): top1=%.3f" % curve[0]["top1"])

# 固定方法参考点
fixed = {m: {"top1": float(np.mean([PT[p][m] for p in pairs if m in PT[p]])),
             "cost_ms": COST[m]} for m in METHODS}
bestm = max(METHODS, key=lambda m: fixed[m]["top1"])
fixed["best_single"] = {"top1": fixed[bestm]["top1"], "cost_ms": COST[bestm], "method": bestm}

# ---- LOO 保形 (regret = pair最优 - 推荐): 对19个LOO regret做留一覆盖率 ----
sel0 = loo_pick(0.0)
regret = np.array([max(PT[p].values()) - PT[p][sel0[p]] for p in pairs])
conf = {}
for alpha in (0.1, 0.2, 0.3):
    cover, qs = 0, []
    for i in range(len(regret)):
        others = np.delete(regret, i)
        q = float(np.quantile(others, 1 - alpha))
        qs.append(q)
        if regret[i] <= q + 1e-12:
            cover += 1
    conf[f"alpha={alpha}"] = {"coverage": cover / len(regret),
                              "q_typical": float(np.median(qs))}
print("LOO regret: mean %.3f median %.3f max %.3f" %
      (regret.mean(), np.median(regret), regret.max()))
print("conformal:", conf)

json.dump({"curve": curve, "fixed": fixed, "conformal": conf,
           "regret_loo": [float(x) for x in regret],
           "cost_ms": COST},
          open(cpath("daas_v2.json"), "w", encoding="utf-8"), indent=1)

# ---- Pareto 图 ----
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(4.6, 3.2))
xs = [c["cost_ms"] for c in curve]
ys = [c["top1"] for c in curve]
ax.plot(xs, ys, "o-", ms=3, lw=1.2, color="#333333", label="DAAS-v2 ($\\lambda$ sweep)")
for m in METHODS:
    if m in ("Granger", "Random"):
        continue
    ax.scatter([fixed[m]["cost_ms"]], [fixed[m]["top1"]], marker="x", s=28, color="#888888")
    ax.annotate(m, (fixed[m]["cost_ms"], fixed[m]["top1"]), fontsize=6,
                xytext=(3, 3), textcoords="offset points", color="#555555")
ax.set_xscale("log")
ax.set_xlabel("attribution cost (ms per window, log scale)")
ax.set_ylabel("mean variable-type top-1 (19 pairs)")
ax.legend(fontsize=7, loc="lower right")
ax.grid(alpha=0.25, lw=0.4)
fig.tight_layout()
out = os.path.normpath(os.path.join(cpath(".."), "..", "paper", "fig_daas_pareto.pdf"))
fig.savefig(out)
print("figure ->", out)
