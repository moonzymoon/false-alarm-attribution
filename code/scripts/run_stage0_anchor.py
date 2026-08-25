"""阶段0 锚点实验: CondAttr(复现) 在 SWaT 真异常上的归因质量.

设置:
  - 打分器: iforest-SWaT (第6篇缓存口径, 重打分层已验证 spearman=1.0);
  - 正常库: 弱训练+校准段 (normal.csv 部分) 窗口;
  - 查询: 每个攻击区间内 iforest 分数最高的窗口;
  - 真值 (可复现的结构化推导, 攻击=值操纵):
      freeze 版 (保守): 攻击区间内零方差但正常时非常数的通道;
      freeze+dev 版 (宽松): 再加区间内 |z|>4 持续 >50% 的通道.
    投稿前需与 iTrust 官方 List of Attacks 逐条核对.
  - 对照: 全局均值替换反事实 (P4 数值路迁移), 同一评估.

输出: _cache/stage0_anchor.npz + 控制台报告.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_raw, split_of, cpath, WINDOW  # noqa: E402
import scorers_rescore as rs  # noqa: E402
from baselines.condattr import CondAttr  # noqa: E402


def attack_intervals(Y, b):
    """SWaT 攻击区间: 本地 attack.csv 是"仅攻击行拼接"版 (全标 Attack, 单块),
    用时间戳断点 (>=10s) 恢复各次攻击; 35 段中 1 段长达 35900s (疑标注卡死) 排除.
    返回全流 (降采样后) 坐标的 [(start, end)]."""
    import pandas as pd
    from common import DATA_ROOT
    df = pd.read_csv(os.path.join(DATA_ROOT, "SWaT", "attack.csv"), usecols=[" Timestamp"])
    t = pd.to_datetime(df[" Timestamp"], dayfirst=True, errors="coerce")
    dt = np.diff(t.values).astype("timedelta64[s]").astype(int)
    big = np.where(dt >= 10)[0]
    bounds = np.concatenate([[0], big + 1, [len(t)]])
    lens = np.diff(bounds)
    n_norm_ds = 277420  # ceil(1387098/5): normal.csv 降采样后长度
    ivs = []
    for s, e in zip(bounds[:-1], bounds[1:]):
        if (e - s) > 3600:  # 排除 35900s 异常长段
            continue
        ivs.append((n_norm_ds + s // 5, n_norm_ds + e // 5))
    return ivs


def derive_gt(X, a, b, s, e, frozen_rarity=None):
    """区间 [s,e] 的被操纵通道.
    freeze 版 (保守): 区间内零方差 + 正常数据中"同样长度冻结"罕见 (<5%) —
      排除整个攻击期本来就少切换的执行器 (P101/P203/MV304 等的假阳性来源);
    freeze+dev 版 (宽松): 再加 |z|>4 持续>50% 的通道 (含后果通道, 会高估 R@3)."""
    seg = X[s:e + 1]
    L = len(seg)
    ref_mu, ref_sd = X[a:b].mean(0), X[a:b].std(0) + 1e-8
    ref_var = X[a:b].var(0)
    seg_var = seg.var(0)
    frozen = (seg_var < 1e-10) & (ref_var > 0.05)
    if frozen_rarity is not None:            # 正常段中该通道出现 >=L 长度冻结的频率
        frozen &= frozen_rarity < 0.05
    dev = (np.abs(seg - ref_mu) > 4 * ref_sd).mean(0) > 0.5
    gt_freeze = np.where(frozen)[0]
    gt_loose = np.where(frozen | dev)[0]
    return gt_freeze, gt_loose


def frozen_rarity_profile(X, a, b, L, n=200, seed=0):
    """正常(校准)段随机抽 n 个长 L 的子段, 统计各通道冻结频率 (D,)."""
    rng = np.random.default_rng(seed)
    starts = rng.integers(a, b - L, size=n)
    fr = np.zeros(X.shape[1])
    for s in starts:
        fr += (X[s:s + L].var(0) < 1e-10)
    return fr / n


def global_cf_attribution(f_score, W, ref_mu, window=WINDOW):
    """全局反事实基线 (P4 数值路迁移): j 替换为全局正常均值, 分数降幅."""
    w, D = W.shape
    flat = W.reshape(1, -1)
    s_orig = float(f_score(flat)[0])
    drops = np.zeros(D)
    for j in range(D):
        Wcf = W.copy()
        Wcf[:, j] = ref_mu[j]
        drops[j] = s_orig - float(f_score(Wcf.reshape(1, -1))[0])
    return drops


def topk_hit(phi, gt, k=3):
    if len(gt) == 0:
        return None
    top = np.argsort(-phi)[:k]
    return float(len(set(top) & set(gt)) > 0)


def main():
    X, Y = load_raw("SWaT")
    a, b = split_of(len(X))
    D = X.shape[1]
    ifo = rs._iforest_model("SWaT", X)
    f = lambda flats: -ifo.decision_function(flats)

    # 正常库窗口 (弱训练+校准)
    rng = np.random.default_rng(42)
    db_ends = rng.choice(np.arange(a + WINDOW - 1, b), size=40000, replace=False)
    db = rs.make_windows_at(X, db_ends)

    print("拟合 CondAttr (UMAP 10d, K=3) ...", flush=True)
    ca = CondAttr(f).fit(db)

    ivs = attack_intervals(Y, b)
    ivs = [(s, min(e, len(X) - 1)) for s, e in ivs]
    print(f"攻击区间数: {len(ivs)}")
    ref_mu = X[a:b].mean(0)
    rows = []
    for n, (s, e) in enumerate(ivs):
        ends = np.arange(s, e + 1)
        sc = f(rs.make_windows_at(X, ends))
        w_end = int(ends[np.argmax(sc)])
        W = X[w_end - WINDOW + 1:w_end + 1]
        rarity = frozen_rarity_profile(X, a, b, len(ends))
        gt_f, gt_l = derive_gt(X, a, b, s, e, frozen_rarity=rarity)
        phi_ca, info = ca.attribute(W)
        phi_gc = global_cf_attribution(f, W, ref_mu)
        rows.append({
            "attack": n, "start": int(s), "end": int(e), "len": int(e - s + 1),
            "peak_score": float(sc.max()), "gt_freeze": gt_f, "gt_loose": gt_l,
            "phi_ca": phi_ca, "phi_gcf": phi_gc,
            "hit_ca_f": topk_hit(phi_ca, gt_f), "hit_ca_l": topk_hit(phi_ca, gt_l),
            "hit_gc_f": topk_hit(phi_gc, gt_f), "hit_gc_l": topk_hit(phi_gc, gt_l),
        })
        print(f"  A{n:02d} [{s}:{e}] len={e-s+1} gtF={list(gt_f)} gtL={list(gt_l)} "
              f"CA(f/l)={rows[-1]['hit_ca_f']}/{rows[-1]['hit_ca_l']} "
              f"GCF(f/l)={rows[-1]['hit_gc_f']}/{rows[-1]['hit_gc_l']}")

    withf = [r for r in rows if r["hit_ca_f"] is not None]
    withl = [r for r in rows if r["hit_ca_l"] is not None]
    r3_ca_f = np.mean([r["hit_ca_f"] for r in withf]) if withf else float("nan")
    r3_ca_l = np.mean([r["hit_ca_l"] for r in withl]) if withl else float("nan")
    r3_gc_f = np.mean([r["hit_gc_f"] for r in withf]) if withf else float("nan")
    r3_gc_l = np.mean([r["hit_gc_l"] for r in withl]) if withl else float("nan")
    print("\n===== R@3 汇总 =====")
    print(f"CondAttr(复现): freeze GT {r3_ca_f:.3f} (n={len(withf)}), loose GT {r3_ca_l:.3f} (n={len(withl)})")
    print(f"全局反事实  : freeze GT {r3_gc_f:.3f}, loose GT {r3_gc_l:.3f}")
    print(f"DFKI 论文报告 (其自有检测器/窗口50): R@3 VAE=0.537, UMAP=0.481; ShaTS=0.393; KernelSHAP=0.055")

    np.savez_compressed(cpath("stage0_anchor.npz"),
                        rows=np.array(rows, dtype=object),
                        summary=np.array([r3_ca_f, r3_ca_l, r3_gc_f, r3_gc_l]))


if __name__ == "__main__":
    main()
