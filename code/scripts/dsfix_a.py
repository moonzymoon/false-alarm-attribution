# -*- coding: utf-8 -*-
"""DeepSeek-feedback fixes, batch 1: protocol & methods (factual/math corrections)."""
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
    print("DS1:", tag)

# DS1-1 (#1) contributions count
rep("(3)~The method--detector matching study across seven" + NL +
    "non-trivial attribution families (plus two control baselines), five detectors and five testbeds, with bootstrap confidence",
    "(3)~The method--detector matching study across eight" + NL +
    "non-trivial attribution families (plus a random control), five detectors and five testbeds, with bootstrap confidence",
    "contributions count 8+1")

# DS1-2 (#5) suppression hedge
rep("alarms; they do not explain an individual alarm.",
    "alarms; with few exceptions they do not explain an individual alarm.",
    "suppression hedge")

# DS1-3 (#3) interlock scope in formulation
rep("process-benign; the required action is sensor maintenance rather than process" + NL +
    "intervention, the situation that alarm-management rationalization targets",
    "process-benign; the required action is sensor maintenance rather than process" + NL +
    "intervention. We restrict scope to sensor faults that do not trigger process-level" + NL +
    "safety interlocks (extreme failures that propagate are process anomalies outside" + NL +
    "this definition), which is the situation alarm-management rationalization targets",
    "interlock scope")

# DS1-4 (#26) mode identity clarification
rep("Predicting the " + B + "emph{identity} of an unseen mode is outside the" + NL +
    "task (Section~" + B + "ref{sec:protocol} explains why this is not well-posed).",
    "In operation the mode-level output is the generic verdict " + B + "texttt{mode}: the" + NL +
    "held-out identity is known to the protocol but never predicted, and the $k$ in the" + NL +
    "display merely indexes the cause family. Predicting the " + B + "emph{identity} of an" + NL +
    "unseen mode is outside the task (Section~" + B + "ref{sec:protocol} explains why this" + NL +
    "is not well-posed).",
    "mode identity clarification")

# DS1-5 restore joint drift in protocol + classical-stream note
rep("variance inflation" + NL + "$" + B + "times 5$) whose post-injection score exceeds",
    "variance inflation" + NL + "$" + B + "times 5$, and two-channel joint drift) whose post-injection score exceeds",
    "restore joint drift")

# DS1-6 (#6/#16) Delta=+infty correction and gate explanation
rep("For variable-only methods, $" + B + "Delta$ is undefined and the first condition reduces to" + NL +
    "$" + B + "kappa<" + B + "gamma$ (equivalent to setting $" + B + "Delta=-" + B + "infty$, so the mode condition is never satisfied).",
    "For variable-only methods, $" + B + "Delta$ is undefined and the rule reduces to a single" + NL +
    "gate: a window is typed mode-level exactly when $" + B + "kappa<" + B + "gamma$ (equivalently," + NL +
    "$" + B + "Delta=+" + B + "infty" + B + ", so the second condition is always satisfied). Variable-only" + NL +
    "methods therefore still issue mode verdicts on low-confidence windows; their" + NL +
    "non-zero mode recall in Table~" + B + "ref{tab:main} reflects this confidence gate, not" + NL +
    "an explicit mode model.",
    "Delta plus infinity")

# DS1-7 (#7/#24/#28/#4) confidence conventions rewrite (code-accurate)
rep("Confidence is defined uniformly as the share of the top-1 channel:" + NL +
    "$" + B + "kappa(w) = " + B + "phi_{j" + B + "ast}(w) / " + B + "sum_j " + B + "phi_j(w)$ where $j" + B + "ast = " + B + "arg" + B + "max_j " + B + "phi_j$; for score-drop methods (GlobalCF, RC-CA," + NL +
    "RegimeGlobal, CondAttr) the drops are first clipped at zero. This single definition makes the rejection rule $" + B + "kappa<" + B + "gamma$" + " comparable across methods. If all clipped scores sum to zero, $" + B + "kappa=0$.",
    "Confidence is a top-1 dominance measure, implemented in two normalizations." + NL +
    "Score-drop methods (GlobalCF, RC-CA, RegimeGlobal, CondAttr) use the largest" + NL +
    "single-channel drop relative to the alarm score, $" + B + "kappa(w)=" + B + "max_j" + B + "phi_j/(|" + B +
    "s(w)|+" + B + "epsilon)$; the remaining methods use the top channel's share of total" + NL +
    "importance, $" + B + "kappa(w)=" + B + "phi_{j" + B + "ast}(w)/(" + B + "sum_j" + B + "phi_j+" + B + "epsilon)$." + NL +
    "Granger's importances may be negative and enter the ratio unclipped, so its $" + B + "kappa$" + NL +
    "can fall outside $[0,1]$; the per-method $" + B + "gamma$ calibration absorbs this. Random" + NL +
    "uses $" + B + "kappa=" + B + "max_j" + B + "phi_j$, so its gate degenerates to a chance-level cut." + NL +
    "Throughout, a rejection threshold is such a confidence gate that routes a" + NL +
    "low-confidence variable-level verdict to the mode hypothesis; no method abstains.",
    "confidence conventions")

# DS1-8 (#25) tie-breaking
rep("$u" + B + "in" + B + "mathbb{R}^{|w|}$; all other channels and timestamps are unchanged.",
    "$u" + B + "in" + B + "mathbb{R}^{|w|}$; all other channels and timestamps are unchanged. Ties in $" + B + "arg" + B + "max$ are broken by the lowest channel index.",
    "argmax ties")

# DS1-9 (#34) RC-CA template definition
rep("within the" + NL +
    "predicted mode, the $k$-nearest normal windows ($k{=}5$) define a" + NL +
    "conditional-expectation template;",
    "within the" + NL +
    "predicted mode, the $k{=}5$ nearest normal windows are averaged into a single" + NL +
    "whole-window template (each channel is replaced by its own value in that" + NL +
    "template, preserving the template's cross-channel structure);",
    "rcca template")

# DS1-10 (#23) Delta direction
rep("$" + B + "Delta = s(w^{" + B + "mathrm{glob}})-s(w^{" + B + "mathrm{mode}})$" + NL +
    "(equivalently the difference of the two score drops) contrasts mode-aware" + NL +
    "and global full replacement;",
    "$" + B + "Delta = s(w^{" + B + "mathrm{glob}})-s(w^{" + B + "mathrm{mode}})$" + NL +
    "(equivalently, the mode-template drop minus the global-template drop) contrasts" + NL +
    "mode-aware and global full replacement;",
    "delta direction")

# DS1-11 (#33) UMAP stability note
rep("provide the replacement trajectory per channel " + B + "cite{mishra2026condattr}.",
    "provide the replacement trajectory per channel " + B + "cite{mishra2026condattr}. UMAP's out-of-sample transform is approximate and can be unstable for far queries, an additional variance source specific to our reimplementation.",
    "umap stability")

# DS1-12 (#12/#27) DAAS formal details
rep("where $" + B + "mathcal{M}$ is the set of methods and $" + B + "mathcal{D}_d$ the" + NL +
    "training data sets for detector $d$.",
    "where $" + B + "mathcal{M}$ is the set of methods applicable to $d$ (Grad is excluded for" + NL +
    "non-differentiable scorers), $" + B + "mathcal{D}_d$ comprises the data sets with units for" + NL +
    "detector $d$ minus the held-out one under leave-one-out, $" + B + "mathrm{top1}(m,d,ds)$ is" + NL +
    "the mean top-1 over that pair's units, and ties in the $" + B + "arg" + B + "max$ are broken by" + NL +
    "method order.",
    "daas formal details")

# DS1-13 (#11) DAAS scope qualifier
rep("not as a statistically significant improvement; the residual",
    "not as a statistically significant improvement. DAAS optimizes localization (top-1);" + NL +
    "extending the rule to typing- and repair-aware selection is left open. The residual",
    "daas scope")

# DS1-14 (#11) contribution 5 localization qualifier
rep("(5)~DAAS, a detector-aware selection rule that matches or outperforms any" + NL +
    "single fixed method.",
    "(5)~DAAS, a detector-aware selection rule that, for localization, matches or" + NL +
    "outperforms any single fixed method.",
    "contribution 5 scope")

# DS1-15 (#36) implementation details paragraph after Random
rep("maximum score (so the rejection rule degenerates to a random cut, as intended).",
    "maximum score (so the rejection rule degenerates to a random cut, as intended)." + NL + NL +
    B + "textbf{Implementation details.} The GMM operates on standardized window" + NL +
    "statistics reduced by PCA (95" + B + "% retained variance, whitened). The AERec" + NL +
    "autoencoder is a three-layer MLP (input$" + B + "to$128$" + B + "to$32$" + B + "to$input, ReLU)" + NL +
    "trained for 30 epochs with Adam ($10^{-3}$). The Granger ridge uses $" + B + "lambda=10^{-3}$" + NL +
    "with an unpenalized intercept. zDev uses a MAD floor of $" + B + "epsilon=10^{-9}$. The" + NL +
    "CondAttr UMAP embedding is 10-dimensional. Full per-unit configurations ship" + NL +
    "with the released code.",
    "implementation details")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in DS batch 1")
