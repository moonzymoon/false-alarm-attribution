# -*- coding: utf-8 -*-
"""C2 final analysis: 3-seed stability of the PCA/OCSVM matching matrix."""
import json
import numpy as np

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
s0 = json.load(open(C + "new_scorer_results.json", encoding="utf-8"))
s1 = json.load(open(C + "new_scorer_results_seed1000.json", encoding="utf-8"))
s2 = json.load(open(C + "new_scorer_results_seed2000.json", encoding="utf-8"))
METHODS = ["RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"]

def pooled(d, det, metric):
    out = {}
    for m in METHODS:
        vals = [u[m][metric] for k, u in d.items()
                if k.startswith(det + "_") and m in u
                and isinstance(u[m], dict) and u[m].get(metric) is not None]
        out[m] = float(np.mean(vals)) if vals else None
    return out

report = {}
for det in ("pca", "ocsvm"):
    for metric, label in [("layer2_top1", "top1"), ("layer1_macro_f1", "L1")]:
        t0, t1, t2 = pooled(s0, det, metric), pooled(s1, det, metric), pooled(s2, det, metric)
        print(f"===== {det} {label} (seed0 / seed1000 / seed2000) =====")
        for m in METHODS:
            a, b, c = t0[m], t1[m], t2[m]
            if a is None:
                continue
            swing = max(a, b, c) - min(a, b, c)
            print(f"  {m:10s} {a:.3f} / {b:.3f} / {c:.3f}   swing={swing:.3f}")
            report[f"{det}_{label}_{m}"] = [a, b, c, swing]
        # best method per seed
        bests = [max(t, key=lambda m: t[m] or -1) for t in (t0, t1, t2)]
        print(f"  best per seed: {bests}")
        report[f"{det}_{label}_best"] = bests

json.dump(report, open(C + "seed_stability_3seed.json", "w", encoding="utf-8"), indent=1)
print("\nsaved -> seed_stability_3seed.json")
