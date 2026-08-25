# -*- coding: utf-8 -*-
"""C2 analysis: PCA/OCSVM matrix stability across construction seeds.
Compares seed-0 (original) vs seed-1000 (and later seed-2000)."""
import json
import numpy as np

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
s0 = json.load(open(C + "new_scorer_results.json", encoding="utf-8"))
s1 = json.load(open(C + "new_scorer_results_seed1000.json", encoding="utf-8"))

def pooled(d, det, metric):
    vals, names = [], []
    for k, u in d.items():
        if not k.startswith(det + "_"):
            continue
        for m, v in u.items():
            pass
    return vals, names

METHODS = ["RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"]

def table(d, det, metric="layer1_macro_f1"):
    out = {}
    for m in METHODS:
        vals = [u[m][metric] for k, u in d.items()
                if k.startswith(det + "_") and m in u
                and isinstance(u[m], dict) and u[m].get(metric) is not None]
        out[m] = float(np.mean(vals)) if vals else None
    return out

for det in ("pca", "ocsvm"):
    print(f"===== {det}: L1 (seed0 vs seed1000) =====")
    t0 = table(s0, det)
    t1 = table(s1, det)
    order0 = [m for m in sorted(t0, key=lambda x: -(t0[x] or -1))]
    order1 = [m for m in sorted(t1, key=lambda x: -(t1[x] or -1))]
    for m in METHODS:
        a, b = t0[m], t1[m]
        print(f"  {m:10s} {a if a is None else f'{a:.3f}'} -> {b if b is None else f'{b:.3f}'}"
              f"  diff={'' if (a is None or b is None) else f'{b-a:+.3f}'}")
    print("  rank seed0 :", order0[:4])
    print("  rank seed1k:", order1[:4])
    print(f"  top-3 set overlap: {len(set(order0[:3]) & set(order1[:3]))}/3")

# also top-1 stability
for det in ("pca", "ocsvm"):
    t0 = table(s0, det, "layer2_top1")
    t1 = table(s1, det, "layer2_top1")
    print(f"===== {det}: top-1 (seed0 vs seed1000) =====")
    for m in METHODS:
        a, b = t0[m], t1[m]
        if a is not None and b is not None:
            print(f"  {m:10s} {a:.3f} -> {b:.3f}  diff={b-a:+.3f}")

json.dump({"pca_L1_seed0": table(s0, "pca"), "pca_L1_seed1000": table(s1, "pca"),
           "ocsvm_L1_seed0": table(s0, "ocsvm"), "ocsvm_L1_seed1000": table(s1, "ocsvm")},
          open(C + "seed_stability_partial.json", "w", encoding="utf-8"), indent=1)
