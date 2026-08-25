# -*- coding: utf-8 -*-
"""Recompute pooled MIL column, detector-table values, and DAAS LOO over 17 pairs
after the cmhmil PSM/SMAP extension."""
import json, collections

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
d = json.load(open(C + "all_results_5det.json", encoding="utf-8"))
rg = json.load(open(C + "regimeglobal_new_scorers.json", encoding="utf-8"))
for u, mv in rg.items():
    d[u].update(mv)
ext = json.load(open(C + "cmhmil_ext.json", encoding="utf-8"))

# add the two new units in the all_results schema (top1 only)
for ds, mres in ext.items():
    if "error" in mres:
        continue
    name = f"cmhmil_{ds}_var"
    d[name] = {m: {"layer2_top1": v["top1"], "layer2_top3": v["top3"], "n_test": v["n"]}
               for m, v in mres.items() if isinstance(v, dict) and "top1" in v}
print("units now:", len(d))

# pooled MIL column per method
import statistics as st
mil = [k for k in d if k.startswith("cmhmil_")]
print("MIL units:", mil)
for m in ["RC-CA", "GlobalCF", "CondAttr", "AERec", "Grad", "Granger", "zDev", "Random"]:
    vals = [d[k][m]["layer2_top1"] for k in mil if m in d[k] and "layer2_top1" in d[k][m]]
    if vals:
        per_unit = {k.replace("cmhmil_", "").replace("_var", ""): round(d[k][m]["layer2_top1"], 3) for k in mil if m in d[k]}
        print(f"{m:10s} pooled={st.mean(vals):.3f}  per-unit={per_unit}")

# DAAS over 17 pairs
pairs = collections.defaultdict(lambda: collections.defaultdict(list))
for k, u in d.items():
    det, ds = k.split("_")[0], k.split("_")[1]
    for m, v in u.items():
        if isinstance(v, dict) and v.get("layer2_top1") is not None:
            pairs[(det, ds)][m].append(v["layer2_top1"])
tab = {p: {m: sum(v) / len(v) for m, v in mv.items()} for p, mv in pairs.items()}
best = {p: max(tab[p], key=tab[p].get) for p in tab}
CF = ["RC-CA", "GlobalCF", "CondAttr"]
TOL = 0.05
def loo(family=False):
    cs = ct = tot = 0
    for (det, ds) in sorted(tab):
        train = [p for p in tab if p[0] == det and p[1] != ds]
        if not train:
            continue
        if family:
            pred = "AERec" if det == "iforest" else max(
                CF, key=lambda m: sum(tab[p][m] for p in train if m in tab[p]) / sum(1 for p in train if m in tab[p]))
        else:
            sc = collections.defaultdict(list)
            for p in train:
                for m, v in tab[p].items():
                    sc[m].append(v)
            pred = max(sc, key=lambda m: sum(sc[m]) / len(sc[m]))
        cs += pred == best[(det, ds)]
        ct += tab[(det, ds)].get(pred, -1) >= tab[(det, ds)][best[(det, ds)]] - TOL
        tot += 1
    return cs, ct, tot
for nm, fam in [("DAAS method", False), ("family rule", True)]:
    cs, ct, tot = loo(fam)
    print(f"{nm}: strict {cs}/{tot} = {cs/tot:.2f}  tol {ct}/{tot} = {ct/tot:.2f}")
fixed = {m: (sum(best[p] == m for p in best), sum(tab[p][m] >= tab[p][best[p]] - TOL for p in tab if m in tab[p]), len(tab)) for m in ["AERec", "RC-CA", "CondAttr"]}
for m, (a, b, c) in fixed.items():
    print(f"always-{m}: strict {a}/{c} = {a/c:.2f}  tol {b}/{c} = {b/c:.2f}")
print("best per pair:", {f"{p[0]}/{p[1]}": b for p, b in sorted(best.items())})
json.dump({f"{p[0]}/{p[1]}": {m: round(v, 4) for m, v in mv.items()} for p, mv in tab.items()},
          open(C + "pairs_table_17.json", "w", encoding="utf-8"), indent=1)
