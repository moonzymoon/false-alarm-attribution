"""修复实验 + 对照组 (v3 必改2): 归因→修正闭环的可操作性验证.

设计: 对每个有效 regime k (留出重训 iforest M0, FAR@τ_k 已知):
  - 定向修复: 训练池补入 10% 量级的 regime k 窗口 (模拟"归因说工况型→定向采集该工况");
  - 随机对照: 补入同量级随机其他正常窗 (排除"补任何数据都变好"的混淆);
  - 重训后在该 regime 剩余测试正常窗上测 FAR (补充进训练的窗不再参与评测, 防泄漏).
预期: 定向组 FAR 下降显著高于随机组; 效应量诚实报告 (重构型可 20-40%, 此处 iforest).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath  # noqa: E402
from regimes.regimes import RegimeModel, features_at  # noqa: E402

FAR = 0.05


def run(dataset, frac=0.10):
    from sklearn.ensemble import IsolationForest
    X, Y = load_raw(dataset)
    a, b = split_of(len(X))
    rm = RegimeModel().fit(X, seed=0)
    K = rm.K
    tr_ends = np.arange(a + WINDOW - 1, b)
    reg_tr = rm.transform(features_at(X, tr_ends))
    cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
    test_ends = np.arange(b + WINDOW - 1, len(X))
    body_ok = (cs[test_ends + 1] - cs[test_ends + 1 - WINDOW]) == 0
    tn = test_ends[body_ok]
    reg_test = rm.transform(features_at(X, tn))

    rows = []
    for k in range(K):
        fit_ends = tr_ends[reg_tr != k]
        rng = np.random.default_rng(0)
        if len(fit_ends) > 200_000:
            fit_ends = fit_ends[np.sort(rng.choice(len(fit_ends), 200_000, replace=False))]

        def fit_and_far(extra_ends_pool, tag, exclude=None):
            ifo = IsolationForest(n_estimators=100, contamination="auto",
                                  random_state=0, n_jobs=-1)
            idx = np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))
            feats = X[idx].reshape(len(fit_ends), -1)
            if len(extra_ends_pool):
                xe = np.asarray(extra_ends_pool)
                xidx = np.arange(WINDOW)[None, :] + (xe[:, None] - (WINDOW - 1))
                feats = np.vstack([feats, X[xidx].reshape(len(xe), -1)])
            ifo.fit(feats)
            calw = X[np.arange(WINDOW)[None, :] + (fit_ends[:, None] - (WINDOW - 1))].reshape(len(fit_ends), -1)
            tau = float(np.quantile(-ifo.decision_function(calw), 1 - FAR))
            ev = tn[(reg_test == k)]
            if exclude is not None and len(exclude):
                ev = np.array([e for e in ev if e not in set(exclude.tolist())])
            ew = X[np.arange(WINDOW)[None, :] + (ev[:, None] - (WINDOW - 1))].reshape(len(ev), -1)
            far = float((-ifo.decision_function(ew) > tau).mean())
            return far

        pool_k_all = tn[reg_test == k]           # 可用作"定向采集"的该工况数据
        n_var = int(len(fit_ends) * frac)
        if len(pool_k_all) < n_var or len(pool_k_all) < 300:
            continue
        rng2 = np.random.default_rng(3)
        picked = rng2.choice(pool_k_all, size=n_var, replace=False)
        eval_k = np.array([e for e in pool_k_all if e not in set(picked.tolist())])
        if len(eval_k) < 100:
            continue
        # 用 eval 集统一评测三种模型
        far0 = fit_and_far([], "base", exclude=picked)
        far_t = fit_and_far(picked, "targeted", exclude=picked)
        rnd_pool = tn[reg_test != k]
        rnd = rng2.choice(rnd_pool, size=n_var, replace=False) if len(rnd_pool) >= n_var else rnd_pool
        far_r = fit_and_far(rnd, "random", exclude=picked)
        rows.append({"dataset": dataset, "regime": int(k), "n_var": n_var,
                     "far_base": far0, "far_targeted": far_t, "far_random": far_r,
                     "drop_targeted": far0 - far_t, "drop_random": far0 - far_r,
                     "gap_pp": 100 * ((far0 - far_t) - (far0 - far_r))})
        print(f"[{ds_str(dataset)}] regime{k}: FAR {far0:.2%} -> 定向 {far_t:.2%} / "
              f"随机 {far_r:.2%} (定向-随机 = {rows[-1]['gap_pp']:.1f}pp)", flush=True)
    return rows


def ds_str(ds):
    return ds


if __name__ == "__main__":
    import json
    all_rows = []
    for ds in ("SWaT", "SMD", "MetroPT3"):
        try:
            all_rows.extend(run(ds))
        except Exception as e:
            import traceback; traceback.print_exc()
    with open(cpath("repair_experiment.json"), "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=1)
    if all_rows:
        gt = np.mean([r["gap_pp"] for r in all_rows])
        print(f"\n平均 (定向-随机) FAR 下降差: {gt:.1f}pp (≥10pp 为归因指导价值成立线)")
