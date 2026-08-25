"""从 _cache 的各 JSON 汇总生成 02_实验记录/主实验_两层评估.md."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ROOT_DIR, cpath  # noqa: E402


def main():
    r = json.load(open(cpath("main_results.json"), encoding="utf-8"))
    mix = [u for u in r if "_mix_" in u]
    var_units = [u for u in r if u.endswith("_var")]
    md = ["# 主实验：两层公平评估（R1-R2 修改后，2026-08-15）", ""]
    md.append("混合真值单元：留出 regime 重训 iforest 下同时生成工况型（留出 regime FA 窗）与"
              "变量型（注入致因 FA 窗，注入前≤τ）实例；γ/δ 在各单元验证集按宏F1标定，测试集固定；"
              "oracle 为测试集反推上限。")
    md.append("")
    md.append("## 第一层：成因类型二分类（宏 F1，14 混合单元）")
    md.append("")
    md.append("| 方法 | 宏F1 均值±std | 变量召回 | 工况召回 | 第二层 top1 | top3 |")
    md.append("|---|---|---|---|---|---|")
    for m in ("RC-CA", "GlobalCF", "RegimeGlobal", "CondAttr", "AERec", "Granger", "zDev", "Random"):
        l1 = [r[u][m]["layer1_macro_f1"] for u in mix if "error" not in r[u][m]]
        vr = [r[u][m]["var_recall"] for u in mix if "error" not in r[u][m]]
        rr = [r[u][m]["reg_recall"] for u in mix if "error" not in r[u][m]]
        t1 = [r[u][m]["layer2_top1"] for u in mix if r[u][m].get("layer2_top1") is not None]
        t3 = [r[u][m]["layer2_top3"] for u in mix if r[u][m].get("layer2_top3") is not None]
        md.append(f"| {m} | {np.mean(l1):.3f}±{np.std(l1):.3f} | {np.mean(vr):.2f} | "
                  f"{np.mean(rr):.2f} | {np.mean(t1):.3f} | {np.mean(t3):.3f} |")
    md.append("")
    md.append("### 分数据集（宏 F1 / top3）")
    md.append("")
    md.append("| 数据集 | RC-CA | GlobalCF | CondAttr | AERec |")
    md.append("|---|---|---|---|---|")
    for ds in ("SWaT", "SMD", "MetroPT3"):
        sub = [u for u in mix if ds in u]
        row = f"| {ds} ({len(sub)}单元) "
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger"):
            l1 = np.mean([r[u][m]["layer1_macro_f1"] for u in sub])
            t3 = np.mean([r[u][m]["layer2_top3"] for u in sub
                          if r[u][m].get("layer2_top3") is not None])
            row += f"| {l1:.3f} / {t3:.3f} "
        md.append(row + "|")
    md.append("")
    md.append("## 逐单元明细")
    md.append("")
    md.append("| 单元 | n | RC-CA | GlobalCF | CondAttr | AERec |")
    md.append("|---|---|---|---|---|---|")
    for u in mix:
        row = f"| {u} | {r[u]['RC-CA']['n_test']} "
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Granger"):
            v = r[u][m]
            t1 = v.get("layer2_top1")
            t1s = f"/{t1:.2f}" if t1 is not None else ""
            row += f"| {v['layer1_macro_f1']:.2f}{t1s} "
        md.append(row + "|")
    md += ["", "## 固定深度打分器单元（cmhmil，仅第二层，单类型不参与第一层）", ""]
    for u in var_units:
        row = f"| {u} |"
        for m in ("RC-CA", "GlobalCF", "CondAttr", "AERec", "Grad"):
            v = r[u].get(m)
            row += f" {m}={v.get('layer2_top1', float('nan')):.2f}/{v.get('layer2_top3', float('nan')):.2f} |" if v and "error" not in v else " - |"
        md.append("| 单元 | " + " | ".join(("RC-CA", "GlobalCF", "CondAttr", "AERec", "Grad")) + " |")
        md.append(row)
    # 附属实验
    for name, fname in (("边缘分层（弱注入 vs 强注入 top1）", "margin_analysis.json"),
                        ("自然 FA 案例（iforest×SWaT top20 事件）", "natural_cases.json"),
                        ("消融（GMM K / kNN / 种子）", "ablation.json"),
                        ("修复对照（定向 vs 随机）", "repair_experiment.json"),
                        ("归因指导修复", "repair_guided.json"),
                        ("命题假设检验", "proposition_checks.json"),
                        ("KL-强度曲线", "kl_strength_curve.json")):
        p = cpath(fname)
        if os.path.exists(p):
            md.append(f"\n- `{fname}` 已产出（见对应分析）")
        else:
            md.append(f"\n- `{fname}` **缺失**")
    out = os.path.join(ROOT_DIR, "02_实验记录", "主实验_两层评估.md")
    open(out, "w", encoding="utf-8").write("\n".join(md))
    print("已写入", out)


if __name__ == "__main__":
    main()
