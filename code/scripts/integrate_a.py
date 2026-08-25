# -*- coding: utf-8 -*-
"""Integrate A-tier results into the paper (Wilcoxon, gamma stability, repair table,
meta-selector negative result) + fix the false <=0.05 calibration-loss claim."""
import io
B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
n = 0

def rep(old, new, tag):
    global s, n
    assert old in s, f"NOT FOUND: {tag}"
    assert s.count(old) == 1, f"NOT UNIQUE: {tag}"
    s = s.replace(old, new)
    n += 1
    print("A:", tag)

# A2: Wilcoxon after the bootstrap CI sentence in Main comparison
rep("the same resampled unit sets for both methods. Five observations emerge.",
    "the same resampled unit sets for both methods. Wilcoxon signed-rank tests across" + NL +
    "units confirm the separation: AERec versus GlobalCF top-1 $p{=}0.0004$ (Cliff's" + NL +
    "$" + B + "delta{=}0.49$, 20 wins / 2 losses), versus CondAttr $p{=}0.0008$, versus zDev" + NL +
    "$p{=}0.0002$, and versus GlobalCF on typing $p{=}0.0049$; within the counterfactual" + NL +
    "family the contrasts are null (RC-CA versus GlobalCF top-1 $p{=}0.82$; CondAttr versus" + NL +
    "GlobalCF $p{=}0.25$), and RegimeGlobal's typing edge is marginal ($p{=}0.048$)." + NL +
    "Five observations emerge.",
    "wilcoxon tests")

# A1: fix the false <=0.05 claim
rep("additionally report " + B + "emph{oracle} thresholds (best achievable on test) to" + NL +
    "quantify calibration loss ($" + B + "le$0.05 throughout).",
    "we additionally report " + B + "emph{oracle} thresholds (best achievable on test) to" + NL +
    "quantify calibration loss (median 0.019; 91" + B + "% of unit--method pairs within 0.10;" + NL +
    "worst case 0.43, RC-CA on one SWaT unit).",
    "oracle gap honest stats")

# A1: gamma stability analysis into Ablations and robustness
rep(B + "subsection{Ablations and robustness}" + NL + "RC-CA is insensitive",
    B + "subsection{Ablations and robustness}" + NL +
    B + "textbf{Calibration-threshold stability.} Calibrated $" + B + "gamma$ values vary by" + NL +
    "7--32$" + B + "times$ across units of the same detector (e.g., GlobalCF on the isolation" + NL +
    "forest spans 0.08--2.05), so no deployment-global threshold exists; the per-unit" + NL +
    "calibration that the injected validation split provides is necessary, and its cost is" + NL +
    "the oracle gap reported above (median 0.019)." + NL +
    "RC-CA is insensitive",
    "gamma stability paragraph")

# A3: repair comparison table (after the variable-level paragraph, before Natural FAs)
rep(B + "subsection{Natural false alarms}" + B + "label{sec:natural}",
    B + "begin{table}[t]" + NL +
    B + "caption{Repair outcomes under cause-guided versus control interventions." + NL +
    "Mode-level: mean FAR reduction over the 14 repair units (and over the 11 with base" + NL +
    "FAR above 10" + B + "%). Variable-level: mean share of variable-type alarms resolved" + NL +
    "over the same units (Supplementary Tables~S6--S7).}" + NL +
    B + "label{tab:repair}" + NL +
    B + "begin{tabular}{lcc}" + NL +
    B + "toprule" + NL +
    "Intervention & Guided & Control " + B + B + " " + B + "midrule" + NL +
    "Mode-level FAR drop (pp, all 14) & +27.8 & +5.7 (random) " + B + B + NL +
    "Mode-level FAR drop (pp, 11 units) & +34.4 & +6.2 (random) " + B + B + NL +
    "Naive alarm supplementation (pp) & " + B + "multicolumn{2}{c}{+3.1 (all 14) / +4.0 (11 units)} " + B + B + NL +
    "Variable-level resolution & 91" + B + "% (RC-CA-guided) & 11" + B + "% (random channel) " + B + B + NL +
    "Ground-truth-channel correction & " + B + "multicolumn{2}{c}{57--83" + B + "%} " + B + B + NL +
    B + "bottomrule" + NL +
    B + "end{tabular}" + NL +
    B + "end{table}" + NL + NL +
    B + "subsection{Natural false alarms}" + B + "label{sec:natural}",
    "repair table")

# reference the new table in the repair text
rep("Mode-directed addition" + NL + "reduces FAR by 22.1" + B + "pp{} more than the random control on average",
    "Table~" + B + "ref{tab:repair} summarizes both repair levels. Mode-directed addition" + NL + "reduces FAR by 22.1" + B + "pp{} more than the random control on average",
    "repair table ref")

# A4: meta-selector negative result in DAAS paragraph
rep("extending the rule to typing- and repair-aware selection is left open.",
    "extending the rule to typing- and repair-aware selection is left open. We also" + NL +
    "tested feature-driven selectors (logistic regression, a shallow random forest, and" + NL +
    "1-NN on detector identity plus dataset size features) under the same leave-one-out:" + NL +
    "none exceeded the table rules (best 33" + B + "% strict / 67" + B + "% tolerant), so at 15 pairs" + NL +
    "the bottleneck is training volume rather than feature expressiveness.",
    "meta selector negative")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "A-tier integrations applied")
