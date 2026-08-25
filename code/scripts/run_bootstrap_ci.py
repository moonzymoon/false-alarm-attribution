"""主表 bootstrap 置信区间 + 配对显著性 (审稿意见 M2).
对 14 个混合评估单元做有放回重采样 (B=2000):
  - 每方法: L1 宏F1 / top1 / top3 / var_R / reg_R 的均值 95% CI;
  - 配对差: RC-CA−GlobalCF, CondAttr−GlobalCF, AERec−GlobalCF, AERec−CondAttr
    (同一重采样单元子集上计算, CI 不含 0 即显著).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

B = 2000
METRICS = ["layer1_macro_f1", "layer2_top1", "layer2_top3", "var_recall", "reg_recall"]
PAIRS = [("RC-CA", "GlobalCF"), ("CondAttr", "GlobalCF"),
         ("AERec", "GlobalCF"), ("AERec", "CondAttr"), ("RC-CA", "CondAttr")]


def main():
    r = json.load(open(cpath("main_results.json"), encoding="utf-8"))
    units = [u for u in r if "_mix_" in u]
    rng = np.random.default_rng(0)
    methods = sorted({m for u in units for m in r[u] if "error" not in r[u][m]})
    # 数据矩阵: (n_units,) per (method, metric)
    data = {(m, k): np.array([r[u][m].get(k, np.nan) for u in units
                              if "error" not in r[u][m]]) for m in methods for k in METRICS}
    n = len(units)
    out = {"n_units": n, "B": B, "ci": {}, "paired": {}}
    # bootstrap 均值分布
    boots = {}
    idx = rng.integers(0, n, size=(B, n))
    for m in methods:
        out["ci"][m] = {}
        for k in METRICS:
            arr = data[(m, k)]
            if np.all(np.isnan(arr)):
                continue
            bm = np.array([np.nanmean(arr[i]) for i in idx])
            boots[(m, k)] = bm
            out["ci"][m][k] = {"mean": float(np.nanmean(arr)),
                               "lo": float(np.nanpercentile(bm, 2.5)),
                               "hi": float(np.nanpercentile(bm, 97.5))}
    # 配对差 (L1 与 top1)
    for a, b in PAIRS:
        out["paired"][f"{a}-{b}"] = {}
        for k in ("layer1_macro_f1", "layer2_top1"):
            da, db = data[(a, k)], data[(b, k)]
            diffs = da - db
            bd = np.array([np.nanmean(diffs[i]) for i in idx])
            out["paired"][f"{a}-{b}"][k] = {
                "mean_diff": float(np.nanmean(diffs)),
                "lo": float(np.nanpercentile(bd, 2.5)),
                "hi": float(np.nanpercentile(bd, 97.5)),
                "significant": bool(np.nanpercentile(bd, 2.5) > 0 or np.nanpercentile(bd, 97.5) < 0)}
    with open(cpath("bootstrap_ci.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)
    print(f"n_units={n}, B={B}")
    print("== 各方法 L1 宏F1: mean [95% CI] ==")
    for m in methods:
        c = out["ci"][m].get("layer1_macro_f1")
        t = out["ci"][m].get("layer2_top1")
        if c:
            print(f"  {m:13s}: L1 {c['mean']:.3f} [{c['lo']:.3f},{c['hi']:.3f}]  "
                  f"top1 {t['mean']:.3f} [{t['lo']:.3f},{t['hi']:.3f}]" if t else "")
    print("== 配对差 (显著=CI 不含 0) ==")
    for p, v in out["paired"].items():
        for k, s in v.items():
            print(f"  {p:22s} {k:16s}: {s['mean_diff']:+.3f} [{s['lo']:+.3f},{s['hi']:+.3f}] "
                  f"{'*显著*' if s['significant'] else '不显著'}")


def hierarchical_bootstrap():
    """E5: 两级 (单元->窗口) 分层 bootstrap 的 pooled top-1 CI."""
    r = json.load(open(cpath("main_results.json"), encoding="utf-8"))
    mix = [u for u in r if "_mix_" in u]
    rng = np.random.default_rng(2)
    print("== 两级 bootstrap pooled top-1 ==")
    out = {}
    for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev"):
        units_hits = [np.array(r[u][m]["layer2_hits_top1"]) for u in mix
                      if r[u].get(m, {}).get("layer2_hits_top1")]
        if not units_hits:
            continue
        bm = []
        for _ in range(2000):
            us = rng.choice(len(units_hits), len(units_hits))
            pooled = np.concatenate([units_hits[i] if len(units_hits[i]) else np.array([0])
                                     for i in us])
            bm.append(pooled[rng.integers(0, len(pooled), len(pooled))].mean())
        pooled_all = np.concatenate(units_hits).mean()
        out[m] = {"top1": float(pooled_all), "lo": float(np.percentile(bm, 2.5)),
                  "hi": float(np.percentile(bm, 97.5))}
        print(f"  {m}: {pooled_all:.3f} [{np.percentile(bm,2.5):.3f},{np.percentile(bm,97.5):.3f}]")
    json.dump(out, open(cpath("hier_bootstrap.json"), "w"))


def window_bootstrap():
    """变量级单元 (cmhmil/AT) 的窗口级 bootstrap CI (回应小样本质疑, esp. AT n=54)."""
    r = json.load(open(cpath("main_results.json"), encoding="utf-8"))
    rng = np.random.default_rng(1)
    print("== 窗口级 bootstrap (变量级单元, B=2000) ==")
    out = {}
    for u in [x for x in r if x.endswith("_var")]:
        out[u] = {}
        for m, v in r[u].items():
            hits = v.get("layer2_hits_top1")
            if not hits or "error" in v:
                continue
            h = np.array(hits)
            bm = np.array([h[rng.integers(0, len(h), len(h))].mean() for _ in range(2000)])
            out[u][m] = {"top1": float(h.mean()),
                         "lo": float(np.percentile(bm, 2.5)),
                         "hi": float(np.percentile(bm, 97.5))}
            print(f"  {u} {m}: top1={h.mean():.3f} [{np.percentile(bm,2.5):.3f},{np.percentile(bm,97.5):.3f}]")
    import os
    p = cpath("window_bootstrap.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
    window_bootstrap()
    hierarchical_bootstrap()
