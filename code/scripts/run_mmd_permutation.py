# -*- coding: utf-8 -*-
"""#23: MMD permutation test for natural-vs-injected confidence distributions.
Mirrors run_natural_validation's shift computation, adds a permutation p-value."""
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, WINDOW, cpath, get_scores
import evaluation.gt_pool as gp
import evaluation.two_layer as tl
from rcca.rcca import _RegimeBank
from evaluation.alignment import mmd_rbf

def mmd2_stat(A, B, n=400, seed=0):
    rng = np.random.default_rng(seed)
    A = A[rng.choice(len(A), min(n, len(A)), replace=False)]
    B = B[rng.choice(len(B), min(n, len(B)), replace=False)]
    Z = np.vstack([A, B])
    d2 = ((Z[:, None] - Z[None]) ** 2).sum(-1)
    gamma = 1.0 / np.median(d2[d2 > 0])
    K = np.exp(-gamma * d2)
    nA, nB = len(A), len(B)
    mmd2 = (K[:nA, :nA].sum() - np.trace(K[:nA, :nA])) / (nA * (nA - 1)) \
         + (K[nA:, nA:].sum() - np.trace(K[nA:, nA:])) / (nB * (nB - 1)) \
         - 2 * K[:nA, nA:].mean()
    return float(mmd2)

def perm_p(A, B, n_perm=200, sub=400):
    rng = np.random.default_rng(1)
    idx = np.arange(len(A) + len(B))
    obs = mmd2_stat(A, B, n=sub)
    null = []
    for _ in range(n_perm):
        rng.shuffle(idx)
        Ai = np.vstack([A, B])[idx[:len(A)]]
        Bi = np.vstack([A, B])[idx[len(A):]]
        null.append(mmd2_stat(Ai, Bi, n=sub))
    null = np.array(null)
    p = float((null >= obs).mean())
    return obs, p

def run():
    out = {}
    for ds in ("SWaT", "SMD", "MetroPT3"):
        units = gp._mixed_unit(ds)
        if not units:
            continue
        u = units[0]
        bank = _RegimeBank(u.pool_windows(), seed=0)
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        # natural FA windows (all above tau, random 400)
        cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
        te = np.arange(b + WINDOW - 1, len(X))
        ok = (cs[te + 1] - cs[te + 1 - WINDOW]) == 0
        tn = te[ok]
        idx = np.arange(WINDOW)[None, :] + (tn[:, None] - (WINDOW - 1))
        s = u.score(X[idx])
        fa = s > u.tau
        nat_idx = idx[fa]
        rng = np.random.default_rng(0)
        if len(nat_idx) > 400:
            nat_idx = nat_idx[rng.choice(len(nat_idx), 400, replace=False)]
        W_nat = X[nat_idx]
        # injected var windows from the unit
        W = u.windows()
        y = (u.gt_type == "variable").astype(int)
        W_inj = W[y == 1]
        # conf via RC-CA
        attr_n = tl.METHODS["RC-CA"](u, W_nat, bank)
        attr_i = tl.METHODS["RC-CA"](u, W_inj, bank)
        c_nat, c_inj = attr_n["conf"], attr_i["conf"]
        obs, p = perm_p(c_nat[:, None], c_inj[:, None])
        out[ds] = {"mmd2": obs, "perm_p": p, "n_nat": len(c_nat), "n_inj": len(c_inj)}
        print(f"{ds}: MMD^2={obs:.5f} perm-p={p:.3f} (n_nat={len(c_nat)}, n_inj={len(c_inj)})", flush=True)
    json.dump(out, open(cpath("mmd_permutation.json"), "w"), indent=1)
    print("saved -> mmd_permutation.json")

if __name__ == "__main__":
    run()
