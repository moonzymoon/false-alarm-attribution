"""消融实验 (R2): (a) GMM 工况数 K ∈ {4,6,8,10}; (b) RC-CA 邻域 K_nn ∈ {1,3,5,10};
(c) 方法运行稳定性: bank 种子 {0,1,2} 的指标均值±std.
在混合单元上重跑 RC-CA (其余方法对 K/K_nn 不敏感, 只随种子波动).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402


def rcca_only_eval(unit, bank, knn=None):
    """跑 RC-CA + 两层协议, 返回核心指标 (复用 two_layer 的标定逻辑)."""
    W = unit.windows()
    y = (unit.gt_type == "variable").astype(int)
    val, test = unit.val_mask, ~unit.val_mask
    attr = rcca_attribute(unit, W, bank, K=knn or 5)
    gamma, delta = tl.calibrate(tl._sub(attr, val), y[val])
    pred = tl._predict(attr, gamma, delta)
    m = {"layer1_macro_f1": tl._macro_f1(y[test], pred[test])}
    vmask = test & (y == 1)
    if vmask.sum():
        phi = attr["phi"][vmask]
        top1 = [int(np.argsort(-phi[i])[0] in set(unit.gt_vars[gi]))
                for i, gi in enumerate(np.where(vmask)[0])]
        m["layer2_top1"] = float(np.mean(top1))
    rmask = test & (y == 0)
    if rmask.sum():
        m["regime_hit"] = float(np.mean(np.asarray(attr["regime"])[rmask]
                                        == np.asarray(unit.gt_regime)[rmask]))
    return m


def main():
    import json
    from evaluation.gt_pool import build_all
    units = build_all()
    units = [u for u in units if u.name.startswith("iforest_") and "_mix_" in u.name]
    res = {"K_gmm": {}, "K_nn": {}, "seed": {}}
    for u in units:
        P = u.pool_windows()
        # (a) GMM K
        for K in (4, 6, 8, 10):
            bank = _RegimeBank(P, seed=0); bank.gmm.n_components = K  # 重新 fit 需要真实重聚
            from sklearn.mixture import GaussianMixture
            bank.gmm = GaussianMixture(K, covariance_type="diag", random_state=0,
                                       n_init=2, max_iter=200, reg_covar=1e-3).fit(bank.Fs)
            bank.labels = bank.gmm.predict(bank.Fs)
            bank.members = {k: np.where(bank.labels == k)[0] for k in range(K)}
            res["K_gmm"].setdefault(u.name, {})[K] = rcca_only_eval(u, bank)
            print(f"{u.name} K={K}: {res['K_gmm'][u.name][K]}", flush=True)
        # (b) kNN 邻域
        bank = _RegimeBank(P, seed=0)
        for knn in (1, 3, 5, 10):
            res["K_nn"].setdefault(u.name, {})[knn] = rcca_only_eval(u, bank, knn=knn)
            print(f"{u.name} K_nn={knn}: {res['K_nn'][u.name][knn]}", flush=True)
        # (c) 种子
        for sd in (0, 1, 2):
            bank = _RegimeBank(P, seed=sd)
            res["seed"].setdefault(u.name, {})[sd] = rcca_only_eval(u, bank)
            print(f"{u.name} seed={sd}: {res['seed'][u.name][sd]}", flush=True)
    with open(cpath("ablation.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    print("已写入 ablation.json")


if __name__ == "__main__":
    main()
