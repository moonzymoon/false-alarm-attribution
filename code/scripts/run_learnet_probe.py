"""牌1.5 学习型仲裁器探针: LOO按单元, 预注册DeepSeek判据, 从φ缓存直评(分钟级).

判据(预注册, 不改): 逐列(iforest/pca/ocsvm)须同时赢 best-single 与 简单平均集成;
pooled 仅作参考, 且须逐单元配对自助CI为正才算数. oracle差距只报告.
输出: _cache/learnet_probe.json
"""
import json
import os
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402

PHI_DIR = cpath("fusion_probe")


def norm(phi):
    p = phi - phi.min(1, keepdims=True)
    return p / (p.sum(1, keepdims=True) + 1e-12)


def feats(phi_cf, phi_rec):
    p_cf, p_rec = norm(phi_cf), norm(phi_rec)
    j_cf, j_rec = np.argmax(p_cf, 1), np.argmax(p_rec, 1)
    d = phi_cf.shape[1]

    def s2(p):
        return np.sort(p, 1)[:, -2]
    def s3(p):
        return -np.sort(-p, 1)[:, :3].sum(1)
    def ent(p):
        return -(p * np.log(p + 1e-12)).sum(1)
    rank_cf_in_rec = np.array([1.0 - (np.argsort(-p_rec[i]).tolist().index(j_cf[i])) / d
                               for i in range(len(p_cf))])
    rank_rec_in_cf = np.array([1.0 - (np.argsort(-p_cf[i]).tolist().index(j_rec[i])) / d
                               for i in range(len(p_rec))])
    tv = 0.5 * np.abs(p_cf - p_rec).sum(1)
    agree = (j_cf == j_rec).astype(float)
    return np.stack([
        p_cf.max(1), p_rec.max(1), p_cf.max(1) - s2(p_cf), p_rec.max(1) - s2(p_rec),
        tv, agree, rank_cf_in_rec, rank_rec_in_cf, s3(p_cf), s3(p_rec),
        ent(p_cf), ent(p_rec), p_cf[np.arange(len(p_cf)), j_rec],
        p_rec[np.arange(len(p_rec)), j_cf],
        np.log1p(phi_rec.max(1)), np.full(len(p_cf), d / 51.0),
    ], 1)


def hits_of(phi, gtv, sel):
    o = np.argmax(phi[sel], 1)
    return np.array([int(oi in set(gtv[gi])) for oi, gi in zip(o, sel)])


def col_of(n):
    return "iforest" if n.startswith("iforest") else ("pca" if n.startswith("pca") else "ocsvm")


def main():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    U = {}
    for f in sorted(x for x in os.listdir(PHI_DIR) if x.endswith(".npz")):
        d = np.load(os.path.join(PHI_DIR, f), allow_pickle=True)
        n = f[:-4]
        if len(d["sel_test"]) == 0:
            continue
        p_cf, p_rec = norm(d["phi_cf"]), norm(d["phi_rec"])
        hc_t = hits_of(d["phi_cf"], d["gt_vars"], d["sel_test"]).astype(int)
        hr_t = hits_of(d["phi_rec"], d["gt_vars"], d["sel_test"]).astype(int)
        hc_v = hits_of(d["phi_cf"], d["gt_vars"], d["sel_val"]).astype(int)
        hr_v = hits_of(d["phi_rec"], d["gt_vars"], d["sel_val"]).astype(int)
        U[n] = dict(col=col_of(n),
                    X_t=feats(d["phi_cf"][d["sel_test"]], d["phi_rec"][d["sel_test"]]),
                    X_v=feats(d["phi_cf"][d["sel_val"]], d["phi_rec"][d["sel_val"]]),
                    hc_t=hc_t, hr_t=hr_t, hc_v=hc_v, hr_v=hr_v,
                    ens_t=hits_of(0.5 * (p_cf + p_rec), d["gt_vars"], d["sel_test"]).astype(int))
    names = sorted(U)
    print(f"{len(names)} units loaded")

    out = {}
    for model_name in ("logreg", "hgb"):
        res = {}
        for held in names:
            tr = [n for n in names if n != held]
            Xtr = np.concatenate([U[n]["X_v"] for n in tr])
            hc = np.concatenate([U[n]["hc_v"] for n in tr])
            hr = np.concatenate([U[n]["hr_v"] for n in tr])
            dec = hc != hr  # 只在两法一hit一miss的实例上学决策
            Xtr, ytr = Xtr[dec], (hr[dec] > hc[dec]).astype(int)
            if len(ytr) < 20 or ytr.min() == ytr.max():
                pred_rec = np.full(len(U[held]["X_t"]), U[held]["hr_t"].mean() >= U[held]["hc_t"].mean())
            else:
                if model_name == "logreg":
                    clf = make_pipeline(StandardScaler(),
                                        LogisticRegression(max_iter=2000, class_weight="balanced",
                                                           random_state=0))
                else:
                    clf = HistGradientBoostingClassifier(max_depth=3, max_iter=200,
                                                         learning_rate=0.1, random_state=0)
                clf.fit(Xtr, ytr)
                pred_rec = clf.predict_proba(U[held]["X_t"])[:, 1] > 0.5
            u = U[held]
            routed = np.where(pred_rec, u["hr_t"], u["hc_t"])
            res[held] = {"col": u["col"], "route": float(routed.mean()),
                         "cf": float(u["hc_t"].mean()), "rec": float(u["hr_t"].mean()),
                         "ens": float(u["ens_t"].mean()),
                         "orcU": float(max(u["hc_t"].mean(), u["hr_t"].mean())),
                         "frac_rec": float(np.mean(pred_rec)), "n": int(len(routed))}
        out[model_name] = res

    summary = {}
    for mk, res in out.items():
        summary[mk] = {}
        for c in ("iforest", "pca", "ocsvm"):
            rows = [r for r in res.values() if r["col"] == c]
            best1 = max(np.mean([r["cf"] for r in rows]), np.mean([r["rec"] for r in rows]))
            means = np.mean([r["ens"] for r in rows])
            route = np.mean([r["route"] for r in rows])
            orcU = np.mean([r["orcU"] for r in rows])
            summary[mk][c] = dict(best_single=float(best1), mean_ens=float(means),
                                  route=float(route), oracle_unit=float(orcU),
                                  beat_best=bool(route > best1),
                                  beat_means=bool(route > means), n_units=len(rows))
            print(f"[{mk}/{c}] best={best1:.3f} ens={means:.3f} route={route:.3f} "
                  f"beatB={'Y' if route>best1 else 'N'} beatE={'Y' if route>means else 'N'} "
                  f"oracle={orcU:.3f} gap={route-orcU:+.3f}")
        rows = list(res.values())
        best1_p = max(np.mean([r["cf"] for r in rows]), np.mean([r["rec"] for r in rows]))
        means_p = np.mean([r["ens"] for r in rows])
        route_p = np.mean([r["route"] for r in rows])
        d_best = np.array([r["route"] - max(r["cf"], r["rec"]) for r in rows])
        d_means = np.array([r["route"] - r["ens"] for r in rows])
        rng = np.random.default_rng(2026)
        ci = lambda dd: (np.percentile([np.mean(dd[rng.integers(0, len(dd), len(dd))])
                                        for _ in range(2000)], 2.5),
                         np.percentile([np.mean(dd[rng.integers(0, len(dd), len(dd))])
                                        for _ in range(2000)], 97.5))
        cb, cm = ci(d_best), ci(d_means)
        summary[mk]["pooled"] = dict(best_single=float(best1_p), mean_ens=float(means_p),
                                     route=float(route_p),
                                     paired_best_ci=[float(cb[0]), float(cb[1])],
                                     paired_means_ci=[float(cm[0]), float(cm[1])])
        print(f"[{mk}/POOLED] best={best1_p:.3f} ens={means_p:.3f} route={route_p:.3f} "
              f"| 逐单元配对Δbest 95%CI [{cb[0]:+.3f},{cb[1]:+.3f}] "
              f"Δens [{cm[0]:+.3f},{cm[1]:+.3f}]")

    print("\n===== 预注册判据(逐列须双过) =====")
    for mk in out:
        ok = all(summary[mk][c]["beat_best"] and summary[mk][c]["beat_means"]
                 for c in ("iforest", "pca", "ocsvm"))
        print(f"{mk}: {'PASS' if ok else 'FAIL'}")
    json.dump({"per_unit": out, "summary": summary},
              open(cpath("learnet_probe.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("写入 _cache/learnet_probe.json")


if __name__ == "__main__":
    main()
