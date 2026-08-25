"""TreeSHAP 取反的方向/排序保真验证 (回应外部审查 B#17):
对 2 个 iforest 混合单元的报警窗, 比较每窗的
  (a) negated-TreeSHAP 逐通道重要度 (论文所用, 与 run_shap_attr 同码路)
  (b) GlobalCF 逐通道得分下降 (独立于 TreeSHAP 的得分型度量)
报告: 每窗 Spearman 相关(均值/中位) + top-1 通道一致率 + 对 GT 通道的 top-1 命中对比.
输出 _cache/validate_treeshap.json
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath  # noqa: E402
import evaluation.gt_pool as gp  # noqa: E402
import evaluation.two_layer as tl  # noqa: E402
from rcca.rcca import _RegimeBank  # noqa: E402


def main():
    from scipy.stats import spearmanr
    units = [u for u in gp._mixed_unit("SWaT") if u.gt_regime[0] in (1, 5)][:2]
    out = []
    for u in units:
        bank = _RegimeBank(u.pool_windows(), seed=0)
        W = u.windows()
        n, T, D = W.shape
        import shap
        ex = shap.TreeExplainer(u.iforest_model)
        sv = np.asarray(ex.shap_values(W.reshape(n, T * D), check_additivity=False))
        if sv.ndim == 3:
            sv = sv[..., -1]
        phi_shap = -sv.reshape(n, T, D).sum(1)                     # (n, D) 论文口径
        phi_cf = tl.METHODS["GlobalCF"](u, W, bank)["phi"]          # (n, D) 得分下降
        rhos = [spearmanr(phi_shap[i], phi_cf[i]).statistic for i in range(n)]
        top_agree = float(np.mean(np.argmax(phi_shap, 1) == np.argmax(phi_cf, 1)))
        vm = u.gt_type == "variable"
        gtv = [v[0] if v else -1 for v in u.gt_vars]
        hit_shap = float(np.mean(np.argmax(phi_shap[vm], 1) == np.asarray(gtv)[vm]))
        hit_cf = float(np.mean(np.argmax(phi_cf[vm], 1) == np.asarray(gtv)[vm]))
        rec = {"unit": u.name, "n_windows": n,
               "spearman_mean": float(np.nanmean(rhos)),
               "spearman_median": float(np.nanmedian(rhos)),
               "top1_agree_with_GlobalCF": top_agree,
               "top1_hit_gt_shap": hit_shap, "top1_hit_gt_globalcf": hit_cf}
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    s = [r["spearman_median"] for r in out]
    a = [r["top1_agree_with_GlobalCF"] for r in out]
    summary = {"per_unit": out,
               "spearman_median_overall": float(np.mean(s)),
               "top1_agree_overall": float(np.mean(a))}
    json.dump(summary, open(cpath("validate_treeshap.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)
    print("SUMMARY:", json.dumps(summary["spearman_median_overall"]),
          json.dumps(summary["top1_agree_overall"]), flush=True)


if __name__ == "__main__":
    main()
