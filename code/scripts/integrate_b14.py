# -*- coding: utf-8 -*-
"""Integrate B1 (window decoupling) and B4 (compound stress test) into the paper."""
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
    print("B14:", tag)

# B1: window decoupling appended to the runtime paragraph
rep("roughly two orders of magnitude more per-window cost.",
    "roughly two orders of magnitude more per-window cost." + NL + NL +
    B + "textbf{Window-length decoupling.} Rebuilding the isolation-forest units" + NL +
    "end-to-end with window lengths 32 and 64 leaves the tree-ensemble pattern" + NL +
    "intact (AERec top-1 0.70/0.69 versus GlobalCF 0.50/0.59 on the rebuilt" + NL +
    "subsets, against 0.75/0.48 at the default length 16), so the reconstruction" + NL +
    "advantage on tree ensembles is not an artefact of the short window. The" + NL +
    "transformer half of the mirror symmetry cannot be tested at short windows" + NL +
    "(its native formulation requires length 100), so that side of the decoupling" + NL +
    "remains open.",
    "window decoupling")

# B4: compound stress test in the limitations single-cause sentence
rep("compound" + NL +
    "causes (simultaneous sensor degradation and an unseen mode) are outside the current" + NL +
    "single-cause construction, and real false alarms may additionally involve" + NL +
    "multivariate micro-shifts, concept drift, or detector overfitting that our" + NL +
    "injections do not cover.",
    "compound" + NL +
    "causes (simultaneous sensor degradation and an unseen mode) are outside the current" + NL +
    "single-cause construction. A stress test with three-channel correlated" + NL +
    "covariance shifts (strength $2" + B + "sigma$) confirms this boundary empirically:" + NL +
    "all families degrade (pooled top-1 AERec 0.50, RC-CA 0.24, GlobalCF 0.21," + NL +
    "against a $3/d$ chance level of about 0.12), so compound micro-shifts are a" + NL +
    "genuine open problem rather than a hypothetical one. Real false alarms may" + NL +
    "additionally involve concept drift or detector overfitting that our injections" + NL +
    "do not cover.",
    "compound stress test")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "B1+B4 integrations applied")
