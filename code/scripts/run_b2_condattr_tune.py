# -*- coding: utf-8 -*-
"""B2: CondAttr neighbourhood-size tuning K in {3,5,10} on the 23 iforest mixed units.

Deterministic rebuild of the mixed units via gt_pool (same seeds as the main run);
UMAP fit once per unit, neighbour aggregation and rescoring per K.
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank
from baselines.condattr import CondAttr
import scorers_rescore as rs

RESULTS = {}

def evaluate_unit_K(unit, K):
    """CondAttr with neighbourhood size K on this unit (mirrors tl.condattr_attribute)."""
    bank = _RegimeBank(unit.pool_windows(), seed=0)
    W = unit.windows()
    n, Wn, D = W.shape

    def f(flats):
        return rs.score_windows(unit.scorer, unit.dataset,
                                flats.reshape(len(flats), Wn, -1),
                                iforest_model=unit.iforest_model)

    ca = CondAttr(f).fit(bank.P.reshape(len(bank.P), -1))
    qe = ca._reducer.transform(W.reshape(n, -1).astype(np.float32))
    dd = np.linalg.norm(ca.embed_[None] - qe[:, None], axis=2)
    nb = np.argsort(dd, 1)[:, :K]
    nb_mean = ca.db_feats_[nb].reshape(n, K, Wn, D).mean(1)

    # per-channel replacement rescoring (as in two_layer._var_replacement_scores)
    reps = [np.where(np.arange(D)[None, None, :] == j, nb_mean, W).astype(np.float32)
            for j in range(D)]
    sc = unit.score(np.concatenate(reps, 0)).reshape(D, n).T   # (n, D)
    s_orig = unit.score(W)
    drops = s_orig[:, None] - sc
    attr = {"phi": drops, "conf": drops.max(1) / (np.abs(s_orig) + 1e-9),
            "delta": None, "regime": None}

    y = (unit.gt_type == "variable").astype(int)
    val, test = unit.val_mask, ~unit.val_mask
    g, dlt = tl.calibrate(tl._sub(attr, val), y[val])
    pred = tl._predict(attr, g, dlt)
    out = {"layer1_macro_f1": tl._macro_f1(y[test], pred[test])}
    vm = test & (y == 1)
    if vm.sum() > 0:
        phi = attr["phi"][vm]
        top1 = [int(np.argsort(-phi[i])[0] in set(unit.gt_vars[gi]))
                for i, gi in enumerate(np.where(vm)[0])]
        out["layer2_top1"] = float(np.mean(top1))
        out["n_var"] = int(vm.sum())
    return out

def main():
    t0 = time.time()
    all_units = []
    for ds in ("SWaT", "SMD", "MetroPT3", "PSM", "SMAP"):
        us = gp._mixed_unit(ds)
        print(f"{ds}: {len(us)} mixed units", flush=True)
        all_units.extend(us)
    print(f"total units: {len(all_units)}  ({time.time()-t0:.0f}s)", flush=True)

    for K in (3, 5, 10):
        RESULTS[K] = {}
        for u in all_units:
            try:
                m = evaluate_unit_K(u, K)
                RESULTS[K][u.name] = m
                print(f"K={K} {u.name}: L1={m['layer1_macro_f1']:.3f} "
                      f"top1={m.get('layer2_top1', float('nan')):.3f} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:
                RESULTS[K][u.name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"K={K} {u.name}: ERROR {type(e).__name__}", flush=True)

    # pooled summary
    summary = {}
    for K, units in RESULTS.items():
        l1 = [v["layer1_macro_f1"] for v in units.values() if "layer1_macro_f1" in v]
        t1 = [v["layer2_top1"] for v in units.values() if "layer2_top1" in v]
        summary[K] = {"L1": float(np.mean(l1)), "top1": float(np.mean(t1)), "n": len(l1)}
        print(f"K={K}: L1={summary[K]['L1']:.3f} top1={summary[K]['top1']:.3f} (n={len(l1)})", flush=True)

    json.dump({"per_unit": RESULTS, "summary": summary},
              open(cpath("condattr_tuning.json"), "w", encoding="utf-8"), indent=1)
    print("saved -> condattr_tuning.json", flush=True)

if __name__ == "__main__":
    main()
