# -*- coding: utf-8 -*-
"""Re-apply the 7 edits lost in the deleted region (verbatim from session)."""
import io

B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()
n_applied = 0

def rep(old, new, tag):
    global s, n_applied
    assert old in s, f"NOT FOUND: {tag}"
    assert s.count(old) == 1, f"NOT UNIQUE: {tag}"
    s = s.replace(old, new)
    n_applied += 1
    print("applied:", tag)

# ---- 1. Detectors section ----
old1 = (B + "subsection{Detectors and data}" + NL +
        "Three detector families with fixed checkpoints: (i)~window-flattened" + NL +
        "isolation forest; (ii)~a weakly-supervised deep multiple-instance detector" + NL +
        "built on attention pooling " + B + "cite{ilse2018attention}; (iii)~Anomaly" + NL +
        "Transformer " + B + "cite{xu2022at}. Datasets: SWaT " + B + "cite{goh2017swat,mathur2016swat}" + NL +
        "(51 channels; the local distribution is the attack-rows-only variant, whose" + NL +
        "per-attack segmentation we recover from timestamp gaps), SMD" + NL +
        B + "cite{su2019smd} (38 channels, machine-1-1), MetroPT3 " + B + "cite{marques2024metropt3}" + NL +
        "(15 channels, metro air compressor). Thresholds target FAR 5" + B + "% (1" + B + "% in the" + NL +
        "robustness appendix). Cross-run distribution shift on SWaT is measured and" + NL +
        "reported rather than hidden.")
new1 = (B + "subsection{Detectors and data}" + NL +
        "Five detectors spanning three families, all with fixed checkpoints:" + NL +
        "(i)~a window-flattened isolation forest " + B + "cite{liu2008iforest} (discrete" + NL +
        "tree ensemble); (ii)~PCA reconstruction error on flattened windows (50" + NL +
        "retained components; smooth linear scorer); (iii)~a one-class SVM with RBF" + NL +
        "kernel ($" + B + "nu{=}0.05$; smooth kernel scorer); (iv)~a weakly-supervised deep" + NL +
        "multiple-instance detector built on attention pooling " + B + "cite{ilse2018attention};" + NL +
        "(v)~Anomaly Transformer " + B + "cite{xu2022at}. The classical pair (ii)--(iii) is" + NL +
        "included precisely because their score geometry differs from both the tree" + NL +
        "ensemble and the deep detectors, extending the matching study beyond deep" + NL +
        "architectures. Detectors (ii)--(iii) run on SWaT, SMD and PSM (retraining" + NL +
        "per held-out mode follows the same protocol as the isolation forest);" + NL +
        "detectors (iv)--(v) contribute native variable-level units on SWaT and SMD." + NL +
        "Datasets: SWaT " + B + "cite{goh2017swat,mathur2016swat}" + NL +
        "(51 channels; the local distribution is the attack-rows-only variant, whose" + NL +
        "per-attack segmentation we recover from timestamp gaps), SMD" + NL +
        B + "cite{su2019smd} (38 channels, machine-1-1), MetroPT3 " + B + "cite{marques2024metropt3}" + NL +
        "(15 channels, metro air compressor), PSM " + B + "cite{abdulaal2021psm} (25" + NL +
        "channels, pooled server metrics) and SMAP " + B + "cite{hundman2019smap} (25" + NL +
        "channels, spacecraft telemetry channel subset). Thresholds target FAR 5" + B + "%" + NL +
        "(1" + B + "% in the robustness appendix). Cross-run distribution shift on SWaT is" + NL +
        "measured and reported rather than hidden.")
rep(old1, new1, "detectors section")

# ---- 2. Dataset table ----
old2 = (B + "caption{Datasets and evaluation units.}" + NL +
        B + "label{tab:datasets}" + NL +
        B + "begin{tabular}{lrrrr}" + NL +
        B + "toprule" + NL +
        "Dataset & Channels & Length & Mixed units & Var-level units " + B + B + " " + B + "midrule" + NL +
        "SWaT & 51 & 288k & 5 & 1 (AT) " + B + B + NL +
        "PSM & 25 & 220k & 4 & 0 " + B + B + NL +
        "SMAP & 25 & 563k & 5 & 0 " + B + B + NL +
        "SMD & 38 & 1.4M & 4 & 2 (AT, MIL) " + B + B + NL +
        "MetroPT3 & 15 & 3.0M & 5 & 0 " + B + B + NL +
        B + "bottomrule" + NL +
        B + "end{tabular}" + NL +
        B + "end{table}")
new2 = (B + "caption{Datasets and evaluation units per detector (mixed units; superscript" + NL +
        "$v$ marks native variable-level units of the deep detectors). Total: 54" + NL +
        "mixed + 4 variable-level = 58 units.}" + NL +
        B + "label{tab:datasets}" + NL +
        B + "begin{tabular}{lrrrrrrr}" + NL +
        B + "toprule" + NL +
        "Dataset & Channels & Length & iforest & PCA & OCSVM & AT & MIL " + B + B + " " + B + "midrule" + NL +
        "SWaT & 51 & 288k & 5 & 4 & 5 & $1^{v}$ & $1^{v}$ " + B + B + NL +
        "SMD & 38 & 1.4M & 4 & 5 & 6 & $1^{v}$ & $1^{v}$ " + B + B + NL +
        "MetroPT3 & 15 & 3.0M & 5 & -- & -- & -- & -- " + B + B + NL +
        "PSM & 25 & 220k & 4 & 4 & 7 & -- & -- " + B + B + NL +
        "SMAP & 25 & 563k & 5 & -- & -- & -- & -- " + B + B + NL +
        B + "bottomrule" + NL +
        B + "end{tabular}" + NL +
        B + "end{table}")
rep(old2, new2, "dataset table")

# ---- 3. Main comparison passage ----
old3 = ("Table~" + B + "ref{tab:main} reports layer-(i) macro-F1 and layer-(ii) top-1 on the" + NL +
        "58 evaluation units across five detectors. Because all 58 evaluation units across five detectors use the retrainable" + NL +
        "isolation-forest detector (mode-level units require retraining;" + NL +
        "Section~" + B + "ref{sec:limitations}), cause-typing conclusions are drawn on this" + NL +
        "family, while localization conclusions span all three families" + NL +
        "(Section~" + B + "ref{sec:matching}). Means carry bootstrap 95" + B + "% CIs computed by")
new3 = ("Table~" + B + "ref{tab:main} reports layer-(i) macro-F1 and layer-(ii) top-1 on the" + NL +
        "23 mixed units of the retrainable isolation-forest detector, the reference" + NL +
        "family of the protocol study (mixed cause ground truth requires retraining;" + NL +
        "Section~" + B + "ref{sec:limitations}); the detector-resolved view over all 58" + NL +
        "units and five detectors follows in Section~" + B + "ref{sec:matching}. Means carry bootstrap 95" + B + "% CIs computed by")
rep(old3, new3, "main passage scope")

# ---- 3b. narrative numbers in main passage ----
old3b = ("First, " + B + "emph{a calibrated rejection rule already reaches 0.64; mode-aware replacement lifts this to 0.70 (a modest increment, not a qualitative change)}")
new3b = ("First, " + B + "emph{a calibrated rejection rule already reaches 0.69; mode-aware replacement lifts this to 0.74 (a modest increment, not a qualitative change)}")
rep(old3b, new3b, "narrative first")

old3c = ("Second, " + B + "emph{AERec leads top-1 significantly} ($+0.30$ over GlobalCF," + NL +
         "CI $[0.15,0.43]$), confirming a deviation-reading advantage on injected")
new3c = ("Second, " + B + "emph{AERec leads top-1 significantly} ($+0.27$ over GlobalCF," + NL +
         "CI $[0.17,0.38]$), confirming a deviation-reading advantage on injected")
rep(old3c, new3c, "narrative second")

old3d = ("while adding neighbourhood conditioning (RC-CA)" + NL +
         "shifts performance toward localization (top-1 0.406 versus 0.384) at some" + NL +
         "cost to mode recall (0.73). Mode-aware replacement thus buys typing; local" + NL +
         "conditional expectations buy localization.")
new3d = ("while adding neighbourhood conditioning (RC-CA)" + NL +
         "preserves localization (top-1 0.480 versus 0.482) at a modest cost to" + NL +
         "typing (0.697) and mode recall (0.75). Mode-aware replacement thus buys" + NL +
         "typing; local conditional expectations keep localization intact while" + NL +
         "trading a little typing for it.")
rep(old3d, new3d, "narrative third")

# ---- 4. Granger fix ----
old4 = ("dynamics, which types causes well (L1 0.709, second only to AERec; mode recall" + NL +
        "0.94) yet fails to localize injected faults (top-1 0.000, below the random")
new4 = ("dynamics, which types causes adequately (L1 0.659 with 0.92 mode recall)" + NL +
        "yet fails to localize injected faults (top-1 0.045, below the random")
rep(old4, new4, "granger fix")

# ---- 5. MIL range ----
rep("counterfactuals reach" + NL + "0.54--0.95",
    "counterfactuals reach" + NL + "0.50--0.95", "MIL range")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n_applied, "edits re-applied")
