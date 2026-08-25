# -*- coding: utf-8 -*-
"""DeepSeek-feedback fixes, batch 2: results/discussion/limitations/appendix."""
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
    print("DS2:", tag)

# DS2-1 (#8/#30) Granger vs Random baseline, joint-drift-aware
rep("yet fails to localize injected faults (top-1 0.045, below the random baseline of" + NL +
    "1/d).",
    "yet fails to localize injected faults (top-1 0.045, at the Random control level:" + NL +
    "0.053 observed, versus a uniform-guess expectation of $1/d$ for single-channel and" + NL +
    "$2/d$ for joint two-channel ground truths, averaging about $1.35/d$ because roughly" + NL +
    "a third of variable-type instances are joint injections).",
    "granger random baseline")

# DS2-2 (#13) RegimeGlobal referent
rep("First, " + B + "emph{a calibrated rejection rule already reaches 0.69; mode-aware replacement lifts this to 0.74",
    "First, " + B + "emph{a calibrated rejection rule already reaches 0.69; mode-aware replacement (RegimeGlobal) lifts this to 0.74",
    "regimeglobal referent")

# DS2-3 (#15) paired bootstrap citation
rep("differences have CIs covering zero, and all clearly exceed Random (0.474).",
    "differences have CIs covering zero (paired bootstrap, Supplementary Table~S3), and" + NL +
    "all clearly exceed Random (0.474).",
    "paired ci citation")

# DS2-4 (#14) pooled AT column note
rep("while AERec collapses to" + NL +
    "0.04 [0.01, 0.07];",
    "while AERec collapses to" + NL +
    "0.04 [0.01, 0.07]; the pooled AT column of Table~" + B + "ref{tab:detector} averages this" + NL +
    "SWaT unit with the weaker AT/SMD pairing;",
    "pooled AT note")

# DS2-5 (#10/#35) AT/SMD qualification
rep("single unit (the AT/SMD stream yields too few injection-caused alarms to" + NL +
    "qualify), so we treat its direction as suggestive:",
    "single unit (the AT/SMD stream yields too few injection-caused alarms for a mixed" + NL +
    "unit and enters the study as a native variable-level unit instead), so we treat" + NL +
    "its direction as suggestive:",
    "at/smd qualification")

# DS2-6 (#31) margin comparability caveat
rep("the qualitative picture is stable at 10" + B + "% and 50" + B + "%" + NL +
    "cuts, Supplementary Table~S14) ",
    "the qualitative picture is stable at 10" + B + "% and 50" + B + "%" + NL +
    "cuts, Supplementary Table~S14; margins are threshold-normalized per unit and the" + NL +
    "stratification is read within-detector, since score scales still differ across" + NL +
    "testbeds) ",
    "margin caveat")

# DS2-7 (#9) beta range note
rep("and the attribution-versus-injection-strength curves (Fig.~" + B + "ref{fig:beta})",
    "and the attribution-versus-injection-strength curves (Fig.~" + B + "ref{fig:beta};" + NL +
    "$" + B + "beta" + B + "in" + B + "{0.05,0.1,0.2,0.4" + B + "}$, extending beyond the protocol range)",
    "beta range note")

# DS2-8 (#17) natural tallies hedge
rep("compressor-duty quantities on MetroPT3.",
    "compressor-duty quantities on MetroPT3; these tallies are descriptive, as natural" + NL +
    "alarms carry no cause ground truth.",
    "natural tallies hedge")

# DS2-9 (#19) MMD implementation details
rep("MetroPT3 (MMD 0.03--0.06) but more for SMD (0.23).",
    "MetroPT3 (RBF-kernel MMD with median-heuristic" + NL +
    "bandwidth, 400-window subsamples: 0.03--0.06) but more for SMD (0.23).",
    "mmd details")

# DS2-10 (#18) A1 bounds -> entangles
rep("so" + NL +
    "the result bounds sensitivity to both) moves scores",
    "so" + NL +
    "the probe entangles both rather than bounding them separately) moves scores",
    "a1 bounds wording")

# DS2-11 (#29) A4 step definition
rep("fraction of probe windows whose score is non-decreasing in $o$",
    "fraction of consecutive offset steps (pooled over probe windows) whose score" + NL +
    "does not decrease in $o$",
    "a4 step definition")

# DS2-12 (#20) GT-correction propagation
rep("because the mode-conditioned expectation differs" + NL +
    "from the exact pre-injection values and correlated channels may retain" + NL +
    "elevated scores)",
    "because the mode-conditioned expectation differs" + NL +
    "from the exact pre-injection values and the injected deviation may propagate to" + NL +
    "correlated neighbours that retain elevated scores)",
    "gt propagation")

# DS2-13 (#2) single-cause limitation
rep("First, injected faults are" + NL +
    "structured single-channel deviations, and real false alarms may involve" + NL +
    "multivariate micro-shifts, concept drift, or detector overfitting that our" + NL +
    "injections do not cover.",
    "First, injected faults are" + NL +
    "structured single- or two-channel deviations with one dominant cause; compound" + NL +
    "causes (simultaneous sensor degradation and an unseen mode) are outside the current" + NL +
    "single-cause construction, and real false alarms may additionally involve" + NL +
    "multivariate micro-shifts, concept drift, or detector overfitting that our" + NL +
    "injections do not cover.",
    "single-cause limitation")

# DS2-14 (#21/#22) Proposition -> first-order account
prop_start = s.index(B + "section*{Appendix: Matching Sensitivity Condition}")
prop_end = s.index(B + "section*{Declarations}")
old_block = s[prop_start:prop_end]
new_block = (B + "section*{Appendix: A First-Order View of Replacement Attribution}" + NL + NL +
    "By a first-order expansion of the scorer around the alarm window, the score drop" + NL +
    "of replacing channel $j$ with reference trajectory $u_j$ satisfies" + NL +
    "$" + B + "phi_j = s(w)-s(w_{[j" + B + "leftarrow u_j]}) " + B + "approx -" + B + "nabla_{x_j} f(w)^{" + B + "top}(u_j - x_j)$:" + NL +
    "the product of the local score sensitivity along channel $j$ and the alignment" + NL +
    "between the replacement direction and that sensitivity. Two implications follow." + NL +
    "First, the sign of $" + B + "phi_j$ depends on this alignment, not on the magnitude of the" + NL +
    "sensitivity alone, so a large deviation on a channel the scorer ignores yields no" + NL +
    "attribution signal. Second, when sensitivities are comparable across channels, the" + NL +
    "ranking induced by $" + B + "phi_j$ is driven by deviation magnitude: scorers with localized," + NL +
    "non-saturating response surfaces (the transformer in our study) separate the" + NL +
    "injected channel sharply, while saturating scorers (the flattened tree ensemble)" + NL +
    "compress score drops and favour deviation readers instead. This is an informal" + NL +
    "first-order account of the empirical matching pattern, not a theorem: it ignores" + NL +
    "cross-channel coupling in the replacement and higher-order terms." + NL + NL)
s = s[:prop_start] + new_block + s[prop_end:]
n += 1
print("DS2: proposition -> first-order account")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in DS batch 2")
