# -*- coding: utf-8 -*-
"""DeepSeek round-2 fixes, batch R2: claims scoping, definitions, descriptions."""
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
    print("R2:", tag)

# R2-1 (#1/#2) abstract typing claim scoping
rep("cause typing is largely solved" + NL +
    "by calibrated rejection (macro-F1 0.69--0.74), redirecting effort to",
    "cause typing on injected ground truth is largely solved" + NL +
    "by the calibrated confidence gate alone (macro-F1 0.69--0.74; 0.83 with the" + NL +
    "learned reader), redirecting effort to",
    "abstract typing scope")

# R2-2 (#3) abstract transformer single-pairing flag
rep("replacement is near-perfect on a transformer/SWaT pairing (top-1 0.93)",
    "replacement is near-perfect on a transformer/SWaT pairing (top-1 0.93;" + NL +
    "single-pairing evidence)",
    "abstract transformer flag")

# R2-3 (#1) intro finding 3 scoping
rep("A calibrated rejection rule reaches macro-F1 0.69--0.74 across" + NL +
    "counterfactual methods on cause typing, but the calibration data come from" + NL +
    "the injected validation",
    "A calibrated confidence gate alone reaches macro-F1 0.69--0.74 across" + NL +
    "counterfactual methods on injected cause typing (0.83 with the learned reader;" + NL +
    "natural-alarm typing remains open), but the calibration data come from" + NL +
    "the injected validation",
    "intro finding3 scope")

# R2-4 (#4) DAAS label-free -> at deployment
rep("so we present the rules as a consistent label-free" + NL +
    "heuristic that is never worse",
    "so we present the rules as a deployment-time label-free heuristic (the" + NL +
    "historical detector--data-set performance records it needs are supplied" + NL +
    "offline by the protocol, not from the target windows) that is never worse",
    "daas label-free scope")

# R2-5 (#6) Granger negation wording
rep("score would not help either, since that would promote a trivially high-ranked" + NL +
    "normal channel rather than the faulted one.",
    "score would not help either: negation simply promotes some arbitrary" + NL +
    "low-influence channel, typically a quiet normal one, rather than the faulted" + NL +
    "channel, whose influence is low but not uniquely lowest.",
    "granger negation wording")

# insert after the mode-selection sentence instead
rep("Modes are selected by a pre-registered rule ($" + B + "ge$200 test windows",
    "The GMM defining the partition is fit transductively on the full series:" + NL +
    "no cause labels are used, and the detector never trains on the held-out" + NL +
    "cluster's windows, so the holdout logic is unaffected by where the GMM was" + NL +
    "fit; the partition itself is cluster-label-arbitrary and only moderately" + NL +
    "stable to the fitting set (train-only refits give adjusted Rand indices" + NL +
    "0.04--0.96 across testbeds), which is why mode-level claims rest on the" + NL +
    "operational holdout-and-repair logic rather than on partition identity." + NL +
    "Modes are selected by a pre-registered rule ($" + B + "ge$200 test windows",
    "gmm transductive statement")

# R2-7 (#10) regimes operational validity
rep("so as not to over-claim interpretability.",
    "so as not to over-claim interpretability; the protocol's mode-level claims" + NL +
    "are operational (holdout plus repair-validated) and do not depend on the" + NL +
    "clusters having physical semantics.",
    "regimes operational")

# R2-8 (#12) competitive vs positive definition
rep("whereas on smooth detectors the counterfactual premium is positive on eight of" + NL +
    "the twelve detector--data-set pairs (up to +0.89 on the transformer/SWaT",
    "whereas on smooth detectors the counterfactual premium over AERec is" + NL +
    "strictly positive on eight of the twelve detector--data-set pairs and a" + NL +
    "near-tie on the rest (up to +0.89 on the transformer/SWaT",
    "premium definition")

# R2-9 (#13) appendix replacement-scope
rep("the score drop" + NL +
    "of replacing channel $j$ with reference trajectory $u_j$ satisfies",
    "the score drop" + NL +
    "of replacing channel $j$ (and only channel $j$, in the notation of" + NL +
    "Section~" + B + "ref{sec:methods}) with reference trajectory $u_j$ satisfies",
    "appendix scope")

# R2-10 (#14) Granger t range
rep("is the resulting increase in the other channels'" + NL +
    "prediction errors on the query window",
    "is the resulting increase in the other channels'" + NL +
    "prediction errors over the query window's time steps",
    "granger t range")

# R2-11 (#15) kappa<0 note
rep("Granger's importances may be negative and enter the ratio unclipped, so its $" + B + "kappa$" + NL +
    "can fall outside $[0,1]$;",
    "Granger's importances may be negative and enter the ratio unclipped, and" + NL +
    "score-drop methods can likewise yield $" + B + "kappa<0$ when every replacement raises the" + NL +
    "score; in both cases the calibrated $" + B + "gamma$ absorbs the scale,",
    "kappa negative note")

# R2-12 (#16) gamma/delta unit-local
rep("low-confidence variable-level verdict to the mode hypothesis; no method abstains.",
    "low-confidence variable-level verdict to the mode hypothesis; no method abstains." + NL +
    "Both $" + B + "gamma$ and $" + B + "delta$ are unit-local quantities, recalibrated per unit on" + NL +
    "its validation split; no cross-unit comparison of their raw values is made anywhere.",
    "gamma unit-local")

# R2-13 (#17) repair temporal ordering
rep("Mode-directed addition" + NL +
    "reduces FAR by 22.1",
    "The repair stage simulates a second deployment round: train (mode absent)," + NL +
    "detect alarms, collect a sample of the current mode, retrain, re-evaluate." + NL +
    "Mode-directed addition" + NL +
    "reduces FAR by 22.1",
    "repair ordering")

# R2-14 (#24) A4 sample size and counts
rep("fraction of consecutive offset steps (pooled over probe windows) whose score" + NL +
    "does not decrease in $o$",
    "fraction of consecutive offset steps (150 probe windows, 8 offset steps" + NL +
    "each) whose score does not decrease in $o$",
    "a4 sample size")

# R2-15 (#25) hierarchical bootstrap description
rep("A two-level (unit-then-window) hierarchical bootstrap gives pooled top-1 95" + B + "% CIs",
    "A two-level hierarchical bootstrap (units resampled with replacement, their" + NL +
    "test windows pooled proportionally to unit size, windows then resampled with" + NL +
    "replacement at the pooled size; percentile CIs, $B{=}2000$, no bias correction)" + NL +
    "gives pooled top-1 95" + B + "% CIs",
    "hier bootstrap description")

# R2-16 (#29) two orders -> 50-200x
rep("at roughly two orders of" + NL +
    "magnitude more per-window cost.",
    "at 50--200 times more per-window cost.",
    "runtime multiplier")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in R2")
