# -*- coding: utf-8 -*-
"""B3: per-method runtime on fixed query batches (3 iforest units x 100 windows).
Reports wall-clock seconds per 100 windows and per window, plus scorer-call counts.
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank

def timed(fn, unit, W, bank, reps=3):
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn(unit, W, bank)
        ts.append(time.perf_counter() - t0)
    return float(np.median(ts))

def main():
    out = {}
    for ds in ("SWaT", "SMD", "MetroPT3"):
        u = gp._mixed_unit(ds)[0]
        bank = _RegimeBank(u.pool_windows(), seed=0)
        W = u.windows()[:100]
        d = W.shape[2]
        out[ds] = {"channels": int(d), "windows": 100}
        for mn in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"):
            try:
                t = timed(tl.METHODS[mn], u, W, bank)
                scorer_calls = {"RC-CA": d + 2, "GlobalCF": d + 1, "CondAttr": d + 1,
                                "AERec": 1, "Granger": 1, "zDev": 0, "Random": 0}.get(mn, 1)
                out[ds][mn] = {"sec_per_100win": round(t, 3),
                               "ms_per_window": round(t * 10, 2),
                               "scorer_calls_per_window": scorer_calls}
                print(f"{ds:9s} {mn:10s} {t:7.2f}s/100win  {t*10:6.2f} ms/win  calls={scorer_calls}", flush=True)
            except Exception as e:
                out[ds][mn] = {"error": f"{type(e).__name__}"}
                print(f"{ds} {mn}: ERROR {type(e).__name__}", flush=True)
    json.dump(out, open(cpath("runtime_timing.json"), "w", encoding="utf-8"), indent=1)
    print("saved -> runtime_timing.json", flush=True)

if __name__ == "__main__":
    main()
