# -*- coding: utf-8 -*-
"""Round-2 fixes: verified-number corrections (margin strat, 8/11->9/11, typing range)."""
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
    print("C:", tag)

# C1. abstract typing range
rep("cause typing is largely solved" + NL +
    "by calibrated rejection (macro-F1 0.64--0.79), redirecting effort to",
    "cause typing is largely solved" + NL +
    "by calibrated rejection (macro-F1 0.69--0.74 across counterfactual" + NL +
    "methods), redirecting effort to",
    "abstract typing range")

# C2. intro finding 3 typing range
rep("A calibrated rejection rule reaches macro-F1 0.64--0.79 on" + NL +
    "cause typing, but the calibration data come from the injected validation",
    "A calibrated rejection rule reaches macro-F1 0.69--0.74 across" + NL +
    "counterfactual methods on cause typing, but the calibration data come from" + NL +
    "the injected validation",
    "intro typing range")

# C3. margin stratification numbers (cache-verified)
rep("shows AERec's top-1 advantage persists for weak" + NL +
    "injections (0.66 versus 0.37--0.42 for the counterfactual family) and" + NL +
    "widens for strong ones (0.76 versus 0.53--0.71). The advantage is therefore",
    "shows AERec's top-1 advantage persists for weak" + NL +
    "injections (0.74 versus 0.32--0.41 for the counterfactual family on the 10" + NL +
    "units with weak-margin instances) and remains large for strong ones (1.00" + NL +
    "versus 0.53--0.78 on the 4 units with strong-margin instances). The advantage is therefore",
    "margin numbers")

# C4. fig_margin caption
rep(B + "caption{Margin stratification of variable-type top-1 accuracy: the" + NL +
    "reconstruction reader's advantage persists for weak alarms but narrows," + NL +
    "quantifying the injection-protocol preference for deviation readers.}",
    B + "caption{Margin stratification of variable-type top-1 accuracy: the" + NL +
    "reconstruction reader's advantage persists across weak- and strong-margin" + NL +
    "alarms, quantifying the injection-protocol preference for deviation readers.}",
    "margin caption")

# C5. 8/11 -> 9/11 (three places)
rep("Mode-directed data" + NL +
    "addition outperforms a random control by 22.1 pp (positive in 8 of 11 units" + NL +
    "with repair headroom)",
    "mode-directed data" + NL +
    "addition outperforms a random control by 22.1 pp (positive in 9 of 11 units" + NL +
    "with repair headroom)",
    "intro 9/11")
rep("(28.2" + B + "pp{}" + NL +
    "across the 11 units whose base FAR exceeds 10" + B + "%, with 8/11 positive)",
    "(28.2" + B + "pp{}" + NL +
    "across the 11 units whose base FAR exceeds 10" + B + "%, with 9/11 positive)",
    "repair 9/11 (a)")
rep("conditional, positive in 8 of the 11 units with non-trivial base FAR",
    "conditional, positive in 9 of the 11 units with non-trivial base FAR",
    "repair 9/11 (b)")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "fixes in batch C")
