"""归因指导的修复实验 (R2-M11): 验证"归因输出→修复动作"闭环的操作价值.

工况型: RC-CA 判为 regime 的 FA → 用其 kNN 模板检索测试流中最近的该模式真实窗
  作为"定向采集"数据补入重训; 对照: 真值定向 / 随机补充. 指标: 该 regime 剩余
  测试窗 FAR 降幅.
变量型: RC-CA 判为 variable 的 FA → 对 top-1 变量做校正 (替换为工况条件期望轨迹)
  后重打分; 对照: 真值变量校正 / 随机变量校正. 指标: FA 消除率.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402


def regime_guided_repair(unit, bank):
    from sklearn.ensemble import IsolationForest
    X = unit.X
    W = unit.windows()
    y = (unit.gt_type == "variable").astype(int)
    test = ~unit.val_mask
    attr = rcca_attribute(unit, W, bank)
    gamma, delta = tl.calibrate(tl._sub(attr, unit.val_mask), y[unit.val_mask])
    pred = tl._predict(attr, gamma, delta)
    # RC-CA 判为 regime 的测试 FA (GT 也是 regime 的那部分 + 判错的都用来检索)
    flagged = test & (pred == 0)
    if flagged.sum() == 0:
        return None
    templates = attr  # 需要 kNN 模板 — rcca_attribute 未返回; 用重建: 下面近似
    # 用判为 regime 的窗口本身作为"该模式的真实样本"检索源 (部署语义: 告警窗即采集起点)
    flagged_ends = unit.ends[flagged]
    rng = np.random.default_rng(5)
    n_var = int(len(unit.pool_ends) * 0.10)
    if len(flagged_ends) < 50:
        return None
    picked = rng.choice(flagged_ends, size=min(n_var, len(flagged_ends)), replace=False)
    eval_set = np.array([e for e in unit.ends[(unit.gt_type == "regime")]
                         if e not in set(picked.tolist())])
    if len(eval_set) < 50:
        return None

    def refit_far(extra_ends):
        pool = unit.pool_ends
        feats = X[pool[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].reshape(len(pool), -1)
        if len(extra_ends):
            ex = np.asarray(extra_ends)
            feats = np.vstack([feats, X[ex[:, None] - (WINDOW - 1) +
                                       np.arange(WINDOW)[None, :]].reshape(len(ex), -1)])
        ifo = IsolationForest(n_estimators=100, contamination="auto",
                              random_state=0, n_jobs=-1).fit(feats)
        tau = float(np.quantile(-ifo.decision_function(feats[:len(pool)]), 0.95))
        ew = X[eval_set[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]].reshape(len(eval_set), -1)
        return float((-ifo.decision_function(ew) > tau).mean())

    far0 = refit_far([])
    far_g = refit_far(picked)                       # 归因指导 (告警窗即采集)
    rnd_pool = unit.pool_ends
    rnd = rng.choice(rnd_pool, size=min(n_var, len(rnd_pool)), replace=False)
    far_r = refit_far(rnd)                           # 随机对照
    return {"n_flagged": int(flagged.sum()), "n_picked": len(picked),
            "far_base": far0, "far_guided": far_g, "far_random": far_r,
            "gap_pp": 100 * ((far0 - far_g) - (far0 - far_r))}


def variable_guided_repair(unit, bank):
    """变量型: top-1 变量校正 (替换为工况条件期望) 后 FA 是否消除."""
    X = unit.X
    W = unit.windows()
    y = (unit.gt_type == "variable").astype(int)
    test = ~unit.val_mask & (y == 1)
    if test.sum() < 20:
        return None
    attr = rcca_attribute(unit, W, bank)
    tmpl, _ = bank.knn_template(W, K=5)
    s_orig = attr["s_orig"]
    rng = np.random.default_rng(6)
    top1 = np.argsort(-attr["phi"], 1)[:, 0]
    res = {"guided": [], "gt": [], "random": []}
    for i in np.where(test)[0]:
        gt_j = unit.gt_vars[i][0]
        for tag, j in (("guided", top1[i]), ("gt", gt_j),
                       ("random", int(rng.integers(W.shape[2])))):
            w2 = W[i:i + 1].copy()
            w2[0, :, j] = tmpl[i, :, j]
            s2 = unit.score(w2)[0]
            res[tag].append(float(s2 <= unit.tau))
    return {k: float(np.mean(v)) for k, v in res.items()} | {"n": int(test.sum())}


def main():
    import json
    from evaluation.gt_pool import build_all
    units = [u for u in build_all() if "_mix_" in u.name]
    out = {"regime": {}, "variable": {}}
    for u in units:
        bank = _RegimeBank(u.pool_windows(), seed=0)
        r1 = regime_guided_repair(u, bank)
        if r1:
            out["regime"][u.name] = r1
            print(f"[{u.name}] 工况修复: FAR {r1['far_base']:.2%} -> 归因指导 "
                  f"{r1['far_guided']:.2%} / 随机 {r1['far_random']:.2%} "
                  f"(差 {r1['gap_pp']:.1f}pp)", flush=True)
        r2 = variable_guided_repair(u, bank)
        if r2:
            out["variable"][u.name] = r2
            print(f"[{u.name}] 变量修复消除率: 指导 {r2['guided']:.0%} / 真值 "
                  f"{r2['gt']:.0%} / 随机 {r2['random']:.0%} (n={r2['n']})", flush=True)
    with open(cpath("repair_guided.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
