"""T0-2a: 生成自然告警人工标注包 (供用户标注 ~120 窗口).

采样口径: 与论文 400-alarm 探针 (run_natural_validation.py) 完全一致 ——
同一 rng(0) 顺序对 fa_idx 子样 400; 再从 400 中按分数四分位分层抽 40/数据集.
每窗口输出一张 PNG (通道偏差条形图 + 热图) + labels.csv 模板 + 元数据缓存.
输出目录: <项目>/04_投稿准备/T0_投稿前实验包/标注包/
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import cpath, load_raw, split_of, WINDOW  # noqa: E402

OUT = os.path.normpath(os.path.join(cpath(".."), "..", "04_投稿准备",
                                    "T0_投稿前实验包", "标注包"))
FIG = os.path.join(OUT, "figs")
N_PER_DS = 40


Z_CLIP = 12.0   # 显示/统计用每步 |z| 上限 (近恒定通道 MAD≈0 会使 z 爆到 1e9, 截断保留"是否动了"信息)
HM_CLIP = 8.0   # 热力图统一色标


def robust_z_profile(X, a, b, ends):
    """窗口内每通道 mean|robust z| (对池中位数/MAD 标准化; 每步 |z| 截断 Z_CLIP)."""
    mu_med = np.median(X[a:b], 0)
    mad = 1.4826 * np.median(np.abs(X[a:b] - mu_med), 0) + 1e-9
    i = ends[:, None] - (WINDOW - 1) + np.arange(WINDOW)[None, :]
    W = X[i]                                    # (n, w, d)
    Z = (W - mu_med[None, None, :]) / mad[None, None, :]
    prof = np.clip(np.abs(Z), 0, Z_CLIP).mean(1)
    return Z, prof                              # (n,w,d) 原始, (n,d) 截断均值


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(FIG, exist_ok=True)
    rng = np.random.default_rng(0)     # 与 run_natural_validation 完全一致
    sel_rng = np.random.default_rng(42)
    meta = []
    csv_rows = ["window_id,dataset,label,top_channels,notes"]

    for ds in ("SWaT", "SMD", "MetroPT3"):
        X, Y = load_raw(ds)
        a, b = split_of(len(X))
        d = np.load(cpath(f"fa_iforest_{ds}_far5.npz"))
        tau = float(d["tau"])
        idx = d["fa_idx"]
        scores = d["fa_scores"]
        if len(idx) > 400:
            pick400 = np.sort(rng.choice(len(idx), 400, replace=False))
            idx, scores = idx[pick400], scores[pick400]
        # 分层: 分数四分位各抽 10
        qs = np.quantile(scores, [0.25, 0.5, 0.75])
        strata = np.digitize(scores, qs)
        chosen = []
        for s in range(4):
            cand = np.where(strata == s)[0]
            take = min(10, len(cand))
            chosen.extend(sel_rng.choice(cand, take, replace=False).tolist())
        chosen = np.array(sorted(chosen))
        ends, sc = idx[chosen], scores[chosen]
        Z, prof = robust_z_profile(X, a, b, ends)
        print(f"[{ds}] 标注窗 {len(ends)} (来自同口径400样本)", flush=True)

        for k in range(len(ends)):
            wid = f"{ds}_w{k:03d}"
            p = prof[k]
            order = np.argsort(-p)
            top12 = order[:12][::-1]
            top15h = order[:15]
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2),
                                           gridspec_kw={"width_ratios": [1, 1.3]})
            ax1.barh(range(len(top12)), p[top12], color="#3b6fb6")
            ax1.set_yticks(range(len(top12)))
            ax1.set_yticklabels([f"ch{j}" for j in top12], fontsize=7)
            ax1.axvline(np.median(p), ls="--", lw=0.8, color="#888888")
            ax1.set_xlabel("mean |z| (robust, capped at 12)", fontsize=8)
            ax1.set_title("channel deviation (top 12)", fontsize=9)
            vmax = HM_CLIP
            im = ax2.imshow(np.clip(Z[k][:, top15h].T, -vmax, vmax), aspect="auto",
                            cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                            interpolation="nearest")
            ax2.set_yticks(range(len(top15h)))
            ax2.set_yticklabels([f"ch{j}" for j in top15h], fontsize=6)
            ax2.set_xlabel("time step in window", fontsize=8)
            ax2.set_title("window heatmap, top 15 channels (blue=low, red=high)", fontsize=9)
            plt.colorbar(im, ax=ax2, fraction=0.04)
            n_hi = int((p > 5).sum())
            frac_hi = float((p > 3).mean())
            fig.suptitle(f"{wid} | {ds} | score={sc[k]:.3f} (tau={tau:.3f}) | "
                         f"channels|z|>5: {n_hi}, >3: {frac_hi:.0%}", fontsize=9)
            fig.tight_layout(rect=[0, 0, 1, 0.94])
            fig.savefig(os.path.join(FIG, wid + ".png"), dpi=140)
            plt.close(fig)
            meta.append({"window_id": wid, "dataset": ds,
                         "end": int(ends[k]), "score": float(sc[k]),
                         "tau": tau, "n_ch_z5": n_hi, "frac_z3": frac_hi})
            csv_rows.append(f"{wid},{ds},,,")

    json.dump(meta, open(cpath("label_windows_meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "labels.csv"), "w", encoding="utf-8-sig") as f:
        f.write("\n".join(csv_rows) + "\n")
    print(f"共 {len(meta)} 窗 → {FIG}")
    print(f"CSV 模板 → {os.path.join(OUT, 'labels.csv')}")


if __name__ == "__main__":
    main()
