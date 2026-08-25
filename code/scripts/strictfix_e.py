# -*- coding: utf-8 -*-
"""Round-4 fixes: DAAS statistical honesty + abstract word budget."""
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
    print("E:", tag)

# E1. DAAS CI caveat (pre-empt worst-case reviewer attack on n=15 power)
rep("Detector-aware selection is thus consistently the strongest label-free" + NL +
    "strategy available, and the residual gap to perfect selection reiterates" + NL +
    "that the matching relation is detector--data-set specific rather than" + NL +
    "detector-generic.",
    "At $n{=}15$ these proportions carry wide binomial uncertainty (95" + B + "% CIs" + NL +
    "overlap: $[0.25,0.70]$ versus $[0.15,0.58]$ strict, $[0.48,0.89]$ versus" + NL +
    "$[0.30,0.75]$ tolerant), so we present the rules as a consistent label-free" + NL +
    "heuristic that is never worse than the best fixed method across both" + NL +
    "granularities, not as a statistically significant improvement; the residual" + NL +
    "gap to perfect selection reiterates that the matching relation is" + NL +
    "detector--data-set specific rather than detector-generic.",
    "DAAS CI caveat")

# E2. soften contribution 5
rep("(5)~DAAS, a detector-aware selection rule that outperforms any single method.",
    "(5)~DAAS, a detector-aware selection rule that matches or outperforms any" + NL +
    "single fixed method.",
    "contribution 5 softening")

# E3. abstract word budget back to 200
rep("by calibrated rejection (macro-F1 0.69--0.74 across counterfactual" + NL +
    "methods), redirecting effort to",
    "by calibrated rejection (macro-F1 0.69--0.74), redirecting effort to",
    "abstract trim")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in batch E")
