"""工况识别验证运行 (阶段1 任务3): GMM vs 物理阶段标签 ARI/NMI + 通道画像.

- SWaT: 阶段标签从原始 normal.csv 执行器列推导 (P101 进水 / MV303 反洗 / 其余待机),
  对齐降采样后与 GMM 窗级聚类比 ARI/NMI;
- MetroPT3: Motor_current 占空比运行段 (负载/卸载) 作物理标签;
- SMD: 无物理工况 -> 仅报 GMM 结构 (BIC/簇占比), 论文口径用"模式条件化".
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, WINDOW  # noqa: E402
from regimes.regimes import (RegimeModel, alignment_report,  # noqa: E402
                             features_at, metropt3_cycle_labels,
                             swat_stage_labels)


def run(dataset, seed=0):
    X, Y = load_raw(dataset)
    a, _ = split_of(len(X))
    rm = RegimeModel().fit(X, seed=seed)
    print(f"[{dataset}] BIC 曲线: " + ", ".join(f"K={k}:{v:.0f}" for k, v in rm.bic_.items()))
    print(f"[{dataset}] BIC 最优 K={rm.K}")

    # 弱训练段窗级聚类标签 (SWaT 阶段标签仅覆盖 normal 段, 需先限制窗范围)
    max_end = min(a + 300_000, len(X))
    if dataset == "SWaT":
        max_end = min(max_end, len(swat_stage_labels()) - 1)
    ends = np.arange(a + WINDOW - 1, max_end)
    F = features_at(X, ends)
    pred = rm.transform(F)
    frac = {k: float((pred == k).mean()) for k in range(rm.K)}

    out = {"dataset": dataset, "K": rm.K, "bic": rm.bic_, "cluster_frac": frac}
    if dataset == "SWaT":
        stage = swat_stage_labels()
        stage_win = {}
        maj = np.zeros(len(ends), np.int8)
        for v in (1, 2, 3):
            cs = np.cumsum(np.concatenate([[0], (stage == v).astype(np.int64)]))
            cnt = cs[ends + 1] - cs[ends + 1 - WINDOW]
            stage_win[v] = cnt
        maj = np.array([1, 2, 3])[np.argmax(np.stack([stage_win[v] for v in (1, 2, 3)]), 0)]
        rep = alignment_report(pred, maj)
        out["physical"] = "SWaT P101/MV303 推导阶段"
        out["alignment"] = rep
        print(f"[SWaT] 阶段占比: " + ", ".join(
            f"stage{v}={float((maj==v).mean()):.1%}" for v in (1, 2, 3)))
        print(f"[SWaT] ARI={rep['ari']:.3f} NMI={rep['nmi']:.3f}")
    elif dataset == "MetroPT3":
        cyc = metropt3_cycle_labels(X)
        cs1 = np.cumsum(np.concatenate([[0], (cyc == 1).astype(np.int64)]))
        cs0 = np.cumsum(np.concatenate([[0], (cyc == 0).astype(np.int64)]))
        n1 = cs1[ends + 1] - cs1[ends + 1 - WINDOW]
        n0 = cs0[ends + 1] - cs0[ends + 1 - WINDOW]
        maj = (n1 > n0).astype(np.int8)
        rep = alignment_report(pred, maj)
        out["physical"] = "MetroPT3 Motor_current 负载/卸载"
        out["alignment"] = rep
        print(f"[MetroPT3] 负载占比={float(maj.mean()):.1%} "
              f"ARI={rep['ari']:.3f} NMI={rep['nmi']:.3f}")
    else:
        out["physical"] = "无物理标签 (SMD: 模式条件化口径)"
        print(f"[SMD] 无物理阶段标签, 簇占比: " + ", ".join(f"C{k}={v:.1%}" for k, v in frac.items()))

    # 通道画像: 簇中心反变换回特征空间, 取前 D 维 (通道均值画像)
    prof = {}
    for k in range(rm.K):
        mean_pca = rm.gmm.means_[k][None]
        mean_feat = rm.scaler.inverse_transform(rm.pca.inverse_transform(mean_pca))[0]
        prof[k] = {"frac": frac[k], "ch_mean": mean_feat[:X.shape[1]].round(4).tolist()}
    out["profile_ch_mean"] = prof
    np.savez_compressed(cpath(f"regime_{dataset}.npz"), K=rm.K,
                        bic=np.array(list(rm.bic_.items()), dtype=float),
                        ends=ends[:200000], pred=pred[:200000])
    return out


if __name__ == "__main__":
    import json
    results = {}
    for ds in ("SWaT", "MetroPT3", "SMD"):
        try:
            results[ds] = run(ds)
        except Exception as e:
            import traceback; traceback.print_exc()
            results[ds] = {"error": f"{type(e).__name__}: {e}"}
    with open(cpath("regime_report.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("已写入 regime_report.json")
