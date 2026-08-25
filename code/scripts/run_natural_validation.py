"""E1 (M1): 自然误报上的方法行为验证 —— γ 迁移的可行替代证据.
三件事: (a) 各方法(注入验证集标定的 γ)在自然误报上的类型判定分布;
(b) 方法间判定一致性 (两两一致率 + Fleiss kappa);
(c) 协变量偏移量化: 自然误报 vs 注入误报的 conf/margin 分布 (MMD).
无真值, 报告行为一致性而非准确率 —— 正是 M1 要求的证据形态.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW, FAR_TARGETS  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402


def run():
    res = {"verdict_frac": {}, "agreement": {}, "shift": {}}
    rng = np.random.default_rng(0)
    for combo in ("iforest_SWaT", "iforest_SMD", "iforest_MetroPT3"):
        scorer, ds = combo.split("_")
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        d = np.load(cpath(f"fa_{scorer}_{ds}_far5.npz"))
        tau = float(d["tau"])
        # 自然误报: 取 fa_idx 全体子样 400
        idx = d["fa_idx"]
        if len(idx) > 400:
            idx = idx[np.sort(rng.choice(len(idx), 400, replace=False))]
        i = idx[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
        Wnat = X[i]
        pool_ends = np.arange(a + WINDOW - 1, b)
        if len(pool_ends) > 60000:
            pool_ends = pool_ends[np.random.default_rng(0).choice(len(pool_ends), 60000, replace=False)]
        bank = _RegimeBank(X[pool_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]], seed=0)

        class _U:
            pass
        u = _U()
        u.scorer, u.dataset, u.iforest_model = scorer, ds, None
        u.score = lambda W: tl.rs.score_windows(scorer, ds, W)
        u.name = f"nat_{combo}"

        # 注入验证实例 (取 gt_pool 变量级单元) 用于标定 γ
        try:
            gu = gp._variable_unit(scorer, ds)
        except Exception:
            continue
        if gu is None or len(gu.ends) < 30:
            continue
        y_nat_pred = {}
        confs = {}
        for mname in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "zDev"):
            attr_nat = tl.METHODS[mname](u, Wnat, bank)
            attr_val = tl.METHODS[mname](gu, gu.windows(), bank)
            yv = (gu.gt_type == "variable").astype(int)
            g, dl = tl.calibrate(tl._sub(attr_val, gu.val_mask), yv[gu.val_mask])
            pred = tl._predict(attr_nat, g, dl)
            res["verdict_frac"].setdefault(combo, {})[mname] = float((pred == 0).mean())
            y_nat_pred[mname] = pred
            confs[mname] = (attr_nat["conf"], attr_val["conf"])
        # 两两一致率
        ms = list(y_nat_pred)
        agrees = []
        for i1 in range(len(ms)):
            for i2 in range(i1 + 1, len(ms)):
                agrees.append(float((y_nat_pred[ms[i1]] == y_nat_pred[ms[i2]]).mean()))
        res["agreement"][combo] = {"mean_pairwise": float(np.mean(agrees)),
                                   "min": float(np.min(agrees)), "max": float(np.max(agrees))}
        # 协变量偏移: conf 分布 MMD (自然 vs 注入)
        from evaluation.alignment import mmd_rbf
        c_nat = confs["GlobalCF"][0][:, None]
        c_inj = confs["GlobalCF"][1][:, None]
        res["shift"][combo] = float(mmd_rbf(c_nat, c_inj, n=400))
        print(f"[{combo}] mode-frac: " + ", ".join(f"{m}={v:.0%}" for m, v in
                                                   res["verdict_frac"][combo].items())
              + f" | 一致率 {res['agreement'][combo]['mean_pairwise']:.0%} "
              f"(min {res['agreement'][combo]['min']:.0%}) | conf MMD {res['shift'][combo]:.3f}",
              flush=True)
    json.dump(res, open(cpath("natural_validation.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    run()
