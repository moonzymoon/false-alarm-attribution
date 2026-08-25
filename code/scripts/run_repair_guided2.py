"""工况级指导修复 v2 (R3 残余项4, 修正设计缺陷):
  - 评测集 = 该 regime 的全部测试正常窗 (非 FA 子集);
  - τ 固定用基础模型 (留出重训版) 的校准阈值, 不随重训重算;
  - 三组: 基线(不补) / 定向(补该 regime 随机真窗) / 随机(补其他 regime 窗) /
    归因指导(补 RC-CA 判为 regime 的告警窗——部署语义: 告警即采集起点).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import WINDOW, load_raw, split_of, cpath  # noqa: E402
from rcca.rcca import _RegimeBank, rcca_attribute  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402


def main():
    import json
    from sklearn.ensemble import IsolationForest
    rows = []
    for ds in ("SWaT", "SMD", "MetroPT3"):
        print(f"[{ds}] 重建混合单元 (取 regime 上下文) ...", flush=True)
        units = gp._mixed_unit(ds)
        ctx = gp._MIX_CTX[ds]
        tn, reg_test, tr_ends, reg_tr = ctx["tn"], ctx["reg_test"], ctx["tr_ends"], ctx["reg_tr"]
        X, Y = load_raw(ds)
        a, b = split_of(len(X))

        def wins(stream_ends):
            return stream_ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]

        for u in units:
            k = int(u.gt_regime[0])
            tau_fixed = u.tau                       # 基础模型 (留出重训) 的校准阈值
            pool = u.pool_ends
            feats_pool = X[wins(pool)].reshape(len(pool), -1)
            eval_ends = tn[reg_test == k]
            rng = np.random.default_rng(11)
            n_var = int(len(pool) * 0.10)
            pool_k = tn[reg_test == k]
            # 归因指导: RC-CA 判 regime 的告警窗
            bank = _RegimeBank(u.pool_windows(), seed=0)
            W = u.windows()
            y = (u.gt_type == "variable").astype(int)
            attr = rcca_attribute(u, W, bank)
            g, d = tl.calibrate(tl._sub(attr, u.val_mask), y[u.val_mask])
            pred = tl._predict(attr, g, d)
            flagged = u.ends[(~u.val_mask) & (pred == 0)]
            variants = {"base": [], "guided": flagged,
                        "targeted": rng.choice(pool_k, size=min(n_var, len(pool_k)), replace=False),
                        "random": rng.choice(tn[reg_test != k], size=n_var, replace=False)}
            rec = {"dataset": ds, "regime": k, "n_flagged": len(flagged),
                   "n_eval": len(eval_ends), "far": {}}
            for tag, extra in variants.items():
                if len(extra) and tag == "guided" and len(extra) > n_var:
                    extra = rng.choice(extra, n_var, replace=False)
                feats = feats_pool
                if len(extra):
                    feats = np.vstack([feats, X[wins(np.asarray(extra))].reshape(len(extra), -1)])
                ifo = IsolationForest(n_estimators=100, contamination="auto",
                                      random_state=0, n_jobs=-1).fit(feats)
                ew = X[wins(eval_ends)].reshape(len(eval_ends), -1)
                rec["far"][tag] = float((-ifo.decision_function(ew) > tau_fixed).mean())
            rec["gap_guided_pp"] = 100 * (rec["far"]["base"] - rec["far"]["guided"]
                                          - (rec["far"]["base"] - rec["far"]["random"]))
            rec["gap_targeted_pp"] = 100 * (rec["far"]["base"] - rec["far"]["targeted"]
                                            - (rec["far"]["base"] - rec["far"]["random"]))
            rows.append(rec)
            print(f"  regime{k}: base {rec['far']['base']:.1%} | 定向 {rec['far']['targeted']:.1%} | "
                  f"指导 {rec['far']['guided']:.1%} | 随机 {rec['far']['random']:.1%} "
                  f"(定向gap {rec['gap_targeted_pp']:+.1f}pp, 指导gap {rec['gap_guided_pp']:+.1f}pp)",
                  flush=True)
    with open(cpath("repair_guided2.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1, default=float)
    if rows:
        print(f"\n平均: 定向gap {np.mean([r['gap_targeted_pp'] for r in rows]):+.1f}pp, "
              f"指导gap {np.mean([r['gap_guided_pp'] for r in rows]):+.1f}pp")


if __name__ == "__main__":
    main()
