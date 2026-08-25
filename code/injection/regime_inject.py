"""工况级注入 (阶段1 任务2b): 训练集留出某正常工况 -> 留出工况即真值.

仅 iforest (可廉价重训): 从弱训练段剔除工况 k 的窗口后重训,
  - 阈值: 留出后模型的校准段 (regime != k) 正常窗分位;
  - 工况型 FA: 测试段属于 regime k 的全窗正常窗且超阈 -> 真值 regime(k);
  - 渐变过渡组: 测试段内容向 regime k 源段渐变混合 (α: 0→1), 过渡窗超阈 -> 真值 regime(k, 过渡).

cmhmil/AT 不可重训 (固定 checkpoint), 工况级真值协议只覆盖 iforest —— 如实记录.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath, FAR_TARGETS  # noqa: E402
from regimes.regimes import RegimeModel  # noqa: E402


def fit_iforest_excluding(X, a, b, regime_win, keep_regimes, window=WINDOW,
                          max_fit=200_000, seed=0):
    """用弱训练段中 regime ∈ keep_regimes 的窗口拟合 IsolationForest.
    regime_win: 与窗口对齐的 regime 标签函数/数组 (窗尾索引 -> regime)."""
    from sklearn.ensemble import IsolationForest
    ends = np.arange(a + window - 1, b)
    reg = regime_win(ends)
    mask = np.isin(reg, keep_regimes)
    ends_fit = ends[mask]
    if len(ends_fit) > max_fit:
        rng = np.random.default_rng(seed)
        ends_fit = ends_fit[np.sort(rng.choice(len(ends_fit), max_fit, replace=False))]
    idx = np.arange(window)[None, :] + (ends_fit[:, None] - (window - 1))
    feats = X[idx].reshape(len(ends_fit), -1)
    ifo = IsolationForest(n_estimators=100, contamination="auto",
                          random_state=seed, n_jobs=-1).fit(feats)
    return ifo, ends, reg


def scores_of(ifo, X, ends, window=WINDOW):
    idx = np.arange(window)[None, :] + (ends[:, None] - (window - 1))
    return -ifo.decision_function(X[idx].reshape(len(ends), -1))


def run_regime_holdout(dataset, n_gradual=10, seed=0):
    """主入口: 对数据集做 GMM 工况识别 + 逐工况留出注入. 返回记录列表."""
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    rm = RegimeModel().fit(X, seed=seed)
    K = rm.K

    # 全流窗口 regime 预测 (分块, 降内存)
    def regime_of_ends(ends):
        out = np.empty(len(ends), np.int32)
        for i in range(0, len(ends), 200_000):
            e = ends[i:i + 200_000]
            idx = np.arange(WINDOW)[None, :] + (e[:, None] - (WINDOW - 1))
            F = np.concatenate([X[idx].mean(1),
                                ((X[idx] * (np.arange(WINDOW) - (WINDOW - 1) / 2)[None, :, None]).sum(1)
                                 / (((np.arange(WINDOW) - (WINDOW - 1) / 2) ** 2).sum())),
                                X[idx].var(1)], axis=1).astype(np.float32)
            out[i:i + 200_000] = rm.transform(F)
        return out

    # 测试段全窗正常掩码
    cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
    test_ends = np.arange(b + WINDOW - 1, len(X))
    body_ok = (cs[test_ends + 1] - cs[test_ends + 1 - WINDOW]) == 0
    test_normal_ends = test_ends[body_ok]
    reg_test = regime_of_ends(test_normal_ends)

    records = []
    for k in range(K):
        # 重训: 剔除 regime k
        keep = [r for r in range(K) if r != k]
        from sklearn.ensemble import IsolationForest
        ends_tr = np.arange(a + WINDOW - 1, b)
        reg_tr = regime_of_ends(ends_tr)
        fit_ends = ends_tr[np.isin(reg_tr, keep)]
        rng = np.random.default_rng(seed)
        if len(fit_ends) > 200_000:
            fit_ends = fit_ends[np.sort(rng.choice(len(fit_ends), 200_000, replace=False))]
        idx = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
        feats = X[idx].reshape(len(fit_ends), -1)
        ifo = IsolationForest(n_estimators=100, contamination="auto",
                              random_state=seed, n_jobs=-1).fit(feats)
        # 阈值: 留出后模型的校准段正常窗 (regime!=k)
        cal_ends = ends_tr[reg_tr != k]
        tau = {t: float(np.quantile(scores_of(ifo, X, cal_ends), 1 - t)) for t in FAR_TARGETS}
        # 测试段 regime==k 的正常窗分数
        mask_k = reg_test == k
        n_k = int(mask_k.sum())
        if n_k == 0:
            continue
        sk = scores_of(ifo, X, test_normal_ends[mask_k])
        for t in FAR_TARGETS:
            fa = sk > tau[t]
            records.append({"cause_type": "regime", "regime": int(k), "far_target": t,
                            "tau": tau[t], "n_regime_windows": n_k,
                            "n_fa_windows": int(fa.sum()),
                            "valid_rate": float(fa.mean()),
                            "mean_score": float(sk.mean()), "mode": "holdout"})
        # 渐变过渡: 从 regime k 取源段, 混入测试段正常位置
        src_ends = test_normal_ends[mask_k]
        if len(src_ends) > 50:
            src_pool = src_ends[np.linspace(0, len(src_ends) - 1, 200).astype(int)]
            dst_candidates = test_normal_ends[::max(1, len(test_normal_ends) // (n_gradual * 40))]
            # 渐变混合只统计全窗正常的窗口 (防与真实异常重叠造成真值污染)
            ends_all = np.arange(b + WINDOW - 1, len(X))
            body_ok_all = (cs[ends_all + 1] - cs[ends_all + 1 - WINDOW]) == 0
            ok_set = set(ends_all[body_ok_all].tolist())
            rng2 = np.random.default_rng(seed + 1)
            dsts = rng2.choice(dst_candidates, size=min(n_gradual, len(dst_candidates)), replace=False) \
                if len(dst_candidates) > n_gradual else dst_candidates
            L = 200
            for d in dsts:
                if d - L // 2 < b or d + L // 2 >= len(X):
                    continue
                Xm = X.copy()
                src0 = int(rng2.choice(src_pool))
                t_rel = np.arange(L) / (L - 1)
                alpha = t_rel ** 2  # 渐变: 前平后陡
                for i, tt in enumerate(range(d - L // 2, d + L // 2)):
                    src_pt = min(src0 + i, len(X) - 1)
                    Xm[tt] = (1 - alpha[i]) * X[tt] + alpha[i] * X[src_pt]
                ends = np.array([e for e in range(d - L // 2 + WINDOW - 1, d + L // 2)
                                 if e in ok_set], dtype=int)
                s_after = scores_of(ifo, Xm, ends)
                for t in FAR_TARGETS:
                    records.append({"cause_type": "regime", "regime": int(k), "far_target": t,
                                    "tau": tau[t], "n_regime_windows": len(ends),
                                    "n_fa_windows": int((s_after > tau[t]).sum()),
                                    "valid_rate": float((s_after > tau[t]).mean()),
                                    "mean_score": float(s_after.mean()), "mode": "gradual"})
    return records, rm


if __name__ == "__main__":
    import json
    all_stats = {}
    for ds in ("SWaT", "SMD", "MetroPT3"):
        print(f"[iforest,{ds}] 工况级注入 ...", flush=True)
        try:
            recs, rm = run_regime_holdout(ds)
            np.savez_compressed(cpath(f"inj_regime_iforest_{ds}.npz"),
                                records=np.array(recs, dtype=object),
                                K=rm.K, bic=json.dumps(rm.bic_))
            agg = {}
            for r in recs:
                key = f"K{r['regime']}_{r['mode']}_far{int(r['far_target']*100)}"
                agg.setdefault(key, []).append(r)
            stats = {k: {"valid_rate": float(np.mean([x["valid_rate"] for x in v])),
                         "n_regime_windows": v[0]["n_regime_windows"],
                         "n_fa_windows": int(np.sum([x["n_fa_windows"] for x in v]))}
                     for k, v in agg.items()}
            all_stats[ds] = {"K": rm.K, "bic": rm.bic_, "stats": stats}
            print(f"  K={rm.K} (BIC 最优); " + "; ".join(
                f"{k}: v={v['valid_rate']:.0%} nFA={v['n_fa_windows']}" for k, v in stats.items()))
        except Exception as e:
            import traceback; traceback.print_exc()
            all_stats[ds] = {"error": f"{type(e).__name__}: {e}"}
    with open(cpath("inj_regime_summary.json"), "w", encoding="utf-8") as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=1)
    print("汇总已写入 inj_regime_summary.json")
