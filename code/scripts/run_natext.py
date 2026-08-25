# -*- coding: utf-8 -*-
"""Natural-FA typing analysis extended to PSM and SMAP (cmhmil units from C1)."""
import sys, os, json
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from common import load_raw, split_of, WINDOW, cpath
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank
import evaluation.gt_pool as gp

def main():
    ext = json.load(open(cpath("cmhmil_ext.json"), encoding="utf-8"))
    out = {}
    for ds in ("PSM", "SMAP"):
        if ds not in ext or "error" in ext[ds]:
            continue
        # rebuild the cmhmil var unit to get gamma and windows
        try:
            u = gp._variable_unit("cmhmil", ds)
        except Exception as e:
            print(ds, "unit build failed:", e); continue
        if u is None or len(u.ends) < 30:
            print(ds, "insufficient"); continue
        bank = _RegimeBank(u.pool_windows(), seed=0)
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        # natural FA windows from the cmhmil fa cache
        d = np.load(cpath(f"fa_cmhmil_{ds}_far5.npz"))
        tau = float(d["tau"])
        cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
        te = np.arange(b + WINDOW - 1, len(X))
        ok = (cs[te + 1] - cs[te + 1 - WINDOW]) == 0
        tn = te[ok]
        idx = np.arange(WINDOW)[None, :] + (tn[:, None] - (WINDOW - 1))
        s = u.score(X[idx])
        fa = s > tau
        nat_idx = idx[fa]
        rng = np.random.default_rng(0)
        if len(nat_idx) > 400:
            nat_idx = nat_idx[rng.choice(len(nat_idx), 400, replace=False)]
        W_nat = X[nat_idx]
        # verdict fractions for the main methods
        res = {}
        for mn in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev"):
            try:
                W = u.windows()
                y = (u.gt_type == "variable").astype(int)
                val = u.val_mask
                attr_v = tl.METHODS[mn](u, W, bank)
                g2, d2 = tl.calibrate(tl._sub(attr_v, val), y[val])
                attr_n = tl.METHODS[mn](u, W_nat, bank)
                pred = tl._predict(attr_n, g2, d2)
                res[mn] = {"mode_frac": float((pred == 0).mean()), "n": len(W_nat)}
                print(f"{ds} {mn}: mode-frac {res[mn]['mode_frac']:.2f} (n={len(W_nat)})", flush=True)
            except Exception as e:
                res[mn] = {"error": type(e).__name__}
                print(f"{ds} {mn}: ERROR {type(e).__name__}", flush=True)
        # cross-method agreement on natural verdicts
        verd = {}
        for mn in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev"):
            if "mode_frac" in res.get(mn, {}):
                pass
        out[ds] = res
    json.dump(out, open(cpath("natural_ext.json"), "w"), indent=1)
    print("saved -> natural_ext.json")

if __name__ == "__main__":
    main()
