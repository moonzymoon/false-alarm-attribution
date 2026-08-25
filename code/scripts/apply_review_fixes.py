"""外部模型四批审查 -> 核实后的批量正文修正 (只改已核实项).
E1/E2 数据错误(SHAP AT 0.79->0.74); 其余为澄清/措辞/引用修正. 全部 assert 唯一匹配."""
import re

TEX = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\Springer_JIIS_FalseAlarmAttribution.tex"
SI = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\JIIS_submission\source\JIIS_SI.tex"

s = open(TEX, encoding="utf-8").read()
edits = [
    # E1 数据错误: SHAP AT 池化 0.79(旧2单元) -> 0.74(4单元窗口加权, at_ext_all.json=0.7384)
    ("0.79 pooled on the transformer (including",
     "0.74 pooled over the transformer's four units (including"),
    # E2 同源数据错误 (claims 表)
    ("0.69 on PCA/OCSVM (vs counterfactuals $\\geq$0.84), 0.79 on AT",
     "0.69 on PCA/OCSVM (vs counterfactuals $\\geq$0.84), 0.74 on AT"),
    # E3 CondAttr 邻域语义澄清 (代码核实: 整窗近邻平均成模板)
    ("and $K{=}3$ nearest contextual neighbours\nprovide the replacement trajectory per channel",
     "and the $K{=}3$ nearest contextual neighbours\nare averaged into a whole-window template from which each channel's replacement\ntrajectory is taken"),
    # E4 calibration loss 定义
    ("quantify calibration loss (median 0.019;",
     "quantify calibration loss, the macro-F1 gap between oracle and calibrated\nthresholds (median 0.019;"),
    # E5 Delta 直觉
    ("(equivalently, the mode-template drop minus the global-template drop) contrasts",
     "(equivalently, the mode-template drop minus the global-template drop; positive\n$\\Delta$ means mode-aware replacement lowers the score more than global\nreplacement) contrasts"),
    # E6 GlobalCF 对齐口径
    ("per-timestep mean trajectory of channel $j$ over the pool",
     "per-timestep mean trajectory of channel $j$ over the pool (computed at\nwindow-relative positions)"),
    # E7 保形措辞精化 + 嵌套lambda新证据 (0.833)
    ("covers 79\\% of held-out pairs at nominal 80\\% with a typical bound of 0.08; with\n$n{=}19$ pairs this is an empirical, small-sample guarantee.",
     "covers 79\\% of held-out pairs at nominal 80\\% with conformal quantile 0.076; with\n$n{=}19$ heterogeneous pairs, exchangeability is approximate, so we read this as\nan empirical calibration check rather than a distribution-free guarantee. A\nfully nested variant, in which $\\lambda$ is re-selected within each fold by an\ninner leave-one-out over the training pairs only, yields 0.833 mean top-1, so\nthe frontier point's selection does not drive the advantage."),
    # E8 引言贡献(5) 保形限定
    ("with a\nleave-one-out conformal regret bound.",
     "with an\nempirical leave-one-out conformal regret bound."),
    # E9 never worse 弱化
    ("that is never worse than the best fixed method across both\ngranularities, not as a statistically significant improvement.",
     "that is at least as good as the best fixed method on these 19 pairs across\nboth granularities, not as a statistically significant improvement."),
    # E10 二项区间方法名 (数值已核=精确Clopper-Pearson)
    ("so we present the rules as a deployment-time label-free heuristic (the",
     "so we present the rules as a deployment-time label-free heuristic with exact\nbinomial (Clopper--Pearson) intervals (the"),
    # E11 TreeSHAP 口径
    ("(negated: the explainer returns\npath-length contributions, which are anti-correlated with the anomaly\nscore);",
     "(negated: the explainer returns\npath-length contributions, which are anti-correlated with the anomaly score;\nthe values are exact for the path-length game, of which the anomaly score is a\nmonotone transform);"),
    # E12 Granger 变体声明
    ("means zeroing the $j$-th column of $B$ (no refit), and",
     "means zeroing the $j$-th column of $B$ (no refit; a closed-form linear\nleave-out approximation rather than a per-subset refit), and"),
    # E13 两层任务 (ii) 与 mode 身份一致性
    ("(ii)\nfine-grained identification (which channel, or which mode).",
     "(ii) fine-grained\nidentification (which channel; mode identity is deliberately not a target,\nDefinition~1)."),
    # E14 大写
    ("(6)~an open reference implementation",
     "(6)~An open reference implementation"),
    # E15 首个区间标注 CI
    ("(window-level top-1 0.93 [0.89, 0.96])",
     "(window-level top-1 0.93, 95\\% CI [0.89, 0.96])"),
    # E16 反直觉发现具体化
    ("two of which contradict our own initial hypotheses\nand are reported as such:",
     "two of which contradict our own initial hypotheses (the non-collapse of\nglobal counterfactuals on mode alarms, and calibration alone solving most of\ntyping) and are reported as such:"),
    # E17 repair headroom 定义
    ("addition outperforms a random control by 22.1 pp (positive in 9 of 11 units\nwith repair headroom);",
     "addition outperforms a random control by 22.1 pp (positive in 9 of 11 units\nwith repair headroom, i.e.\\ base FAR above 10\\%);"),
    # E18 模糊限定语删除
    ("with few exceptions they do not explain an individual alarm.",
     "they do not explain an individual alarm."),
    # E19 自引用修正
    ("\\subsection{Ablations and robustness}\n",
     "\\subsection{Ablations and robustness}\\label{sec:ablations}\n"),
    ("column-resolved\nrobustness is quantified in Section~\\ref{sec:results} (ablations).",
     "column-resolved robustness is quantified in Section~\\ref{sec:ablations}."),
    # E20 表2 术语与CI说明
    ("Method & L1 & top-1 & top-3 & var-R & reg-R \\\\",
     "Method & L1 & top-1 & top-3 & var-R & mode-R \\\\"),
    ("var-R/reg-R = class recalls.",
     "var-R/mode-R = class recalls."),
    ("Detector-resolved\npooling over all 62 units follows in Table~\\ref{tab:detector}.}",
     "Detector-resolved pooling over all 62 units follows in Table~\\ref{tab:detector};\nCIs are shown for L1 and top-1, and omitted for top-3/recalls for space.}"),
    # E21 AT/PSM 溯源
    ("AT/PSM is all-perfect (every counterfactual at\n0.99--1.00 top-1 with AERec also at 1.00)",
     "AT/PSM is all-perfect (every counterfactual at 0.99--1.00 top-1 with AERec also\nat 1.00; per-pair values in Table~S2 of Online Resource~1)"),
    # E22 多重比较说明
    ("and RegimeGlobal's typing edge is marginal ($p{=}0.048$).\nFive observations emerge.",
     "and RegimeGlobal's typing edge is marginal ($p{=}0.048$; $p$-values are\nuncorrected, and only the AERec contrasts survive Holm correction across the\nreported family).\nFive observations emerge."),
    # E23 修复实验检测器范围
    ("\\subsection{Repair loop}\\label{sec:repair}\n\\textbf{Mode-level.}",
     "\\subsection{Repair loop}\\label{sec:repair}\n(All repair experiments use the retrainable isolation-forest detector, since\nrepair manipulates its training set.)\n\\textbf{Mode-level.}"),
    # E24 exactly-best 定义
    ("the family-level rule recovers the exactly-best method in 8 of 19\nheld-out pairs (42\\%)",
     "the family-level rule recovers the exactly-best method (the pair's top scorer\namong all methods) in 8 of 19 held-out pairs (42\\%)"),
]
n_ok = 0
for old, new in edits:
    c = s.count(old)
    assert c == 1, f"match={c} for: {old[:60]!r}"
    s = s.replace(old, new)
    n_ok += 1
open(TEX, "w", encoding="utf-8").write(s)
print(f"main tex: {n_ok} edits applied")

# E25 SI 一阶注记: 不可微检测器说明
t = open(SI, encoding="utf-8").read()
old25 = "it ignores\ncross-channel coupling in the replacement and higher-order terms."
new25 = ("it ignores\ncross-channel coupling in the replacement and higher-order terms, and for\nnon-differentiable scorers (the tree ensemble) the derivative is read as a local\nfinite difference.")
assert t.count(old25) == 1, "SI anchor not found"
open(SI, "w", encoding="utf-8").write(t.replace(old25, new25))
print("SI: 1 edit applied")
