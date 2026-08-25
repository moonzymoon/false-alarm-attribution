# -*- coding: utf-8 -*-
"""A1/A4 assumption audit extended to PCA and OCSVM detectors.
A1: within-window per-channel time permutation -> score shift.
A4: single-channel offset ramp -> non-decreasing step fraction."""
import sys, os, json
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from common import load_raw, split_of, WINDOW, cpath
import evaluation.gt_pool as gp
from rcca.rcca import _RegimeBank

def main():
    out = {}
    for ds in ("SWaT",):
        units = gp._mixed_unit(ds)
        for u in units[:1]:
            for scorer, tag in (("pca", "pca"), ("ocsvm", "ocsvm")):
                # rebuild a classical-detector unit on this dataset's normal pool
                from sklearn.decomposition import PCA
                from sklearn.svm import OneClassSVM
                X, Y = load_raw(ds)
                a, b = split_of(len(X))
                pool = u.pool_windows()
                flat = pool.reshape(len(pool), -1)
                if scorer == "pca":
                    model = PCA(n_components=min(flat.shape[1], 50), random_state=0).fit(flat)
                    def score(W):
                        f2 = W.reshape(len(W), -1)
                        proj = model.inverse_transform(model.transform(f2))
                        return np.mean((f2 - proj) ** 2, axis=1)
                else:
                    sub = flat[np.random.default_rng(0).choice(len(flat), min(30000, len(flat)), replace=False)]
                    model = OneClassSVM(kernel="rbf", nu=0.05).fit(sub)
                    def score(W):
                        return -model.decision_function(W.reshape(len(W), -1))
                W = u.windows()[:300]
                rng = np.random.default_rng(5)
                # A1: permute each channel's within-window order
                Wp = W.copy()
                for j in range(W.shape[2]):
                    for i in range(len(W)):
                        Wp[i, :, j] = Wp[i, rng.permutation(WINDOW), j]
                s0, s1 = score(W), score(Wp)
                shift = np.abs(s1 - s0) / (np.std(s0) + 1e-12)
                # A4: offset ramp on one active channel
                D = W.shape[2]
                j = int(np.argmax(X[a:b].std(0)))
                offs = np.linspace(0, 20, 9)
                steps_all = []
                for i in range(len(W)):
                    vals = []
                    for off in offs:
                        Wo = W[i:i+1].copy()
                        Wo[0, :, j] += off * (X[a:b].std(0)[j] + 1e-12)
                        vals.append(float(score(Wo)[0]))
                    v = np.array(vals)
                    steps_all.append((np.diff(v) >= -1e-12))
                mono = float(np.concatenate(steps_all).mean())
                out[f"{tag}_{ds}"] = {
                    "a1_median_shift_over_std": float(np.median(shift)),
                    "a4_monotone_frac": mono, "n_windows": len(W), "n_steps": len(offs)-1,
                }
                print(f"{tag}/{ds}: A1 median shift {np.median(shift):.4f} sd, A4 mono {mono:.3f}", flush=True)
    json.dump(out, open(cpath("audit_ext_pca_ocsvm.json"), "w"), indent=1)
    print("saved -> audit_ext_pca_ocsvm.json")

if __name__ == "__main__":
    main()
