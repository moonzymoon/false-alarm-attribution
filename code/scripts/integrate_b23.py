# -*- coding: utf-8 -*-
"""Integrate B2 (CondAttr K-tuning) and B3 (runtime) into the paper."""
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
    print("B:", tag)

# B2: CondAttr K-insensitivity in ablations
rep("neighbourhood size (top-1 0.49--0.50 for" + NL +
    "$k" + B + "in" + B + "{1,3,5,10" + B + "}$) and random seeds (L1 s.d." + B + " $" + B + "le$0.012).",
    "neighbourhood size (top-1 0.49--0.50 for" + NL +
    "$k" + B + "in" + B + "{1,3,5,10" + B + "}$) and random seeds (L1 s.d." + B + " $" + B + "le$0.012)." + NL +
    "CondAttr is likewise insensitive to its own neighbourhood size (pooled top-1" + NL +
    "0.529/0.529/0.538 for $K{=}3/5/10$ across the 23 mixed units), so its position in" + NL +
    "the comparison is not an artefact of an untuned $K$.",
    "condattr K tuning")

# B3: runtime paragraph at the end of ablations (before the repair subsection)
rep(B + "subsection{Repair loop}" + B + "label{sec:repair}",
    B + "textbf{Runtime.} Replacement-based attribution costs one scorer call per" + NL +
    "channel: on SWaT ($d{=}51$) GlobalCF takes about 1.1 ms per window and RC-CA" + NL +
    "4.2 ms, against roughly 0.02 ms for AERec's single reconstruction pass and 0.7 ms" + NL +
    "for Granger (zDev's 1.5--7.0 ms is dominated by pool-statistic recomputation and" + NL +
    "amortizes once cached). The detector-matched choice thus carries a real cost" + NL +
    "asymmetry: on tree ensembles the winning method (AERec) is also the cheapest," + NL +
    "whereas on smooth detectors the counterfactual premium buys 0.2--0.7 top-1 at" + NL +
    "roughly two orders of magnitude more per-window cost." + NL + NL +
    B + "subsection{Repair loop}" + B + "label{sec:repair}",
    "runtime paragraph")

io.open(P, "w", encoding="utf-8", newline=NL).write(s)
print(n, "B2+B3 integrations applied")
