# -*- coding: utf-8 -*-
"""C1-lite: extend the deep-MIL detector's variable-level coverage to PSM and SMAP
using existing checkpoints (no training). Steps per dataset:
1. collect_fa('cmhmil', ds) -> tau at FAR5 (cache npz)
2. gt_pool._variable_unit('cmhmil', ds) -> injection-caused FA windows
3. evaluate all applicable methods (incl. Grad: cmhmil is differentiable)
"""
import sys, os, json, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath
from fa_collection.collect import collect_fa, collect_all  # noqa
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank
import numpy as np

def main():
    t0 = time.time()
    out = {}
    for ds in ("PSM", "SMAP"):
        try:
            print(f"[C1] collect_fa cmhmil x {ds} ...", flush=True)
            collect_fa("cmhmil", ds)
        except Exception as e:
            print(f"  collect_fa failed: {type(e).__name__}: {e}", flush=True)
            continue
        try:
            u = gp._variable_unit("cmhmil", ds)
            if u is None or len(u.ends) < 30:
                print(f"  {ds}: insufficient instances", flush=True)
                continue
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            val, test = u.val_mask, ~u.val_mask
            mres = {}
            for mn in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Grad", "Granger", "zDev", "Random"):
                try:
                    attr = tl.METHODS[mn](u, W, bank)
                    g, d = tl.calibrate(tl._sub(attr, val), y[val])
                    pred = tl._predict(attr, g, d)
                    m = {"layer2_top1": None}
                    vm = test & (y == 1)
                    phi = attr["phi"][vm]
                    top1 = [int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                            for i, gi in enumerate(np.where(vm)[0])]
                    top3 = [int(len(set(np.argsort(-phi[i])[:3]) & set(u.gt_vars[gi])) > 0)
                            for i, gi in enumerate(np.where(vm)[0])]
                    m = {"top1": float(np.mean(top1)), "top3": float(np.mean(top3)),
                         "n": int(vm.sum())}
                    mres[mn] = m
                    print(f"  {ds} {mn}: top1={m['top1']:.3f} top3={m['top3']:.3f} n={m['n']}", flush=True)
                except Exception as e:
                    mres[mn] = {"error": f"{type(e).__name__}"}
                    print(f"  {ds} {mn}: ERROR {type(e).__name__}", flush=True)
            out[ds] = mres
            print(f"[C1] {ds} done ({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            out[ds] = {"error": f"{type(e).__name__}: {e}"}
            print(f"  {ds} unit build failed: {e}", flush=True)

    json.dump(out, open(cpath("cmhmil_ext.json"), "w", encoding="utf-8"), indent=1)
    print("saved -> cmhmil_ext.json", flush=True)

if __name__ == "__main__":
    main()
