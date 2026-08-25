# -*- coding: utf-8 -*-
"""B1: window-length decoupling - iforest mixed units rebuilt at WINDOW in {16,32,64}
on SWaT and SMD (subset of regimes), evaluating counterfactual vs deviation readers.

Patches common.WINDOW BEFORE importing gt_pool so all window arithmetic follows.
"""
import sys, os, json, time

WIN = int(sys.argv[1]) if len(sys.argv) > 1 else 32
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import common
common.WINDOW = WIN                      # patch before gt_pool import
import numpy as np
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank

t0 = time.time()
out = {}
for ds in ("SWaT", "SMD"):
    units = gp._mixed_unit(ds)
    units = units[:3]                    # 3 regimes per dataset for cost control
    out[ds] = {}
    for u in units:
        try:
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            val, test = u.val_mask, ~u.val_mask
            mres = {}
            for mn in ("GlobalCF", "RC-CA", "AERec", "zDev"):
                attr = tl.METHODS[mn](u, W, bank)
                g, d = tl.calibrate(tl._sub(attr, val), y[val])
                pred = tl._predict(attr, g, d)
                m = {"layer1_macro_f1": tl._macro_f1(y[test], pred[test])}
                vm = test & (y == 1)
                if vm.sum() > 0:
                    phi = attr["phi"][vm]
                    m["layer2_top1"] = float(np.mean([
                        int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                        for i, gi in enumerate(np.where(vm)[0])]))
                mres[mn] = m
            out[ds][u.name] = mres
            t1 = {mn: round(v.get("layer2_top1", float("nan")), 3) for mn, v in mres.items()}
            print(f"win={WIN} {u.name}: top1 {t1} ({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            out[ds][u.name] = {"error": f"{type(e).__name__}: {e}"}
            print(f"win={WIN} {u.name}: ERROR {type(e).__name__}: {e}", flush=True)

json.dump(out, open(common.cpath(f"window_{WIN}.json"), "w", encoding="utf-8"), indent=1)
print(f"saved -> window_{WIN}.json  total {time.time()-t0:.0f}s", flush=True)
