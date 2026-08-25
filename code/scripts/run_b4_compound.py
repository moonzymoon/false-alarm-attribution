# -*- coding: utf-8 -*-
"""B4: compound-cause stress test - 3-channel correlated covariance shift injected
on process-normal test regions (no mean shift). Methods must rank any of the 3
perturbed channels. Run on iforest mixed-unit rebuilds (SWaT r1/r2, SMD r1/r2,
MetroPT3 r1/r3).
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank
from injection.inject import SEG_LEN, active_channels, sample_normal_segments

def covshift(X, s, L, js, c, mu, sigma, rng):
    """3-channel correlated noise: z (L,3) -> js get c*sigma_j * correlated noise."""
    Xm = X.copy()
    r = np.array([[1.0, 0.6, 0.3], [0.6, 1.0, 0.6], [0.3, 0.6, 1.0]])
    A = np.linalg.cholesky(r)
    z = rng.standard_normal((L, 3)) @ A.T          # correlated columns
    for idx, j in enumerate(js):
        Xm[s:s + L, j] += c * sigma[j] * z[:, idx]
    return Xm

def main():
    t0 = time.time()
    out = {}
    for ds, keep in (("SWaT", 2), ("SMD", 2), ("MetroPT3", 2)):
        units = gp._mixed_unit(ds)[:keep]
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
        active = active_channels(X, a, b)
        rng = np.random.default_rng(11)
        out[ds] = {}
        for u in units:
            try:
                bank = _RegimeBank(u.pool_windows(), seed=0)
                # inject covshift segments; keep injection-caused windows
                Ws, gts, s0s, s1s = [], [], [], []
                for s in sample_normal_segments(Y, b, SEG_LEN, 10, seed=777):
                    js = [int(j) for j in rng.choice(active, size=3, replace=False)]
                    Xm = covshift(X, s, SEG_LEN, js, 2.0, mu, sigma, rng)
                    ends = np.arange(s + WINDOW - 1, s + SEG_LEN)
                    idx = ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
                    sa = u.score(Xm[idx]); sb = u.score(X[idx])
                    m = (sa > u.tau) & (sb <= u.tau)
                    if m.sum():
                        Ws.append(Xm[idx][m]); gts.extend([set(js)] * int(m.sum()))
                if not Ws:
                    out[ds][u.name] = {"n": 0}
                    continue
                Wc = np.concatenate(Ws, 0)
                mres = {"n": len(Wc)}
                for mn in ("GlobalCF", "RC-CA", "AERec", "zDev", "Random"):
                    attr = tl.METHODS[mn](u, Wc, bank)
                    phi = attr["phi"]
                    t1 = float(np.mean([int(np.argsort(-phi[i])[0] in g) for i, g in enumerate(gts)]))
                    t3 = float(np.mean([int(len(set(np.argsort(-phi[i])[:3]) & g) > 0)
                                        for i, g in enumerate(gts)]))
                    mres[mn] = {"top1": t1, "top3": t3}
                out[ds][u.name] = mres
                summary = ", ".join(k + ":" + format(v["top1"], ".2f")
                                    for k, v in mres.items() if isinstance(v, dict))
                print(f"{u.name}: n={len(Wc)} top1={summary} ({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:
                out[ds][u.name] = {"error": f"{type(e).__name__}: {e}"}
                print(f"{u.name}: ERROR {type(e).__name__}: {e}", flush=True)

    json.dump(out, open(cpath("compound_covshift.json"), "w", encoding="utf-8"), indent=1)
    print("saved -> compound_covshift.json", flush=True)

if __name__ == "__main__":
    main()
