# -*- coding: utf-8 -*-
"""Re-apply tab:main rebuild and DAAS honest rewrite."""
import io

B = chr(92)
NL = chr(10)
P = r"D:\0科研\工作1\第10篇SCI\paper\IDA_SAGE_FalseAlarmAttribution.tex"
s = io.open(P, encoding="utf-8").read()

# ---- tab:main ----
old = (B + "caption{Main results on 58 evaluation units across five detectors (mean over units, bootstrap 95" + B + "% CI" + NL +
       "in brackets; $B{=}2000$). L1 = cause-typing macro-F1; top-1/top-3 on the" + NL +
       "variable-type subset; var-R/reg-R = class recalls.}" + NL +
       B + "label{tab:main}" + NL +
       B + "begin{tabular}{lccccc}" + NL +
       B + "toprule" + NL +
       "Method & L1 & top-1 & top-3 & var-R & reg-R " + B + B + NL +
       B + "midrule" + NL +
       "RC-CA        & 0.678 [0.600, 0.748] & 0.406 [0.289, 0.528] & 0.769 & 0.70 & 0.73 " + B + B + NL +
       "GlobalCF     & 0.643 [0.574, 0.720] & 0.377 [0.265, 0.501] & 0.675 & 0.49 & 0.84 " + B + B + NL +
       "RegimeGlobal & 0.695 [0.637, 0.761] & 0.384 [0.269, 0.504] & 0.746 & 0.54 & 0.87 " + B + B + NL +
       "CondAttr     & 0.678 [0.612, 0.743] & 0.454 [0.354, 0.557] & 0.709 & 0.56 & 0.85 " + B + B + NL +
       "AERec        & 0.765 [0.663, 0.858] & " + B + "textbf{0.680} [0.586, 0.768] & " + B + "textbf{0.815} & 0.60 & 0.92 " + B + B + NL +
       "Granger      & 0.709 [0.625, 0.795] & 0.000 [$<$0.002] & 0.029 & 0.49 & " + B + "textbf{0.94} " + B + B + NL +
       "zDev         & 0.622 [0.525, 0.719] & 0.159 [0.091, 0.239] & 0.331 & 0.51 & 0.72 " + B + B + NL +
       "Random       & 0.467 [0.446, 0.486] & 0.048 [0.030, 0.068] & 0.139 & 0.28 & 0.70 " + B + B + NL +
       B + "bottomrule" + NL +
       B + "end{tabular}" + NL +
       B + "end{table}")
new = (B + "caption{Main results on the 23 isolation-forest mixed units (the" + NL +
       "retrainable reference family; mean over units, bootstrap 95" + B + "% CI in" + NL +
       "brackets; $B{=}2000$). L1 = cause-typing macro-F1; top-1/top-3 on the" + NL +
       "variable-type subset; var-R/reg-R = class recalls. Detector-resolved" + NL +
       "pooling over all 58 units follows in Table~" + B + "ref{tab:detector}.}" + NL +
       B + "label{tab:main}" + NL +
       B + "begin{tabular}{lccccc}" + NL +
       B + "toprule" + NL +
       "Method & L1 & top-1 & top-3 & var-R & reg-R " + B + B + NL +
       B + "midrule" + NL +
       "RC-CA        & 0.697 [0.643, 0.742] & 0.480 [0.359, 0.598] & 0.795 & 0.73 & 0.75 " + B + B + NL +
       "GlobalCF     & 0.693 [0.635, 0.745] & 0.484 [0.357, 0.610] & 0.748 & 0.58 & 0.85 " + B + B + NL +
       "RegimeGlobal & 0.739 [0.689, 0.787] & 0.482 [0.356, 0.603] & 0.789 & 0.64 & 0.87 " + B + B + NL +
       "CondAttr     & 0.692 [0.640, 0.738] & 0.529 [0.425, 0.629] & 0.771 & 0.60 & 0.83 " + B + B + NL +
       "AERec        & " + B + "textbf{0.828} [0.752, 0.894] & " + B + "textbf{0.754} [0.672, 0.828] & " + B + "textbf{0.876} & 0.70 & " + B + "textbf{0.95} " + B + B + NL +
       "Granger      & 0.659 [0.591, 0.731] & 0.045 [0.004, 0.096] & 0.071 & 0.42 & 0.92 " + B + B + NL +
       "zDev         & 0.712 [0.623, 0.796] & 0.424 [0.279, 0.572] & 0.632 & 0.53 & 0.89 " + B + B + NL +
       "Random       & 0.474 [0.459, 0.488] & 0.053 [0.040, 0.067] & 0.145 & 0.28 & 0.70 " + B + B + NL +
       B + "bottomrule" + NL +
       B + "end{tabular}" + NL +
       B + "end{table}")
assert old in s, "tab:main not found"
s = s.replace(old, new)
print("tab:main rebuilt")

# ---- DAAS ----
old_d = ("where $" + B + "mathcal{M}$ is the set of methods and $" + B + "mathcal{D}_d$ the" + NL +
         "training data sets for detector $d$. Under leave-one-out cross-validation," + NL +
         "DAAS achieves 82" + B + "% of held-out pairs (vs." + B + NL +
         "11" + B + "% for random and 41" + B + "% for always choosing AERec)---imperfect" + NL +
         "but consistently better than any single-method strategy.")
new_d = ("where $" + B + "mathcal{M}$ is the set of methods and $" + B + "mathcal{D}_d$ the" + NL +
         "training data sets for detector $d$. We also evaluate a family-level" + NL +
         "variant that assigns the reconstruction reader to discrete tree ensembles" + NL +
         "and the best-performing counterfactual method to smooth detectors, which" + NL +
         "is the smoothness-matching rule stated above. Under leave-one-out" + NL +
         "cross-validation over the 15 detector--data-set pairs of the matching" + NL +
         "study, DAAS recovers the exactly-best method in 6 of 15 held-out pairs" + NL +
         "(40" + B + "%) and the family-level rule in 7 of 15 (47" + B + "%), ahead of the best" + NL +
         "fixed strategy (always-AERec or always-RC-CA, 5 of 15, 33" + B + "%) and the" + NL +
         "random baseline (11" + B + "%). Because several pairs are near-ties, we also score" + NL +
         "predictions within 0.05 top-1 of the pair's best method: the family rule" + NL +
         "then covers 11 of 15 pairs (73" + B + "%) versus 53" + B + "% for the best fixed method." + NL +
         "Detector-aware selection is thus consistently the strongest label-free" + NL +
         "strategy available, and the residual gap to perfect selection reiterates" + NL +
         "that the matching relation is detector--data-set specific rather than" + NL +
         "detector-generic.")
assert old_d in s, "DAAS not found"
s = s.replace(old_d, new_d)
print("DAAS rewritten")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print("done")
