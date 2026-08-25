"""第4/5种检测器(PCA+OCSVM) × 4数据集 × 9归因方法 = 扩展匹配研究."""
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.svm import OneClassSVM
from sklearn.metrics import precision_recall_fscore_support, f1_score
from common import load_raw, split_of, WINDOW, cpath
from regimes.regimes import RegimeModel, features_at
from rcca.rcca import _RegimeBank
import evaluation.two_layer as tl
from injection.inject import (SEG_LEN, active_channels, apply_variable_fault,
                              sample_normal_segments)

FAR = 0.05
DATASETS = ["SWaT", "SMD", "PSM"]
SCORERS = ["pca", "ocsvm"]
VAR_CONFIGS = [("drift", 0.1), ("drift", 0.2), ("stuck", 1.0), ("var", 5.0)]


class NSUnit:
    """新检测器评估单元."""
    def __init__(self, name, scorer, dataset, tau, model, X, ends,
                 gt_type, gt_vars, gt_kind, gt_regime, val_mask, pool_ends, W_store=None):
        self.name, self.scorer, self.dataset, self.tau = name, scorer, dataset, tau
        self.model = model; self.X = X
        self.ends, self.gt_type = ends, gt_type
        self.gt_vars, self.gt_kind, self.gt_regime = gt_vars, gt_kind, gt_regime
        self.val_mask, self.pool_ends = val_mask, pool_ends
        self.W_store = W_store
        self.iforest_model = model if scorer == "iforest" else None

    def windows(self, idx=None):
        if self.W_store is not None:
            return self.W_store if idx is None else self.W_store[idx]
        e = self.ends if idx is None else self.ends[idx]
        i = e[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
        return self.X[i]

    def score(self, W):
        flat = W.reshape(len(W), -1)
        if self.scorer == "pca":
            proj = self.model.inverse_transform(self.model.transform(flat))
            return np.mean((flat - proj) ** 2, axis=1)
        elif self.scorer == "ocsvm":
            return -self.model.decision_function(flat)
        raise ValueError(self.scorer)

    def pool_windows(self):
        i = self.pool_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
        return self.X[i]


def _fit(scorer, feats):
    if scorer == "pca":
        return PCA(n_components=min(feats.shape[1], 50), random_state=0).fit(feats)
    elif scorer == "ocsvm":
        return OneClassSVM(kernel="rbf", nu=0.05).fit(feats)
    raise ValueError(scorer)


def _score(scorer, model, flat):
    if scorer == "pca":
        proj = model.inverse_transform(model.transform(flat))
        return np.mean((flat - proj) ** 2, axis=1)
    elif scorer == "ocsvm":
        return -model.decision_function(flat)


def run():
    all_res = {}
    for ds in DATASETS:
        print(f"\n===== {ds} =====", flush=True)
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        rm = RegimeModel().fit(X, seed=0)
        cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
        te = np.arange(b + WINDOW - 1, len(X))
        ok = (cs[te + 1] - cs[te + 1 - WINDOW]) == 0
        tn = te[ok]
        if len(tn) > 200000:
            tn = tn[np.sort(np.random.default_rng(1).choice(len(tn), 200000, replace=False))]
        reg_test = rm.transform(features_at(X, tn))
        tr_ends = np.arange(a + WINDOW - 1, b)
        reg_tr = rm.transform(features_at(X, tr_ends))
        mu, sigma = X[a:b].mean(0), X[a:b].std(0) + 1e-8
        active = active_channels(X, a, b)
        rng = np.random.default_rng(7)

        for scorer in SCORERS:
            print(f"  --- {scorer} ---", flush=True)
            for k in range(rm.K):
                fit_ends = tr_ends[reg_tr != k]
                if len(fit_ends) < 500:
                    continue
                if len(fit_ends) > 50000:
                    fit_ends = fit_ends[np.sort(np.random.default_rng(0).choice(len(fit_ends), 50000, replace=False))]
                idx_f = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
                feats_f = X[idx_f].reshape(len(fit_ends), -1)
                model = _fit(scorer, feats_f)
                cal = tr_ends[reg_tr != k][:20000]
                idx_c = np.arange(WINDOW)[None, :] + (cal[:, None] - (WINDOW - 1))
                s_cal = _score(scorer, model, X[idx_c].reshape(len(cal), -1))
                tau = float(np.quantile(s_cal, 1 - FAR))

                mask_k = reg_test == k
                n_win_k = int(mask_k.sum())
                if n_win_k < 200:
                    continue
                ends_k = tn[mask_k]
                idx_k = np.arange(WINDOW)[None, :] + (ends_k[:, None] - (WINDOW - 1))
                sk = _score(scorer, model, X[idx_k].reshape(len(ends_k), -1))
                fa_k = sk > tau
                if int(fa_k.sum()) < 50:
                    continue

                r_ends = ends_k[fa_k]
                rng2 = np.random.default_rng(1)
                if len(r_ends) > 400:
                    r_ends = r_ends[np.sort(rng2.choice(len(r_ends), 400, replace=False))]

                v_ends, v_vars, v_kind, v_trial, v_wins = [], [], [], [], []
                tid = 0
                for kind, st in VAR_CONFIGS:
                    starts = sample_normal_segments(Y, b, SEG_LEN, 8,
                                                    seed=abs(hash((kind, st, k, scorer))) % 2**31)
                    for s in starts:
                        j = int(rng.choice(active))
                        Xm, _ = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
                        ends = np.arange(s + WINDOW - 1, s + SEG_LEN)
                        Wm = Xm[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                        W0 = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                        s_a = _score(scorer, model, Wm.reshape(len(Wm), -1))
                        s_b2 = _score(scorer, model, W0.reshape(len(W0), -1))
                        fa = np.where((s_a > tau) & (s_b2 <= tau))[0]
                        if len(fa):
                            pick = rng.choice(fa, size=min(5, len(fa)), replace=False)
                            v_ends.extend(ends[pick]); v_vars.extend([[j]]*len(pick))
                            v_kind.extend([kind]*len(pick)); v_trial.extend([tid]*len(pick))
                            v_wins.append(Wm[pick])
                        tid += 1

                if len(r_ends) + len(v_ends) < 25:
                    continue
                ends = np.concatenate([r_ends, np.array(v_ends, int)])
                gt_type = np.array(["regime"]*len(r_ends) + ["variable"]*len(v_ends))
                gt_vars = [None]*len(r_ends) + v_vars
                gt_kind = ["regime_holdout"]*len(r_ends) + v_kind
                gt_regime = np.array([k]*len(ends))
                trials = np.array([0]*len(r_ends) + v_trial)
                val_mask = trials % 2 == 0
                if len(r_ends):
                    val_mask[:len(r_ends)] = rng2.random(len(r_ends)) < 0.5

                pool_ends = np.sort(fit_ends)
                if len(pool_ends) > 60000:
                    pool_ends = pool_ends[np.sort(rng2.choice(len(pool_ends), 60000, replace=False))]

                W_store = None
                if v_wins:
                    W_store = np.concatenate(
                        [X[r_ends[:, None] - (WINDOW-1) + np.arange(WINDOW)[None, :]]] + v_wins, 0)

                unit = NSUnit(f"{scorer}_{ds}_mix_r{k}", scorer, ds, tau, model, X,
                              ends, gt_type, gt_vars, gt_kind, gt_regime, val_mask, pool_ends, W_store)

                print(f"    r{k}: n={len(ends)}(v{len(v_ends)}/r{len(r_ends)})", end=" → ", flush=True)

                try:
                    bank = _RegimeBank(unit.pool_windows(), seed=0)
                    W = unit.windows()
                    y = (unit.gt_type == "variable").astype(int)
                    val, test = unit.val_mask, ~unit.val_mask
                    mres = {}
                    for mn in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger", "zDev", "Random"):
                        try:
                            attr = tl.METHODS[mn](unit, W, bank)
                            g, d = tl.calibrate(tl._sub(attr, val), y[val])
                            og, od = tl.calibrate(tl._sub(attr, test), y[test])
                            pred = tl._predict(attr, g, d)
                            m = {"layer1_macro_f1": tl._macro_f1(y[test], pred[test]),
                                 "layer1_oracle": tl._macro_f1(y[test], tl._predict(attr, og, od)[test])}
                            vm = test & (y == 1)
                            if vm.sum() > 0:
                                phi = attr["phi"][vm]
                                top1 = [int(np.argsort(-phi[i])[0] in set(unit.gt_vars[gi]))
                                        for i, gi in enumerate(np.where(vm)[0])]
                                m["layer2_top1"] = float(np.mean(top1))
                                m["layer2_hits_top1"] = top1
                            prf = precision_recall_fscore_support(y[test], pred[test], labels=[1,0], zero_division=0)
                            m.update({"var_f1": float(prf[2][0]), "reg_f1": float(prf[2][1]),
                                      "var_recall": float(prf[1][0]), "reg_recall": float(prf[1][1])})
                            mres[mn] = m
                        except Exception as e:
                            mres[mn] = {"error": f"{type(e).__name__}"}
                    all_res[unit.name] = mres
                    line = " ".join(f"{mn}={m.get('layer1_macro_f1', -1):.2f}" for mn, m in mres.items())
                    print(line, flush=True)
                except Exception as e:
                    print(f"EVAL_FAIL {type(e).__name__}: {e}", flush=True)

    with open(cpath("new_scorer_results.json"), "w", encoding="utf-8") as f:
        json.dump(all_res, f, ensure_ascii=False, indent=1, default=float)
    print(f"\n{len(all_res)} units → new_scorer_results.json")


if __name__ == "__main__":
    run()
