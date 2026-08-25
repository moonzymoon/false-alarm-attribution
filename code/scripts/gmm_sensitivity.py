"""GMM train-only 敏感性: 用训练段数据拟合 GMM, 与全序列拟合的模式分配对比.
选 3 个代表单元(SWaT/SMD/MetroPT3 各 1), 只比较模式分配一致性和 top-1 变化."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402
from regimes.regimes import RegimeModel, features_at  # noqa: E402


def main():
    out = {}
    for ds in ("SWaT", "SMD", "MetroPT3"):
        X, Y = load_raw(ds)
        a, b = split_of(len(X))

        # 全序列拟合 (论文当前做法)
        rm_full = RegimeModel().fit(X, seed=0)

        # 仅训练段拟合
        rm_train = RegimeModel().fit(X[a:b], seed=0)

        # 测试段正常窗的模式分配对比
        cs = np.cumsum(np.concatenate([[0], (Y != 0).astype(np.int64)]))
        te = np.arange(b + WINDOW - 1, min(b + 50000, len(X)))
        ok = (cs[te + 1] - cs[te + 1 - WINDOW]) == 0
        tn = te[ok][:5000]

        reg_full = rm_full.transform(features_at(X, tn))
        reg_train = rm_train.transform(features_at(X, tn))

        # 一致率: 同一窗口被分到同一模式的比例
        # (模式编号可能不同, 用匈牙利匹配)
        from scipy.optimize import linear_sum_assignment
        K = max(rm_full.K, rm_train.K)
        conf = np.zeros((K, K))
        for i, j in zip(reg_full, reg_train):
            conf[i, j] += 1
        row, col = linear_sum_assignment(-conf)
        mapping = dict(zip(col, row))
        reg_train_mapped = np.array([mapping.get(r, -1) for r in reg_train])
        agree = float(np.mean(reg_full == reg_train_mapped))

        # ARI (不考虑编号对应)
        from sklearn.metrics import adjusted_rand_score
        ari = float(adjusted_rand_score(reg_full, reg_train))

        rec = {"dataset": ds, "n_test_windows": len(tn),
               "full_K": rm_full.K, "train_K": rm_train.K,
               "hungarian_agreement": round(agree, 3),
               "adjusted_rand_index": round(ari, 3)}
        out[ds] = rec
        print(f"[{ds}] K_full={rm_full.K} K_train={rm_train.K} "
              f"agree={agree:.1%} ARI={ari:.3f}", flush=True)

    json.dump(out, open(cpath("gmm_sensitivity.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    mean_agree = np.mean([v["hungarian_agreement"] for v in out.values()])
    mean_ari = np.mean([v["adjusted_rand_index"] for v in out.values()])
    print(f"\n平均匈牙利一致率: {mean_agree:.1%} | 平均 ARI: {mean_ari:.3f}")
    print("判定:", "稳定(无泄露影响)" if mean_agree > 0.85 else "需注意")


if __name__ == "__main__":
    main()
