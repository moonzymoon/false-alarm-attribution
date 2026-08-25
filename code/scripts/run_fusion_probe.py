"""牌1 可行性探针: Self-Routing Attribution (GlobalCF vs AERec 仲裁路由).

范围: iforest 23 混合单元 + PCA 13 + OCSVM 18 (= 54 混合单元).
仲裁器 v0: 分歧度 D = 0.5*||p_cf - p_rec||_1 (逐实例归一化通道分布的 TV 距离),
  (θ, 方向) 在各单元注入验证段标定 (与 γ/δ 同口径), 测试段不动.
基线 (DeepSeek 成功判据的三基线):
  1. best-single: 列内 max(GlobalCF, AERec) (以及全方法最优, 参考)
  2. mean-ensemble: 0.5*(p_cf + p_rec) 的 argmax (简单平均集成)
  3. oracle-unit: 逐单元取两法较优者 (单元级路由上限); 另报 oracle-instance 参考
成功判据: 各列 routing > best-single 且 > mean-ensemble, 且 >= 0.95 * oracle-unit.
输出: _cache/fusion_probe_results.json + _cache/fusion_probe/<unit>.npz (φ 缓存, 可续跑)
用法: python scripts/run_fusion_probe.py [--smoke] [--columns iforest,pca,ocsvm]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

PHI_DIR = cpath("fusion_probe")
WINDOW = None  # set after import common.WINDOW


def _norm(phi):
    """逐实例平移归一化到非负和一 (argmax 不变)."""
    p = phi - phi.min(axis=1, keepdims=True)
    s = p.sum(axis=1, keepdims=True)
    return p / (s + 1e-12)


def _hits(phi, gt_vars, idx):
    out = []
    for i in idx:
        out.append(int(np.argmax(phi[i]) in gt_vars[i]))
    return np.array(out)


def _top1(phi, gt_vars, sel):
    o = np.argmax(phi[sel], axis=1)
    return float(np.mean([int(oi in gt_vars[gi]) for oi, gi in zip(o, sel)]))


# ---------------- 单元构建 ----------------
def build_iforest_units():
    from evaluation import gt_pool
    gt_pool.set_far(0.05)
    units = gt_pool.build_all()
    return [u for u in units if "_mix_" in u.name]


def build_ns_units():
    """PCA/OCSVM 混合单元 (与 run_new_scorers.py 完全同种子构造, 跳过评估)."""
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.svm import OneClassSVM
    from common import load_raw, split_of, WINDOW
    from regimes.regimes import RegimeModel, features_at
    from injection.inject import (SEG_LEN, active_channels, apply_variable_fault,
                                  sample_normal_segments)
    sys.modules[__name__].__dict__.setdefault("_NS_WINDOW", WINDOW)
    FAR = 0.05
    DATASETS = ["SWaT", "SMD", "PSM"]
    VAR_CONFIGS = [("drift", 0.1), ("drift", 0.2), ("stuck", 1.0), ("var", 5.0)]

    class NSUnit:
        def __init__(self, name, scorer, dataset, tau, model, X, ends,
                     gt_type, gt_vars, gt_kind, gt_regime, val_mask, pool_ends, W_store=None):
            self.name, self.scorer, self.dataset, self.tau = name, scorer, dataset, tau
            self.model = model
            self.X = X
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

    units = []
    for ds in DATASETS:
        print(f"\n[ns-build] {ds}", flush=True)
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

        for scorer in ("pca", "ocsvm"):
            for k in range(rm.K):
                fit_ends = tr_ends[reg_tr != k]
                if len(fit_ends) < 500:
                    continue
                if len(fit_ends) > 50000:
                    fit_ends = fit_ends[np.sort(np.random.default_rng(0).choice(
                        len(fit_ends), 50000, replace=False))]
                idx_f = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
                feats_f = X[idx_f].reshape(len(fit_ends), -1)
                model = _fit(scorer, feats_f)
                cal = tr_ends[reg_tr != k][:20000]
                idx_c = np.arange(WINDOW)[None, :] + (cal[:, None] - (WINDOW - 1))
                flat_c = X[idx_c].reshape(len(cal), -1)
                if scorer == "pca":
                    s_cal = np.mean((flat_c - model.inverse_transform(
                        model.transform(flat_c))) ** 2, axis=1)
                else:
                    s_cal = -model.decision_function(flat_c)
                tau = float(np.quantile(s_cal, 1 - FAR))

                mask_k = reg_test == k
                n_win_k = int(mask_k.sum())
                if n_win_k < 200:
                    continue
                ends_k = tn[mask_k]
                idx_k = np.arange(WINDOW)[None, :] + (ends_k[:, None] - (WINDOW - 1))
                flat_k = X[idx_k].reshape(len(ends_k), -1)
                if scorer == "pca":
                    sk = np.mean((flat_k - model.inverse_transform(
                        model.transform(flat_k))) ** 2, axis=1)
                else:
                    sk = -model.decision_function(flat_k)
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
                    starts = sample_normal_segments(
                        Y, b, SEG_LEN, 8, seed=abs(hash((kind, st, k, scorer))) % 2**31)
                    for s in starts:
                        j = int(rng.choice(active))
                        Xm, _ = apply_variable_fault(X, s, SEG_LEN, [j], kind, st, mu, sigma)
                        ends = np.arange(s + WINDOW - 1, s + SEG_LEN)
                        Wm = Xm[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                        W0 = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                        s_a = _score_ns(scorer, model, Wm.reshape(len(Wm), -1))
                        s_b2 = _score_ns(scorer, model, W0.reshape(len(W0), -1))
                        fa = np.where((s_a > tau) & (s_b2 <= tau))[0]
                        if len(fa):
                            pick = rng.choice(fa, size=min(5, len(fa)), replace=False)
                            v_ends.extend(ends[pick]); v_vars.extend([[j]] * len(pick))
                            v_kind.extend([kind] * len(pick)); v_trial.extend([tid] * len(pick))
                            v_wins.append(Wm[pick])
                        tid += 1

                if len(r_ends) + len(v_ends) < 25:
                    continue
                ends = np.concatenate([r_ends, np.array(v_ends, int)])
                gt_type = np.array(["regime"] * len(r_ends) + ["variable"] * len(v_ends))
                gt_vars = [None] * len(r_ends) + v_vars
                gt_kind = ["regime_holdout"] * len(r_ends) + v_kind
                gt_regime = np.array([k] * len(ends))
                trials = np.array([0] * len(r_ends) + v_trial)
                val_mask = trials % 2 == 0
                if len(r_ends):
                    val_mask[:len(r_ends)] = rng2.random(len(r_ends)) < 0.5

                pool_ends = np.sort(fit_ends)
                if len(pool_ends) > 60000:
                    pool_ends = pool_ends[np.sort(rng2.choice(len(pool_ends), 60000,
                                                               replace=False))]

                W_store = None
                if v_wins:
                    W_store = np.concatenate(
                        [X[r_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]] + v_wins, 0)

                units.append(NSUnit(f"{scorer}_{ds}_mix_r{k}", scorer, ds, tau, model, X,
                                    ends, gt_type, gt_vars, gt_kind, gt_regime,
                                    val_mask, pool_ends, W_store))
                print(f"  built {scorer}_{ds}_mix_r{k} n={len(ends)}", flush=True)
    return units


def _score_ns(scorer, model, flat):
    if scorer == "pca":
        proj = model.inverse_transform(model.transform(flat))
        return np.mean((flat - proj) ** 2, axis=1)
    return -model.decision_function(flat)


# ---------------- φ 计算与缓存 ----------------
def compute_phi(unit):
    """返回 dict(phi_cf, phi_rec, sel_test, sel_val, gt_vars). 仅变量型实例."""
    path = os.path.join(PHI_DIR, unit.name + ".npz")
    if os.path.exists(path):
        d = np.load(path, allow_pickle=True)
        return {k: d[k] for k in d.files}
    import torch
    import evaluation.two_layer as tl
    from rcca.rcca import _RegimeBank
    torch.manual_seed(0)
    np.random.seed(0)
    bank = _RegimeBank(unit.pool_windows(), seed=0)
    W = unit.windows()
    y = (unit.gt_type == "variable").astype(int)
    attr_cf = tl.global_cf_attribute(unit, W, bank)
    torch.manual_seed(0)
    attr_rec = tl.ae_recon_attribute(unit, W, bank)
    val = unit.val_mask
    sel_val = np.where(val & (y == 1))[0]
    sel_test = np.where((~val) & (y == 1))[0]
    gt = [set(v) if v is not None else set() for v in unit.gt_vars]
    out = {"phi_cf": attr_cf["phi"], "phi_rec": attr_rec["phi"],
           "sel_test": sel_test, "sel_val": sel_val,
           "gt_vars": np.array([sorted(g) for g in gt], dtype=object)}
    os.makedirs(PHI_DIR, exist_ok=True)
    np.savez_compressed(path, **out)
    return out


# ---------------- 仲裁与评估 ----------------
def evaluate_unit_phi(d):
    phi_cf, phi_rec = d["phi_cf"], d["phi_rec"]
    gtv = d["gt_vars"]
    sel_test, sel_val = d["sel_test"], d["sel_val"]
    p_cf, p_rec = _norm(phi_cf), _norm(phi_rec)
    D = 0.5 * np.abs(p_cf - p_rec).sum(1)          # TV 距离 ∈ [0,1]

    def hit(phi, i):
        return int(np.argmax(phi[i]) in set(gtv[i]))

    r = {}
    r["n_test"] = int(len(sel_test))
    if len(sel_test) == 0:
        return r
    r["top1_cf"] = float(np.mean([hit(phi_cf, i) for i in sel_test]))
    r["top1_rec"] = float(np.mean([hit(phi_rec, i) for i in sel_test]))
    # mean ensemble
    pm = 0.5 * (p_cf + p_rec)
    r["top1_meanens"] = float(np.mean([hit(pm, i) for i in sel_test]))
    # oracle
    hc = np.array([hit(phi_cf, i) for i in sel_test])
    hr = np.array([hit(phi_rec, i) for i in sel_test])
    r["top1_oracle_inst"] = float(np.mean(hc | hr))
    r["top1_oracle_unit"] = float(max(r["top1_cf"], r["top1_rec"]))
    # ---- 自路由: (θ, 方向) 在 val 标定 ----
    if len(sel_val) >= 5:
        hv_c = np.array([hit(phi_cf, i) for i in sel_val])
        hv_r = np.array([hit(phi_rec, i) for i in sel_val])
        Dv = D[sel_val]
        best = (-1.0, None, None)
        for direction in ("rec_on_high", "cf_on_high"):
            for q in np.linspace(0.05, 0.95, 19):
                th = float(np.quantile(Dv, q))
                use_rec = (Dv > th) if direction == "rec_on_high" else (Dv <= th)
                acc = float(np.mean(np.where(use_rec, hv_r, hv_c)))
                if acc > best[0]:
                    best = (acc, th, direction)
        _, theta, direction = best
        use_rec = (D[sel_test] > theta) if direction == "rec_on_high" else (D[sel_test] <= theta)
        routed = np.where(use_rec, hr, hc)
        r.update({"theta": theta, "direction": direction,
                  "top1_routing": float(np.mean(routed)),
                  "frac_rec": float(np.mean(use_rec))})
    else:
        # 验证实例不足: 回退到列级全局 θ (二次阶段统一处理), 先置 None
        r.update({"theta": None, "direction": None, "top1_routing": None})
    return r


def main():
    global WINDOW
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="每列只跑 2 个单元")
    ap.add_argument("--columns", default="iforest,pca,ocsvm")
    args = ap.parse_args()
    from common import WINDOW as _W
    WINDOW = _W

    columns = {}
    if "iforest" in args.columns:
        us = build_iforest_units()
        columns["iforest"] = us[:2] if args.smoke else us
    if "pca" in args.columns or "ocsvm" in args.columns:
        ns = build_ns_units()
        if "pca" in args.columns:
            columns["pca"] = [u for u in ns if u.scorer == "pca"][:2] if args.smoke \
                else [u for u in ns if u.scorer == "pca"]
        if "ocsvm" in args.columns:
            columns["ocsvm"] = [u for u in ns if u.scorer == "ocsvm"][:2] if args.smoke \
                else [u for u in ns if u.scorer == "ocsvm"]

    results = {}
    for col, units in columns.items():
        results[col] = {}
        print(f"\n===== column {col}: {len(units)} units =====", flush=True)
        for u in units:
            d = compute_phi(u)
            r = evaluate_unit_phi(d)
            results[col][u.name] = r
            if r.get("top1_routing") is not None:
                print(f"  {u.name:28s} n={r['n_test']:4d} cf={r['top1_cf']:.3f} "
                      f"rec={r['top1_rec']:.3f} ens={r['top1_meanens']:.3f} "
                      f"route={r['top1_routing']:.3f} (θ={r['theta']:.3f},{r['direction']},"
                      f"{r['frac_rec']:.0%}rec) orcU={r['top1_oracle_unit']:.3f}", flush=True)
            else:
                print(f"  {u.name:28s} n={r['n_test']:4d} (val insuff, deferred)", flush=True)

    # ---- 汇总 (单元均值口径, 与正文 Table 4 一致) ----
    summary = {}
    for col, res in results.items():
        rows = [r for r in res.values() if r.get("top1_routing") is not None]
        if not rows:
            continue
        agg = {k: float(np.mean([r[k] for r in rows])) for k in
               ("top1_cf", "top1_rec", "top1_meanens", "top1_routing",
                "top1_oracle_unit", "top1_oracle_inst")}
        agg["n_units"] = len(rows)
        agg["best_single"] = max(agg["top1_cf"], agg["top1_rec"])
        agg["vs_best_single"] = agg["top1_routing"] - agg["best_single"]
        agg["vs_meanens"] = agg["top1_routing"] - agg["top1_meanens"]
        agg["vs_oracle_unit"] = agg["top1_routing"] - agg["top1_oracle_unit"]
        agg["ratio_oracle"] = agg["top1_routing"] / agg["top1_oracle_unit"] if agg["top1_oracle_unit"] else float("nan")
        summary[col] = agg
        print(f"\n[{col}] units={agg['n_units']}  GlobalCF={agg['top1_cf']:.3f} "
              f"AERec={agg['top1_rec']:.3f}  best-single={agg['best_single']:.3f} "
              f"mean-ens={agg['top1_meanens']:.3f}")
        print(f"       ROUTING={agg['top1_routing']:.3f}  Δbest={agg['vs_best_single']:+.3f} "
              f"Δens={agg['vs_meanens']:+.3f}  oracle-unit={agg['top1_oracle_unit']:.3f} "
              f"ratio={agg['ratio_oracle']:.3f}  (oracle-inst={agg['top1_oracle_inst']:.3f})")

    with open(cpath("fusion_probe_results.json"), "w", encoding="utf-8") as f:
        json.dump({"per_unit": results, "summary": summary}, f,
                  ensure_ascii=False, indent=1, default=float)
    print("\n写入 _cache/fusion_probe_results.json")
    # 判据输出
    print("\n===== DeepSeek 三基线判据 =====")
    for col, a in summary.items():
        ok1 = a["vs_best_single"] > 0
        ok2 = a["vs_meanens"] > 0
        ok3 = a["ratio_oracle"] >= 0.95
        print(f"[{col}] beat best-single: {'PASS' if ok1 else 'FAIL'} ({a['vs_best_single']:+.3f}) | "
              f"beat mean-ens: {'PASS' if ok2 else 'FAIL'} ({a['vs_meanens']:+.3f}) | "
              f">=0.95*oracle: {'PASS' if ok3 else 'FAIL'} (ratio {a['ratio_oracle']:.3f})")


if __name__ == "__main__":
    main()
