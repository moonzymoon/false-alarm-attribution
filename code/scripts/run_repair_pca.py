"""修复实验推广到 PCA 检测器 (回应外部审查 D#26: repair 仅 iforest).
协议 = repair_guided2 (v2): base / mode-directed / guided(RC-CA 判 regime 的报警窗) /
random(其他 regime 窗), tau 固定基础模型校准值, 评测 = 留出 mode 全部正常窗 FAR.
PCA 拟合单线程秒级, 对卡顿机器友好. 输出 _cache/repair_pca.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath, FAR_TARGETS  # noqa: E402
from regimes.regimes import RegimeModel, features_at  # noqa: E402
from injection.inject import (SEG_LEN, active_channels,  # noqa: E402
                              sample_normal_segments, apply_variable_fault)
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402

VAR_CONFIGS = [("drift", 0.1), ("drift", 0.2), ("stuck", 1.0), ("var", 5.0)]
FAR = 0.05
EVAL_CAP = 60000


def main():
    from sklearn.decomposition import PCA
    rows = []
    for ds in ("SWaT", "SMD"):
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

        def wins(e):
            e = np.asarray(e, dtype=np.int64)
            return e[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]

        def pca_fit(feats):
            return PCA(n_components=min(feats.shape[1], 50), random_state=0).fit(feats)

        def pca_score(model, flat):
            proj = model.inverse_transform(model.transform(flat))
            return np.mean((flat - proj) ** 2, axis=1)

        for k in range(rm.K):
            fit_ends = tr_ends[reg_tr != k]
            if len(fit_ends) < 500:
                continue
            if len(fit_ends) > 50000:
                fit_ends = fit_ends[np.sort(np.random.default_rng(0).choice(
                    len(fit_ends), 50000, replace=False))]
            fit_ends = np.asarray(fit_ends, dtype=np.int64)
            _dbg = fit_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
            feats_f = X[_dbg].reshape(len(fit_ends), -1)
            model = pca_fit(feats_f)
            cal = tr_ends[reg_tr != k][:20000]
            s_cal = pca_score(model, X[wins(cal)].reshape(len(cal), -1))
            tau = float(np.quantile(s_cal, 1 - FAR))
            mask_k = reg_test == k
            if int(mask_k.sum()) < 200:
                continue
            ends_k = np.asarray(tn[mask_k], dtype=np.int64)
            sk = pca_score(model, X[wins(ends_k)].reshape(len(ends_k), -1))
            if int((sk > tau).sum()) < 50:
                continue
            r_ends = np.asarray(ends_k[sk > tau], dtype=np.int64)
            rng2 = np.random.default_rng(1)
            if len(r_ends) > 400:
                r_ends = r_ends[np.sort(rng2.choice(len(r_ends), 400, replace=False))]

            v_ends, v_vars, v_kind, v_trial, v_wins = [], [], [], [], []
            tid = 0
            for kind, st in VAR_CONFIGS:
                starts = sample_normal_segments(Y, b, SEG_LEN, 8,
                                                seed=abs(hash((kind, st, k, "pca"))) % 2**31)
                for s_ in starts:
                    j = int(rng.choice(active))
                    Xm, _ = apply_variable_fault(X, s_, SEG_LEN, [j], kind, st, mu, sigma)
                    ends = np.arange(s_ + WINDOW - 1, s_ + SEG_LEN)
                    Wm = Xm[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                    W0 = X[ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]]
                    s_a = pca_score(model, Wm.reshape(len(Wm), -1))
                    s_b2 = pca_score(model, W0.reshape(len(W0), -1))
                    fa = np.where((s_a > tau) & (s_b2 <= tau))[0]
                    if len(fa):
                        pick = rng.choice(fa, size=min(5, len(fa)), replace=False)
                        v_ends.extend(ends[pick]); v_vars.extend([[j]] * len(pick))
                        v_kind.extend([kind] * len(pick)); v_trial.extend([tid] * len(pick))
                        v_wins.append(Wm[pick])
                    tid += 1
            if len(r_ends) + len(v_ends) < 25:
                continue
            ends = np.concatenate([r_ends, np.array(v_ends, np.int64)]).astype(np.int64)
            gt_type = np.array(["regime"] * len(r_ends) + ["variable"] * len(v_ends))
            trials = np.array([0] * len(r_ends) + v_trial)
            val_mask = trials % 2 == 0
            val_mask[:len(r_ends)] = rng2.random(len(r_ends)) < 0.5
            pool_ends = np.sort(fit_ends).astype(np.int64)
            if len(pool_ends) > 60000:
                pool_ends = pool_ends[np.sort(rng2.choice(len(pool_ends), 60000, replace=False))]

            # --- RC-CA verdicts (轻量伪单元) ---
            class _U:
                pass
            u = _U()
            u.name = f"pca_{ds}_mix_r{k}"
            u.scorer, u.dataset, u.iforest_model = "pca", ds, None
            u.score = lambda W: pca_score(model, W.reshape(len(W), -1))
            bank = _RegimeBank(X[wins(pool_ends)], seed=0)
            Wall = np.concatenate([X[wins(r_ends)]] + ([np.concatenate(v_wins, 0)] if v_wins else []), 0)
            attr = rcca_attribute(u, Wall, bank)
            y = (gt_type == "variable").astype(int)
            g, d = tl.calibrate(tl._sub(attr, val_mask), y[val_mask])
            pred = tl._predict(attr, g, d)
            flagged = ends[(~val_mask) & (pred == 0)]

            # --- 修复: base / targeted / guided / random ---
            eval_ends = ends_k
            if len(eval_ends) > EVAL_CAP:
                eval_ends = eval_ends[np.sort(np.random.default_rng(5).choice(
                    len(eval_ends), EVAL_CAP, replace=False))]
            ew = X[wins(eval_ends)].reshape(len(eval_ends), -1)
            feats_pool = X[wins(pool_ends)].reshape(len(pool_ends), -1)
            n_var = int(len(pool_ends) * 0.10)
            pool_k = tn[reg_test == k]
            variants = {
                "base": [],
                "guided": flagged,
                "targeted": rng.choice(pool_k, size=min(n_var, len(pool_k)), replace=False),
                "random": rng.choice(tn[reg_test != k], size=n_var, replace=False),
            }
            rec = {"dataset": ds, "regime": k, "n_eval": int(len(eval_ends)),
                   "n_flagged": int(len(flagged)), "far": {}}
            for tag, extra in variants.items():
                if len(extra) and tag == "guided" and len(extra) > n_var:
                    extra = rng.choice(extra, n_var, replace=False)
                feats = feats_pool
                if len(extra):
                    feats = np.vstack([feats, X[wins(np.asarray(extra))].reshape(len(extra), -1)])
                m2 = pca_fit(feats)
                rec["far"][tag] = float((pca_score(m2, ew) > tau).mean())
            rec["gap_targeted_pp"] = 100 * (rec["far"]["base"] - rec["far"]["targeted"]
                                             - (rec["far"]["base"] - rec["far"]["random"]))
            rec["gap_guided_pp"] = 100 * (rec["far"]["base"] - rec["far"]["guided"]
                                          - (rec["far"]["base"] - rec["far"]["random"]))
            rows.append(rec)
            print(f"[{ds} r{k}] base {rec['far']['base']:.1%} | 定向 {rec['far']['targeted']:.1%} | "
                  f"指导 {rec['far']['guided']:.1%} | 随机 {rec['far']['random']:.1%} "
                  f"(定向gap {rec['gap_targeted_pp']:+.1f}pp)", flush=True)
    json.dump(rows, open(cpath("repair_pca.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    if rows:
        print("\nPCA 汇总: 定向gap %.1fpp | 指导gap %.1fpp" % (
            np.mean([r["gap_targeted_pp"] for r in rows]),
            np.mean([r["gap_guided_pp"] for r in rows])))


if __name__ == "__main__":
    main()
