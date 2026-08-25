"""E6 (M6): margin 切点敏感性 (10/20/50%); E7 (M7): 修复实验种子稳健性 (SWaT+SMD, seeds 0/1/2)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402


def margin_sens():
    out = {}
    for ds in ("SWaT", "MetroPT3"):
        for u in gp._mixed_unit(ds):
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            test = ~u.val_mask & (y == 1)
            s0 = u.score(W)
            margin = (s0 - u.tau) / (abs(u.tau) + 1e-12)
            rec = {}
            for cut in (0.1, 0.2, 0.5):
                strat = margin < cut
                entry = {}
                for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec"):
                    attr = tl.METHODS[m](u, W, bank)
                    lo = test & strat
                    hi = test & ~strat
                    def top1(mask):
                        if mask.sum() < 5:
                            return None
                        phi = attr["phi"][mask]
                        return float(np.mean([int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                                              for i, gi in enumerate(np.where(mask)[0])]))
                    entry[m] = (top1(lo), top1(hi))
                rec[cut] = entry
            out[u.name] = rec
            print(f"{u.name}: " + "; ".join(f"cut{int(c*100)}%: " + " ".join(
                f"{m}={v[0] if v[0] is None else round(v[0],2)}/{v[1] if v[1] is None else round(v[1],2)}"
                for m, v in entry.items()) for c, entry in rec.items()), flush=True)
    json.dump(out, open(cpath("margin_sensitivity.json"), "w"), default=float)
    print("margin_sensitivity.json 已写")


def repair_seeds():
    from sklearn.ensemble import IsolationForest
    rows = []
    for ds in ("SWaT", "SMD"):
        for u in gp._mixed_unit(ds):
            k = int(u.gt_regime[0])
            ctx = gp._MIX_CTX[ds]
            tn, reg_test = ctx["tn"], ctx["reg_test"]
            X, Y = load_raw(ds)
            a, b = split_of(len(X))
            pool = u.pool_ends
            feats_pool = X[pool[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].reshape(len(pool), -1)
            eval_ends = tn[reg_test == k]
            pool_k = tn[reg_test == k]
            gaps = {sd: [] for sd in (0, 1, 2)}
            for sd in (0, 1, 2):
                rng = np.random.default_rng(sd)
                tau = u.tau
                for tag in ("none", "dir", "rnd"):
                    extra = []
                    if tag == "dir":
                        extra = rng.choice(pool_k, size=min(int(len(pool) * 0.1), len(pool_k) - 50), replace=False)
                    elif tag == "rnd":
                        extra = rng.choice(tn[reg_test != k], size=min(int(len(pool) * 0.1), len(tn[reg_test != k])), replace=False)
                    feats = feats_pool
                    if len(extra):
                        feats = np.vstack([feats, X[np.asarray(extra)[:, None] - (WINDOW - 1)
                                                   + np.arange(WINDOW)[None, :]].reshape(len(extra), -1)])
                    ifo = IsolationForest(n_estimators=100, random_state=sd, n_jobs=-1).fit(feats)
                    ew = X[eval_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].reshape(len(eval_ends), -1)
                    far = float((-ifo.decision_function(ew) > tau).mean())
                    gaps[sd].append((tag, far))
            base = {sd: dict(gaps[sd])["none"] for sd in (0, 1, 2)}
            dir_rnd = [dict(gaps[sd])["rnd"] - dict(gaps[sd])["dir"] for sd in (0, 1, 2)]
            rows.append({"unit": u.name,
                         "base": [base[sd] for sd in (0, 1, 2)],
                         "dir_minus_rnd_pp": [100 * v for v in dir_rnd]})
            print(f"{u.name}: dir-rnd (pp) 三种子 = " +
                  ", ".join(f"{100*v:+.1f}" for v in dir_rnd), flush=True)
    if rows:
        allg = np.array([r["dir_minus_rnd_pp"] for r in rows])
        print(f"跨单元均值 {allg.mean():+.1f}pp ± {allg.std():.1f}; 种子内均值: "
              + ", ".join(f"s{sd}={allg[:, sd].mean():+.1f}" for sd in range(3)))
    json.dump(rows, open(cpath("repair_seeds.json"), "w"), default=float)


if __name__ == "__main__":
    margin_sens()
    repair_seeds()
