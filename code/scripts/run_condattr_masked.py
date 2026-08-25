"""CondAttr 掩码距离检索变体 (R3 残余项2, 附录消融).

论文 Eq.7/10 的检索在非目标通道上算距离 (W^(-j) 掩码); 我们的复现端口用全窗嵌入
距离 (工程折中). 本脚本实现逐变量的掩码检索: 对每个目标传感器 j, 把查询与库窗的
通道 j 置零后查 UMAP transform, 取 K=3 近邻. 代价 O(D) 次 transform —— 在
iforest×SWaT 混合单元上与全窗变体对比 (附录表).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import scorers_rescore as rs  # noqa: E402
from baselines.condattr import CondAttr  # noqa: E402


def masked_condattr_attribute(unit, Warr, bank, K=3, n_query_cap=150, db_cap=3000):
    """逐变量掩码检索的 CondAttr. 附录消融: 库窗截断 db_cap=3000 (UMAP transform
    对 2 万窗的逐变量重嵌入不可行, 截断后每单元 ~D×20s)."""
    from baselines.condattr import CondAttr
    n, Wn, D = Warr.shape
    key = ("condattr_masked", unit.name)
    if key not in tl._CACHE:
        def f(flats):
            return rs.score_windows(unit.scorer, unit.dataset,
                                    flats.reshape(len(flats), Wn, -1),
                                    iforest_model=unit.iforest_model)
        tl._CACHE[key] = CondAttr(f).fit(bank.P.reshape(len(bank.P), -1))
    ca = tl._CACHE[key]
    rng = np.random.default_rng(0)
    keep = np.arange(n) if n <= n_query_cap else np.sort(rng.choice(n, n_query_cap, replace=False))
    db_idx = (np.arange(len(ca.db_feats_)) if len(ca.db_feats_) <= db_cap
              else np.sort(rng.choice(len(ca.db_feats_), db_cap, replace=False)))
    db_raw_full = ca.db_feats_.reshape(len(ca.db_feats_), Wn, D)
    db_raw = db_raw_full[db_idx]
    phi = np.zeros((n, D))
    s_orig = unit.score(Warr)
    for j in range(D):
        q = Warr[keep].copy(); q[:, :, j] = 0
        db_j = db_raw.copy(); db_j[:, :, j] = 0
        qe = ca._reducer.transform(q.reshape(len(keep), -1).astype(np.float32))
        de = ca._reducer.transform(db_j.reshape(len(db_j), -1).astype(np.float32))
        d2 = np.linalg.norm(de[None] - qe[:, None], axis=2)
        nb = np.argsort(d2, 1)[:, :K]
        nb_mean = db_j[nb].mean(1)                       # (nq, W, D) 目标通道已置零
        nb_mean[:, :, j] = db_raw[nb][:, :, :, j].mean(1)  # 恢复目标通道原值
        drops = []
        for i, gi in enumerate(keep):
            w2 = Warr[gi:gi + 1].copy()
            w2[0, :, j] = nb_mean[i, :, j]
            drops.append(s_orig[gi] - unit.score(w2)[0])
        phi[keep, j] = drops
    conf = phi.max(1) / (np.abs(s_orig) + 1e-9)
    return {"phi": phi, "conf": conf, "delta": None, "regime": None}


def main():
    import json
    from evaluation.gt_pool import build_all
    units = [u for u in build_all() if "_mix_" in u.name][:4]   # 附录: 前 4 单元 (SWaT)
    res = {}
    for u in units:
        bank = _RegimeBank(u.pool_windows(), seed=0)
        W = u.windows()
        y = (u.gt_type == "variable").astype(int)
        test = ~u.val_mask
        r_mask = masked_condattr_attribute(u, W, bank)
        r_full = tl.METHODS["CondAttr"](u, W, bank)
        def top1(attr):
            vm = test & (y == 1)
            if vm.sum() == 0:
                return None
            phi = attr["phi"][vm]
            return float(np.mean([int(np.argsort(-phi[i])[0] in set(u.gt_vars[gi]))
                                  for i, gi in enumerate(np.where(vm)[0])]))
        g_m, d_m = tl.calibrate(tl._sub(r_mask, u.val_mask), y[u.val_mask])
        g_f, _ = tl.calibrate(tl._sub(r_full, u.val_mask), y[u.val_mask])
        l1_m = tl._macro_f1(y[test], tl._predict(r_mask, g_m, d_m)[test])
        l1_f = tl._macro_f1(y[test], tl._predict(r_full, g_f, None)[test])
        res[u.name] = {"masked": {"L1": l1_m, "top1": top1(r_mask)},
                       "full": {"L1": l1_f, "top1": top1(r_full)}}
        print(f"{u.name}: masked L1={l1_m:.3f} top1={res[u.name]['masked']['top1']} | "
              f"full L1={l1_f:.3f} top1={res[u.name]['full']['top1']}", flush=True)
    with open(cpath("condattr_masked.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)


if __name__ == "__main__":
    main()
