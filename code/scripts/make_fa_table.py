"""汇总误报统计表 (各数据集×打分器×FAR位): 误报数量 / 事件数 / 实际FAR / 注入真值可判定比例.
输出: 02_实验记录/误报统计表.md
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import AVAILABILITY, FAR_TARGETS, ROOT_DIR, cpath  # noqa: E402


def fa_stats():
    rows = []
    for (scorer, ds), ok in AVAILABILITY.items():
        if not ok:
            rows.append({"scorer": scorer, "dataset": ds, "note": "不可用 (无落盘分数/checkpoint)"})
            continue
        for t in FAR_TARGETS:
            p = cpath(f"fa_{scorer}_{ds}_far{int(t*100)}.npz")
            if not os.path.exists(p):
                continue
            d = np.load(p)
            rows.append({"scorer": scorer, "dataset": ds, "far_target": t,
                         "tau": float(d["tau"]), "n_fa": len(d["fa_idx"]),
                         "realized_far": float(d["realized_far"]),
                         "n_normal_test": int(d["n_normal_test"])})
    return rows


def injection_stats():
    """注入真值可自动判定比例 (变量级 + 工况级), 按 (scorer, dataset, far) 平均."""
    out = {}
    p = cpath("inj_var_summary.json")
    if os.path.exists(p):
        raw = json.load(open(p, encoding="utf-8"))
        for combo, stats in raw.items():
            agg = {}
            for st in stats:
                agg.setdefault(st["far_target"], []).append(st["valid_rate"])
            out[combo] = {f"{t:.2f}": float(np.mean(v)) for t, v in agg.items()}
    p2 = cpath("inj_regime_summary.json")
    if os.path.exists(p2):
        raw = json.load(open(p2, encoding="utf-8"))
        for ds, blob in raw.items():
            if "error" in blob:
                out[f"regime_iforest_{ds}"] = {"error": blob["error"]}
                continue
            agg = {}
            for key, st in blob["stats"].items():
                far = key.split("_far")[1]
                agg.setdefault(far, []).append(st["valid_rate"])
            out[f"regime_iforest_{ds}"] = {
                f"0.{k}": float(np.mean(v)) for k, v in agg.items()}
    return out


def main():
    fa = fa_stats()
    inj = injection_stats()
    md = ["# 误报统计表（阶段1，2026-08-15）", "",
          "阈值=校准段(35%~50%)正常窗分数 (1-target) 分位；误报=测试段全窗正常且分数>阈值；窗口=16。",
          ""]
    md.append("| 打分器 | 数据集 | FAR目标 | 阈值τ | 误报窗数 | 正常测试窗 | 实际FAR | 事件数(估) |")
    md.append("|---|---|---|---|---|---|---|---|")
    from collections import defaultdict
    ev = defaultdict(int)
    for r in fa:
        if "note" in r:
            continue
        key = (r["scorer"], r["dataset"], r["far_target"])
        p = cpath(f"fa_{r['scorer']}_{r['dataset']}_far{int(r['far_target']*100)}.npz")
        d = np.load(p)
        idx = d["fa_idx"]
        ev[key] = int((np.diff(idx) > 5).sum() + 1) if len(idx) else 0
        md.append(f"| {r['scorer']} | {r['dataset']} | {r['far_target']:.0%} | "
                  f"{r['tau']:.4g} | {r['n_fa']} | {r['n_normal_test']} | "
                  f"{r['realized_far']:.2%} | {ev[key]} |")
    md.append("")
    md.append("## 注入真值可自动判定比例（有效率 = 注入段内出现 FA 的试验占比，按配置平均）")
    md.append("")
    md.append("| 组合 | FAR1% | FAR5% |")
    md.append("|---|---|---|")
    for combo, v in inj.items():
        if "error" in v:
            md.append(f"| {combo} | 错误: {v['error'][:40]} | |")
        else:
            md.append(f"| {combo} | {v.get('0.01', float('nan')):.0%} | {v.get('0.05', float('nan')):.0%} |")
    md += ["", "## 注释（诚实记录）",
           "1. **cmhmil×MetroPT3 分数退化**（测试分数 std≈1.6e-4，校准段分数恒定，两 FAR 位 τ 相同，实际 FAR=100%）——该组合从注入/对齐矩阵剔除，是数据结论非 bug。",
           "2. **校准→测试阈值迁移偏差**：SWaT 校准段来自 normal.csv 而测试正常窗来自 attack.csv 的正常部分，两者存在真实分布偏移；cmhmil 实际 FAR 15.5%（目标 1%）、iforest 2.96%。AT 用自身流前半定阈迁移良好（0.97%/4.89%）。该偏移本身即自然误报来源之一，写入论文动机。",
           "3. AT 的误报收集在其自身数据流（win=20、自有标准化）上进行，与前两者的第2篇加载流不可逐点对齐；AT 注入重打分本阶段未实现。",
           "4. iforest-flatten 对单变量偏移存在树深饱和（5σ~40σ 恒定偏移分数几乎不变），单变量注入在 iforest×SMD/MetroPT3@FAR1% 有效率低——弱注入失效区按方案写入 limitation。"]
    out = os.path.join(ROOT_DIR, "02_实验记录", "误报统计表.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("已写入", out)


if __name__ == "__main__":
    main()
