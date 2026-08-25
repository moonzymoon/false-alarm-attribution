# -*- coding: utf-8 -*-
"""A2: Wilcoxon signed-rank tests + effect sizes across the 23 iforest mixed units."""
import json
import numpy as np
from scipy import stats

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
d = json.load(open(C + "all_results_5det.json", encoding="utf-8"))
units = sorted([k for k in d if k.startswith("iforest_") and "_mix" in k])
print(f"iforest mixed units: {len(units)}")

def cliffs_delta(x, y):
    gt = sum((a > b) for a in x for b in y)
    lt = sum((a < b) for a in x for b in y)
    return (gt - lt) / (len(x) * len(y))

PAIRS = [
    ("AERec", "GlobalCF", "layer2_top1"),
    ("AERec", "CondAttr", "layer2_top1"),
    ("AERec", "zDev", "layer2_top1"),
    ("AERec", "GlobalCF", "layer1_macro_f1"),
    ("RegimeGlobal", "GlobalCF", "layer1_macro_f1"),
    ("CondAttr", "GlobalCF", "layer2_top1"),
    ("RC-CA", "GlobalCF", "layer2_top1"),
]
out = {}
for a, b, metric in PAIRS:
    xa = np.array([d[u][a][metric] for u in units if metric in d[u][a]])
    xb = np.array([d[u][b][metric] for u in units if metric in d[u][b]])
    n = len(xa)
    diff = xa - xb
    nz = diff[diff != 0]
    if len(nz) < 5:
        continue
    w, p = stats.wilcoxon(xa, xb, zero_method="wilcox", alternative="two-sided")
    cd = cliffs_delta(xa, xb)
    out[f"{a}|{b}|{metric.split('_')[-1]}"] = {
        "n": n, "mean_diff": float(diff.mean()), "wilcoxon_W": float(w), "p": float(p),
        "cliffs_delta": float(cd), "wins": int((diff > 0).sum()), "losses": int((diff < 0).sum()),
    }
    print(f"{a:13s} vs {b:13s} [{metric:16s}] diff={diff.mean():+.3f} "
          f"p={p:.4f} cliff_delta={cd:+.2f} W/L={int((diff>0).sum())}/{int((diff<0).sum())}")

json.dump(out, open(C + "wilcoxon_tests.json", "w", encoding="utf-8"), indent=1)
print("\nsaved -> wilcoxon_tests.json")
