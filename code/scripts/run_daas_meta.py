# -*- coding: utf-8 -*-
"""A4: feature-driven method selector (meta-learning over 15 detector-dataset pairs)."""
import json, collections
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

C = r"D:\0科研\工作1\第10篇SCI\src\_cache" + "\\"
d = json.load(open(C + "all_results_5det.json", encoding="utf-8"))
rg = json.load(open(C + "regimeglobal_new_scorers.json", encoding="utf-8"))
for u, mv in rg.items():
    d[u].update(mv)

pairs = collections.defaultdict(lambda: collections.defaultdict(list))
for k, u in d.items():
    det, ds = k.split("_")[0], k.split("_")[1]
    for m, v in u.items():
        if isinstance(v, dict) and v.get("layer2_top1") is not None:
            pairs[(det, ds)][m].append(v["layer2_top1"])
tab = {p: {m: sum(v) / len(v) for m, v in mv.items()} for p, mv in pairs.items()}
best = {p: max(tab[p], key=tab[p].get) for p in tab}

META = {"SWaT": (51, 288000), "SMD": (38, 1400000), "MetroPT3": (15, 3000000),
        "PSM": (25, 220000), "SMAP": (25, 563000)}
DETS = ["iforest", "pca", "ocsvm", "AT", "cmhmil"]

def feats(det, ds):
    ch, ln = META[ds]
    return np.array([1.0 if x == det else 0.0 for x in DETS] + [ch / 51.0, np.log10(ln) / 7.0])

items = sorted(tab.keys())
X = np.stack([feats(*p) for p in items])
methods = sorted({b for b in best.values()})   # label space
y = np.array([methods.index(best[p]) for p in items])
print("label space:", methods)
print("labels:", [f"{p[0]}/{p[1]}->{best[p]}" for p in items])

def loo_acc(model_fn):
    correct = tol = 0
    for i in range(len(items)):
        mask = np.ones(len(items), bool); mask[i] = False
        clf = model_fn()
        clf.fit(StandardScaler().fit(X[mask]).transform(X[mask]), y[mask])
        pred = methods[int(clf.predict(StandardScaler().fit(X[mask]).transform(X[i:i+1]))[0])]
        ok = pred == best[items[i]]
        tol_ok = tab[items[i]].get(pred, -1) >= tab[items[i]][best[items[i]]] - 0.05
        correct += ok; tol += tol_ok
    return correct, tol

for name, fn in [
    ("LogisticRegression", lambda: LogisticRegression(max_iter=5000, C=0.5)),
    ("RandomForest(depth2)", lambda: RandomForestClassifier(n_estimators=200, max_depth=2, random_state=0)),
    ("KNN-1", lambda: KNeighborsClassifier(n_neighbors=1)),
]:
    c, t = loo_acc(fn)
    print(f"{name:22s} LOO strict {c}/15 = {c/15:.0%}, tol0.05 {t}/15 = {t/15:.0%}")
print("reference: table DAAS/family rule = 7/15 strict, 11/15 tol")
json.dump({"methods": methods, "labels": {f"{p[0]}/{p[1]}": best[p] for p in items}},
          open(C + "daas_meta_features.json", "w", encoding="utf-8"), indent=1)
